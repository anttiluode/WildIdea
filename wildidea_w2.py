#!/usr/bin/env python3
"""WildIdea W2: adaptive three-probe system identification."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


N_SITES = 64
CANDIDATE_CENTERS = tuple(range(4, 64, 8))  # 4..60, eight classes
N_CLASSES = len(CANDIDATE_CENTERS)
RINGDOWN_STEPS = 14
DT = 0.08
C2 = 0.9
BACKGROUND_DAMPING = 0.10
BACKGROUND_STIFFNESS = 0.10
DEFECT_EXTRA_DAMPING = 0.35
DEFECT_SIGMA = 7.0
INITIAL_SIGMA = 0.01
AMBIENT_VELOCITY_NOISE = 0.003
PULSE_AMPLITUDE = 0.8
PROBE_BUDGET = 3

MODEL_SAMPLES_PER_CELL = 250
MODEL_SEED_START = 1_500_000
TEST_EPISODES = 1600
TEST_SEED_START = 2_500_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814
VARIANCE_FLOOR = 1e-4


def defect_profile(class_id: int) -> np.ndarray:
    center = CANDIDATE_CENTERS[class_id]
    idx = np.arange(N_SITES)
    direct = np.abs(idx - center)
    distance = np.minimum(direct, N_SITES - direct)
    return DEFECT_EXTRA_DAMPING * np.exp(
        -(distance.astype(float) ** 2) / (2.0 * DEFECT_SIGMA**2)
    )


def probe_receipt(class_id: int, seed: int, probe_index: int) -> float:
    """Standardized ping and local ring-down receipt."""
    if class_id not in range(N_CLASSES):
        raise ValueError("bad class_id")
    if probe_index not in range(N_CLASSES):
        raise ValueError("bad probe_index")

    rng = np.random.default_rng(seed)
    damping = np.full(N_SITES, BACKGROUND_DAMPING, dtype=float)
    damping += defect_profile(class_id)

    x = INITIAL_SIGMA * rng.normal(size=N_SITES)
    velocity = INITIAL_SIGMA * rng.normal(size=N_SITES)
    probe_site = CANDIDATE_CENTERS[probe_index]
    velocity[probe_site] += PULSE_AMPLITUDE

    local_trace = []
    for _ in range(RINGDOWN_STEPS):
        velocity += AMBIENT_VELOCITY_NOISE * rng.normal(size=N_SITES)
        laplacian = np.roll(x, 1) + np.roll(x, -1) - 2.0 * x
        acceleration = C2 * laplacian - BACKGROUND_STIFFNESS * x - damping * velocity
        velocity += DT * acceleration
        x += DT * velocity

        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 100.0:
            raise FloatingPointError("unstable W2 ring-down")

        local_trace.append(
            [
                x[(probe_site - 1) % N_SITES],
                x[probe_site],
                x[(probe_site + 1) % N_SITES],
            ]
        )

    trace = np.asarray(local_trace, dtype=float)
    early_energy = float(np.mean(trace[2:6] ** 2))
    late_energy = float(np.mean(trace[9:13] ** 2))
    return float(math.log((late_energy + 1e-8) / (early_energy + 1e-8)))


def response_seed(class_id: int, probe_index: int, sample_index: int) -> int:
    return MODEL_SEED_START + class_id * 1_000_000 + probe_index * 10_000 + sample_index


def learn_response_model() -> tuple[np.ndarray, np.ndarray]:
    means = np.zeros((N_CLASSES, N_CLASSES), dtype=float)
    class_variances = np.zeros((N_CLASSES, N_CLASSES), dtype=float)

    for class_id in range(N_CLASSES):
        for probe_index in range(N_CLASSES):
            values = np.asarray(
                [
                    probe_receipt(
                        class_id,
                        response_seed(class_id, probe_index, sample_index),
                        probe_index,
                    )
                    for sample_index in range(MODEL_SAMPLES_PER_CELL)
                ],
                dtype=float,
            )
            means[class_id, probe_index] = float(values.mean())
            class_variances[class_id, probe_index] = float(values.var(ddof=1))

    pooled_variance = np.maximum(class_variances.mean(axis=0), VARIANCE_FLOOR)
    return means, pooled_variance


def posterior_update(
    posterior: np.ndarray,
    receipt: float,
    probe_index: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
) -> np.ndarray:
    variance = pooled_variance[probe_index]
    log_likelihood = -0.5 * (
        ((receipt - means[:, probe_index]) ** 2) / variance + math.log(variance)
    )
    log_likelihood -= float(log_likelihood.max())
    updated = posterior * np.exp(log_likelihood)
    total = float(updated.sum())
    if total <= 0.0 or not math.isfinite(total):
        raise FloatingPointError("posterior normalization failed")
    return updated / total


def information_score(
    posterior: np.ndarray,
    probe_index: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
) -> float:
    predicted = means[:, probe_index]
    weighted_mean = float(np.sum(posterior * predicted))
    between_class_variance = float(
        np.sum(posterior * (predicted - weighted_mean) ** 2)
    )
    return between_class_variance / float(pooled_variance[probe_index])


def choose_adaptive_probe(
    posterior: np.ndarray,
    used: set[int],
    means: np.ndarray,
    pooled_variance: np.ndarray,
) -> int:
    candidates = [p for p in range(N_CLASSES) if p not in used]
    return max(
        candidates,
        key=lambda p: (information_score(posterior, p, means, pooled_variance), -p),
    )


def fixed_design_score(
    probes: Sequence[int], means: np.ndarray, pooled_variance: np.ndarray
) -> tuple[float, float]:
    distances = []
    for class_a, class_b in itertools.combinations(range(N_CLASSES), 2):
        distance = sum(
            (means[class_a, p] - means[class_b, p]) ** 2 / pooled_variance[p]
            for p in probes
        )
        distances.append(float(distance))
    return min(distances), float(np.mean(distances))


def choose_best_fixed_schedule(
    means: np.ndarray, pooled_variance: np.ndarray
) -> tuple[int, int, int]:
    schedules = list(itertools.combinations(range(N_CLASSES), PROBE_BUDGET))
    return max(
        schedules,
        key=lambda probes: fixed_design_score(probes, means, pooled_variance),
    )


def test_measurement_seed(episode_seed: int, round_index: int, probe_index: int) -> int:
    # Deterministic receipt noise keyed to episode, round and chosen address.
    return episode_seed + 1000 * round_index + 17 * probe_index


def infer_with_schedule(
    class_id: int,
    episode_seed: int,
    schedule: Sequence[int],
    means: np.ndarray,
    pooled_variance: np.ndarray,
) -> tuple[int, tuple[int, ...]]:
    posterior = np.full(N_CLASSES, 1.0 / N_CLASSES, dtype=float)
    used = []
    for round_index, probe_index in enumerate(schedule):
        receipt = probe_receipt(
            class_id,
            test_measurement_seed(episode_seed, round_index, probe_index),
            probe_index,
        )
        posterior = posterior_update(
            posterior, receipt, probe_index, means, pooled_variance
        )
        used.append(int(probe_index))
    return int(np.argmax(posterior)), tuple(used)


def infer_adaptive(
    class_id: int,
    episode_seed: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
) -> tuple[int, tuple[int, ...]]:
    posterior = np.full(N_CLASSES, 1.0 / N_CLASSES, dtype=float)
    used: set[int] = set()
    sequence = []

    for round_index in range(PROBE_BUDGET):
        if round_index == 0:
            probe_index = 0  # arbitrary under rotational symmetry
        else:
            probe_index = choose_adaptive_probe(
                posterior, used, means, pooled_variance
            )
        used.add(probe_index)
        sequence.append(probe_index)

        receipt = probe_receipt(
            class_id,
            test_measurement_seed(episode_seed, round_index, probe_index),
            probe_index,
        )
        posterior = posterior_update(
            posterior, receipt, probe_index, means, pooled_variance
        )

    return int(np.argmax(posterior)), tuple(sequence)


def paired_bootstrap_ci(adaptive_correct: np.ndarray, fixed_correct: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    paired = adaptive_correct.astype(float) - fixed_correct.astype(float)
    indices = rng.integers(
        0, len(paired), size=(BOOTSTRAP_SAMPLES, len(paired))
    )
    means = paired[indices].mean(axis=1)
    return [float(v) for v in np.quantile(means, [0.025, 0.975])]


def per_class_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> list[float]:
    return [
        float(np.mean(y_pred[y_true == class_id] == class_id))
        for class_id in range(N_CLASSES)
    ]


def run_benchmark() -> dict:
    means, pooled_variance = learn_response_model()
    fixed_schedule = choose_best_fixed_schedule(means, pooled_variance)

    y_true = []
    pred_fixed = []
    pred_random = []
    pred_adaptive = []
    adaptive_sequences: dict[tuple[int, ...], int] = {}
    random_sequences: dict[tuple[int, ...], int] = {}

    for episode_index in range(TEST_EPISODES):
        class_id = episode_index % N_CLASSES
        episode_seed = TEST_SEED_START + episode_index
        y_true.append(class_id)

        fixed_pred, _ = infer_with_schedule(
            class_id, episode_seed, fixed_schedule, means, pooled_variance
        )
        pred_fixed.append(fixed_pred)

        policy_rng = np.random.default_rng(episode_seed + 50_000_000)
        random_schedule = tuple(
            int(p)
            for p in policy_rng.choice(
                N_CLASSES, size=PROBE_BUDGET, replace=False
            )
        )
        random_pred, random_seq = infer_with_schedule(
            class_id, episode_seed, random_schedule, means, pooled_variance
        )
        pred_random.append(random_pred)
        random_sequences[random_seq] = random_sequences.get(random_seq, 0) + 1

        adaptive_pred, adaptive_seq = infer_adaptive(
            class_id, episode_seed, means, pooled_variance
        )
        pred_adaptive.append(adaptive_pred)
        adaptive_sequences[adaptive_seq] = adaptive_sequences.get(adaptive_seq, 0) + 1

    y_true = np.asarray(y_true, dtype=int)
    pred_fixed = np.asarray(pred_fixed, dtype=int)
    pred_random = np.asarray(pred_random, dtype=int)
    pred_adaptive = np.asarray(pred_adaptive, dtype=int)

    fixed_accuracy = float(np.mean(pred_fixed == y_true))
    random_accuracy = float(np.mean(pred_random == y_true))
    adaptive_accuracy = float(np.mean(pred_adaptive == y_true))
    adaptive_minus_fixed = adaptive_accuracy - fixed_accuracy
    adaptive_minus_random = adaptive_accuracy - random_accuracy
    ci = paired_bootstrap_ci(pred_adaptive == y_true, pred_fixed == y_true)
    adaptive_class_accuracy = per_class_accuracy(y_true, pred_adaptive)

    sequence_counts = sorted(
        [
            {"sequence": list(sequence), "count": count}
            for sequence, count in adaptive_sequences.items()
        ],
        key=lambda row: (-row["count"], row["sequence"]),
    )

    criteria = {
        "adaptive_accuracy_at_least_0_60": adaptive_accuracy >= 0.60,
        "adaptive_beats_fixed_by_0_03": adaptive_minus_fixed >= 0.03,
        "paired_bootstrap_ci_above_zero": ci[0] > 0.0,
        "adaptive_beats_random_by_0_05": adaptive_minus_random >= 0.05,
        "per_class_floor": min(adaptive_class_accuracy) >= 0.50,
        "adaptive_policy_branches": len(adaptive_sequences) >= 4,
        "fixed_three_write_budget": True,
    }
    passed = all(criteria.values())

    return {
        "gate": "W2_ADAPTIVE_PROBE_CHOICE",
        "verdict": (
            "ADAPTIVE_PROBING_EARNS_KEEP"
            if passed
            else "ADAPTIVE_PROBING_NOT_EARNED"
        ),
        "response_model": {
            "samples_per_class_probe": MODEL_SAMPLES_PER_CELL,
            "means": means.tolist(),
            "pooled_variance": pooled_variance.tolist(),
        },
        "fixed_schedule_probe_indices": list(fixed_schedule),
        "fixed_schedule_sites": [CANDIDATE_CENTERS[p] for p in fixed_schedule],
        "accuracy": {
            "fixed_3": fixed_accuracy,
            "random_3": random_accuracy,
            "adaptive_3": adaptive_accuracy,
        },
        "adaptive_minus_fixed": float(adaptive_minus_fixed),
        "adaptive_minus_random": float(adaptive_minus_random),
        "paired_bootstrap_95_ci_adaptive_minus_fixed": ci,
        "adaptive_per_class_accuracy": adaptive_class_accuracy,
        "adaptive_distinct_sequences": len(adaptive_sequences),
        "adaptive_sequence_counts": sequence_counts,
        "random_distinct_sequences": len(random_sequences),
        "criteria": criteria,
        "probe_budget": PROBE_BUDGET,
        "pulse_amplitude": PULSE_AMPLITUDE,
        "test_episodes": TEST_EPISODES,
        "test_seed_start": TEST_SEED_START,
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
