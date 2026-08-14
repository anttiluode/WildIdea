#!/usr/bin/env python3
"""WildIdea W4b: brute-force validation-selected fixed-policy adversary.

Frozen design: docs/PREREG_W4B_VALIDATED_FIXED.md
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

import wildidea_w4_nuisance as w4


VALIDATION_EPISODES = 3200
VALIDATION_SEED_START = 11_000_000
HOLDOUT_EPISODES = 2400
HOLDOUT_SEED_START = 15_000_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814


def quotient_projectors(means: np.ndarray) -> np.ndarray:
    """Return residual projectors for y ~= a*mu + b*1 + c*ramp."""
    identity = np.eye(w4.RECEIPT_DIM, dtype=float)
    projectors = np.zeros(
        (w4.N_CLASSES, w4.N_CLASSES, w4.RECEIPT_DIM, w4.RECEIPT_DIM),
        dtype=float,
    )
    for class_id in range(w4.N_CLASSES):
        for probe_index in range(w4.N_CLASSES):
            x = np.column_stack(
                [means[class_id, probe_index], w4.ONES, w4.RAMP]
            )
            projectors[class_id, probe_index] = identity - x @ np.linalg.pinv(x)
    return projectors


def precompute_quotient_loglikelihoods(
    *,
    episode_count: int,
    seed_start: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
    projectors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute all legal quotient receipts once for later policy comparison."""
    ll = np.zeros(
        (episode_count, w4.PROBE_BUDGET, w4.N_CLASSES, w4.N_CLASSES),
        dtype=float,
    )
    truth = np.arange(episode_count, dtype=int) % w4.N_CLASSES

    for episode_index in range(episode_count):
        class_id = int(truth[episode_index])
        episode_seed = int(seed_start + episode_index)
        for round_index in range(w4.PROBE_BUDGET):
            for probe_index in range(w4.N_CLASSES):
                y = w4.test_receipt(
                    class_id,
                    episode_seed,
                    round_index,
                    probe_index,
                )
                variance = float(pooled_variance[probe_index])
                losses = np.empty(w4.N_CLASSES, dtype=float)
                for candidate_class in range(w4.N_CLASSES):
                    residual = projectors[candidate_class, probe_index] @ y
                    losses[candidate_class] = float(
                        np.mean(residual * residual) / variance
                    )
                loglike = -0.5 * losses
                loglike -= float(loglike.max())
                ll[episode_index, round_index, probe_index] = loglike
    return ll, truth


def ordered_schedules() -> list[tuple[int, int, int]]:
    return list(itertools.permutations(range(w4.N_CLASSES), w4.PROBE_BUDGET))


def evaluate_fixed_schedule(
    loglike: np.ndarray,
    truth: np.ndarray,
    schedule: tuple[int, int, int],
) -> tuple[float, np.ndarray]:
    total = np.zeros((len(truth), w4.N_CLASSES), dtype=float)
    for round_index, probe_index in enumerate(schedule):
        total += loglike[:, round_index, probe_index, :]
    pred = np.argmax(total, axis=1)
    return float(np.mean(pred == truth)), pred.astype(int)


def select_best_fixed_schedule(
    loglike: np.ndarray,
    truth: np.ndarray,
) -> tuple[tuple[int, int, int], float, list[dict[str, object]]]:
    rows = []
    best_schedule: tuple[int, int, int] | None = None
    best_accuracy = -1.0
    for schedule in ordered_schedules():
        accuracy, _ = evaluate_fixed_schedule(loglike, truth, schedule)
        rows.append({"schedule": list(schedule), "accuracy": float(accuracy)})
        # itertools.permutations is lexicographic for range(8); strict > keeps
        # the earliest schedule when validation accuracy ties exactly.
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_schedule = schedule
    assert best_schedule is not None
    top = sorted(rows, key=lambda row: (-float(row["accuracy"]), row["schedule"]))[:10]
    return best_schedule, float(best_accuracy), top


def adaptive_predictions(
    loglike: np.ndarray,
    pair_distances: np.ndarray,
) -> tuple[np.ndarray, dict[tuple[int, ...], int]]:
    pred = np.zeros(loglike.shape[0], dtype=int)
    sequences: dict[tuple[int, ...], int] = {}
    for episode_index in range(loglike.shape[0]):
        posterior = np.full(w4.N_CLASSES, 1.0 / w4.N_CLASSES, dtype=float)
        used: set[int] = set()
        sequence = []
        for round_index in range(w4.PROBE_BUDGET):
            probe_index = w4.choose_adaptive_probe(
                posterior,
                used,
                pair_distances,
            )
            used.add(probe_index)
            sequence.append(int(probe_index))
            local_ll = loglike[episode_index, round_index, probe_index]
            local_ll = local_ll - float(local_ll.max())
            updated = posterior * np.exp(local_ll)
            posterior = updated / float(updated.sum())
        pred[episode_index] = int(np.argmax(posterior))
        key = tuple(sequence)
        sequences[key] = sequences.get(key, 0) + 1
    return pred, sequences


