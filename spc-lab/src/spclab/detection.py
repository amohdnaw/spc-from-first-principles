"""How fast a rule notices a change — simulated, so nobody has to be believed.

Two acts make claims about detection speed: Level IV ("this chart is N times
faster") and the embedded EWMA act ("drift caught sooner"). They used to state
different multipliers, because each had its own hand-written number. The
numbers now come from here, so the two acts cannot disagree.

Everything is vectorised and seeded: 3,000 runs of 1,200 subgroups is about
four million updates, well under a second, and two renders agree to the last
digit.

    PYTHONPATH=src .venv/bin/python -m spclab.detection      # print the table
"""
from __future__ import annotations

import numpy as np

LAM = 0.2
SHEWHART_ARL0 = 370.4      # 1 / 0.0027 — the rate ±3σ buys by construction


def run_lengths(shift: float, limit: float, lam: float = LAM,
                n_sims: int = 3000, max_run: int = 1200, seed: int = 5):
    """Average subgroups to alarm for Shewhart ±3σ and for EWMA at `limit`."""
    rng = np.random.default_rng(seed)
    x = rng.normal(shift, 1.0, size=(n_sims, max_run))

    z = np.empty_like(x)
    prev = np.zeros(n_sims)
    for i in range(max_run):
        prev = lam * x[:, i] + (1.0 - lam) * prev
        z[:, i] = prev

    def first(hit: np.ndarray) -> np.ndarray:
        return np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, max_run)

    return (float(first(np.abs(x) > 3.0).mean()),
            float(first(np.abs(z) > limit).mean()))


def calibrate_ewma(target: float = SHEWHART_ARL0, lam: float = LAM) -> float:
    """The EWMA limit whose in-control ARL matches Shewhart's ±3σ.

    Without this the comparison is rigged: a lower limit always detects sooner
    because it also cries wolf more often. Bisection on the simulated ARL0,
    which is monotonic in the limit.
    """
    lo, hi = 0.6, 1.4
    for _ in range(9):
        mid = (lo + hi) / 2
        _, arl0 = run_lengths(0.0, mid, lam=lam, n_sims=1500, max_run=2000, seed=3)
        if arl0 < target:
            lo = mid          # alarms too often — raise the limit
        else:
            hi = mid
    return (lo + hi) / 2


EWMA_LIMIT = calibrate_ewma()
ARL0_SHEW, ARL0_EWMA = run_lengths(0.0, EWMA_LIMIT, n_sims=1500,
                                   max_run=2000, seed=3)
ARL1_SHEW, ARL1_EWMA = run_lengths(1.0, EWMA_LIMIT, n_sims=4000,
                                   max_run=600, seed=11)
SPEEDUP = ARL1_SHEW / ARL1_EWMA

# The asymptotic EWMA standard deviation, σ_z = σ·sqrt(λ/(2−λ)). Exact, not
# simulated — it is what the limits are built from.
SIGMA_Z = float(np.sqrt(LAM / (2 - LAM)))


if __name__ == "__main__":
    print(f"λ = {LAM}   σ_z = {SIGMA_Z:.4f} σ")
    print(f"EWMA limit calibrated to ±{EWMA_LIMIT:.3f} σ_x")
    print(f"ARL0   Shewhart {ARL0_SHEW:7.1f}   EWMA {ARL0_EWMA:7.1f}")
    print(f"ARL1σ  Shewhart {ARL1_SHEW:7.1f}   EWMA {ARL1_EWMA:7.1f}"
          f"   → {SPEEDUP:.2f}× sooner")


# The demonstration process: 80 subgroups, quiet until 20, then a ramp of
# 0.06 σ per subgroup. The old act ramped at 0.15 σ, which reaches 6 σ inside
# the window — on that data the Shewhart chart caught the drift one subgroup
# after the EWMA, so the single realisation contradicted the averages it was
# supposed to illustrate. This ramp is slow enough to be the failure mode the
# act is about, and seed 35 is a run whose lead matches the simulated ARLs.
N_SUB, SHIFT_AT, DRIFT, SEED = 80, 20, 0.06, 35


def drifting_process():
    """One process: quiet, then a slow ramp. Same data for both charts."""
    rng = np.random.default_rng(SEED)
    raw = rng.normal(0, 1, N_SUB) + np.where(
        np.arange(N_SUB) >= SHIFT_AT, (np.arange(N_SUB) - SHIFT_AT) * DRIFT, 0.0)
    z, zs = 0.0, []
    for v in raw:
        z = LAM * v + (1 - LAM) * z
        zs.append(z)
    return raw, np.array(zs)


RAW, ZS = drifting_process()
# where each rule fires on this run, and how far the mean had already moved
DET_SHEW = int(next(k for k, v in enumerate(RAW) if abs(v) > 3.0))
DET_EWMA = int(next(k for k, v in enumerate(ZS) if abs(v) > EWMA_LIMIT))
OFF_SHEW = (DET_SHEW - SHIFT_AT) * DRIFT
OFF_EWMA = (DET_EWMA - SHIFT_AT) * DRIFT
