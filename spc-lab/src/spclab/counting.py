"""LEVEL 10 — Counting, not measuring. When the mean fixes the spread.

Levels 3 to 5 spent their time estimating a spread, because for a measurement the
spread is a separate fact about the process that has to be measured and carries
its own error. The moment you stop measuring and start *counting*, that stops
being true: the distribution hands you the variance.

Five claims, none asserted:

1. **For counts the spread is not a free parameter.** A proportion of defective
   items is binomial, so its standard deviation is √(p(1−p)/n) — a function of
   the mean. Defects per unit are Poisson, so the standard deviation is √(c̄).
   Nothing is estimated separately, which is why an attribute chart needs no
   range chart beside it.

2. **Which means a disagreement is information.** If the observed scatter is
   wider than the binomial says it must be, the binomial assumption is wrong —
   usually because p is not constant across subgroups. The ratio of observed to
   theoretical variance is a diagnostic you get for free, and it is the honest
   version of "rational subgrouping" for attribute data.

3. **Chart choice is two questions, not four names.** Are you counting defective
   *items* or *defects*? Is the subgroup size constant? That is the whole
   decision: np, p, c, u.

4. **When the subgroup size varies the limits have to breathe.** Using one set of
   limits computed at the average n misclassifies points, and the rate at which
   it does so is computable rather than a matter of taste.

5. **A lower limit below zero is a tell, and it has a threshold.** LCL stays
   above zero only while n·p̄ > 9(1−p̄). Below that the chart can only signal
   upward, and the familiar "np̄ ≥ 5" rule of thumb is a weaker version of the
   same arithmetic.

Annex — capability when the distribution is not normal: the normal
approximation to a binomial tail is wrong in a direction that flatters the
process, and by how much is worth knowing before quoting a ppm.

    PYTHONPATH=src .venv/bin/python -m spclab.counting
"""
from __future__ import annotations

import math

import numpy as np

from spclab.estimation import betainc

# Three sigma, from Level 6. Attribute charts inherit the same bet.
K = 3.0

# The worked example the page and the lab both use: a solder process inspected
# in subgroups, and a board inspected for defects.
P_BAR = 0.04                 # fraction of items defective
N_CONST = 200                # constant subgroup size
C_BAR = 6.5                  # defects per unit, Poisson
N_VARY = (120, 150, 180, 200, 240, 300, 360)


# ---------------------------------------------------------------------------
# 1. The spread the distribution hands you
# ---------------------------------------------------------------------------
def binomial_sigma(n: int, p: float) -> float:
    """Standard deviation of the *proportion* defective: √(p(1−p)/n)."""
    return math.sqrt(p * (1.0 - p) / n)


def poisson_sigma(c: float) -> float:
    """Standard deviation of a Poisson count: √c. The mean is the variance."""
    return math.sqrt(c)


def p_limits(n: int, p_bar: float = P_BAR, k: float = K) -> dict:
    """p-chart limits at subgroup size n. LCL is reported and also clamped.

    Both are returned on purpose: `lcl_raw` is what the arithmetic says and
    `lcl` is what a chart can draw. Hiding the difference is how "the lower
    limit is zero" turns into "the process cannot run low", which is false.

    `clamped` is true at `lcl_raw == 0` as well as below it: a proportion is
    never negative, so a lower limit sitting exactly on zero can never be
    violated. That chart is still one-sided, and at n exactly k²(1−p̄)/p̄ the
    limit lands exactly there.
    """
    s = binomial_sigma(n, p_bar)
    raw = p_bar - k * s
    # at n exactly k²(1−p̄)/p̄ the limit is algebraically zero and floating point
    # returns +7e-18, which would report a drawable lower limit that is not there
    if abs(raw) < 1e-12:
        raw = 0.0
    return {"cl": p_bar, "ucl": p_bar + k * s, "lcl_raw": raw,
            "lcl": max(0.0, raw), "sigma": s, "clamped": raw <= 0.0}


def np_limits(n: int, p_bar: float = P_BAR, k: float = K) -> dict:
    """np-chart limits — the same chart in counts rather than fractions."""
    d = p_limits(n, p_bar, k)
    return {"cl": n * d["cl"], "ucl": n * d["ucl"], "lcl_raw": n * d["lcl_raw"],
            "lcl": max(0.0, n * d["lcl_raw"]), "sigma": n * d["sigma"],
            "clamped": d["clamped"]}


def c_limits(c_bar: float = C_BAR, k: float = K) -> dict:
    """c-chart limits for defects per unit at constant opportunity."""
    s = poisson_sigma(c_bar)
    raw = c_bar - k * s
    return {"cl": c_bar, "ucl": c_bar + k * s, "lcl_raw": raw,
            "lcl": max(0.0, raw), "sigma": s, "clamped": raw <= 0.0}


