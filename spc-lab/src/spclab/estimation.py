"""LEVEL 5 — Estimation and uncertainty. Every estimate carries error.

Level 4 established that a subgroup mean is drawn from a narrower distribution
than the parts, with standard deviation σ/√n. That is a statement about a
quantity nobody knows: the real σ. Everything downstream in this curriculum —
the limits in Level 6, the capability index in Level 8, the run lengths in
Level 9 — is computed from *estimates*, and this level is where the error in an
estimate gets a size and a shape.

Four claims, none asserted:

1. **The standard error is the spread of an estimate, and it is measurable.**
   Draw many samples of size n and the sample means have their own standard
   deviation. It lands on σ/√n, which is why the formula is worth having.

2. **A 95 % interval means 95 % coverage, and coverage is something you count.**
   Build an interval from each sample and count how often it contains the true
   mean. This is the operational definition, and it is the antidote to the same
   misreading Level 2 dealt with: the interval is the thing that varies, not the
   parameter.

3. **At small n a normal quantile under-covers, and t fixes it — by an amount
   worth seeing.** With n = 5 and σ estimated from the sample, ±1.96 standard
   errors does not deliver 95 %. The t quantile does. This is the whole reason
   t exists, derived by counting rather than asserted from a table.

4. **The interval narrows as √n, so precision is bought at a square-law price.**
   Halving the width costs four times the parts. And the same arithmetic applies
   to the curriculum's own constants: `formulas.d2` is estimated by simulation,
   so it has a standard error too, and there is a number of subgroups below
   which quoting `2.326` to four figures is not honest.

`d2` and the AIAG table come from `formulas`; nothing here recomputes them.

    PYTHONPATH=src .venv/bin/python -m spclab.estimation
"""
from __future__ import annotations

import math

import numpy as np

from spclab.formulas import control_limit_constants

# ---------------------------------------------------------------------------
# The process being estimated. One truth, so every panel and test describes the
# same thing: a stable process the reader is never allowed to see directly.
# ---------------------------------------------------------------------------
TRUE_MEAN = 50.0
TRUE_SIGMA = 0.60

# Sample sizes the act and the lab step through.
SIZES = (2, 5, 10, 25, 100)

# The interval this level is about.
CONF = 0.95
Z_95 = 1.959963984540054          # the normal quantile, exact to double precision

TRIALS = 40_000                   # samples drawn when coverage is counted
SUBGROUP_N = 5                    # the subgroup size the rest of the arc uses


def samples(n: int, trials: int = TRIALS, seed: int = 5) -> np.ndarray:
    """`trials` independent samples of size `n` from the true process."""
    rng = np.random.default_rng(seed)
    return rng.normal(TRUE_MEAN, TRUE_SIGMA, size=(trials, n))


def standard_error_exact(n: int, sigma: float = TRUE_SIGMA) -> float:
    """σ/√n — the spread of the estimate, not of the parts."""
    return sigma / math.sqrt(n)


def standard_error_observed(n: int, trials: int = TRIALS, seed: int = 5) -> float:
    """The spread of the sample means actually obtained. Should match the formula."""
    return float(samples(n, trials, seed).mean(axis=1).std(ddof=1))


def t_quantile(df: int, conf: float = CONF) -> float:
    """The two-sided t quantile, by bisection on the exact CDF.

    scipy is not a dependency of this repo and one distribution does not justify
    adding it. The CDF below is the closed form via the regularised incomplete
    beta function, which `math` provides everything for except the continued
    fraction — so that is written out.
    """
    target = 1.0 - (1.0 - conf) / 2.0
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def t_cdf(t: float, df: int) -> float:
    """P(T ≤ t) for Student's t with `df` degrees of freedom."""
    x = df / (df + t * t)
    p = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b), by continued fraction.

    The symmetry `I_x(a,b) = 1 - I_{1-x}(b,a)` is applied *before* the
    continued fraction, not after. Applied after, the recursion can revisit the
    same branch: at exactly `x == (a+1)/(a+b+2)` both calls take the else and
    ping-pong until the stack dies. Swapping first also saves computing a
    continued fraction whose result is then thrown away.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    if x > (a + 1.0) / (a + b + 2.0):
        return 1.0 - _betainc(b, a, 1.0 - x)
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta) / a
    # Lentz's algorithm
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 300):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2.0 * m - 1.0) * (a + 2.0 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2.0 * m) * (a + 2.0 * m + 1.0))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1.0 - c * d) < 1e-15:
            break
    return front * (f - 1.0)


def coverage(n: int, use_t: bool, trials: int = TRIALS, seed: int = 5) -> float:
    """Fraction of intervals that actually contain the true mean.

    The interval is built the way a practitioner builds it: from the sample's own
    mean and its own standard deviation, because σ is not known.
    """
    s = samples(n, trials, seed)
    m = s.mean(axis=1)
    sd = s.std(axis=1, ddof=1)
    q = t_quantile(n - 1) if use_t else Z_95
    half = q * sd / math.sqrt(n)
    return float(np.mean((m - half <= TRUE_MEAN) & (TRUE_MEAN <= m + half)))


def interval_width(n: int, sigma: float = TRUE_SIGMA, use_t: bool = True) -> float:
    """Full width of the interval at sample size `n`, with σ known."""
    q = t_quantile(n - 1) if use_t else Z_95
    return 2.0 * q * sigma / math.sqrt(n)


