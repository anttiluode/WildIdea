#!/usr/bin/env python3
"""WildIdea W4: nuisance-quotiented disagreement-directed probing.

Frozen design: docs/PREREG_W4_NUISANCE_QUOTIENT.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Sequence

import numpy as np


N_SITES = 64
CANDIDATE_CENTERS = tuple(range(4, 64, 8))
N_CLASSES = len(CANDIDATE_CENTERS)
RINGDOWN_STEPS = 14
LOCAL_CHANNELS = 3
RECEIPT_DIM = RINGDOWN_STEPS * LOCAL_CHANNELS
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
TEST_EPISODES = 2400
TEST_SEED_START = 9_500_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814
VARIANCE_FLOOR = 1e-6

LOG_GAIN_SIGMA = 0.25
OFFSET_SIGMA = 0.04
SLOPE_SIGMA = 0.04

ONES = np.ones(RECEIPT_DIM, dtype=float)
RAMP = np.repeat(np.linspace(-1.0, 1.0, RINGDOWN_STEPS), LOCAL_CHANNELS)


def defect_profile(class_id: int) -> np.ndarray:
    center = CANDIDATE_CENTERS[class_id]
    idx = np.arange(N_SITES)
    direct = np.abs(idx - center)
    distance = np.minimum(direct, N_SITES - direct)
    return DEFECT_EXTRA_DAMPING * np.exp(
        -(distance.astype(float) ** 2) / (2.0 * DEFECT_SIGMA**2)
    )


def probe_receipt_vector(class_id: int, seed: int, probe_index: int) -> np.ndarray:
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
            raise FloatingPointError("unstable W4 ring-down")
        local_trace.append(
            [
                x[(probe_site - 1) % N_SITES],
                x[probe_site],
                x[(probe_site + 1) % N_SITES],
            ]
        )
    return np.asarray(local_trace, dtype=float).reshape(-1)


def response_seed(class_id: int, probe_index: int, sample_index: int) -> int:
    return MODEL_SEED_START + class_id * 1_000_000 + probe_index * 10_000 + sample_index


def learn_response_model() -> tuple[np.ndarray, np.ndarray]:
    means = np.zeros((N_CLASSES, N_CLASSES, RECEIPT_DIM), dtype=float)
    cell_feature_variances = np.zeros((N_CLASSES, N_CLASSES), dtype=float)
    for class_id in range(N_CLASSES):
        for probe_index in range(N_CLASSES):
            values = np.asarray(
                [
                    probe_receipt_vector(
                        class_id,
                        response_seed(class_id, probe_index, sample_index),
                        probe_index,
                    )
                    for sample_index in range(MODEL_SAMPLES_PER_CELL)
                ],
                dtype=float,
            )
            means[class_id, probe_index] = values.mean(axis=0)
            cell_feature_variances[class_id, probe_index] = float(
                np.mean(values.var(axis=0, ddof=1))
            )
    pooled_variance = np.maximum(cell_feature_variances.mean(axis=0), VARIANCE_FLOOR)
    return means, pooled_variance


def apply_measurement_nuisance(clean: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    gain = float(np.exp(rng.normal(0.0, LOG_GAIN_SIGMA)))
    offset = float(rng.normal(0.0, OFFSET_SIGMA))
    slope = float(rng.normal(0.0, SLOPE_SIGMA))
    return gain * np.asarray(clean, dtype=float) + offset * ONES + slope * RAMP


def test_measurement_seed(episode_seed: int, round_index: int, probe_index: int) -> int:
    return episode_seed + 1000 * round_index + 17 * probe_index


def nuisance_seed(episode_seed: int, round_index: int, probe_index: int) -> int:
    return episode_seed + 70_000_000 + 1000 * round_index + 31 * probe_index


def test_receipt(class_id: int, episode_seed: int, round_index: int, probe_index: int) -> np.ndarray:
    clean = probe_receipt_vector(
        class_id,
        test_measurement_seed(episode_seed, round_index, probe_index),
        probe_index,
    )
    return apply_measurement_nuisance(
        clean,
        np.random.default_rng(nuisance_seed(episode_seed, round_index, probe_index)),
    )


def _least_squares_residual(y: np.ndarray, columns: Sequence[np.ndarray]) -> np.ndarray:
    matrix = np.column_stack([np.asarray(col, dtype=float).reshape(-1) for col in columns])
    coeff, *_ = np.linalg.lstsq(matrix, np.asarray(y, dtype=float).reshape(-1), rcond=None)
    return np.asarray(y, dtype=float).reshape(-1) - matrix @ coeff


def quotient_class_loss(y: np.ndarray, mu: np.ndarray, variance: float) -> float:
    residual = _least_squares_residual(y, (mu, ONES, RAMP))
    return float(np.mean(residual * residual) / float(variance))


def raw_class_loss(y: np.ndarray, mu: np.ndarray, variance: float) -> float:
    residual = np.asarray(y, dtype=float) - np.asarray(mu, dtype=float)
    return float(np.mean(residual * residual) / float(variance))


def pair_distance_raw(mu_a: np.ndarray, mu_b: np.ndarray, variance: float) -> float:
    d = np.asarray(mu_a, dtype=float) - np.asarray(mu_b, dtype=float)
    return float(np.mean(d * d) / float(variance))


def pair_distance_quotient(mu_a: np.ndarray, mu_b: np.ndarray, variance: float) -> float:
    a = np.asarray(mu_a, dtype=float)
    b = np.asarray(mu_b, dtype=float)
    d = a - b
    midpoint = 0.5 * (a + b)
    residual = _least_squares_residual(d, (midpoint, ONES, RAMP))
    return float(np.mean(residual * residual) / float(variance))


def precompute_pair_distances(means: np.ndarray, pooled_variance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    raw = np.zeros((N_CLASSES, N_CLASSES, N_CLASSES), dtype=float)
    quotient = np.zeros_like(raw)
    for probe_index in range(N_CLASSES):
        variance = float(pooled_variance[probe_index])
        for a in range(N_CLASSES):
            for b in range(a + 1, N_CLASSES):
                raw_d = pair_distance_raw(means[a, probe_index], means[b, probe_index], variance)
                q_d = pair_distance_quotient(means[a, probe_index], means[b, probe_index], variance)
                raw[a, b, probe_index] = raw[b, a, probe_index] = raw_d
                quotient[a, b, probe_index] = quotient[b, a, probe_index] = q_d
    return raw, quotient


def posterior_update(
    posterior: np.ndarray,
    receipt: np.ndarray,
    probe_index: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
    mode: str,
) -> np.ndarray:
    variance = float(pooled_variance[probe_index])
    if mode == "raw":
        losses = np.asarray(
            [raw_class_loss(receipt, means[c, probe_index], variance) for c in range(N_CLASSES)]
        )
    elif mode == "quotient":
        losses = np.asarray(
            [quotient_class_loss(receipt, means[c, probe_index], variance) for c in range(N_CLASSES)]
        )
    else:
        raise ValueError("mode must be raw or quotient")
    log_likelihood = -0.5 * losses
    log_likelihood -= float(log_likelihood.max())
    updated = np.asarray(posterior, dtype=float) * np.exp(log_likelihood)
    total = float(updated.sum())
    if total <= 0.0 or not math.isfinite(total):
        raise FloatingPointError("posterior normalization failed")
    return updated / total


def information_score(posterior: np.ndarray, probe_index: int, pair_distances: np.ndarray) -> float:
    score = 0.0
    for a in range(N_CLASSES):
        for b in range(a + 1, N_CLASSES):
            score += 2.0 * float(posterior[a]) * float(posterior[b]) * float(
                pair_distances[a, b, probe_index]
            )
    return float(score)


def choose_adaptive_probe(
    posterior: np.ndarray,
    used: set[int],
    pair_distances: np.ndarray,
) -> int:
    candidates = [p for p in range(N_CLASSES) if p not in used]
    return max(
        candidates,
        key=lambda p: (information_score(posterior, p, pair_distances), -p),
    )


def fixed_design_score(probes: Sequence[int], pair_distances: np.ndarray) -> tuple[float, float]:
    distances = []
    for a, b in itertools.combinations(range(N_CLASSES), 2):
        distances.append(float(sum(pair_distances[a, b, p] for p in probes)))
    return float(min(distances)), float(np.mean(distances))


def choose_best_fixed_schedule(pair_distances: np.ndarray) -> tuple[int, int, int]:
    schedules = list(itertools.combinations(range(N_CLASSES), PROBE_BUDGET))
    return max(schedules, key=lambda probes: fixed_design_score(probes, pair_distances))


def infer_with_schedule(
    class_id: int,
    episode_seed: int,
    schedule: Sequence[int],
    means: np.ndarray,
    pooled_variance: np.ndarray,
    mode: str,
    cache: dict[tuple[int, int], np.ndarray],
) -> tuple[int, tuple[int, ...]]:
    posterior = np.full(N_CLASSES, 1.0 / N_CLASSES, dtype=float)
    used = []
    for round_index, probe_index in enumerate(schedule):
        key = (round_index, int(probe_index))
        if key not in cache:
            cache[key] = test_receipt(class_id, episode_seed, round_index, int(probe_index))
        posterior = posterior_update(
            posterior,
            cache[key],
            int(probe_index),
            means,
            pooled_variance,
            mode,
        )
        used.append(int(probe_index))
    return int(np.argmax(posterior)), tuple(used)


def infer_adaptive(
    class_id: int,
    episode_seed: int,
    means: np.ndarray,
    pooled_variance: np.ndarray,
    mode: str,
    pair_distances: np.ndarray,
    cache: dict[tuple[int, int], np.ndarray],
) -> tuple[int, tuple[int, ...]]:
    posterior = np.full(N_CLASSES, 1.0 / N_CLASSES, dtype=float)
    used: set[int] = set()
    sequence = []
    for round_index in range(PROBE_BUDGET):
        probe_index = choose_adaptive_probe(posterior, used, pair_distances)
        used.add(probe_index)
        sequence.append(probe_index)
        key = (round_index, int(probe_index))
        if key not in cache:
            cache[key] = test_receipt(class_id, episode_seed, round_index, int(probe_index))
        posterior = posterior_update(
            posterior,
            cache[key],
            probe_index,
            means,
            pooled_variance,
            mode,
        )
    return int(np.argmax(posterior)), tuple(sequence)


def paired_bootstrap_ci(a_correct: np.ndarray, b_correct: np.ndarray) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    paired = a_correct.astype(float) - b_correct.astype(float)
    indices = rng.integers(0, len(paired), size=(BOOTSTRAP_SAMPLES, len(paired)))
    means = paired[indices].mean(axis=1)
    return [float(v) for v in np.quantile(means, [0.025, 0.975])]


def per_class_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> list[float]:
    return [
        float(np.mean(y_pred[y_true == class_id] == class_id))
        for class_id in range(N_CLASSES)
    ]


def instrument_obligations(means: np.ndarray, pooled_variance: np.ndarray, quotient_pairs: np.ndarray) -> dict[str, bool]:
    mu = means[0, 0].copy()
    variance = float(pooled_variance[0])

    identical = pair_distance_quotient(mu, mu, variance)
    nuisance_only = 1.25 * mu + 0.05 * ONES + 0.03 * RAMP
    nuisance_distance = pair_distance_quotient(mu, nuisance_only, variance)

    basis = np.sin(np.linspace(0.0, 7.0 * np.pi, RECEIPT_DIM))
    structural = basis - _least_squares_residual(basis, ()) if False else basis
    # Explicitly remove the nuisance span before adding the structural component.
    structural = _least_squares_residual(structural, (mu, ONES, RAMP))
    structural_distance = pair_distance_quotient(mu, mu + 0.10 * structural, variance)

    symmetry_a = pair_distance_quotient(mu, means[1, 0], variance)
    symmetry_b = pair_distance_quotient(means[1, 0], mu, variance)

    uniform = np.full(N_CLASSES, 1.0 / N_CLASSES, dtype=float)
    original_scores = np.asarray(
        [information_score(uniform, p, quotient_pairs) for p in range(N_CLASSES)]
    )
    permutation = np.asarray([3, 0, 7, 1, 6, 2, 5, 4], dtype=int)
    permuted = quotient_pairs[permutation][:, permutation, :]
    permuted_scores = np.asarray(
        [information_score(uniform, p, permuted) for p in range(N_CLASSES)]
    )

    transformed = 1.4 * mu - 0.07 * ONES + 0.025 * RAMP
    fit_loss = quotient_class_loss(transformed, mu, variance)

    return {
        "IDENTICAL_ZERO": bool(abs(identical) <= 1e-12),
        "NUISANCE_ONLY_ZERO": bool(nuisance_distance <= 1e-10),
        "STRUCTURE_DETECTED": bool(structural_distance > 1e-4),
        "PAIR_SYMMETRY": bool(abs(symmetry_a - symmetry_b) <= 1e-10),
        "LABEL_INVARIANT": bool(np.allclose(original_scores, permuted_scores, rtol=0.0, atol=1e-10)),
        "TRUE_NUISANCE_FIT": bool(fit_loss <= 1e-10),
    }


def run_benchmark() -> dict:
    means, pooled_variance = learn_response_model()
    raw_pairs, quotient_pairs = precompute_pair_distances(means, pooled_variance)
    obligations = instrument_obligations(means, pooled_variance, quotient_pairs)
    if not all(obligations.values()):
        return {
            "gate": "W4_NUISANCE_QUOTIENT",
            "verdict": "INSTRUMENT_OBLIGATION_FAIL",
            "instrument_obligations": obligations,
        }

    raw_fixed_schedule = choose_best_fixed_schedule(raw_pairs)
    quotient_fixed_schedule = choose_best_fixed_schedule(quotient_pairs)

    y_true = []
    predictions = {
        "raw_adaptive": [],
        "raw_fixed": [],
        "quotient_random": [],
        "quotient_fixed": [],
        "quotient_adaptive": [],
    }
    quotient_sequences: dict[tuple[int, ...], int] = {}

    for episode_index in range(TEST_EPISODES):
        class_id = episode_index % N_CLASSES
        episode_seed = TEST_SEED_START + episode_index
        y_true.append(class_id)
        cache: dict[tuple[int, int], np.ndarray] = {}

        pred, _ = infer_adaptive(
            class_id, episode_seed, means, pooled_variance,
            "raw", raw_pairs, cache,
        )
        predictions["raw_adaptive"].append(pred)

        pred, _ = infer_with_schedule(
            class_id, episode_seed, raw_fixed_schedule,
            means, pooled_variance, "raw", cache,
        )
        predictions["raw_fixed"].append(pred)

        policy_rng = np.random.default_rng(episode_seed + 99_000_000)
        random_schedule = tuple(
            int(p) for p in policy_rng.choice(N_CLASSES, size=PROBE_BUDGET, replace=False)
        )
        pred, _ = infer_with_schedule(
            class_id, episode_seed, random_schedule,
            means, pooled_variance, "quotient", cache,
        )
        predictions["quotient_random"].append(pred)

        pred, _ = infer_with_schedule(
            class_id, episode_seed, quotient_fixed_schedule,
            means, pooled_variance, "quotient", cache,
        )
        predictions["quotient_fixed"].append(pred)

        pred, sequence = infer_adaptive(
            class_id, episode_seed, means, pooled_variance,
            "quotient", quotient_pairs, cache,
        )
        predictions["quotient_adaptive"].append(pred)
        quotient_sequences[sequence] = quotient_sequences.get(sequence, 0) + 1

    y_true_arr = np.asarray(y_true, dtype=int)
    pred_arr = {name: np.asarray(values, dtype=int) for name, values in predictions.items()}
    accuracy = {
        name: float(np.mean(values == y_true_arr))
        for name, values in pred_arr.items()
    }

    qa = pred_arr["quotient_adaptive"] == y_true_arr
    qf = pred_arr["quotient_fixed"] == y_true_arr
    ci = paired_bootstrap_ci(qa, qf)
    adaptive_per_class = per_class_accuracy(y_true_arr, pred_arr["quotient_adaptive"])

    qa_minus_raw = accuracy["quotient_adaptive"] - accuracy["raw_adaptive"]
    qa_minus_random = accuracy["quotient_adaptive"] - accuracy["quotient_random"]
    qa_minus_fixed = accuracy["quotient_adaptive"] - accuracy["quotient_fixed"]

    criteria = {
        "instrument_obligations": all(obligations.values()),
        "quotient_adaptive_accuracy_at_least_0_45": accuracy["quotient_adaptive"] >= 0.45,
        "quotient_adaptive_beats_raw_by_0_15": qa_minus_raw >= 0.15,
        "quotient_adaptive_beats_random_by_0_02": qa_minus_random >= 0.02,
        "quotient_adaptive_beats_fixed_by_0_01": qa_minus_fixed >= 0.01,
        "paired_bootstrap_ci_above_zero": ci[0] > 0.0,
        "per_class_floor": min(adaptive_per_class) >= 0.35,
        "adaptive_policy_branches": len(quotient_sequences) >= 4,
        "fixed_three_write_budget": True,
    }

    if all(criteria.values()):
        verdict = "NUISANCE_QUOTIENT_QUERY_EARNS_KEEP"
    elif (
        criteria["instrument_obligations"]
        and criteria["quotient_adaptive_accuracy_at_least_0_45"]
        and criteria["quotient_adaptive_beats_raw_by_0_15"]
        and criteria["quotient_adaptive_beats_random_by_0_02"]
        and not (
            criteria["quotient_adaptive_beats_fixed_by_0_01"]
            and criteria["paired_bootstrap_ci_above_zero"]
        )
    ):
        verdict = "NUISANCE_MODEL_HELPS_INFERENCE_BUT_ADAPTIVE_QUERY_NOT_EARNED"
    else:
        verdict = "NUISANCE_QUOTIENT_QUERY_NOT_EARNED"

    sequence_counts = sorted(
        [
            {"sequence": list(sequence), "count": int(count)}
            for sequence, count in quotient_sequences.items()
        ],
        key=lambda row: (-row["count"], row["sequence"]),
    )

    return {
        "gate": "W4_NUISANCE_QUOTIENT",
        "preregistration": "docs/PREREG_W4_NUISANCE_QUOTIENT.md",
        "verdict": verdict,
        "instrument_obligations": obligations,
        "nuisance": {
            "log_gain_sigma": LOG_GAIN_SIGMA,
            "offset_sigma": OFFSET_SIGMA,
            "slope_sigma": SLOPE_SIGMA,
        },
        "response_model": {
            "samples_per_class_probe": MODEL_SAMPLES_PER_CELL,
            "pooled_variance": pooled_variance.tolist(),
        },
        "fixed_schedules": {
            "raw_probe_indices": list(raw_fixed_schedule),
            "raw_sites": [CANDIDATE_CENTERS[p] for p in raw_fixed_schedule],
            "quotient_probe_indices": list(quotient_fixed_schedule),
            "quotient_sites": [CANDIDATE_CENTERS[p] for p in quotient_fixed_schedule],
        },
        "accuracy": accuracy,
        "quotient_adaptive_minus_raw_adaptive": float(qa_minus_raw),
        "quotient_adaptive_minus_quotient_random": float(qa_minus_random),
        "quotient_adaptive_minus_quotient_fixed": float(qa_minus_fixed),
        "paired_bootstrap_95_ci_quotient_adaptive_minus_fixed": ci,
        "quotient_adaptive_per_class_accuracy": adaptive_per_class,
        "quotient_adaptive_distinct_sequences": len(quotient_sequences),
        "quotient_adaptive_sequence_counts": sequence_counts,
        "criteria": criteria,
        "probe_budget": PROBE_BUDGET,
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
