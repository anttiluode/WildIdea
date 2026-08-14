#!/usr/bin/env python3
"""WildIdea W1: scheduled active probing versus passive readout.

The scientific contract is frozen in docs/PREREG_W1.md.
This file intentionally uses only NumPy so the full benchmark is easy to audit.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np


N_SITES = 32
N_STEPS = 48
DT = 0.08
C2 = 0.9
BACKGROUND_DAMPING = 0.10
BACKGROUND_STIFFNESS = 0.10
DEFECT_EXTRA_DAMPING = 0.45
DEFECT_SIGMA = 1.5
DEFECT_CENTERS = (4, 12, 20, 28)
INITIAL_SIGMA = 0.02
AMBIENT_VELOCITY_NOISE = 0.004
PULSE_AMPLITUDE = 0.8
PULSE_TIMES = (0, 12, 24, 36)

FEATURE_SEED = 20260814
FEATURE_WIDTH = 16
GLOBAL_OBS_WIDTH = 6
RECURRENT_LEAK = 0.82
RIDGE_ALPHA = 1.0

TRAIN_EPISODES = 800
TEST_EPISODES = 800
TRAIN_SEED_START = 880_000
TEST_SEED_START = 980_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814

ARCHITECTURES = (
    "static_global",
    "recurrent_global",
    "scout_read_only",
    "scout_read_write",
    "scout_random_write",
)
PASSIVE_ARCHITECTURES = (
    "static_global",
    "recurrent_global",
    "scout_read_only",
)


@dataclass(frozen=True)
class Episode:
    field: np.ndarray  # [time, site]
    positions: np.ndarray  # [time], integer site observed by scout
    pulse_count: int
    pulse_amplitude: float


def deterministic_scan_position(t: int) -> int:
    """One full ring scan; pulse times land at 4, 12, 20, 28 exactly."""
    position = (4.0 + (2.0 / 3.0) * float(t)) % float(N_SITES)
    return int(round(position)) % N_SITES


def defect_profile(class_id: int) -> np.ndarray:
    center = DEFECT_CENTERS[class_id]
    idx = np.arange(N_SITES)
    direct = np.abs(idx - center)
    distance = np.minimum(direct, N_SITES - direct)
    return DEFECT_EXTRA_DAMPING * np.exp(
        -(distance.astype(float) ** 2) / (2.0 * DEFECT_SIGMA**2)
    )


def simulate_episode(class_id: int, seed: int, mode: str) -> Episode:
    """Simulate one hidden-defect wave-ring episode.

    Modes:
      passive       deterministic scout path; no writes
      controlled    deterministic path; four fixed writes
      random_write  label-independent random walk; four fixed-amplitude writes
    """
    if class_id not in range(4):
        raise ValueError("class_id must be 0..3")
    if mode not in {"passive", "controlled", "random_write"}:
        raise ValueError(f"unknown mode: {mode}")

    # Dynamics and policy RNGs are separated so ambient forcing is paired between
    # passive and controlled conditions for the same episode seed.
    dyn_rng = np.random.default_rng(seed)
    policy_rng = np.random.default_rng(seed + 10_000_000)

    damping = np.full(N_SITES, BACKGROUND_DAMPING, dtype=float)
    damping += defect_profile(class_id)
    stiffness = np.full(N_SITES, BACKGROUND_STIFFNESS, dtype=float)

    x = INITIAL_SIGMA * dyn_rng.normal(size=N_SITES)
    velocity = INITIAL_SIGMA * dyn_rng.normal(size=N_SITES)

    fields = []
    positions = []
    pulse_count = 0
    random_position = 4

    for t in range(N_STEPS):
        if mode == "random_write":
            if t > 0:
                random_position = int(
                    (random_position + policy_rng.choice((-1, 0, 1))) % N_SITES
                )
            scout_position = random_position
        else:
            scout_position = deterministic_scan_position(t)

        if t in PULSE_TIMES and mode in {"controlled", "random_write"}:
            velocity[scout_position] += PULSE_AMPLITUDE
            pulse_count += 1

        # Weak uncontrolled excitation. Same draws for passive/controlled seed pair.
        velocity += AMBIENT_VELOCITY_NOISE * dyn_rng.normal(size=N_SITES)

        laplacian = np.roll(x, 1) + np.roll(x, -1) - 2.0 * x
        acceleration = C2 * laplacian - stiffness * x - damping * velocity
        velocity += DT * acceleration
        x += DT * velocity

        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 100.0:
            raise FloatingPointError("unstable field episode")

        fields.append(x.copy())
        positions.append(scout_position)

    return Episode(
        field=np.asarray(fields, dtype=float),
        positions=np.asarray(positions, dtype=int),
        pulse_count=pulse_count,
        pulse_amplitude=(PULSE_AMPLITUDE if pulse_count else 0.0),
    )


class FixedFeatureMap:
    """Frozen small observer used by every architecture."""

    def __init__(self, seed: int = FEATURE_SEED):
        rng = np.random.default_rng(seed)
        self.global_projection = rng.normal(
            size=(GLOBAL_OBS_WIDTH, N_SITES)
        ) / math.sqrt(N_SITES)
        self.global_input = rng.normal(scale=0.35, size=(FEATURE_WIDTH, GLOBAL_OBS_WIDTH))
        self.scout_input = rng.normal(scale=0.35, size=(FEATURE_WIDTH, 5))

    def static_global(self, episode: Episode) -> np.ndarray:
        observation = self.global_projection @ episode.field[-1]
        return np.tanh(self.global_input @ observation)

    def recurrent_global(self, episode: Episode) -> np.ndarray:
        state = np.zeros(FEATURE_WIDTH, dtype=float)
        for field in episode.field:
            observation = self.global_projection @ field
            state = np.tanh(RECURRENT_LEAK * state + self.global_input @ observation)
        return state

    def scout(self, episode: Episode) -> np.ndarray:
        state = np.zeros(FEATURE_WIDTH, dtype=float)
        for field, position in zip(episode.field, episode.positions):
            left = (int(position) - 1) % N_SITES
            center = int(position)
            right = (int(position) + 1) % N_SITES
            angle = 2.0 * math.pi * float(position) / float(N_SITES)
            observation = np.array(
                [field[left], field[center], field[right], math.sin(angle), math.cos(angle)],
                dtype=float,
            )
            state = np.tanh(RECURRENT_LEAK * state + self.scout_input @ observation)
        return state


def episode_features(class_id: int, seed: int, feature_map: FixedFeatureMap) -> Tuple[Dict[str, np.ndarray], Dict[str, float]]:
    passive = simulate_episode(class_id, seed, "passive")
    controlled = simulate_episode(class_id, seed, "controlled")
    random_write = simulate_episode(class_id, seed, "random_write")

    features = {
        "static_global": feature_map.static_global(passive),
        "recurrent_global": feature_map.recurrent_global(passive),
        "scout_read_only": feature_map.scout(passive),
        "scout_read_write": feature_map.scout(controlled),
        "scout_random_write": feature_map.scout(random_write),
    }
    receipts = {
        "controlled_pulse_count": float(controlled.pulse_count),
        "controlled_pulse_amplitude": float(controlled.pulse_amplitude),
        "random_pulse_count": float(random_write.pulse_count),
        "random_pulse_amplitude": float(random_write.pulse_amplitude),
    }
    return features, receipts


def build_dataset(start_seed: int, n_episodes: int) -> Tuple[Dict[str, np.ndarray], np.ndarray, Dict[str, float]]:
    if n_episodes % 4:
        raise ValueError("episode count must be divisible by four for exact balance")

    fmap = FixedFeatureMap()
    matrices = {name: [] for name in ARCHITECTURES}
    labels = []
    pulse_receipts = []

    for episode_index in range(n_episodes):
        class_id = episode_index % 4
        seed = start_seed + episode_index
        features, receipt = episode_features(class_id, seed, fmap)
        for name in ARCHITECTURES:
            matrices[name].append(features[name])
        labels.append(class_id)
        pulse_receipts.append(receipt)

    receipt_summary = {
        "controlled_min_pulses": min(r["controlled_pulse_count"] for r in pulse_receipts),
        "controlled_max_pulses": max(r["controlled_pulse_count"] for r in pulse_receipts),
        "controlled_min_amplitude": min(r["controlled_pulse_amplitude"] for r in pulse_receipts),
        "controlled_max_amplitude": max(r["controlled_pulse_amplitude"] for r in pulse_receipts),
        "random_min_pulses": min(r["random_pulse_count"] for r in pulse_receipts),
        "random_max_pulses": max(r["random_pulse_count"] for r in pulse_receipts),
        "random_min_amplitude": min(r["random_pulse_amplitude"] for r in pulse_receipts),
        "random_max_amplitude": max(r["random_pulse_amplitude"] for r in pulse_receipts),
    }

    return (
        {name: np.asarray(rows, dtype=float) for name, rows in matrices.items()},
        np.asarray(labels, dtype=int),
        receipt_summary,
    )


def fit_ridge_classifier(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale < 1e-12] = 1.0

    z_train = (x_train - mean) / scale
    z_test = (x_test - mean) / scale

    # Intercept is explicit and unpenalized.
    z_train = np.column_stack([z_train, np.ones(len(z_train))])
    z_test = np.column_stack([z_test, np.ones(len(z_test))])
    target = np.eye(4, dtype=float)[y_train]

    penalty = RIDGE_ALPHA * np.eye(z_train.shape[1])
    penalty[-1, -1] = 0.0
    weights = np.linalg.solve(z_train.T @ z_train + penalty, z_train.T @ target)
    scores = z_test @ weights
    return np.argmax(scores, axis=1)


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> list[list[int]]:
    matrix = np.zeros((4, 4), dtype=int)
    for truth, pred in zip(y_true, y_pred):
        matrix[int(truth), int(pred)] += 1
    return matrix.tolist()


def paired_bootstrap_difference(active_correct: np.ndarray, passive_correct: np.ndarray) -> Tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    paired = active_correct.astype(float) - passive_correct.astype(float)
    indices = rng.integers(0, len(paired), size=(BOOTSTRAP_SAMPLES, len(paired)))
    means = paired[indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def run_benchmark(train_episodes: int = TRAIN_EPISODES, test_episodes: int = TEST_EPISODES) -> dict:
    x_train, y_train, train_receipt = build_dataset(TRAIN_SEED_START, train_episodes)
    x_test, y_test, test_receipt = build_dataset(TEST_SEED_START, test_episodes)

    predictions = {}
    results = {}
    for architecture in ARCHITECTURES:
        pred = fit_ridge_classifier(x_train[architecture], y_train, x_test[architecture])
        predictions[architecture] = pred
        accuracy = float(np.mean(pred == y_test))
        results[architecture] = {
            "accuracy": accuracy,
            "confusion_matrix": confusion_matrix(y_test, pred),
        }

    strongest_passive = max(
        PASSIVE_ARCHITECTURES,
        key=lambda name: results[name]["accuracy"],
    )
    active_name = "scout_read_write"
    random_name = "scout_random_write"

    active_accuracy = results[active_name]["accuracy"]
    passive_accuracy = results[strongest_passive]["accuracy"]
    random_accuracy = results[random_name]["accuracy"]
    active_minus_passive = active_accuracy - passive_accuracy
    active_minus_random = active_accuracy - random_accuracy

    bootstrap_ci = paired_bootstrap_difference(
        predictions[active_name] == y_test,
        predictions[strongest_passive] == y_test,
    )

    pulse_budget_ok = bool(
        train_receipt["controlled_min_pulses"] == 4
        and train_receipt["controlled_max_pulses"] == 4
        and test_receipt["controlled_min_pulses"] == 4
        and test_receipt["controlled_max_pulses"] == 4
        and train_receipt["controlled_min_amplitude"] == PULSE_AMPLITUDE
        and train_receipt["controlled_max_amplitude"] == PULSE_AMPLITUDE
        and test_receipt["controlled_min_amplitude"] == PULSE_AMPLITUDE
        and test_receipt["controlled_max_amplitude"] == PULSE_AMPLITUDE
    )

    criteria = {
        "active_accuracy_at_least_0_50": active_accuracy >= 0.50,
        "beats_strongest_passive_by_0_05": active_minus_passive >= 0.05,
        "paired_bootstrap_ci_above_zero": bootstrap_ci[0] > 0.0,
        "beats_random_write_by_0_03": active_minus_random >= 0.03,
        "fixed_write_budget": pulse_budget_ok,
    }
    passed = all(criteria.values())

    return {
        "gate": "W1_ACTIVE_INTERNAL_PROBING",
        "verdict": "ACTIVE_PROBING_EARNS_KEEP" if passed else "ACTIVE_PROBING_NOT_EARNED",
        "frozen_config": {
            "train_episodes": train_episodes,
            "test_episodes": test_episodes,
            "train_seed_start": TRAIN_SEED_START,
            "test_seed_start": TEST_SEED_START,
            "sites": N_SITES,
            "steps": N_STEPS,
            "feature_width": FEATURE_WIDTH,
            "global_observation_width": GLOBAL_OBS_WIDTH,
            "ridge_alpha": RIDGE_ALPHA,
            "pulse_amplitude": PULSE_AMPLITUDE,
            "pulse_times": list(PULSE_TIMES),
        },
        "results": results,
        "strongest_passive": strongest_passive,
        "active_minus_strongest_passive": float(active_minus_passive),
        "active_minus_random_write": float(active_minus_random),
        "paired_bootstrap_95_ci": list(bootstrap_ci),
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "criteria": criteria,
        "pulse_receipt_train": train_receipt,
        "pulse_receipt_test": test_receipt,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, help="optional output JSON path")
    parser.add_argument("--train-episodes", type=int, default=TRAIN_EPISODES)
    parser.add_argument("--test-episodes", type=int, default=TEST_EPISODES)
    args = parser.parse_args()

    result = run_benchmark(args.train_episodes, args.test_episodes)
    text = json.dumps(result, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