def parts_for_width(target: float, sigma: float = TRUE_SIGMA,
                    use_t: bool = True) -> int:
    """How many parts to reach a given interval width, by search.

    Two answers, and the difference is the honest part. With the quantile held
    fixed (σ known, z) the width is proportional to 1/√n, so halving it costs
    exactly four times the parts — a clean square law. With t the quantile is
    *also* shrinking as df grows, so halving costs less than four times at small
    n and approaches four times as n grows. Quoting the square law without that
    caveat overstates the price of precision on small samples.
    """
    n = 2
    while interval_width(n, sigma, use_t) > target and n < 10_000_000:
        n += 1
    return n


# ---------------------------------------------------------------------------
# The curriculum's own constants are estimates too.
# ---------------------------------------------------------------------------
def d2_estimates(reps: int = 60, subgroups: int = 2_000,
                 n: int = SUBGROUP_N, seed: int = 11) -> np.ndarray:
    """Independent estimates of d₂, each from `subgroups` simulated subgroups.

    d₂ is E(R/σ) for a normal sample of size n. `formulas` estimates it by
    simulation, so the spread of these replicates *is* the standard error of
    that estimate — the number a four-figure table never shows.
    """
    rng = np.random.default_rng(seed)
    out = np.empty(reps)
    for i in range(reps):
        x = rng.normal(0.0, 1.0, size=(subgroups, n))
        out[i] = (x.max(axis=1) - x.min(axis=1)).mean()
    return out


def subgroups_for_d2_digits(places: int = 3, n: int = SUBGROUP_N,
                            seed: int = 11) -> int:
    """Subgroups needed before d₂'s `places`-th decimal is stable.

    The standard error of a mean of `m` ranges is sd(R)/√m, so the m that pins
    the estimate to half a unit in the last place is a closed form, not a search.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(200_000, n))
    sd_range = float((x.max(axis=1) - x.min(axis=1)).std(ddof=1))
    half_ulp = 0.5 * 10.0 ** (-places)
    return int(math.ceil((Z_95 * sd_range / half_ulp) ** 2))


# ---------------------------------------------------------------------------
# Computed once; read by the act, the sheets, the page and the tests.
# ---------------------------------------------------------------------------
SE_EXACT = {n: standard_error_exact(n) for n in SIZES}
SE_OBSERVED = {n: standard_error_observed(n) for n in SIZES}

T_AT = {n: t_quantile(n - 1) for n in SIZES}
COVER_Z = {n: coverage(n, use_t=False) for n in SIZES}
COVER_T = {n: coverage(n, use_t=True) for n in SIZES}

WIDTH_AT = {n: interval_width(n) for n in SIZES}
WIDTH_AT_Z = {n: interval_width(n, use_t=False) for n in SIZES}

# the square law, and what t does to it
_BASE = SIZES[1]
HALVE_FROM = _BASE
HALVE_WIDTH_T = WIDTH_AT[_BASE]
HALVE_N_T = parts_for_width(WIDTH_AT[_BASE] / 2.0, use_t=True)
HALVE_N_Z = parts_for_width(WIDTH_AT_Z[_BASE] / 2.0, use_t=False)

_D2 = d2_estimates()
D2_PUBLISHED = control_limit_constants(SUBGROUP_N)["d2"]
D2_MEAN = float(_D2.mean())
D2_SE = float(_D2.std(ddof=1))
D2_SUBGROUPS_FOR_3DP = subgroups_for_d2_digits(3)


if __name__ == "__main__":
    print(f"true process: mean {TRUE_MEAN}, sigma {TRUE_SIGMA}\n")
    print("  the standard error is the spread of an estimate")
    print(f"  {'n':>5}  {'sigma/sqrt(n)':>14}  {'observed':>10}")
    for n in SIZES:
        print(f"  {n:>5}  {SE_EXACT[n]:>14.4f}  {SE_OBSERVED[n]:>10.4f}")
    print()
    print(f"  coverage of a nominal {CONF*100:.0f} % interval, counted over {TRIALS:,} samples")
    print(f"  {'n':>5}  {'z=1.96':>9}  {'t':>9}  {'t quantile':>11}")
    for n in SIZES:
        print(f"  {n:>5}  {COVER_Z[n]:>9.4f}  {COVER_T[n]:>9.4f}  {T_AT[n]:>11.3f}")
    print()
    print("  the interval narrows as root n")
    for n in SIZES:
        print(f"  {n:>5}  width {WIDTH_AT[n]:.4f}")
    print(f"  sigma known (z): halving the width at n={HALVE_FROM} needs "
          f"n = {HALVE_N_Z}  ({HALVE_N_Z / HALVE_FROM:.1f}x the parts)")
    print(f"  sigma estimated (t): halving {HALVE_WIDTH_T:.3f} needs "
          f"n = {HALVE_N_T}  ({HALVE_N_T / HALVE_FROM:.1f}x) - cheaper, because "
          f"t shrinks too")
    print()
    print("  the curriculum's own d2 is an estimate")
    print(f"  published        {D2_PUBLISHED:.4f}")
    print(f"  60 replicates    mean {D2_MEAN:.4f}  se {D2_SE:.4f}")
    print(f"  subgroups needed to pin the 3rd decimal: {D2_SUBGROUPS_FOR_3DP:,}")
