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
