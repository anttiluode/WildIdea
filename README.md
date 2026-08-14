# WildIdea

A small engineering test born from a large speculative question.

The speculation was about minds, present moments, internal sweeps, fields, prediction, bodily state, and the old COM-instanton/scout toy. This repository does **not** treat those ideas as evidence.

The first thing it tests is much smaller:

> **Can a tiny moving read/write process extract useful information from a fixed dynamical medium that passive observation misses?**

The working picture is:

```text
external action
    = move the organism through world-space

internal probe
    = perturb a dynamical state-space and read what comes back
```

That is ordinary active sensing / system identification territory. The interesting question is whether the particular minimal architecture earns anything under controlled comparison.

## W1

`docs/PREREG_W1.md` freezes the first benchmark before evaluation.

A 32-site damped wave ring contains one hidden high-damping region. Five readout conditions attempt to identify which quadrant contains it:

```text
A  static global readout
B  recurrent global readout
C  moving local scout, read only
D  moving local scout, read + controlled writes
E  random-walk local scout, equal write budget
```

Every learned output uses the same 16-dimensional fixed feature state and the same ridge classifier. D must beat the strongest passive baseline and the equal-energy random-write adversary to pass.

Run:

```bash
python wildidea_w1.py --json artifacts/w1_result.json
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## What a pass would mean

Only that active probing earned its keep in this frozen toy task.

It would **not** establish a neuroscience or consciousness theory. In W1 the probe path is scheduled rather than learned. A later experiment would have to ask whether state-dependent adaptive probing earns anything over predetermined probing and standard active-sensing baselines.

## What happens to the HTML demo

Not yet.

The visual page will be built **after** W1 is frozen and read, so the demo explains the result reality gave us rather than turning the hoped-for result into a polished story first.
