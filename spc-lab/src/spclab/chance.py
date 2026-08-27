"""LEVEL 2 — Chance. What a probability is a statement about.

Level 1 showed that nothing repeats and that many parts make a shape nobody
chose. That shape invites a number — "99.73 % inside" — and Level 6 will price
±3σ with one. Before either is allowed, this level has to earn the right to say
such a thing at all, because almost every misuse of a control chart on a shop
floor is a misreading of what its percentage claims.

Four claims, none asserted:

1. **A proportion is a long-run frequency, not a property of a trial.**
   The relative frequency of heads settles toward one half. It does not
   approach it steadily, and no individual flip is ever "half a head".

2. **The rate converges while the gap grows.** This is the one that kills the
   law of averages, and it is exact rather than rhetorical. In n fair flips the
   expected surplus of heads over tails grows without limit,

       E|S_n| = 2^(1-n) · n · C(n-1, ⌊(n-1)/2⌋)   →   √(2n/π)

   while the expected error in the *rate* is that same quantity over 2n, so it
   shrinks like 1/√n. Both statements are about the same sequence: a deficit is
   never repaid, and the proportion converges anyway because the denominator
   outruns it.

3. **Independence means the sequence has no memory.** After a run of k heads
   the next flip is a head with frequency ½, for every k. "It is due" has no
   arithmetic behind it. This is also the assumption every control limit rests
   on, which is why it is stated here and not later.

4. **What "0.27 %" is a claim about.** Not this part, and not the fraction of
   parts outside specification. It is the rate at which an unchanged process
   trips its own chart. Its consequence is the level's punchline: run the 370
   subgroups that "one alarm in 370" names and the chance of having been
   falsely alarmed at least once is not certainty but

       1 − (1−α)^(1/α) → 1 − 1/e ≈ 63.2 %

   and because the waiting time is geometric, the *typical* wait is shorter
   than the average one — half of all first false alarms arrive by ln2/α.

α and the average run length are **not recomputed here**. They are imported from
the modules that already publish them (`act_style.inside`, `detection`), because
a second computation of a published number is how a figure ends up disagreeing
with its own library.

    PYTHONPATH=src .venv/bin/python -m spclab.chance
"""
from __future__ import annotations

import math

import numpy as np

from spclab.formulas import inside
from spclab.detection import SHEWHART_ARL0

# ---------------------------------------------------------------------------
# The coin. One sequence, reused everywhere, so the page, the act, the figure
# sheets and the tests all describe the same flips.
# ---------------------------------------------------------------------------
FLIPS = 10_000
FLIP_SEED = 2

# Milestones the act reads out. Chosen to span three orders of magnitude,
# because the whole point is that one quantity grows while the other shrinks.
MILESTONES = (100, 10_000, 1_000_000)

# Run lengths whose successor is examined for memory.
STREAKS = (1, 2, 3, 4, 5, 6)

DIE_FACES = np.arange(1, 7)


def flips(n: int = FLIPS, seed: int = FLIP_SEED) -> np.ndarray:
    """`n` fair flips as +1 (head) and −1 (tail)."""
    rng = np.random.default_rng(seed)
    return np.where(rng.random(n) < 0.5, 1, -1)


def rate_trace(seq: np.ndarray) -> np.ndarray:
    """Running relative frequency of heads after each flip."""
    heads = np.cumsum(seq > 0)
    return heads / np.arange(1, len(seq) + 1)


def gap_trace(seq: np.ndarray) -> np.ndarray:
    """Running |heads − tails| — the surplus that never gets repaid."""
    return np.abs(np.cumsum(seq))


def expected_gap_exact(n: int) -> float:
    """E|S_n| for a symmetric ±1 walk, in closed form.

    E|S_n| = 2^(1-n) · n · C(n-1, ⌊(n-1)/2⌋), evaluated through log-gamma
    because 2^(1-n) underflows and C(n-1, ·) overflows long before n reaches a
    million — the largest milestone this level reads out.
    """
    if n <= 0:
        return 0.0
    k = (n - 1) // 2
    log = ((1 - n) * math.log(2.0) + math.log(n)
           + math.lgamma(n) - math.lgamma(k + 1) - math.lgamma(n - k))
    return math.exp(log)


def expected_gap_asymptote(n: int) -> float:
    """The limit form: √(2n/π)."""
    return math.sqrt(2.0 * n / math.pi)


def expected_rate_error(n: int) -> float:
    """E|p̂ − ½| — the same surplus, divided by the 2n that outruns it."""
    return expected_gap_exact(n) / (2.0 * n)


def brute_expected_gap(n: int) -> float:
    """E|S_n| summed over the exact binomial distribution.

    Only usable for small n, and that is its purpose: it checks the closed form
    rather than trusting it.
    """
    return float(sum(math.comb(n, h) * abs(2 * h - n) for h in range(n + 1))
                 / 2.0 ** n)


