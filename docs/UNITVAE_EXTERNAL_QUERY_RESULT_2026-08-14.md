# External result: unitVAE teacher-query scheduling — 2026-08-14

This is the first WildIdea follow-up run on an existing practical online-learning system with a **real expensive teacher query** and persistent consequences.

It is not a brain/consciousness result and it is not evidence for a special ChiralField mechanism.

## Substrate

The tested system used the `unitvae4` student architecture:

```text
webcam/video frame
      |
      v
cheap adaptive encoder/decoder student
      |
      +-------------------------------+
                                      |
query policy decides whether          |
to buy an expensive SVD-VAE target    |
      |                               |
      v                               |
real VAE encode/decode                 |
      |                               |
      v                               |
(frame, latent, reconstruction)        |
enters replay buffer ------------------+
      |
      v
later student updates sample accumulated receipts
```

The benchmark used real prerecorded webcam clips. Teacher targets were acquired with the actual Stable Video Diffusion VAE and cached once, together with measured teacher latency, so policy replay could use identical teacher receipts while still charging the real acquisition cost.

Benchmark targets used the VAE posterior mode/mean rather than stochastic latent sampling.

## External acquisition cost

Calibration clip:

```text
2456 frames
teacher acquisition time 754,889.98 ms
wall-clock precache       938.50 s
```

Holdout clip:

```text
1855 frames
teacher acquisition time 574,095.29 ms
wall-clock precache       714.26 s
```

The average real teacher acquisition was therefore roughly 0.31 s/frame on this machine.

## Calibration compiler

A periodic schedule family was searched on the calibration clip before holdout inspection.

Frozen calibration Pareto set:

| interval | queries | charged teacher ms | mean eval reconstruction MSE |
|---:|---:|---:|---:|
| 60 | 48 | 15,084.60 | 0.00479811 |
| 15 | 130 | 40,246.83 | 0.00479690 |
| 20 | 130 | 40,308.85 | 0.00477401 |
| 5  | 375 | 115,741.17 | 0.00472759 |

The key calibration observation was already that teacher-call count had sharply diminishing returns: almost eight times more teacher queries (`48 -> 375`) changed mean reconstruction MSE only from about `0.004798` to `0.004728`.

These four periodic schedules are frozen. Do not retune them from holdout.

## Holdout run actually executed

The intended command supplied:

```text
--policies periodic,motion,chiral
--periodic-intervals 60,20,15,5
```

However the current harness uses `--periodic-intervals` only in `sweep` mode. In `compare` mode it executed exactly one periodic arm using the default `--interval 20`.

Therefore the full frozen four-point periodic frontier has **not yet been scored on holdout**.

The actual holdout comparison was:

| policy | teacher queries | charged teacher ms | mean eval recon MSE | p90 eval recon MSE |
|---|---:|---:|---:|---:|
| periodic-20 | 100 | 31,043.10 | 0.00563522 | 0.00470421 |
| motion (`0.05`) | 8 | 2,667.97 | 0.00594888 | 0.00538298 |
| chiral (`2.5`) | 1561 | 482,729.86 | 0.00556643 | 0.00502222 |

All arms used the same seed (`42`), same replay capacity (`128`), same batch size (`4`), and the same `1852` student updates.

## What the run says

### 1. Current motion trigger did not really run as an adaptive policy

The motion arm queried only frames `0..7`: the mandatory bootstrap and nothing afterward.

So the threshold `0.05` was too high for this holdout representation.

Do **not** interpret this as evidence that motion-triggered querying is bad. It was effectively an eight-receipt baseline.

But that baseline itself is informative:

```text
8 teacher receipts
2.67 s charged teacher compute
mean MSE 0.00594888
```

versus periodic-20:

```text
100 teacher receipts
31.04 s charged teacher compute
mean MSE 0.00563522
```

The eight-receipt student used about **91.4% less teacher compute** for only about **5.6% worse mean reconstruction MSE**.

