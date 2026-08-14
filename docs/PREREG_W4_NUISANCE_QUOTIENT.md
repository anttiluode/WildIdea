# W4 preregistration — nuisance-quotiented disagreement probing

Date frozen: 2026-08-14

Status: **FROZEN BEFORE HOLDOUT EVALUATION**

## Why this gate exists

W2 established, in a clean synthetic wave medium, that a three-query adaptive policy can outperform the best fixed three-query schedule.

A later off-repo W3/K2 adversary killed the special role of dynamic chart growth: a fixed bank of alternative models plus disagreement-directed probing matched the growing-chart system. See `W3_OFFREPO_BOUNDARY.md`.

That leaves a narrower surviving primitive:

> choose the next intervention where currently plausible models predict different consequences.

TransientWaveCompiler supplies an adversary to that primitive. In a reciprocal inverse problem, a large candidate response can be diagnostically useless if it lies in the span of already-fittable physical or measurement-nuisance directions. TWC therefore separates raw sensitivity from *residualized novelty* after projecting away nuisance/model tangents.

W4 asks whether the same distinction matters for WildIdea.

## Question

> Under measurement-chain drift that can masquerade as model disagreement, does an adaptive query policy operating in a nuisance-quotiented response space outperform (a) raw disagreement probing and (b) the best fixed nuisance-aware three-probe design?

This is not a novelty claim over optimal experimental design, active sensing, profile likelihood, nuisance projection, or invariant representation methods.

## Medium

Use the same 64-site damped wave ring and eight hidden damping-defect locations as W2.

The receipt changes from W2's scalar early/late-energy ratio to the full local ring-down trace:

- 14 time steps;
- three neighboring read sites around the probe;
- flattened to a 42-dimensional receipt.

The underlying physical simulation parameters remain the W2 values.

## Measurement nuisance

The *test* receipt is transformed independently for each queried probe:

```text
y = gain * x + offset * 1 + slope * ramp
```

with frozen nuisance distribution:

```text
log(gain) ~ Normal(0, 0.25)
offset    ~ Normal(0, 0.04)
slope     ~ Normal(0, 0.04)
```

The ramp runs linearly from `-1` to `+1` over the 14 time samples and is repeated for the three local channels.

These nuisance variables are not hidden defect information. They deliberately create an out-of-training measurement shift.

## Two inference geometries

### RAW

Class likelihood uses ordinary squared Euclidean residual to the learned clean class/probe mean, scaled by the pooled within-probe variance.

Probe information score uses ordinary posterior-weighted between-class Euclidean separation.

### QUOTIENT

For candidate class mean `mu`, score an observed receipt `y` after fitting the three-dimensional nuisance model

```text
y ~= a * mu + b * 1 + c * ramp
```

by least squares. The remaining residual is the class mismatch.

For query selection, pairwise class-mean difference `d = mu_a - mu_b` is projected away from the nuisance tangent span

```text
span(mean(mu_a, mu_b), 1, ramp)
```

and only the residualized difference contributes to disagreement.

This is deliberately analogous to TWC's distinction between raw candidate sensitivity and response novelty after nuisance/model projection. It is not claimed to reproduce TWC's exact filter geometry.

## Arms

All arms receive exactly three writes.

1. `raw_adaptive` — raw likelihood + raw disagreement query selection.
2. `raw_fixed` — raw likelihood + best fixed raw three-probe schedule.
3. `quotient_random` — quotient likelihood + random three-probe schedule.
4. `quotient_fixed` — quotient likelihood + best fixed three-probe schedule under residualized pair separation.
5. `quotient_adaptive` — quotient likelihood + residualized disagreement query selection.

Fixed schedules are selected only from the training response model, never from holdout outcomes.

## Instrument obligations before scoring outcomes

The implementation must pass all of the following:

- `IDENTICAL_ZERO`: identical model responses have zero residualized disagreement.
- `NUISANCE_ONLY_ZERO`: a response differing only by gain + offset + ramp is approximately zero-distance in quotient geometry.
- `STRUCTURE_DETECTED`: adding a component outside the nuisance span produces strictly positive quotient distance.
- `PAIR_SYMMETRY`: swapping model A/B leaves pair distance unchanged.
- `LABEL_INVARIANT`: permuting class labels leaves each probe's uniform-prior information score unchanged.
- `TRUE_NUISANCE_FIT`: a synthetic nuisance-transformed class mean is fitted back to near-zero quotient residual for the generating class.

If any obligation fails, the benchmark has no scientific verdict.

## Frozen sample sizes and seeds

Training response model:

```text
250 clean physical receipts per class x probe cell
MODEL_SEED_START = 1_500_000
```

A small design pilot was used while constructing the benchmark and is **not evidence**. It used only 80 training samples/cell and test episodes beginning at `2_500_000`. Its outcomes must not be reported as the W4 result.

The holdout is disjoint:

```text
TEST_EPISODES = 2400
TEST_SEED_START = 9_500_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814
```

No threshold or nuisance parameter may be changed after the holdout run begins.

## Primary success clauses

`NUISANCE_QUOTIENT_QUERY_EARNS_KEEP` requires all of:

1. instrument obligations all pass;
2. quotient-adaptive accuracy `>= 0.45`;
3. quotient-adaptive minus raw-adaptive `>= +0.15`;
4. quotient-adaptive minus quotient-random `>= +0.02`;
5. quotient-adaptive minus quotient-fixed `>= +0.01`;
6. paired bootstrap 95% CI for quotient-adaptive minus quotient-fixed is strictly above zero;
7. minimum per-class quotient-adaptive accuracy `>= 0.35`;
8. quotient-adaptive uses at least four distinct three-probe sequences.

If clauses 2–4 pass but clauses 5–6 fail, the verdict is specifically:

```text
NUISANCE_MODEL_HELPS_INFERENCE_BUT_ADAPTIVE_QUERY_NOT_EARNED
```

That outcome would mean the TWC-style nuisance quotient was useful, but the WildIdea attention/query mechanism did not add value beyond a fixed nuisance-aware design.

If quotient and raw arms are comparable, the cross-repo mechanism is not earned.

## Interpretation boundary

A positive W4 would establish only this toy engineering statement:

> when measurement nuisance can imitate physical/model disagreement, removing declared nuisance directions can improve which active query is selected under a fixed query budget.

It would not establish a brain mechanism, consciousness theory, general attention theory, or novelty over active experiment design.