def u_limits(u_bar: float, n: float, k: float = K) -> dict:
    """u-chart limits: defects per unit when the units inspected vary."""
    s = math.sqrt(u_bar / n)
    raw = u_bar - k * s
    return {"cl": u_bar, "ucl": u_bar + k * s, "lcl_raw": raw,
            "lcl": max(0.0, raw), "sigma": s, "clamped": raw <= 0.0}


# ---------------------------------------------------------------------------
# 2. When the data disagrees with the distribution
# ---------------------------------------------------------------------------
def dispersion_ratio(counts: np.ndarray, n: int, p_bar: float | None = None) -> float:
    """Observed variance of the proportion over the binomial variance.

    One for a genuine binomial process. Above one means p moved between
    subgroups — the subgroups were not rational — and every limit computed from
    the binomial is then too tight.
    """
    props = np.asarray(counts, dtype=float) / n
    p = float(props.mean()) if p_bar is None else p_bar
    if p <= 0.0 or p >= 1.0:
        return float("nan")
    return float(props.var(ddof=1) / (p * (1.0 - p) / n))


def simulate_binomial(n: int = N_CONST, p: float = P_BAR, subgroups: int = 400,
                      seed: int = 10) -> np.ndarray:
    """A genuinely binomial process: one p, every subgroup."""
    rng = np.random.default_rng(seed)
    return rng.binomial(n, p, size=subgroups)


def simulate_batch_effect(n: int = N_CONST, p: float = P_BAR, spread: float = 0.5,
                          subgroups: int = 400, seed: int = 10) -> np.ndarray:
    """The same average p, but each subgroup drawn at its own rate.

    This is what a shift change, a supplier lot or an operator looks like in
    attribute data: the mean is untouched and the scatter is not.
    """
    rng = np.random.default_rng(seed)
    lo, hi = p * (1.0 - spread), p * (1.0 + spread)
    ps = rng.uniform(lo, hi, size=subgroups)
    return rng.binomial(n, ps)


# ---------------------------------------------------------------------------
# 3. Chart choice — two questions
# ---------------------------------------------------------------------------
UNIT_ITEM = "items"          # each thing inspected is good or bad → binomial
UNIT_DEFECT = "defects"      # one thing can carry several → Poisson


def chart_for(unit: str, constant_n: bool) -> str:
    """The whole selection rule: np, p, c or u."""
    if unit == UNIT_ITEM:
        return "np" if constant_n else "p"
    if unit == UNIT_DEFECT:
        return "c" if constant_n else "u"
    raise ValueError(f"unit must be {UNIT_ITEM!r} or {UNIT_DEFECT!r}, not {unit!r}")


CHART_TABLE = {(UNIT_ITEM, True): "np", (UNIT_ITEM, False): "p",
               (UNIT_DEFECT, True): "c", (UNIT_DEFECT, False): "u"}


