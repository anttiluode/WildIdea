#!/usr/bin/env python3
"""WildIdea W1b: rotation and feature-map robustness audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import wildidea_w1 as w1


TRAIN_EPISODES = 800
TEST_EPISODES = 800
TRAIN_SEED_START = 1_180_000
TEST_SEED_START = 1_280_000
FEATURE_SEEDS = (20260814, 20260831, 20260917, 20261003, 20261019)


def rotated_scan_position(t: int, phase: int) -> int:
    return int(round((4.0 + 8.0 * phase + (2.0 / 3.0) * float(t)) % w1.N_SITES)) % w1.N_SITES


def simulate_episode(class_id: int, seed: int, mode: str, phase: int) -> w1.Episode:
    if class_id not in range(4):
        raise ValueError("class_id must be 0..3")
    if phase not in range(4):
        raise ValueError("phase must be 0..3")
    if mode not in {"passive", "controlled", "random_write"}:
        raise ValueError(f"unknown mode: {mode}")

    dyn_rng = np.random.default_rng(seed)
    policy_rng = np.random.default_rng(seed + 10_000_000)

    damping = np.full(w1.N_SITES, w1.BACKGROUND_DAMPING, dtype=float)
    damping += w1.defect_profile(class_id)
    stiffness = np.full(w1.N_SITES, w1.BACKGROUND_STIFFNESS, dtype=float)

    x = w1.INITIAL_SIGMA * dyn_rng.normal(size=w1.N_SITES)
    velocity = w1.INITIAL_SIGMA * dyn_rng.normal(size=w1.N_SITES)

    fields = []
    positions = []
    pulse_count = 0
    random_position = rotated_scan_position(0, phase)

    for t in range(w1.N_STEPS):
        if mode == "random_write":
            if t > 0:
                random_position = int(
                    (random_position + policy_rng.choice((-1, 0, 1))) % w1.N_SITES
                )
            scout_position = random_position
        else:
            scout_position = rotated_scan_position(t, phase)

        if t in w1.PULSE_TIMES and mode in {"controlled", "random_write"}:
            velocity[scout_position] += w1.PULSE_AMPLITUDE
            pulse_count += 1

        velocity += w1.AMBIENT_VELOCITY_NOISE * dyn_rng.normal(size=w1.N_SITES)
        laplacian = np.roll(x, 1) + np.roll(x, -1) - 2.0 * x
        acceleration = w1.C2 * laplacian - stiffness * x - damping * velocity
        velocity += w1.DT * acceleration
        x += w1.DT * velocity

        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 100.0:
            raise FloatingPointError("unstable field episode")

        fields.append(x.copy())
        positions.append(scout_position)

    return w1.Episode(
        field=np.asarray(fields, dtype=float),
        positions=np.asarray(positions, dtype=int),
        pulse_count=pulse_count,
        pulse_amplitude=(w1.PULSE_AMPLITUDE if pulse_count else 0.0),
    )


def build_raw_episodes(start_seed: int, n_episodes: int):
    if n_episodes % 16:
        raise ValueError("episode count must be divisible by 16 for class/phase balance")

    rows = []
    for episode_index in range(n_episodes):
        class_id = episode_index % 4
        phase = (episode_index // 4) % 4
        seed = start_seed + episode_index
        rows.append(
            (
                class_id,
                phase,
                simulate_episode(class_id, seed, "passive", phase),
                simulate_episode(class_id, seed, "controlled", phase),
                simulate_episode(class_id, seed, "random_write", phase),
            )
        )
    return rows


def features_for_rows(rows, feature_seed: int):
    fmap = w1.FixedFeatureMap(seed=feature_seed)
    matrices = {name: [] for name in w1.ARCHITECTURES}
    labels = []
    pulse_ok = True

    for class_id, phase, passive, controlled, random_write in rows:
        matrices["static_global"].append(fmap.static_global(passive))
        matrices["recurrent_global"].append(fmap.recurrent_global(passive))
        matrices["scout_read_only"].append(fmap.scout(passive))
        matrices["scout_read_write"].append(fmap.scout(controlled))
        matrices["scout_random_write"].append(fmap.scout(random_write))
        labels.append(class_id)

        pulse_ok = pulse_ok and (
            controlled.pulse_count == 4
            and random_write.pulse_count == 4
            and controlled.pulse_amplitude == w1.PULSE_AMPLITUDE
            and random_write.pulse_amplitude == w1.PULSE_AMPLITUDE
        )

    return (
        {name: np.asarray(values, dtype=float) for name, values in matrices.items()},
        np.asarray(labels, dtype=int),
        bool(pulse_ok),
    )


def class_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> list[float]:
    return [float(np.mean(y_pred[y_true == c] == c)) for c in range(4)]


def run_audit() -> dict:
    train_rows = build_raw_episodes(TRAIN_SEED_START, TRAIN_EPISODES)
    test_rows = build_raw_episodes(TEST_SEED_START, TEST_EPISODES)

    seed_results = []
    all_pulse_ok = True

    for feature_seed in FEATURE_SEEDS:
        x_train, y_train, pulse_train = features_for_rows(train_rows, feature_seed)
        x_test, y_test, pulse_test = features_for_rows(test_rows, feature_seed)
        all_pulse_ok = all_pulse_ok and pulse_train and pulse_test

        accuracies = {}
        predictions = {}
        for architecture in w1.ARCHITECTURES:
            pred = w1.fit_ridge_classifier(
                x_train[architecture], y_train, x_test[architecture]
            )
            predictions[architecture] = pred
            accuracies[architecture] = float(np.mean(pred == y_test))

        strongest_passive = max(
            w1.PASSIVE_ARCHITECTURES,
            key=lambda name: accuracies[name],
        )
        active = accuracies["scout_read_write"]
        random_write = accuracies["scout_random_write"]
        seed_results.append(
            {
                "feature_seed": feature_seed,
                "accuracies": accuracies,
                "strongest_passive": strongest_passive,
                "active_minus_strongest_passive": float(
                    active - accuracies[strongest_passive]
                ),
                "active_minus_random_write": float(active - random_write),
                "active_class_accuracy": class_accuracy(
                    y_test, predictions["scout_read_write"]
                ),
            }
        )

    mean_accuracy = {
        architecture: float(
            np.mean([row["accuracies"][architecture] for row in seed_results])
        )
        for architecture in w1.ARCHITECTURES
    }
    mean_active_minus_passive = float(
        np.mean([row["active_minus_strongest_passive"] for row in seed_results])
    )
    mean_active_minus_random = float(
        np.mean([row["active_minus_random_write"] for row in seed_results])
    )
    mean_class_accuracy = [
        float(np.mean([row["active_class_accuracy"][c] for row in seed_results]))
        for c in range(4)
    ]

    criteria = {
        "beats_strongest_passive_all_5": all(
            row["active_minus_strongest_passive"] > 0.0 for row in seed_results
        ),
        "mean_passive_margin_at_least_0_08": mean_active_minus_passive >= 0.08,
        "beats_random_write_at_least_4_of_5": sum(
            row["active_minus_random_write"] > 0.0 for row in seed_results
        ) >= 4,
        "mean_random_margin_at_least_0_05": mean_active_minus_random >= 0.05,
        "mean_active_accuracy_at_least_0_45": mean_accuracy["scout_read_write"] >= 0.45,
        "every_class_mean_accuracy_at_least_0_35": min(mean_class_accuracy) >= 0.35,
        "fixed_write_budget": all_pulse_ok,
    }
    passed = all(criteria.values())

    return {
        "gate": "W1B_ROTATION_ROBUSTNESS",
        "verdict": (
            "ACTIVE_PROBING_SURVIVES_ROTATION"
            if passed
            else "ACTIVE_PROBING_ROTATION_FRAGILE"
        ),
        "feature_seeds": list(FEATURE_SEEDS),
        "train_seed_start": TRAIN_SEED_START,
        "test_seed_start": TEST_SEED_START,
        "seed_results": seed_results,
        "mean_accuracy": mean_accuracy,
        "mean_active_minus_strongest_passive": mean_active_minus_passive,
        "mean_active_minus_random_write": mean_active_minus_random,
        "mean_active_class_accuracy": mean_class_accuracy,
        "criteria": criteria,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    result = run_audit()
    text = json.dumps(result, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
