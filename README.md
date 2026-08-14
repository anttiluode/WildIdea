# WildIdea

A small engineering test born from a large speculative question.

The speculation was about minds, present moments, internal sweeps, fields, prediction, bodily state, and the old COM-instanton/scout toy. This repository does **not** treat those ideas as evidence.

The engineering question became progressively narrower:

> **When a system can perturb an addressable dynamical medium and read what comes back, what information should determine the next intervention?**

That is active sensing / system identification / optimal experimental design territory. WildIdea's job is not to rename those fields. Its job is to make the original intuition survive boring baselines, nuisance, and explicit stopping lines.

## Current result ladder

### W1 — scheduled active probing

A 32-site damped wave ring contains one hidden high-damping region.

```text
static global             28.375 %
recurrent global          25.500 %
moving scout, read only   30.875 %
moving scout, read+write  50.000 %
random-walk equal writes  29.875 %
```

Frozen verdict:

```text
ACTIVE_PROBING_EARNS_KEEP
```

See `docs/PREREG_W1.md` and `docs/W1_RESULT.md`.

### W1b — rotation / observer robustness

The W1 probe-order asymmetry was attacked with fresh episodes, four balanced scan phases and five fixed feature-map seeds.

```text
mean active read+write       45.525 %
mean strongest-passive gain  +19.3 points
mean random-write gain       +20.2 points
```

Frozen verdict:

```text
ACTIVE_PROBING_SURVIVES_ROTATION
```

See `docs/PREREG_W1B.md` and `docs/W1B_RESULT.md`.

### W2 — adaptive probe choice

Eight possible hidden locations, only three writes. Every active policy uses the same learned Gaussian response table and identical write budget.

```text
random 3-probe schedule     62.2500 %
best fixed 3-probe design   67.1875 %
adaptive 3-probe policy     72.6875 %
```

Adaptive minus fixed: `+5.50` points, paired bootstrap 95% CI `[+2.31, +8.69]` points.

Frozen verdict:

```text
ADAPTIVE_PROBING_EARNS_KEEP
```

See `docs/PREREG_W2.md` and `docs/W2_RESULT.md`.

### W3/K2 boundary — chart growth does not earn architectural importance

A later persistent-medium experiment was run outside the public repo. Its strongest boring adversary used a preallocated bank of three alternative models.

Reported switch/re-entry recovery in probes:

```text
fixed bank + random probes        84.6 / 56.8
fixed bank + disagreement probes   2.6 /  2.5
predictable growth + disagreement  3.3 /  1.9
```

The fixed bank matched the growing-chart system once both could probe where their models disagreed. Dynamic chart growth therefore does **not** earn a special architectural claim from that toy.

See `docs/W3_OFFREPO_BOUNDARY.md`. The note explicitly records that this result was supplied from the off-repo run rather than independently reproduced here.

### W4 — TransientWaveCompiler contact: nuisance quotient matters

W4 imported a lesson earned independently in `TransientWaveCompiler`: large response differences are not necessarily identifiable physical differences when gain/offset/delay/other nuisance directions can explain them.

WildIdea's 42-D ring-down receipt was therefore evaluated in two geometries:

```text
RAW
ordinary response difference

QUOTIENT
response difference after removing declared
measurement-nuisance directions
```

Frozen first holdout (`2400` episodes):

```text
raw adaptive         21.125 %
quotient random      50.208 %
quotient fixed       50.250 %
quotient adaptive    53.750 %
```

Adaptive minus the analytically selected quotient-fixed schedule was `+3.50` points, paired 95% CI `[+1.04, +6.00]` points.

Frozen verdict:

```text
NUISANCE_QUOTIENT_QUERY_EARNS_KEEP
```

The large effect is the nuisance quotient, not the adaptive policy.

See `docs/PREREG_W4_NUISANCE_QUOTIENT.md` and `docs/W4_RESULT.md`.

### W4b — strong fixed baseline kills the adaptive increment

W4's fixed schedule was still not the strongest boring incumbent. W4b used `3200` separate nuisance-matched labelled validation episodes and brute-forced **all 336 ordered three-probe schedules**, then froze the best schedule before a second untouched `2400`-episode holdout.

Validation selected:

```text
probe indices [0, 4, 2]
sites         [4, 36, 20]
```

Second holdout:

```text
validated fixed      53.583 %
adaptive             53.625 %
difference           +0.042 percentage points
95% CI               [-2.375, +2.458] points
```

Frozen verdict:

```text
ADAPTIVE_QUERY_NOT_SEPARATED_FROM_VALIDATED_FIXED
```

So the W4 adaptive advantage was baseline-sensitive. In this stationary synthetic task, a well-selected fixed query sequence performs essentially identically.

See `docs/PREREG_W4B_VALIDATED_FIXED.md` and `docs/W4B_RESULT.md`.

## What survived the full ladder

The current ledger is deliberately less exciting than the original story:

```text
controlled local perturbation can expose hidden state            yes
that effect survives a simple probe-order/observer audit          yes
adaptive query can beat a simple fixed design                     yes
online chart growth is required                                   no
measurement nuisance must be separated from physical disagreement yes
adaptive query beats a strongly validation-selected fixed policy  no
```

The strongest surviving cross-repo lesson is therefore:

> **Before asking where to probe next, determine which predicted differences are actually distinguishable from nuisance.**

That is where `TransientWaveCompiler` genuinely changed WildIdea. TWC's response-space work distinguishes raw sensitivity from the part of a candidate response that remains outside the fitted physical+nuisance tangent space. WildIdea W4 used a simplified version of that discipline and it mattered much more than the adaptive policy itself.

`Vahti` contributes the complementary discipline: a measurement/query score must discharge cheap invariance, degeneracy, null and known-answer obligations before its output is interpreted. W4 adopted that style with explicit pre-outcome obligations for the nuisance quotient.

## Stopping line

Do **not** open W4c by changing nuisance strength, query budget, scoring rule, or fixed-policy baseline until adaptivity wins.

The current synthetic query-selection ladder is closed.

A legitimate continuation needs a different external task where at least one of these is true:

- queries have genuine wall-clock, energy, money, or intervention cost;
- the environment changes online, so a fixed validated schedule can become stale;
- nuisance comes from someone else's instrument/data rather than a WildIdea-authored process;
- an intervention changes future state in a way that cannot be precompiled into one stationary schedule.

That is the remaining territory for the original scout intuition.

## Interactive page

`index.html` illustrates the earlier W2 inference loop. It is **illustration, not evidence**. The frozen evidence lives in the preregistrations, Actions runs, and result receipts.

## Run locally

```bash
python wildidea_w1.py --json artifacts/w1_result.json
python wildidea_w1b.py --json artifacts/w1b_result.json
python wildidea_w2.py --json artifacts/w2_result.json
python wildidea_w4_nuisance.py --json artifacts/w4_nuisance_result.json
python wildidea_w4b_validated_fixed.py --json artifacts/w4b_validated_fixed_result.json
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Brain / consciousness boundary

The repo began from brain and consciousness speculation, but none of the current gates establishes a neural mechanism.

At most, the engineering work sharpens a question that can be taken elsewhere:

> when several ongoing processes predict different consequences of possible interventions, which differences remain physically/observationally meaningful after nuisance is removed, and when is an online query actually worth paying for?

That question can be asked of brains, bodies, instruments, software systems, or the external world. WildIdea currently answers it only for its own controlled testbeds.
