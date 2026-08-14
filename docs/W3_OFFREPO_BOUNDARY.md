# W3 off-repo boundary — persistent medium, chart growth, and the fixed-bank adversary

Date: 2026-08-14

Status: **conversation-supplied result / architectural boundary, not independently reproduced in this repository**

The public WildIdea history currently ends at W2. A later persistent-medium experiment was run outside this repository during the discussion that followed W2. This note records the result so a later session does not rediscover or overclaim it.

## What was tested

The later toy used a never-reset damped wave medium, online transfer-kernel models (“charts”), regime switches, re-entry to a previously encountered regime, and an unlearnable noise regime.

The first version suggested that a held-out-predictability growth rule could create new charts without spawning on pure surprise. That mechanism was then attacked with stronger boring baselines.

The reported common-threshold recovery times, in probes, were:

| arm | switch | re-entry |
|---|---:|---:|
| none / random probes | 87.3 | 79.0 |
| replay / random probes | 192.4 | 190.9 |
| fixed bank of 3 / random probes | 84.6 | 56.8 |
| **fixed bank of 3 / disagreement probes** | **2.6** | **2.5** |
| predictable-growth / random probes | 84.4 | 29.1 |
| predictable-growth / disagreement probes | 3.3 | 1.9 |

The key adversarial result was that the preallocated three-chart bank with disagreement-directed probing matched the dynamically growing chart system. The nominal switch advantage even favored the fixed bank (about 2.6 versus 3.3 probes), and the reported paired uncertainty did not support a growth advantage.

## What died

Do **not** carry forward the claim:

> structured residual -> dynamically spawning charts is an important new architecture.

The fixed-bank adversary removed the need for that interpretation in this toy. The predictable-residual rule still behaved like a useful model-set adaptation / noise-filter mechanism, but it did not earn a special architectural role.

The replay arm was deliberately simple uniform replay across incompatible regimes and performed worse than no replay. That is a weak baseline, not evidence against modern replay/contextual adaptation.

## What survived

The dominant effect was already present without growth:

> **when alternative models predict different consequences, choose the next intervention where those predicted consequences diverge most.**

Within the fixed bank, replacing random probes with disagreement-directed probes reportedly reduced switch recovery from about `84.6` probes to `2.6`, across all reported seeds.

This is active learning / optimal experimental design / auxiliary input design territory. WildIdea does not claim the general principle.

The engineering question that remains interesting is narrower:

> Does disagreement-directed intervention still help when the medium, measurement nuisance, and query cost are not chosen to make disagreement clean?

## Why this changes the next experiment

W2 used a learned response table in a clean synthetic medium. The later W3 toy made the medium persistent but still gave the query policy a comparatively clean disagreement signal.

TransientWaveCompiler supplied a harder lesson independently: a large response direction can be diagnostically useless when it lies in the span of already-fittable physical or measurement-nuisance directions. Its identifiability tools explicitly project candidate response directions away from those nuisance/model tangents.

Therefore the next WildIdea gate should not add another growth rule. It should attack the surviving disagreement policy with nuisance that can masquerade as model disagreement.

See `docs/PREREG_W4_NUISANCE_QUOTIENT.md`.
