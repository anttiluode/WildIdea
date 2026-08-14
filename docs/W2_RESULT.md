# W2 result — adaptive probe choice earns its keep

Date: 2026-08-14

GitHub Actions run: `31797899673`

Evaluated commit: `876be87485e00375634fcbb9be11ee1af1fc7111`

Artifact zip SHA256: `680e95889592e3aae053842b50a917eb8093ffe22c69ddc3e156365ce57e4d30`

## Frozen verdict

```text
ADAPTIVE_PROBING_EARNS_KEEP
```

W2 used eight possible hidden damping locations and only three writes. Every active policy used the same learned Gaussian response table and the same write budget. The only difference was **where the next probe was placed**.

The strongest fixed three-probe design selected from the training response table was:

```text
probe indices  1, 3, 7
ring sites     12, 28, 60
```

## Held-out accuracy

```text
random 3-probe schedule     0.622500
best fixed 3-probe design   0.671875
adaptive 3-probe policy     0.726875
```

So:

```text
adaptive - fixed    +0.055000
adaptive - random   +0.104375
```

The paired 95% bootstrap interval for adaptive minus fixed was:

```text
[+0.023125, +0.086875]
```

All preregistered criteria passed.

## Per-class adaptive accuracy

```text
0  0.840
1  0.800
2  0.780
3  0.600
4  0.700
5  0.600
6  0.770
7  0.725
```

No class fell below the preregistered 0.50 floor.

## Did the policy really branch?

Yes. The adaptive policy produced **13 distinct three-probe sequences** on the held-out set.

The most common examples were:

```text
0 -> 7 -> 1   365 episodes
0 -> 2 -> 3   325 episodes
0 -> 7 -> 6   273 episodes
0 -> 2 -> 4   236 episodes
0 -> 2 -> 6   191 episodes
```

The first probe is always the same by symmetry. The second and third probe locations change because the previous ring-down receipt changed the posterior over hidden states.

That is the first result in this line where the slogan

> **what I can read now changes what I should touch next**

has been turned into an actual benchmark rather than an analogy.

## What W2 supports

A small state-dependent probe policy can use the consequence of an earlier perturbation to select a more informative next perturbation than the strongest fixed three-probe design found from the same response model.

That is a real, narrow engineering result.

## What W2 does not support

This is still standard active-sensing / Bayesian experimental-design territory. The result does not establish novelty over that literature, and it does not show that a brain contains a literal scout.

W2 also resets the low-energy field before each short probe trial. That was deliberate: it isolates **adaptive action selection** cleanly. It means W2 is not yet the stronger "continuous surfer in one persistent medium" experiment.

A future W3 would remove those resets and ask whether a tiny controller can keep querying a continuously evolving recurrent medium, where every probe changes the state that later probes inherit.

At this point there is enough empirical structure to build the first HTML explanation honestly: passive -> scheduled active -> rotation audit -> adaptive choice.
