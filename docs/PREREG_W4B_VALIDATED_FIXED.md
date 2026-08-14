# W4b preregistration — brute-force validated fixed-policy adversary

Date frozen: 2026-08-14

Status: **FROZEN BEFORE W4b VALIDATION/SECOND-HOLDOUT EVALUATION**

Parent result: `docs/W4_RESULT.md`

## Why this exists

W4's nuisance-aware adaptive arm beat the fixed schedule selected analytically from the clean response model by `+3.50` accuracy points on its frozen holdout, with paired bootstrap 95% CI `[+1.04, +6.00]` points.

That fixed schedule is not the strongest boring incumbent.

An engineer who knows the nuisance distribution could take a separate labelled validation set, brute-force every legal fixed three-query policy, and deploy the best one. If that schedule matches the adaptive policy on a second untouched holdout, the W4 “attention/query” increment was mainly a weak fixed baseline.

## Frozen mechanism

Use exactly the W4 medium, 42-D receipts, training response model, nuisance quotient, nuisance distribution, and three-query budget.

No raw arm is needed. W4 already established that nuisance handling dominates raw inference. W4b isolates only:

```text
receipt-dependent adaptive query
versus
strongest validation-selected fixed query sequence
```

## Fixed-policy search space

Enumerate every ordered schedule of three distinct probe indices:

```text
8 * 7 * 6 = 336 schedules
```

The order is included even though the nuisance distribution is stationary, so no hidden “fixed schedule ordering” excuse remains.

For each validation episode, precompute quotient log-likelihoods for every `(round, probe, candidate_class)` combination. Score all 336 schedules by classification accuracy. Choose the unique lexicographically earliest schedule among ties.

The adaptive policy is **not** tuned on validation outcomes; it remains the frozen W4 posterior-weighted residualized-disagreement rule.

## Frozen data split

Training response model remains:

```text
MODEL_SAMPLES_PER_CELL = 250
MODEL_SEED_START = 1_500_000
```

W4's original holdout beginning at `9_500_000` is permanently off limits for W4b model selection.

W4b validation:

```text
VALIDATION_EPISODES = 3200
VALIDATION_SEED_START = 11_000_000
```

W4b second holdout:

```text
HOLDOUT_EPISODES = 2400
HOLDOUT_SEED_START = 15_000_000
BOOTSTRAP_SAMPLES = 20_000
BOOTSTRAP_SEED = 20260814
```

All class labels are balanced by cycling class id `episode_index % 8`.

## Primary question and verdict

The adaptive query policy earns the stronger claim only if, on the second holdout:

1. adaptive accuracy exceeds the validation-selected fixed accuracy by at least `+0.01`;
2. paired bootstrap 95% CI for adaptive minus fixed is strictly above zero;
3. adaptive accuracy remains at least `0.45`;
4. minimum adaptive per-class accuracy remains at least `0.35`.

If all pass:

```text
ADAPTIVE_QUERY_SURVIVES_VALIDATED_FIXED
```

If adaptive is numerically higher but clause 1 or 2 fails:

```text
ADAPTIVE_QUERY_NOT_SEPARATED_FROM_VALIDATED_FIXED
```

If the selected fixed policy is numerically equal or better:

```text
VALIDATED_FIXED_KILLS_ADAPTIVE_INCREMENT
```

W4's nuisance-model result remains positive regardless. W4b is allowed to kill only the additional claim that receipt-dependent query selection is needed beyond a well-selected fixed design.

## Stopping line

Do not respond to a W4b null by:

- increasing the query budget;
- changing nuisance strength;
- changing the pair-distance score;
- changing the validation split;
- adding another hand-designed fixed baseline.

A null closes the current synthetic query-selection ladder. A future continuation must use a different external medium/task where queries have real cost or where the nuisance structure is not authored for WildIdea.
