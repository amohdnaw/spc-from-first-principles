"""LEVEL 11 — Relationships. One sum-of-squares identity, wearing three hats.

This is the bridge level. Everything before it watched one number over time;
this one asks what a number has to do with another number, and the machinery
turns out to be the same arithmetic three times over:

    regression  splits the total variation into explained and residual
    ANOVA       splits it into between-groups and within-groups
    Gage R&R    splits it into part, operator and interaction

Same identity, `SST = SS_explained + SS_residual`, relabelled. Once that is
visible, a Gage R&R stops being a separate technique with its own tables and
becomes a two-way version of a thing already understood — which is exactly the
seam the MSA site continues from.

Five claims, none asserted:

1. **Least squares is a minimisation, so the line can be found rather than
   drawn.** Sweeping the slope traces a parabola in the residual sum of
   squares, and the closed form sits at its minimum — not near it.

2. **R² is a variance ratio, not a grade.** It is the fraction of the total
   variation the line accounts for, and it rises whenever a predictor is added,
   even a column of pure noise. That is not a subtlety; it is the reason
   adjusted R² exists.

3. **Residuals are the diagnostic; R² is only the summary.** A curved
   relationship can score a high R² while the residuals arc visibly, and the
   number never mentions it.

4. **A prediction interval is not a confidence interval.** One covers the mean
   response, the other covers the next observation, and the second is wider by a
   factor that includes the 1 that the first one leaves out. Both are checked by
   counting, the way Level 5 checked coverage.

5. **The bridge.** A two-way decomposition of the same total gives variance
   components for part, operator and their interaction — which is a Gage R&R.
   The percentages are computed here; what to do about them is the MSA site's
   subject, and this curriculum stops at the boundary.

    PYTHONPATH=src .venv/bin/python -m spclab.relationships
"""
from __future__ import annotations

import math

import numpy as np

from spclab.estimation import betainc, t_quantile

# ---------------------------------------------------------------------------
# The worked example: cutting speed against surface roughness. One dataset, so
# the page, the sheets, the lab and the tests all describe the same numbers.
# ---------------------------------------------------------------------------
TRUE_INTERCEPT = 0.42
TRUE_SLOPE = 0.0135
NOISE_SD = 0.11
SPEEDS = np.arange(60, 205, 5, dtype=float)      # m/min
DATA_SEED = 12

CONF = 0.95


def dataset(seed: int = DATA_SEED) -> tuple[np.ndarray, np.ndarray]:
    """Speed and the roughness measured at it — the level's one dataset."""
    rng = np.random.default_rng(seed)
    y = TRUE_INTERCEPT + TRUE_SLOPE * SPEEDS + rng.normal(0.0, NOISE_SD, SPEEDS.size)
    return SPEEDS.copy(), y


# ---------------------------------------------------------------------------
# 1. Least squares, as a minimisation
# ---------------------------------------------------------------------------
def fit(x: np.ndarray, y: np.ndarray) -> dict:
    """Slope and intercept from the normal equations, plus the sums of squares."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = x.size
    xb, yb = x.mean(), y.mean()
    sxx = float(((x - xb) ** 2).sum())
    sxy = float(((x - xb) * (y - yb)).sum())
    slope = sxy / sxx
    intercept = yb - slope * xb
    resid = y - (intercept + slope * x)
    sse = float((resid ** 2).sum())
    sst = float(((y - yb) ** 2).sum())
    return {"n": n, "slope": slope, "intercept": intercept, "sxx": sxx,
            "resid": resid, "sse": sse, "sst": sst, "ssr": sst - sse,
            "r2": 1.0 - sse / sst, "s": math.sqrt(sse / (n - 2)),
            "xbar": float(xb)}


def sse_at_slope(x: np.ndarray, y: np.ndarray, slope: float) -> float:
    """Residual sum of squares for a given slope, intercept re-centred.

    Sweeping this is what makes "least squares" a claim rather than a name.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    intercept = y.mean() - slope * x.mean()
    return float(((y - intercept - slope * x) ** 2).sum())


