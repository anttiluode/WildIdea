# WildIdea W1 — active internal probing gate

Status: **FROZEN BEFORE EVALUATION**

Date: 2026-08-14

This repo began from a deliberately wild intuition: a large dynamical medium may contain more useful computation than a passive readout can expose, and a tiny moving process may extract more by **reading and writing** than by merely observing.

The first gate does **not** test consciousness, neuroscience, CEMI, a homunculus, or whether a brain literally contains a scout. It tests one small engineering statement:

> **Under the same small downstream readout budget, can controlled internal probing reveal a hidden property of a dynamical medium better than passive observation?**

## Why this task

A passive system can only use excitation that happens to be present. An active probe can inject a known perturbation and observe the ring-down. This is ordinary system identification in deliberately minimal form.

The benchmark uses a 32-site damped wave ring with one hidden high-damping region. The class label is which of four quadrants contains the hidden damping defect. All classes have the same topology and the same resting-state distribution. Ambient noise provides weak uncontrolled excitation.

The benchmark therefore asks whether a tiny controlled probe can discover a property of the medium that is only weakly visible in passive activity.

## Frozen architectures

All learned readouts have the same 16-dimensional fixed recurrent feature state and the same ridge classifier (`alpha=1.0`). No architecture trains the field dynamics.

### A — static global

Read six fixed random projections of the **whole field once**, at the final time step. Map them into the same 16-dimensional feature state.

### B — recurrent global

Read the same six fixed random projections of the **whole field at every time step** and update the fixed 16-dimensional recurrent feature state.

This is intentionally a strong passive baseline: it has global access at every step.

### C — moving scout, read-only

Move around the ring on a fixed scan trajectory. At each step read only a three-site local patch plus sine/cosine position. Update the same 16-dimensional recurrent feature state. It cannot perturb the medium.

### D — moving scout, read + controlled write

Use the same scan trajectory and same local read bandwidth as C. At four preregistered times, inject an identical velocity pulse at the scout's current location. The four pulses cover the four candidate defect quadrants. Total injected energy is fixed across episodes and labels.

This is the confirmatory active-probe arm.

### E — random-write adversary

Use the same local read bandwidth and the same number/amplitude of pulses as D, but move by a label-independent random walk. This asks whether any extra injected energy is enough, or whether controlled coverage matters.

E is a diagnostic adversary, not one of the four original conceptual architectures.

## Frozen medium

```text
ring sites                  32
steps                       48
dt                          0.08
wave coupling c^2           0.9
background damping          0.10
background stiffness        0.10
defect extra damping        0.45
defect Gaussian sigma       1.5 sites
defect centers               4, 12, 20, 28
initial x sigma             0.02
initial velocity sigma      0.02
ambient velocity noise      0.004 per step
controlled pulse amplitude  0.8
controlled pulse times      0, 12, 24, 36
```

The deterministic scan traverses one full ring in 48 steps and is aligned so those four pulse times land at the four candidate centers.

## Frozen representation / classifier

- fixed random projection matrices generated from seed `20260814`;
- global observation width: 6;
- scout local observation: 3 field values + `sin(position)` + `cos(position)`;
- recurrent feature width: 16;
- recurrent leak: 0.82;
- `tanh` fixed feature update;
- ridge one-vs-all classifier with `alpha=1.0`;
- no hyperparameter fitting on evaluation labels.

A small development-seed sanity run was used only to verify that the code/task is numerically nondegenerate. **Those seeds are excluded from W1 evaluation.** The frozen evaluation uses a disjoint seed block beginning at `880000`.

## Frozen dataset

```text
train episodes    800
held-out episodes 800
classes            4, exactly balanced
train seeds        880000 .. 880799
test seeds         980000 .. 980799
```

The same episode seed/class pair is used across corresponding passive and controlled-write conditions so correctness comparisons are paired where possible.

## Primary metric

Held-out four-class accuracy.

Chance = 0.25.

For the active arm D, also compute paired correctness difference versus whichever of A/B/C is the strongest passive baseline on the frozen test set. A 95% percentile bootstrap CI is computed with 20,000 paired resamples and seed `20260814`.

## Gate

Call:

```text
ACTIVE_PROBING_EARNS_KEEP
```

only if all are true:

1. D accuracy >= 0.50;
2. D beats the strongest passive baseline among A/B/C by at least **5 percentage points**;
3. the paired bootstrap 95% CI for D minus that strongest passive baseline is entirely above zero;
4. D beats the random-write adversary E by at least **3 percentage points**;
5. all active episodes use exactly four pulses of amplitude 0.8 and no label-dependent write budget.

Otherwise call:

```text
ACTIVE_PROBING_NOT_EARNED
```

## Interpretation boundaries

A pass would establish only this:

> In this frozen toy system-identification task, a tiny local read/write process extracts more label-relevant information from a fixed dynamical medium than the tested passive readouts under the frozen representation budget.

It would **not** show that:

- the brain works this way;
- consciousness is a moving scout;
- active probing is novel;
- the architecture beats general active-sensing/system-identification methods;
- the scout is adaptive or intelligent.

In W1 the probe path is scheduled, not learned. If W1 passes, the next serious question is whether **state-dependent/adaptive probe choice** beats equally budgeted random or predetermined probing on a fresh task.

If W1 fails, do not tune the medium until D wins. Record the null and decide whether the idea is worth reformulating.

## HTML rule

No polished `index.html` demo before the W1 result is frozen. The visual explanation should be written around what the test actually showed, not around the result we hoped to see.
