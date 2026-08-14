# W1 result — active probing earns its keep, with a symmetry caveat

Date: 2026-08-14

First evaluation run: GitHub Actions `31797470492`

Evaluated commit: `1922a385778022a9fffac72603fb0a01ed4c3f96`

Artifact: `w1-active-probe-result` (`SHA256 08bf607448c5f013e1ce426140ee8e1ab208c23268a218a5ffc2f533212470cc` for the uploaded zip)

The preregistration was committed before this evaluation and excluded the development sanity seeds.

## Frozen verdict

```text
ACTIVE_PROBING_EARNS_KEEP
```

All preregistered criteria passed.

## Held-out accuracies

```text
static global             0.28375
recurrent global          0.25500
moving scout, read only   0.30875
moving scout, read+write  0.50000
random-walk equal writes  0.29875
```

Strongest passive baseline: `scout_read_only`.

```text
active - strongest passive   +0.19125
paired bootstrap 95% CI      [+0.15750, +0.22500]
active - random write        +0.20125
```

The controlled and random-write conditions both used exactly four pulses of amplitude `0.8` in every train and test episode.

## What W1 supports

In this frozen toy system-identification task, a tiny local process that can perturb the medium and read the resulting trajectory extracted substantially more label-relevant information than the tested passive readouts. Equal-energy uncontrolled writes did not reproduce the gain.

That is enough to keep the **active internal probing** idea alive as an engineering hypothesis.

It does not establish adaptive intelligence, novelty, neuroscience, consciousness, or superiority to standard active-sensing/system-identification methods.

## Immediate caveat discovered by inspecting the frozen confusion matrix

The active arm is not class-symmetric:

```text
true class 0: 200 / 200 correct
true class 1:  58 / 200 correct
true class 2:  49 / 200 correct
true class 3:  93 / 200 correct
```

The deterministic scan begins at defect center 0 and always visits candidate centers in the same temporal order. Because the fixed recurrent readout is time-asymmetric, one class receives a privileged temporal relationship to the probe schedule.

This does **not** invalidate the frozen W1 gate: the task, schedule and labels were fixed before evaluation and the active arm still beat both passive and equal-energy random-write baselines. But it means the strongest interpretation is not yet "the scout generally identifies hidden structure by probing." Part of the 50% accuracy may depend on probe-order / recurrent-memory geometry.

That is exactly the sort of post-result weakness the next test should attack rather than tune away.

## Next test

Run a fresh-seed **rotation/symmetry audit** in which the starting probe phase is randomized independently of the hidden class and represented to the readout. Repeat across multiple frozen feature-map seeds.

If the active advantage disappears, W1 was a schedule-specific trick.

If it survives, then proceed to the harder question: whether a **state-dependent adaptive probe policy** can outperform predetermined coverage under the same write budget.

No HTML demo yet. The visual story should wait until this robustness audit has spoken.
