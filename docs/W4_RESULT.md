# W4 nuisance-quotiented disagreement probing — frozen result

Date: 2026-08-14

Workflow run: `31805891408`

Frozen preregistration: `docs/PREREG_W4_NUISANCE_QUOTIENT.md`

Verdict:

```text
NUISANCE_QUOTIENT_QUERY_EARNS_KEEP
```

This result is positive under the frozen W4 rules. It is **not** the end of the baseline ladder; a stronger validation-selected fixed-policy adversary is opened below rather than silently treated as already beaten.

## Instrument obligations

All six pre-outcome obligations passed:

```text
IDENTICAL_ZERO        true
NUISANCE_ONLY_ZERO    true
STRUCTURE_DETECTED    true
PAIR_SYMMETRY         true
LABEL_INVARIANT       true
TRUE_NUISANCE_FIT     true
```

The benchmark therefore produced a scientific verdict rather than an instrument failure.

## Holdout result

`2400` disjoint holdout episodes beginning at seed `9_500_000`:

| arm | accuracy |
|---|---:|
| raw adaptive | 0.21125 |
| raw fixed | 0.20333 |
| quotient random | 0.50208 |
| quotient fixed | 0.50250 |
| **quotient adaptive** | **0.53750** |

Key paired differences:

```text
quotient adaptive - raw adaptive        +0.32625
quotient adaptive - quotient random     +0.03542
quotient adaptive - quotient fixed      +0.03500
```

Paired bootstrap 95% CI for quotient-adaptive minus quotient-fixed:

```text
[+0.01042, +0.06000]
```

Per-class quotient-adaptive accuracy:

```text
[0.6533, 0.5467, 0.4700, 0.3900,
 0.5400, 0.4667, 0.6700, 0.5633]
```

The adaptive arm generated 14 distinct three-probe sequences. Most trials began with probe 0 then probe 6, but the third query (and occasionally the second) changed with the earlier receipts.

The training-model fixed designs were:

```text
raw fixed       probes [1, 3, 5] -> sites [12, 28, 44]
quotient fixed  probes [0, 2, 6] -> sites [4, 20, 52]
```

## What was actually learned

The large effect is not “attention.” It is nuisance modeling:

```text
raw adaptive        21.1%
quotient adaptive   53.8%
```

A measurement transform that can be explained by declared gain/offset/ramp directions should not be allowed to masquerade as physical/model disagreement. This is the direct contact imported from TransientWaveCompiler's response-space identifiability discipline.

After that quotient, adaptive probe choice still adds about 3.5 percentage points over the fixed design selected from the clean training response geometry, with a paired interval above zero.

So the narrow W4 result is:

> **Under this frozen nuisance shift, removing declared nuisance directions changes both inference and query selection; the receipt-dependent query policy retains a small additional advantage after nuisance quotienting.**

This remains synthetic active sensing / experimental design. It is not a neuroscience or novelty claim.

## Stronger boring adversary opened immediately

The W4 fixed schedule was selected analytically from pairwise training-model geometry. That is reasonable but not the strongest fixed-policy incumbent.

A stronger baseline can use a completely separate validation set with the *same nuisance process* and exhaustively score every legal ordered three-probe schedule, then freeze the best schedule before a second untouched holdout.

That asks:

> Does adaptive receipt-dependent choice beat the best fixed schedule an engineer could select by brute-force validation under the nuisance distribution?

W4's positive result remains frozen either way. The stronger question is W4b and must not reuse the W4 holdout for schedule selection.