def paired_bootstrap_ci(a_correct: np.ndarray, b_correct: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    paired = a_correct.astype(float) - b_correct.astype(float)
    indices = rng.integers(0, len(paired), size=(BOOTSTRAP_SAMPLES, len(paired)))
    means = paired[indices].mean(axis=1)
    return [float(v) for v in np.quantile(means, [0.025, 0.975])]


def per_class_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> list[float]:
    return [
        float(np.mean(y_pred[y_true == class_id] == class_id))
        for class_id in range(w4.N_CLASSES)
    ]


def run_benchmark() -> dict:
    means, pooled_variance = w4.learn_response_model()
    _raw_pairs, quotient_pairs = w4.precompute_pair_distances(means, pooled_variance)
    projectors = quotient_projectors(means)

    validation_ll, validation_truth = precompute_quotient_loglikelihoods(
        episode_count=VALIDATION_EPISODES,
        seed_start=VALIDATION_SEED_START,
        means=means,
        pooled_variance=pooled_variance,
        projectors=projectors,
    )
    selected_schedule, validation_accuracy, validation_top10 = select_best_fixed_schedule(
        validation_ll,
        validation_truth,
    )

    holdout_ll, holdout_truth = precompute_quotient_loglikelihoods(
        episode_count=HOLDOUT_EPISODES,
        seed_start=HOLDOUT_SEED_START,
        means=means,
        pooled_variance=pooled_variance,
        projectors=projectors,
    )
    fixed_accuracy, fixed_pred = evaluate_fixed_schedule(
        holdout_ll,
        holdout_truth,
        selected_schedule,
    )
    adaptive_pred, adaptive_sequences = adaptive_predictions(
        holdout_ll,
        quotient_pairs,
    )
    adaptive_accuracy = float(np.mean(adaptive_pred == holdout_truth))
    difference = float(adaptive_accuracy - fixed_accuracy)
    ci = paired_bootstrap_ci(
        adaptive_pred == holdout_truth,
        fixed_pred == holdout_truth,
    )
    adaptive_class_accuracy = per_class_accuracy(holdout_truth, adaptive_pred)

    analytic_schedule = w4.choose_best_fixed_schedule(quotient_pairs)
    analytic_accuracy, _ = evaluate_fixed_schedule(
        holdout_ll,
        holdout_truth,
        analytic_schedule,
    )

    criteria = {
        "adaptive_beats_validated_fixed_by_0_01": difference >= 0.01,
        "paired_bootstrap_ci_above_zero": ci[0] > 0.0,
        "adaptive_accuracy_at_least_0_45": adaptive_accuracy >= 0.45,
        "adaptive_per_class_floor": min(adaptive_class_accuracy) >= 0.35,
        "fixed_three_write_budget": True,
    }
    if all(criteria.values()):
        verdict = "ADAPTIVE_QUERY_SURVIVES_VALIDATED_FIXED"
    elif difference > 0.0:
        verdict = "ADAPTIVE_QUERY_NOT_SEPARATED_FROM_VALIDATED_FIXED"
    else:
        verdict = "VALIDATED_FIXED_KILLS_ADAPTIVE_INCREMENT"

    sequence_counts = sorted(
        [
            {"sequence": list(sequence), "count": int(count)}
            for sequence, count in adaptive_sequences.items()
        ],
        key=lambda row: (-row["count"], row["sequence"]),
    )

    return {
        "gate": "W4B_VALIDATED_FIXED_ADVERSARY",
        "preregistration": "docs/PREREG_W4B_VALIDATED_FIXED.md",
        "verdict": verdict,
        "validation": {
            "episodes": VALIDATION_EPISODES,
            "seed_start": VALIDATION_SEED_START,
            "ordered_schedule_count": len(ordered_schedules()),
            "selected_schedule": list(selected_schedule),
            "selected_sites": [w4.CANDIDATE_CENTERS[p] for p in selected_schedule],
            "selected_accuracy": validation_accuracy,
            "top10_schedules": validation_top10,
        },
        "second_holdout": {
            "episodes": HOLDOUT_EPISODES,
            "seed_start": HOLDOUT_SEED_START,
            "validated_fixed_accuracy": fixed_accuracy,
            "adaptive_accuracy": adaptive_accuracy,
            "adaptive_minus_validated_fixed": difference,
            "paired_bootstrap_95_ci": ci,
            "adaptive_per_class_accuracy": adaptive_class_accuracy,
            "analytic_w4_fixed_schedule": list(analytic_schedule),
            "analytic_w4_fixed_accuracy": analytic_accuracy,
            "adaptive_distinct_sequences": len(adaptive_sequences),
            "adaptive_sequence_counts": sequence_counts,
        },
        "criteria": criteria,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = run_benchmark()
    text = json.dumps(result, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