def streak_memory(n: int = 2_000_000, seed: int = 7) -> dict[int, float]:
    """After a run of exactly k heads, how often is the next flip a head?

    If the sequence has no memory every entry is ½. The simulation is the
    evidence that the coin does not know what it just did.
    """
    seq = flips(n, seed) > 0
    out = {}
    for k in STREAKS:
        # positions where the k flips ending at i-1 were all heads, and the
        # flip before those was a tail (so the run is exactly k, not longer)
        if k + 1 > n - 1:
            continue
        idx = np.arange(k + 1, n - 1)
        run = np.ones(len(idx), dtype=bool)
        for j in range(k):
            run &= seq[idx - 1 - j]
        run &= ~seq[idx - 1 - k]
        out[k] = float(seq[idx][run].mean())
    return out


def die_expectation() -> float:
    """Σ x·p(x) for a fair die — a value the die can never show."""
    return float((DIE_FACES * (1.0 / len(DIE_FACES))).sum())


def die_trace(n: int = 3_000, seed: int = 5) -> np.ndarray:
    """Running average of `n` rolls, converging on a number that is not a face."""
    rng = np.random.default_rng(seed)
    rolls = rng.integers(1, 7, size=n)
    return np.cumsum(rolls) / np.arange(1, n + 1)


# ---------------------------------------------------------------------------
# What 0.27 % claims. α and the run length come from the library; only the
# consequences are worked out here.
# ---------------------------------------------------------------------------
ALPHA = 1.0 - inside(3.0)          # erf-derived, same value Level 6 sweeps to
ARL0 = SHEWHART_ARL0               # 1/α, published by detection.py

SHIFT_SUBGROUPS = 100              # a shift's worth of subgroups


def p_any_alarm(n: float, alpha: float = ALPHA) -> float:
    """Chance an unchanged process trips its chart at least once in `n` subgroups."""
    return 1.0 - (1.0 - alpha) ** n


def median_wait(alpha: float = ALPHA) -> float:
    """Median subgroups to the first false alarm — geometric, so ln2/α.

    The gap between this and the mean is the level's practitioner point: "one
    in 370" is an average, and half of all first false alarms arrive far sooner.
    """
    return math.log(2.0) / -math.log1p(-alpha)


# ---------------------------------------------------------------------------
# Computed once, read by the act, the sheets, the page and the tests.
# ---------------------------------------------------------------------------
_SEQ = flips()
RATE_FINAL = float(rate_trace(_SEQ)[-1])
GAP_FINAL = int(gap_trace(_SEQ)[-1])

GAP_AT = {n: expected_gap_exact(n) for n in MILESTONES}
RATE_ERR_AT = {n: expected_rate_error(n) for n in MILESTONES}
ASYMPTOTE_AT = {n: expected_gap_asymptote(n) for n in MILESTONES}

MEMORY = streak_memory()
MEMORY_WORST = float(max(abs(v - 0.5) for v in MEMORY.values()))

DIE_E = die_expectation()

P_IN_SHIFT = p_any_alarm(SHIFT_SUBGROUPS)
P_IN_ARL0 = p_any_alarm(ARL0)
ONE_MINUS_1_OVER_E = 1.0 - 1.0 / math.e
MEDIAN_WAIT = median_wait()


if __name__ == "__main__":
    print(f"{FLIPS:,} flips (seed {FLIP_SEED}): "
          f"rate {RATE_FINAL:.4f}   gap {GAP_FINAL}")
    print()
    print("  the rate converges while the gap grows")
    print(f"  {'n':>9}  {'E|heads-tails|':>15}  {'sqrt(2n/pi)':>12}  {'E|rate-1/2|':>12}")
    for n in MILESTONES:
        print(f"  {n:>9,}  {GAP_AT[n]:>15.1f}  {ASYMPTOTE_AT[n]:>12.1f}  "
              f"{RATE_ERR_AT[n]:>12.5f}")
    print()
    print("  no memory: P(next is a head | run of k heads)")
    for k, v in MEMORY.items():
        print(f"    k={k}  {v:.4f}")
    print(f"  worst departure from one half: {MEMORY_WORST:.4f}")
    print()
    print(f"  a fair die expects {DIE_E:.1f} — a face it does not have")
    print()
    print(f"  alpha {ALPHA:.6f}   ARL0 {ARL0:.1f}")
    print(f"  P(>=1 false alarm in {SHIFT_SUBGROUPS} subgroups) {P_IN_SHIFT:.3f}")
    print(f"  P(>=1 false alarm in {ARL0:.1f} subgroups)  {P_IN_ARL0:.4f}"
          f"   vs 1-1/e {ONE_MINUS_1_OVER_E:.4f}")
    print(f"  median wait to the first false alarm {MEDIAN_WAIT:.0f} subgroups")
