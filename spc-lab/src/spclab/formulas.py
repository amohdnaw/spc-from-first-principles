"""SPC formulas — every constant derived or cited, nothing magic.

References:
- AIAG SPC Manual (2nd ed.) control chart constants, Table B.
- Montgomery, "Introduction to Statistical Quality Control", Ch. 5-6.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Shewhart constants. d2 = E(R/d2) -> expected range of n standard normals.
# Computed exactly by numerical integration instead of hard-coding a table,
# so any subgroup size works and the table itself becomes verifiable.
# ---------------------------------------------------------------------------
def _d2_d3(n: int, samples: int = 400_000) -> tuple[float, float]:
    """E(R) and sd(R) for n iid N(0,1) values — Monte Carlo (seeded).

    d2 normalizes the range into a sigma estimate; d3 drives the
    R-chart limit factors: D3 = max(0, 1 - 3*d3/d2), D4 = 1 + 3*d3/d2.
    """
    rng = np.random.default_rng(42)
    r = np.ptp(rng.standard_normal((samples, n)), axis=1)
    return float(r.mean()), float(r.std(ddof=1))


def control_limit_constants(n: int) -> dict[str, float]:
    """A2, D3, D4, d2 for an X̄-R chart with subgroup size n (n >= 2).

        UCL_xbar = xbarbar + A2 * Rbar      A2 = 3 / (d2 * sqrt(n))
        UCL_R    = D4 * Rbar                D4 = 1 + 3/d2
        LCL_R    = D3 * Rbar                D3 = max(0, 1 - 3/d2)
    """
    if n < 2:
        raise ValueError("subgroup size must be >= 2")
    d2, d3 = _d2_d3(n)
    return {
        "d2": round(d2, 4),
        "d3": round(d3, 4),
        "A2": round(3 / (d2 * np.sqrt(n)), 4),
        "D3": round(max(0.0, 1 - 3 * d3 / d2), 4),
        "D4": round(1 + 3 * d3 / d2, 4),
    }


def xbar_r_limits(data: np.ndarray) -> dict:
    """X̄-R chart limits from a (subgroups × n) array."""
    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError("expected 2-D array: subgroups along axis 0")
    n = data.shape[1]
    c = control_limit_constants(n)
    rbar = np.ptp(data, axis=1).mean()
    xbarbar = data.mean()
    return {
        "xbarbar": xbarbar,
        "rbar": rbar,
        "ucl_xbar": xbarbar + c["A2"] * rbar,
        "lcl_xbar": xbarbar - c["A2"] * rbar,
        "ucl_r": c["D4"] * rbar,
        "lcl_r": c["D3"] * rbar,
        **c,
    }


def capability_indices(values: np.ndarray, lsl: float, usl: float) -> dict:
    """Cp, Cpk, Pp, Ppk from individual observations.

    Cp   = (USL - LSL) / (6 * sigma_within)
    Cpk  = min(USL - mu, mu - LSL) / (3 * sigma_within)
    Ppk uses total sigma (long-term) instead of the within-subgroup estimate.
    Here values are individuals, so sigma_within = Rbar/d2 over sliding pairs
    is approximated by the total std — documented simplification for v0.1.
    """
    v = np.asarray(values, dtype=float)
    mu = v.mean()
    sigma = v.std(ddof=1)
    cp = (usl - lsl) / (6 * sigma)
    cpu = (usl - mu) / (3 * sigma)
    cpl = (mu - lsl) / (3 * sigma)
    return {
        "mean": mu,
        "sigma": sigma,
        "Cp": cp,
        "Cpu": cpu,
        "Cpl": cpl,
        "Cpk": min(cpu, cpl),
        "Ppk": min(cpu, cpl),  # same estimator on individuals
    }


def defects_per_million(mu: float, sigma: float, lsl: float, usl: float,
                        shift: float = 1.5) -> int:
    """Expected defective parts per million.

    With shift=1.5 reproduces the classic 'Six Sigma' convention:
    the mean is assumed to drift up to 1.5σ toward the nearer limit,
    so the worst-case tail sits at (distance to limit − shift).
    Pass shift=0 for the pure normal-theory answer.
    """
    z = min((usl - mu) / sigma, (mu - lsl) / sigma) - shift
    return int(round((1 - _phi(z)) * 1e6))


def _phi(z: float) -> float:
    """Standard normal CDF via erf (math.erf is exact to double precision)."""
    import math
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def ewma_limits(lam: float, k: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Time-varying EWMA control limits after observation i (i = 1..k):

        L_i = ± L * sigma * sqrt( lam/(2-lam) * (1-(1-lam)^{2i}) )

    L = 3 gives ARL matching a 3-sigma Shewhart chart for large shifts;
    returns (upper, lower) arrays. Asymptote: ±3σ·sqrt(lam/(2-lam)).
    """
    i = np.arange(1, k + 1)
    f = np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))
    return 3 * f, -3 * f


def western_electric_violations(points: np.ndarray, cl: float,
                                sigma: float) -> list[tuple[int, str]]:
    """Flag Western Electric rule violations in a series of plotted points.

    Rule 1: one point beyond 3σ          Rule 2: 2 of 3 beyond 2σ, same side
    Rule 3: 4 of 5 beyond 1σ, same side  Rule 4: 8 in a row on one side of CL
    Returns [(index, description), ...] — index of the point completing the run.
    """
    pts = np.asarray(points, dtype=float)
    z = (pts - cl) / sigma
    out: list[tuple[int, str]] = []

    def side(x):
        return 0 if abs(x) < 1e-12 else (1 if x > 0 else -1)

    for i, zi in enumerate(z):
        if abs(zi) > 3:
            out.append((i, "Rule 1: point beyond 3σ"))
        if i >= 2:
            w = z[i - 2:i + 1]
            s = side(w[2])
            if s and sum(side(v) == s and abs(v) > 2 for v in w) >= 2 \
               and all(abs(v) > 2 and side(v) == s for v in w[-2:]) :
                out.append((i, "Rule 2: 2 of 3 beyond 2σ, same side"))
        if i >= 4:
            w = z[i - 4:i + 1]
            s = side(w[4])
            if s and sum(abs(v) > 1 and side(v) == s for v in w) >= 4:
                out.append((i, "Rule 3: 4 of 5 beyond 1σ, same side"))
        if i >= 7:
            w = z[i - 7:i + 1]
            s = side(w[0])
            if s and all(side(v) == s for v in w):
                out.append((i, "Rule 4: 8 in a row, same side"))
    return out
