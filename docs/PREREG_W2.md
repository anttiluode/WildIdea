# WildIdea W2 — adaptive probe-choice gate

Status: **FROZEN AFTER W1/W1b, BEFORE W2 EVALUATION**

Date: 2026-08-14

W1 showed that scheduled read/write probing can reveal a hidden damping defect better than passive observation. W1b showed that this survives randomized probe order and five fixed feature maps.

W2 asks the harder question:

> **When the write budget is too small to cover every candidate location, can the result of one probe change where the system should probe next, and does that adaptive choice beat the strongest fixed probe schedule?**

This is still ordinary active sensing / system identification. It is not a consciousness test.

## Fresh task

Use a 64-site damped wave ring with one hidden high-damping region centered at one of eight candidate addresses:

```text
4, 12, 20, 28, 36, 44, 52, 60
```

Only **three** probes are allowed, so exhaustive coverage is impossible.

Each probe is a standardized local velocity impulse followed by a short ring-down observation. To keep the inference model auditable, each probe trial begins from a fresh low-energy state sampled from the same distribution. This is closer to classical material/system identification than to a continuously self-modifying brain-like medium; the continuous-state version is a later question.

## Frozen medium / probe

```text
sites                        64
candidate hidden centers      8
ring-down steps               14
dt                            0.08
wave coupling c^2             0.9
background damping            0.10
background stiffness          0.10
defect extra damping          0.35
defect Gaussian sigma         7.0 sites
initial x sigma               0.01
initial velocity sigma        0.01
ambient velocity noise        0.003 / step
probe amplitude               0.8
probe budget                  3
```

The scalar probe receipt is frozen as:

```text
log( late local patch energy / early local patch energy )

early = steps 2:6
late  = steps 9:13
patch = probe site plus immediate left/right neighbors
```

## Learned response model

Before evaluation, estimate for every `(hidden_class, probe_address)` pair the mean ring-down receipt from training simulations. Estimate one pooled observation variance per probe address across classes.

The downstream inference model is a simple Gaussian likelihood table. Every active policy uses **the same learned response model**; only probe selection differs.

A development-seed pilot was used to verify that the task is numerically nondegenerate and that the adaptive policy actually branches. Those development seeds are excluded from W2.

Frozen response-model seeds begin at `1500000`.

## Policies

### FIXED-3 — strongest predetermined schedule

Choose one 3-address set before seeing any test episode. The set is selected **only from the learned training response table**, by maximizing:

1. minimum pairwise class Mahalanobis separation;
2. then mean pairwise separation as tie-breaker.

No test labels are used to select the schedule.

At test time, probe those three addresses and update the same Gaussian posterior after each observation.

### RANDOM-3

Choose three distinct addresses uniformly without replacement, independently of the hidden class. Use the same Gaussian posterior update.

### ADAPTIVE-3

Start with probe address 0 (candidate center 4; symmetry makes the first address arbitrary).

After each receipt, update the posterior over eight hidden classes. Choose the next unused probe address maximizing the posterior-weighted variance of predicted class means divided by that probe's learned noise variance:

```text
score(p) = Var_posterior[ mean_response(class, p) ] / noise_variance(p)
```

This is a cheap information-seeking heuristic. It is not trained by reinforcement learning.

## Fresh evaluation

```text
response-model samples  250 per class x probe
held-out episodes       1600 (200 per class)
response-model seed     1500000 + deterministic class/probe/sample offset
test seed start         2500000
bootstrap samples       20000
bootstrap seed          20260814
```

## Primary gate

Call:

```text
ADAPTIVE_PROBING_EARNS_KEEP
```

only if all are true:

1. ADAPTIVE-3 held-out accuracy >= **0.60**;
2. ADAPTIVE-3 beats FIXED-3 by at least **3 percentage points**;
3. paired bootstrap 95% CI for ADAPTIVE-3 minus FIXED-3 is entirely above zero;
4. ADAPTIVE-3 beats RANDOM-3 by at least **5 percentage points**;
5. mean per-class ADAPTIVE-3 accuracy is >=0.60 and no class accuracy is below **0.50**;
6. the adaptive policy produces at least **4 distinct three-probe sequences** on the test set, proving the later probe choices actually depend on observed state;
7. every policy uses exactly three writes of amplitude `0.8`.

Otherwise:

```text
ADAPTIVE_PROBING_NOT_EARNED
```

## Interpretation

A pass would support a narrow but real engineering statement:

> A small state-dependent probe policy can use the result of an earlier perturbation to choose a more informative next perturbation than the strongest fixed three-probe design found from the same learned response model.

This would be a stronger result than W1/W1b because the write action itself branches on what became readable.

It would still not establish novelty over active experimental design, Bayesian sensing, adaptive system identification, or biological scanning mechanisms.

## HTML rule

If W2 finishes cleanly, pass or fail, we have enough empirical structure to build the first `index.html` around the actual sequence of results:

```text
passive -> scheduled active -> rotation audit -> adaptive choice
```

Do not alter W2 after seeing the held-out result in order to make the demo prettier.