# ---------------------------------------------------------------------------
# 4. Varying n, and the cost of pretending otherwise
# ---------------------------------------------------------------------------
def average_n_misclassification(ns=N_VARY, p_bar: float = P_BAR,
                                trials: int = 200_000, seed: int = 3) -> dict:
    """How often average-n limits disagree with the correct per-n limits.

    Both charts are shown the same subgroups. A disagreement is a point the
    average-n chart calls a signal when the honest chart does not, or misses
    when the honest chart signals.
    """
    rng = np.random.default_rng(seed)
    n_arr = np.array(ns)
    n_bar = float(n_arr.mean())
    fixed = p_limits(int(round(n_bar)), p_bar)
    false_signal = missed = 0
    per = max(1, trials // len(n_arr))
    for n in n_arr:
        counts = rng.binomial(int(n), p_bar, size=per)
        props = counts / n
        right = p_limits(int(n), p_bar)
        out_right = (props > right["ucl"]) | (props < right["lcl_raw"])
        out_fixed = (props > fixed["ucl"]) | (props < fixed["lcl_raw"])
        false_signal += int((out_fixed & ~out_right).sum())
        missed += int((out_right & ~out_fixed).sum())
    total = per * len(n_arr)
    return {"n_bar": n_bar, "false_signal": false_signal / total,
            "missed": missed / total,
            "disagree": (false_signal + missed) / total,
            "spread": (int(n_arr.min()), int(n_arr.max()))}


# ---------------------------------------------------------------------------
# 5. When the lower limit falls off the bottom
# ---------------------------------------------------------------------------
def n_for_positive_lcl(p_bar: float = P_BAR, k: float = K) -> int:
    """Smallest n with LCL above zero.

        p̄ − k√(p̄(1−p̄)/n) > 0  ⟺  n > k²(1−p̄)/p̄

    For k = 3 that is 9(1−p̄)/p̄, which is where the shop-floor "np̄ ≥ 5" rule
    of thumb comes from — and why 5 is not enough.
    """
    return int(math.floor(k * k * (1.0 - p_bar) / p_bar)) + 1


def np_bar_threshold(p_bar: float = P_BAR, k: float = K) -> float:
    """The same condition read as a count: n·p̄ must exceed k²(1−p̄)."""
    return k * k * (1.0 - p_bar)


# ---------------------------------------------------------------------------
# Annex. Capability when the distribution is not normal
# ---------------------------------------------------------------------------
def binomial_tail(n: int, p: float, at_least: int) -> float:
    """Exact P(X ≥ at_least) for a binomial, via the beta identity.

        P(X ≥ k) = I_p(k, n − k + 1)

    Summing `math.comb(n, x)` term by term is the obvious way and it breaks:
    at n = 20 000 the binomial coefficient overflows a float long before the
    sum finishes. `spclab.estimation.betainc` is already here for Level 5's t
    distribution, so this reuses it rather than growing a second copy.
    """
    if at_least <= 0:
        return 1.0
    if at_least > n:
        return 0.0
    return betainc(at_least, n - at_least + 1, p)


def normal_tail_approx(n: int, p: float, at_least: int) -> float:
    """The normal approximation to the same tail, as a Cpk-style calculation would."""
    mu = n * p
    sd = math.sqrt(n * p * (1.0 - p))
    z = (at_least - mu) / sd
    return 0.5 * (1.0 - math.erf(z / math.sqrt(2.0)))


def tail_error(n: int = N_CONST, p: float = P_BAR, at_least: int = 16) -> dict:
    """Exact against approximate, and which way the error flatters the process."""
    ex = binomial_tail(n, p, at_least)
    ap = normal_tail_approx(n, p, at_least)
    return {"exact": ex, "approx": ap, "ratio": ex / ap if ap else float("inf"),
            "approx_understates": ap < ex}


# ---------------------------------------------------------------------------
# Computed once; read by the sheets, the page, the lab's tests and pytest.
# ---------------------------------------------------------------------------
P_AT_CONST = p_limits(N_CONST)
NP_AT_CONST = np_limits(N_CONST)
C_AT = c_limits()
LIMITS_BY_N = {n: p_limits(n) for n in N_VARY}

_CLEAN = simulate_binomial()
_BATCHED = simulate_batch_effect()
DISPERSION_CLEAN = dispersion_ratio(_CLEAN, N_CONST)
DISPERSION_BATCHED = dispersion_ratio(_BATCHED, N_CONST)

MISCLASS = average_n_misclassification()

N_FOR_LCL = n_for_positive_lcl()
NP_THRESHOLD = np_bar_threshold()

TAIL = tail_error()

SELECTION = {k: v for k, v in CHART_TABLE.items()}


if __name__ == "__main__":
    print(f"the example: p̄ = {P_BAR}, n = {N_CONST}, c̄ = {C_BAR}\n")
    print("  1. the distribution hands you the spread")
    print(f"     p-chart  σ = √(p̄(1−p̄)/n) = {P_AT_CONST['sigma']:.5f}"
          f"   UCL {P_AT_CONST['ucl']:.4f}  LCL {P_AT_CONST['lcl']:.4f}"
          f"{'  (clamped from ' + format(P_AT_CONST['lcl_raw'], '.4f') + ')' if P_AT_CONST['clamped'] else ''}")
    print(f"     c-chart  σ = √c̄ = {C_AT['sigma']:.4f}"
          f"   UCL {C_AT['ucl']:.3f}  LCL {C_AT['lcl']:.3f}")
    print()
    print("  2. a disagreement is information")
    print(f"     one p, every subgroup      dispersion ratio {DISPERSION_CLEAN:.3f}")
    print(f"     p drifting between them    dispersion ratio {DISPERSION_BATCHED:.3f}")
    print()
    print("  3. chart choice is two questions")
    for (unit, const), name in CHART_TABLE.items():
        print(f"     {unit:8} n {'constant' if const else 'varies  '} -> {name}-chart")
    print()
    print("  4. pretending n is constant when it is not")
    print(f"     n from {MISCLASS['spread'][0]} to {MISCLASS['spread'][1]}, "
          f"average {MISCLASS['n_bar']:.0f}")
    print(f"     false signals {MISCLASS['false_signal']*100:.3f} %   "
          f"missed {MISCLASS['missed']*100:.3f} %   "
          f"disagreement {MISCLASS['disagree']*100:.3f} %")
    print()
    print("  5. the lower limit falls off the bottom")
    print(f"     LCL > 0 needs n > k²(1−p̄)/p̄ = {N_FOR_LCL - 1} , so n ≥ {N_FOR_LCL}")
    print(f"     read as a count: n·p̄ must exceed {NP_THRESHOLD:.2f}"
          f"  (the rule of thumb says 5)")
    print()
    print("  annex. capability when the distribution is not normal")
    print(f"     P(X ≥ 16) exact {TAIL['exact']:.6f}   normal {TAIL['approx']:.6f}"
          f"   ratio {TAIL['ratio']:.2f}")
    print(f"     the approximation {'understates' if TAIL['approx_understates'] else 'overstates'}"
          f" the risk")