# ---------------------------------------------------------------------------
# 2. R² rises for free
# ---------------------------------------------------------------------------
def r2_with_noise_predictors(k: int, seed: int = 5) -> float:
    """R² after adding `k` columns of pure noise to the model.

    Least squares cannot do worse by being given more columns, so R² cannot
    fall. Every point it gains here is bought with nothing.
    """
    x, y = dataset()
    n = x.size
    rng = np.random.default_rng(seed)
    cols = [np.ones(n), x] + [rng.normal(size=n) for _ in range(k)]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sse = float((resid ** 2).sum())
    sst = float(((y - y.mean()) ** 2).sum())
    return 1.0 - sse / sst


def adjusted_r2(r2: float, n: int, p: int) -> float:
    """R² penalised for the number of predictors — the honest summary."""
    return 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1)


# ---------------------------------------------------------------------------
# 3. A high R² that should not be trusted
# ---------------------------------------------------------------------------
def curved_dataset(seed: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """A genuinely curved relationship, fitted with a straight line."""
    rng = np.random.default_rng(seed)
    x = SPEEDS.copy()
    y = 0.30 + 0.00006 * (x - 60) ** 2 + rng.normal(0.0, 0.025, x.size)
    return x, y


def residual_runs(resid: np.ndarray) -> int:
    """Longest run of residuals with the same sign.

    A straight line through a curve leaves its signature here, not in R².
    Level 1 used the same statistic to show that a histogram throws away order.
    """
    best = run = 1
    for a, b in zip(resid, resid[1:]):
        run = run + 1 if (a > 0) == (b > 0) else 1
        best = max(best, run)
    return int(best)


# ---------------------------------------------------------------------------
# 4. Two intervals that are not the same interval
# ---------------------------------------------------------------------------
def interval_half_widths(f: dict, x0: float, conf: float = CONF) -> tuple[float, float]:
    """(confidence, prediction) half-widths for the response at x0.

        mean response : t·s·√( 1/n + (x₀−x̄)²/Sxx )
        new reading   : t·s·√( 1 + 1/n + (x₀−x̄)²/Sxx )

    The only difference is that 1, and it is the variance of the new reading
    itself — which is why no amount of data shrinks the prediction interval to
    nothing.
    """
    t = t_quantile(f["n"] - 2, conf)
    lev = 1.0 / f["n"] + (x0 - f["xbar"]) ** 2 / f["sxx"]
    return t * f["s"] * math.sqrt(lev), t * f["s"] * math.sqrt(1.0 + lev)


def count_coverage(trials: int = 4000, seed: int = 21, conf: float = CONF) -> dict:
    """Count how often each interval covers what it claims to cover."""
    rng = np.random.default_rng(seed)
    x = SPEEDS.copy()
    x0 = float(x.mean() + 0.6 * (x.max() - x.mean()))
    true_mean = TRUE_INTERCEPT + TRUE_SLOPE * x0
    ci_hit = pi_hit = 0
    for _ in range(trials):
        y = TRUE_INTERCEPT + TRUE_SLOPE * x + rng.normal(0.0, NOISE_SD, x.size)
        f = fit(x, y)
        yhat = f["intercept"] + f["slope"] * x0
        hc, hp = interval_half_widths(f, x0, conf)
        if abs(yhat - true_mean) <= hc:
            ci_hit += 1
        new_reading = true_mean + rng.normal(0.0, NOISE_SD)
        if abs(yhat - new_reading) <= hp:
            pi_hit += 1
    return {"x0": x0, "ci": ci_hit / trials, "pi": pi_hit / trials}


# ---------------------------------------------------------------------------
# 5. The same identity as ANOVA, and then as a Gage R&R
# ---------------------------------------------------------------------------
def f_sf(f_stat: float, df1: int, df2: int) -> float:
    """P(F > f_stat) — the incomplete beta again, from Level 5."""
    if f_stat <= 0:
        return 1.0
    x = df2 / (df2 + df1 * f_stat)
    return betainc(df2 / 2.0, df1 / 2.0, x)


def one_way(groups: list[np.ndarray]) -> dict:
    """SST = SSB + SSW, and the F ratio built out of them."""
    all_v = np.concatenate(groups)
    grand = all_v.mean()
    ssb = float(sum(g.size * (g.mean() - grand) ** 2 for g in groups))
    ssw = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
    sst = float(((all_v - grand) ** 2).sum())
    k, n = len(groups), all_v.size
    msb, msw = ssb / (k - 1), ssw / (n - k)
    return {"ssb": ssb, "ssw": ssw, "sst": sst, "df1": k - 1, "df2": n - k,
            "msb": msb, "msw": msw, "f": msb / msw,
            "p": f_sf(msb / msw, k - 1, n - k),
            "eta2": ssb / sst}


# The gauge study the bridge ends on: parts measured by operators, twice each.
PARTS, OPERATORS, REPEATS = 10, 3, 2
PART_SD, OPERATOR_SD, INTERACT_SD, REPEAT_SD = 0.90, 0.30, 0.28, 0.26


def gauge_study(seed: int = 7, parts: int = PARTS, operators: int = OPERATORS,
                repeats: int = REPEATS) -> np.ndarray:
    """A (part, operator, repeat) array — the shape every Gage R&R arrives in.

    The sizes are arguments so the estimator can be checked against the
    variances it was built from. A ten-part study is far too small to recover
    them, which is a fact about gauge studies worth knowing and not a reason to
    leave the estimator unguarded.
    """
    rng = np.random.default_rng(seed)
    part = rng.normal(0.0, PART_SD, (parts, 1, 1))
    oper = rng.normal(0.0, OPERATOR_SD, (1, operators, 1))
    inter = rng.normal(0.0, INTERACT_SD, (parts, operators, 1))
    err = rng.normal(0.0, REPEAT_SD, (parts, operators, repeats))
    return 10.0 + part + oper + inter + err


# The variances the study is built from, so a test can ask for them back.
TRUE_COMPONENTS = {"part": PART_SD ** 2, "operator": OPERATOR_SD ** 2,
                   "interaction": INTERACT_SD ** 2, "repeat": REPEAT_SD ** 2}


def two_way_components(y: np.ndarray) -> dict:
    """Variance components from the same sums-of-squares identity, two-way.

    This is a Gage R&R: repeatability is the error term, reproducibility is the
    operator term, and "gauge" is their sum against the part-to-part variation.
    What the numbers mean for accepting a gauge is the MSA site's subject.
    """
    p, o, r = y.shape
    grand = y.mean()
    part_m = y.mean(axis=(1, 2), keepdims=True)
    oper_m = y.mean(axis=(0, 2), keepdims=True)
    cell_m = y.mean(axis=2, keepdims=True)

    ss_part = float(o * r * ((part_m - grand) ** 2).sum())
    ss_oper = float(p * r * ((oper_m - grand) ** 2).sum())
    ss_int = float(r * ((cell_m - part_m - oper_m + grand) ** 2).sum())
    ss_err = float(((y - cell_m) ** 2).sum())
    ss_tot = float(((y - grand) ** 2).sum())

    ms_part = ss_part / (p - 1)
    ms_oper = ss_oper / (o - 1)
    ms_int = ss_int / ((p - 1) * (o - 1))
    ms_err = ss_err / (p * o * (r - 1))

    v_err = ms_err
    v_int = max(0.0, (ms_int - ms_err) / r)
    v_oper = max(0.0, (ms_oper - ms_int) / (p * r))
    v_part = max(0.0, (ms_part - ms_int) / (o * r))
    total = v_err + v_int + v_oper + v_part
    gauge = v_err + v_int + v_oper
    return {"ss": {"part": ss_part, "operator": ss_oper, "interaction": ss_int,
                   "repeat": ss_err, "total": ss_tot},
            # the mean squares, because the components are an inversion of them:
            #   E[MS_part] = σ²_err + r σ²_int + o r σ²_part
            #   E[MS_oper] = σ²_err + r σ²_int + p r σ²_oper
            #   E[MS_int]  = σ²_err + r σ²_int
            #   E[MS_err]  = σ²_err
            # Returning them lets a test check the inversion exactly rather than
            # hoping a tolerance on noisy data notices a wrong subtraction.
            "ms": {"part": ms_part, "operator": ms_oper, "interaction": ms_int,
                   "repeat": ms_err},
            "shape": {"parts": p, "operators": o, "repeats": r},
            "var": {"part": v_part, "operator": v_oper, "interaction": v_int,
                    "repeat": v_err},
            "total": total, "gauge": gauge,
            "pct": {k: 100.0 * v / total for k, v in
                    (("part", v_part), ("operator", v_oper),
                     ("interaction", v_int), ("repeat", v_err))},
            "pct_gauge": 100.0 * gauge / total}


# ---------------------------------------------------------------------------
# Computed once; read by the sheets, the page, the lab and the tests.
# ---------------------------------------------------------------------------
X, Y = dataset()
FIT = fit(X, Y)
SLOPE_GRID = np.linspace(FIT["slope"] - 0.006, FIT["slope"] + 0.006, 241)
SSE_CURVE = np.array([sse_at_slope(X, Y, s) for s in SLOPE_GRID])

R2_PLAIN = FIT["r2"]
R2_WITH_NOISE = {k: r2_with_noise_predictors(k) for k in (1, 3, 6, 10)}
ADJ_WITH_NOISE = {k: adjusted_r2(v, FIT["n"], 1 + k) for k, v in R2_WITH_NOISE.items()}

CX, CY = curved_dataset()
CURVED_FIT = fit(CX, CY)
CURVED_RUN = residual_runs(CURVED_FIT["resid"])
STRAIGHT_RUN = residual_runs(FIT["resid"])

X0 = float(X.mean() + 0.6 * (X.max() - X.mean()))
HALF_CI, HALF_PI = interval_half_widths(FIT, X0)
COVERAGE = count_coverage()

GAUGE = two_way_components(gauge_study())

MSA_SITE = "https://msa.amohdnaw.xyz"


if __name__ == "__main__":
    print(f"speed vs roughness, n = {FIT['n']}\n")
    print("  1. least squares is a minimisation")
    print(f"     closed form slope {FIT['slope']:.5f}   intercept {FIT['intercept']:.4f}")
    best = float(SLOPE_GRID[int(SSE_CURVE.argmin())])
    print(f"     sweeping the slope, SSE is least at {best:.5f}"
          f"  (gap {abs(best - FIT['slope']):.2e})")
    print()
    print("  2. R² rises for free")
    print(f"     the line alone            R² {R2_PLAIN:.4f}")
    for k in sorted(R2_WITH_NOISE):
        print(f"     plus {k:>2} noise columns    R² {R2_WITH_NOISE[k]:.4f}"
              f"   adjusted {ADJ_WITH_NOISE[k]:.4f}")
    print()
    print("  3. residuals say what R² cannot")
    print(f"     straight relationship  R² {FIT['r2']:.3f}   longest same-sign run "
          f"{STRAIGHT_RUN}")
    print(f"     curved relationship    R² {CURVED_FIT['r2']:.3f}   longest same-sign run "
          f"{CURVED_RUN}")
    print()
    print("  4. two intervals, counted")
    print(f"     at x₀ = {X0:.0f}: confidence half-width {HALF_CI:.4f}, "
          f"prediction {HALF_PI:.4f}  (×{HALF_PI / HALF_CI:.2f})")
    print(f"     counted coverage: mean response {COVERAGE['ci']*100:.1f} %, "
          f"next reading {COVERAGE['pi']*100:.1f} %")
    print()
    print("  5. the same identity, two-way — a Gage R&R")
    for k in ("part", "operator", "interaction", "repeat"):
        print(f"     {k:<12} {GAUGE['pct'][k]:>6.2f} % of total variance")
    print(f"     gauge (everything but the parts) {GAUGE['pct_gauge']:.2f} %")
    print(f"     the arithmetic continues at {MSA_SITE}")
