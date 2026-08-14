# WildIdea

A small engineering test born from a large speculative question.

The speculation was about minds, present moments, internal sweeps, fields, prediction, bodily state, and the old COM-instanton/scout toy. This repository does **not** treat those ideas as evidence.

The engineering question is smaller:

> **Can a tiny moving read/write process extract useful information from a fixed dynamical medium that passive observation misses — and can what it reads change where it should probe next?**

The working picture is:

```text
external action
    = move the organism through world-space

internal probe
    = perturb a dynamical state-space and read what comes back
```

That is ordinary active sensing / system identification territory. The point of the repo is to make the wild intuition earn increasingly less-wild statements.

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

The adaptive policy produced 13 distinct three-probe sequences; later probe locations really changed as a function of earlier ring-down receipts.

Frozen verdict:

```text
ADAPTIVE_PROBING_EARNS_KEEP
```

See `docs/PREREG_W2.md` and `docs/W2_RESULT.md`.

## Interactive page

`index.html` now tells the result sequence and contains a browser illustration of the frozen W2 inference loop.

The browser toy is **illustration, not evidence**. The evidence is the frozen GitHub Actions runs and result receipts in `docs/`.

## Run locally

```bash
python wildidea_w1.py --json artifacts/w1_result.json
python wildidea_w1b.py --json artifacts/w1b_result.json
python wildidea_w2.py --json artifacts/w2_result.json
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## What the current results mean

They support a narrow engineering progression:

```text
passive observation
      ↓
controlled local perturbation helps
      ↓
result survives probe-order rotation
      ↓
previous result can improve next probe choice
```

They do **not** establish a neuroscience or consciousness theory, and none of this is claimed as novelty over active sensing, Bayesian experimental design, or system identification.

W2 also resets the low-energy medium before each short probe trial. The stronger speculative picture — a tiny controller continually surfing one persistent evolving medium, where every write changes the state inherited by later writes — remains untested.

That is the natural W3 if the line continues.
