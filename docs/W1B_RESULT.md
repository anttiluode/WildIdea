# W1b result — active probing survives rotation

Date: 2026-08-14

GitHub Actions run: `31797633133`

Evaluated commit: `7e2402f56594f4c613087e8407c8230f020508b8`

Artifact zip SHA256: `d4c6237c1b921dfa722abca000a6214ed2d3504f096ea26c1be8c0017cae966c`

## Frozen verdict

```text
ACTIVE_PROBING_SURVIVES_ROTATION
```

The W1 asymmetry audit passed every preregistered criterion.

The controlled probe order was independently rotated through all four starting phases, balanced within every hidden class, and the full experiment was repeated under five frozen feature-map seeds.

## Mean held-out accuracy across five feature maps

```text
static global             0.25050
recurrent global          0.26025
moving scout, read only   0.23100
moving scout, read+write  0.45525
random-walk equal writes  0.25325
```

The active arm beat the strongest passive baseline in **5/5** feature seeds.

```text
mean active - strongest passive   +0.193
mean active - random write        +0.202
```

Mean active per-class accuracy after rotation:

```text
class 0  0.472
class 1  0.484
class 2  0.386
class 3  0.479
```

The pathological W1 result in which class 0 was 200/200 correct disappeared. The classes are not perfectly equal, but every preregistered class floor passed and the active advantage remained about twenty percentage points.

## Interpretation

W1 was not merely a lucky temporal alignment between one hidden class and one fixed probe schedule. The same narrow engineering effect survives independent scan rotation and multiple fixed observer maps:

> controlled local perturbation reveals hidden dynamical structure that weak passive observation and equal-energy uncontrolled perturbation do not expose as effectively.

This still does not establish adaptive intelligence. W1/W1b use predetermined coverage.

The next test is W2: only three probes for eight candidate locations, forcing the result of one probe to influence which location is queried next.
