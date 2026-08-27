"""What variation is, before any statistic is put on it — simulated, not asserted.

Level 1 makes two claims that sound like opinions and are not:

1. **A histogram throws away time order.** Not approximately — exactly. Take one
   set of measurements and write it down in two orders: as it happened, and
   sorted. Sorted is what a monotone drift looks like. Same mean, same standard
   deviation, identical histogram bin for bin, and one of those processes needs
   an engineer today. That is why the rest of the curriculum plots in time order
   instead of piling measurements into bins.

2. **Adjusting after every part makes the output worse, by exactly a factor of
   two in variance.** This is Deming's funnel, rule 2. It is not a simulation
   artefact; the algebra is four lines and the simulation agrees:

       outcome_i = aim_i + e_i,          e_i ~ N(0, σ²) iid
       rule 2:   aim_{i+1} = aim_i − outcome_i

       aim_1 = 0        → outcome_1 = e_1
       aim_2 = −e_1     → outcome_2 = e_2 − e_1        Var = 2σ²
       aim_3 = −e_2     → outcome_3 = e_3 − e_2        Var = 2σ²

   Every outcome after the first is a difference of two independent draws, so
   the variance is 2σ² forever and the spread is √2 ≈ 1.414 times worse. The
   operator is working hard and doubling the variance.

Both numbers are exported so the act, the page and the tests cannot disagree.

    PYTHONPATH=src .venv/bin/python -m spclab.variation      # print the table
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# The twelve parts. Level 1 introduces them, Level 3 puts a mean and a sigma on
# them, so they must be the same twelve — an earlier draft of Level 1 invented
# its own and claimed a 26 µm span while Level 3 was claiming 47 µm about the
# same "twelve parts off one machine". Level 3 asserts equality against these
# rather than importing them, which keeps its own random stream (and therefore
# its four extra handfuls) byte-identical.
# ---------------------------------------------------------------------------
NOMINAL_MM = 12.0
TWELVE_SHAFTS_MM = np.array([12.000, 12.006, 11.995, 11.982, 11.991, 11.980,
                             12.001, 12.027, 11.990, 11.988, 12.010, 12.007])
TWELVE_DEV_UM = np.round((TWELVE_SHAFTS_MM - NOMINAL_MM) * 1000.0, 1)
TWELVE_SPAN_UM = float(round(TWELVE_DEV_UM.max() - TWELVE_DEV_UM.min()))
TWELVE_CLOSEST_UM = float(round(np.min(np.diff(np.sort(TWELVE_DEV_UM))), 1))

# Deming's funnel, in the two rules that matter on a shop floor.
LEAVE_IT = "leave-it"        # rule 1: never adjust; the process is what it is
ADJUST_EVERY = "adjust"      # rule 2: after every part, correct by what you just saw

# Exact results of the algebra above, for anything that wants the closed form.
TAMPER_VAR_RATIO_EXACT = 2.0
TAMPER_SIGMA_RATIO_EXACT = float(np.sqrt(2.0))


def funnel(rule: str, n: int = 2000, sigma: float = 1.0, seed: int = 4) -> np.ndarray:
    """Outcomes of `n` parts under one adjustment rule, in units of `sigma`.

    Both rules see the *same* random draws, so any difference in the output is
    the rule's doing and not luck.
    """
    e = np.random.default_rng(seed).normal(0.0, sigma, size=n)
    if rule == LEAVE_IT:
        return e
    if rule == ADJUST_EVERY:
        # aim_{i+1} = aim_i − outcome_i, which collapses to outcome_i = e_i − e_{i-1}
        out = np.empty(n)
        aim = 0.0
        for i in range(n):
            out[i] = aim + e[i]
            aim -= out[i]
        return out
    raise ValueError(f"unknown rule {rule!r}")


def tamper_ratio(n: int = 200_000, seed: int = 4) -> tuple[float, float]:
    """Simulated (variance, spread) penalty for adjusting after every part."""
    left = funnel(LEAVE_IT, n=n, seed=seed)
    adjusted = funnel(ADJUST_EVERY, n=n, seed=seed)
    v = float(adjusted.var(ddof=1) / left.var(ddof=1))
    return v, float(np.sqrt(v))


def same_histogram_pair(n: int = 240, seed: int = 12) -> tuple[np.ndarray, np.ndarray]:
    """One set of measurements, delivered in two different orders.

    The strongest form of the claim, and the honest one: these are not two
    similar samples, they are the *same numbers*. Same mean, same standard
    deviation, same histogram bin for bin — zero difference, not a small one.
    The only thing that differs is the order they arrived in, and that is the
    difference between a process you can leave alone and one that is walking.

    Returns `(arrived_stable, arrived_drifting)`. The second is the same
    multiset sorted, which is what a monotone drift looks like when you write
    the measurements down in the order they happened.
    """
    values = np.random.default_rng(seed).normal(0.0, 1.0, size=n)
    return values.copy(), np.sort(values)


def histograms_identical(a: np.ndarray, b: np.ndarray, bins: int = 14) -> bool:
    """Do two series fall into identical bins? Used to prove the claim, not illustrate it."""
    lo = min(a.min(), b.min())
    hi = max(a.max(), b.max())
    ca, _ = np.histogram(a, bins=bins, range=(lo, hi))
    cb, _ = np.histogram(b, bins=bins, range=(lo, hi))
    return bool((ca == cb).all())


def run_of_same_side(series: np.ndarray) -> int:
    """Longest run on one side of the mean — the order-dependent evidence.

    This is the thing a histogram cannot see. Western Electric's rule 4 (eight
    in a row) is a formalisation of it; Level 7 prices it.
    """
    side = series > series.mean()
    best = run = 1
    for i in range(1, len(side)):
        run = run + 1 if side[i] == side[i - 1] else 1
        best = max(best, run)
    return int(best)


TAMPER_VAR_RATIO, TAMPER_SIGMA_RATIO = tamper_ratio()

_STABLE, _DRIFTING = same_histogram_pair()
PAIR_N = len(_STABLE)
PAIR_MEAN_GAP = float(abs(_STABLE.mean() - _DRIFTING.mean()))
PAIR_SD_GAP = float(abs(_STABLE.std(ddof=1) - _DRIFTING.std(ddof=1)))
PAIR_BINS_IDENTICAL = histograms_identical(_STABLE, _DRIFTING)
PAIR_RUN_STABLE = run_of_same_side(_STABLE)
PAIR_RUN_DRIFTING = run_of_same_side(_DRIFTING)


if __name__ == "__main__":
    print(f"The twelve parts: span {TWELVE_SPAN_UM:.0f} µm, "
          f"closest pair {TWELVE_CLOSEST_UM:.0f} µm")
    print()
    print("Deming's funnel — adjusting after every part")
    print(f"  variance ratio   simulated {TAMPER_VAR_RATIO:.3f}   "
          f"exact {TAMPER_VAR_RATIO_EXACT:.3f}")
    print(f"  spread ratio     simulated {TAMPER_SIGMA_RATIO:.3f}   "
          f"exact {TAMPER_SIGMA_RATIO_EXACT:.3f}")
    print()
    print(f"Same {PAIR_N} measurements, two arrival orders")
    print(f"  mean gap {PAIR_MEAN_GAP:.1e}   sd gap {PAIR_SD_GAP:.1e}   "
          f"bins identical: {PAIR_BINS_IDENTICAL}")
    print(f"  longest run on one side of the mean:  "
          f"stable {PAIR_RUN_STABLE}   drifting {PAIR_RUN_DRIFTING}")
