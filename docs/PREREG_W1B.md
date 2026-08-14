# WildIdea W1b — rotation / feature-map robustness audit

Status: **FROZEN AFTER W1, BEFORE W1b EVALUATION**

Date: 2026-08-14

W1 passed its preregistered gate, but its frozen confusion matrix exposed a serious weakness: the controlled scan always began at candidate 0, and class 0 was classified perfectly while the other classes were much weaker. W1b attacks that schedule asymmetry directly.

This is a post-result robustness audit, not an independent confirmation.

## Frozen change relative to W1

The physical medium, write amplitude, write count, downstream classifier and observation widths remain unchanged.

The deterministic scout scan now has one of four starting phases. Across the balanced dataset, **every hidden class occurs equally often with every starting phase**. The phase is label-independent. Pulse times remain `0,12,24,36`, so every controlled episode still probes all four candidate centers exactly once, but their temporal order rotates.

The local scout continues to observe absolute sine/cosine position, so randomizing scan phase does not withhold coordinate information.

## Fresh data

```text
train episodes     800
held-out episodes  800
train seed start   1180000
test seed start    1280000
classes             4 balanced
scan phases         4 balanced within each class
```

No W1 train/test episode is reused.

## Feature-map robustness

Run the complete train/test comparison under five frozen fixed-feature seeds:

```text
20260814
20260831
20260917
20261003
20261019
```

Nothing is tuned per seed.

## Architectures

Same five conditions as W1:

```text
A static global
B recurrent global
C moving scout, read only
D moving scout, controlled read+write
E random-walk scout, equal write budget
```

## W1b metrics

For each feature seed report:

- held-out accuracy for A-E;
- strongest passive accuracy among A/B/C;
- D minus strongest passive;
- D minus E;
- D per-class accuracy.

Also report means across the five feature seeds.

## W1b gate

Call:

```text
ACTIVE_PROBING_SURVIVES_ROTATION
```

only if all are true:

1. D beats the strongest passive baseline in **all 5/5** feature seeds;
2. mean(D - strongest passive) >= **0.08**;
3. D beats equal-energy random write E in at least **4/5** feature seeds;
4. mean(D - E) >= **0.05**;
5. mean D accuracy >= **0.45**;
6. every hidden class has mean D accuracy across feature seeds >= **0.35**;
7. every controlled and random-write episode still uses exactly four writes of amplitude `0.8`.

Otherwise call:

```text
ACTIVE_PROBING_ROTATION_FRAGILE
```

## Interpretation

A pass means the W1 advantage is not explained solely by one lucky fixed probe order or one lucky fixed random feature map.

It still does not establish adaptive scouting. The path remains predetermined.

If W1b passes, the next gate is W2: a fresh task where the probe budget is too small to exhaustively cover all candidates, so a **state-dependent probe policy** must decide what to inspect next and is compared against strong predetermined/random active-sensing baselines.

If W1b fails, keep W1 as a schedule-specific toy result and do not build a celebratory HTML demo around it.