This implies strong receipt redundancy in this task.

### 2. Current Chiral trigger queried almost everything

The Chiral arm made `1561` policy queries out of `1762` approximately query-eligible non-evaluation frames: about **88.6%**.

Compared with periodic-20 it spent about **15.5x** the teacher compute:

```text
482.73 s vs 31.04 s
```

for only about a **1.22% reduction** in mean reconstruction MSE:

```text
0.00563522 -> 0.00556643
```

That does not earn a special Chiral trigger.

It mainly says the fixed Chiral threshold did not transfer into a useful acquisition budget on this clip.

### 3. The important negative result is deeper than threshold tuning

The teacher in this experiment is a deterministic VAE reconstruction map. It is smooth and close to a reconstruction/identity operation across many nearby video frames.

The observed diminishing returns suggest that **external state change does not automatically imply teacher-query value**.

A person can move substantially while the teacher's mapping remains easy for the student to interpolate from a small number of receipts.

This sharpens the WildIdea boundary:

```text
LIVE CHANGE
    is not enough

LIVE CHANGE THAT ALTERS THE MARGINAL VALUE OF AN EXPENSIVE RECEIPT
    is the thing runtime must detect
```

## The KYY/TWC correction to the query signal

The present triggers use environmental change:

```text
frame difference
ChiralField motion mass
```

But KYY's receiver-relative lesson says the relevant quantity is not arbitrary hidden/environmental motion. It is motion that matters to the current receiver/objective.

For this task the receiver is the student model and the consequence is future student error.

So a better conceptual query score is not:

```text
how much did the world move?
```

but:

```text
how likely is another teacher receipt to change the student's future useful predictions enough to justify its cost?
```

TWC says to remove differences that are explainable nuisance. KYY says to remove differences that are null to the receiver. Combined:

```text
raw world change
    -> remove nuisance/redundant change
    -> estimate student-relevant residual
    -> divide by real query cost
```

This is the strongest conceptual upgrade produced by the external run.

## Current verdicts

```text
SPECIAL_CHIRAL_TRIGGER_NOT_EARNED
DEFAULT_MOTION_TRIGGER_NOT_EXERCISED_BEYOND_BOOTSTRAP
UNITVAE_TEACHER_RECEIPTS_HIGHLY_REDUNDANT
FULL_FROZEN_PERIODIC_HOLDOUT_FRONTIER_INCOMPLETE
```

Do not tune motion/chiral thresholds on this holdout and call the tuned result the same gate.

The current holdout has now been seen.

## What may still be completed without violating the freeze

The periodic schedules `60, 15, 20, 5` were frozen on calibration before holdout.

Because the compare harness accidentally ignored `--periodic-intervals`, it is legitimate to execute the three missing frozen periodic arms (`60`, `15`, `5`) on the same cached holdout. This is completion of a predeclared baseline, not post-hoc model selection.

Do not alter the interval set.

After those three arms are scored, the frozen periodic holdout frontier can be closed.

## A new runtime gate, if one is ever run

A fair new adaptive gate would require a **third untouched video**.

Calibration data may be used to choose/freeze:

```text
motion threshold family
Chiral threshold family
or a cheap student-error/value predictor
```

Then one untouched third clip tests the frozen runtime policies against the frozen periodic compiler.

The more promising direction is not another motion threshold. It is a cheap **student-relative query-value signal**: uncertainty, ensemble disagreement, representation novelty, or a learned predictor of expected teacher residual / future loss reduction.

That signal must still face a boring baseline and a real teacher-cost frontier.

## What WildIdea learned

The external experiment changed the question again.

Earlier:

> Does adaptive probing beat fixed probing?

After W4b:

> Does live state make the compiled experiment stale?

After this unitVAE experiment:

> **Does live state contain information about the marginal value of an expensive receipt to the current receiver, beyond what an offline compiler already knows?**

That is narrower, more useful, and easier to falsify.
