# W4b brute-force validated fixed-policy adversary — result

Date: 2026-08-14

Workflow run: `31806187808`

Frozen preregistration: `docs/PREREG_W4B_VALIDATED_FIXED.md`

Verdict:

```text
ADAPTIVE_QUERY_NOT_SEPARATED_FROM_VALIDATED_FIXED
```

## Why this gate mattered

W4 found a `+3.50` percentage-point advantage for nuisance-aware adaptive probing over a fixed schedule selected analytically from the clean response geometry.

W4b gave the fixed-policy incumbent a much stronger opportunity:

- `3200` nuisance-matched labelled validation episodes;
- all `336` ordered three-probe schedules;
- classification accuracy used directly for schedule selection;
- a completely separate `2400`-episode second holdout;
- adaptive policy left unchanged from W4.

## Validation-selected fixed policy

The best validation schedule was:

```text
probe indices [0, 4, 2]
sites         [4, 36, 20]
validation accuracy 0.533125
```

The top of the validation table was not a single absurd outlier; several schedules clustered around `0.53` accuracy.

## Untouched second holdout

```text
validated fixed accuracy   0.535833
adaptive accuracy          0.536250
adaptive - fixed           0.000417
```

That is about `+0.042` percentage points: practically zero.

Paired bootstrap 95% CI:

```text
[-0.02375, +0.02458]
```

The interval spans zero widely, and the preregistered `+0.01` minimum improvement clause fails.

Adaptive per-class accuracy remained healthy enough for the task:

```text
[0.6367, 0.5400, 0.5600, 0.4167,
 0.5167, 0.4333, 0.6233, 0.5633]
```

The adaptive policy still produced 18 distinct query sequences. Branching therefore occurred; it simply did not buy accuracy beyond a well-selected fixed policy in this stationary synthetic task.

For context, the original W4 analytically selected fixed schedule `[0,2,6]` scored `0.5275` on this second holdout. The validation-selected fixed schedule improved that to `0.535833`, essentially closing the entire adaptive gap.

## Honest ledger

### Survives

The nuisance quotient is the major W4 result:

```text
raw adaptive       0.21125   (W4 first holdout)
quotient adaptive  0.53750
```

Declared gain/offset/ramp directions were able to masquerade as model disagreement unless they were removed from the response geometry. The TWC-inspired separation between raw response size and residualized identifiable structure earned its keep in this toy.

### Does not survive

The stronger claim

> receipt-dependent disagreement probing is needed beyond a well-selected fixed three-probe policy

is **not supported**.

The W4 adaptive advantage was a baseline-sensitive effect. Once the fixed schedule was selected by brute-force validation under the real nuisance distribution, fixed and adaptive performance were indistinguishable.

### Already dead from W3/K2

Dynamic chart growth had already failed to beat a preallocated model bank once both could use disagreement-directed probes.

## Current boundary

The synthetic ladder now says:

```text
controlled local perturbation can help                 W1   yes
scheduled effect survives rotation                     W1b  yes
adaptive probing beats a simple fixed design           W2   yes
chart growth is architecturally necessary              W3   no
nuisance-aware response geometry matters               W4   yes
adaptive query beats a strongly selected fixed policy  W4b  no
```

Do not open W4c by changing the nuisance process, query budget, scoring rule, or fixed-policy baseline.

If WildIdea continues, it must move to a different external medium/task where at least one of the following is true:

- a query has genuine wall-clock, energy, money, or intervention cost;
- the environment changes online so a fixed validated schedule can become stale;
- nuisance structure comes from someone else's instrument/data rather than being authored for this benchmark;
- the action changes the future state in a way that cannot be precompiled into one stationary fixed schedule.

That is the remaining place where `what should I query next?` can still be more than ordinary offline design.
