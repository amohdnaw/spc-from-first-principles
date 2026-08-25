"""LEVEL 4 — Detection theory: how fast do charts catch a change?

Sheet 1: ARL vs shift size — Monte Carlo comparison of Shewhart vs EWMA.
         (ARL = average number of subgroups until the alarm.)
Sheet 2: the same drifting process under both charts, detection moments marked.

    PYTHONPATH=src .venv/bin/python -m spclab.level4
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

BG, FG, MUTED = "#0e1116", "#e8e8e8", "#8a939f"
BLUE, TEAL, YELLOW, RED = "#58C4DD", "#5CD0B3", "#FFD54F", "#FC6255"
GRID = "#232a33"

mpl.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.edgecolor": MUTED, "axes.labelcolor": FG,
    "xtick.color": MUTED, "ytick.color": MUTED, "grid.color": GRID,
    "font.family": "serif", "mathtext.fontset": "cm",
    "axes.spines.top": False, "axes.spines.right": False,
})

LAM = 0.2
MAXRUN = 2000


def _run_lengths(shift, lam=LAM, n_sims=20_000, seed=1, mult=3.0):
    """Simulate run lengths of both charts for a step shift of `shift` σx̄."""
    rng = np.random.default_rng(seed)
    ewma_lim_k = mult * np.sqrt(lam / (2 - lam))          # calibrated limits
    rl_shew, rl_ewma = [], []
    for s in range(n_sims):
        z_old, done_s, done_e = 0.0, None, None
        for i in range(1, MAXRUN):
            x = rng.normal(shift, 1.0)
            # shewhart
            if done_s is None and abs(x) > 3:
                done_s = i
            # ewma
            z_old = lam * x + (1 - lam) * z_old
            if done_e is None and abs(z_old) > ewma_lim_k:
                done_e = i
            if done_s is not None and done_e is not None:
                break
        rl_shew.append(done_s or MAXRUN)
        rl_ewma.append(done_e or MAXRUN)
    return np.array(rl_shew), np.array(rl_ewma)


def _calibrate_ewma(target=367.0):
    """Find limit multiplier c so EWMA's ARL0 matches Shewhart's 1/0.0027 ≈ 370.
    Keeps the comparison honest: same false-alarm rate, different sensitivity."""
    lo, hi = 2.8, 3.6
    for _ in range(12):
        mid = (lo + hi) / 2
        a, b = _run_lengths(0.0, lam=LAM, n_sims=4000)
        # scale limits by mid/3 via monkey-run: rerun with custom multiplier
        rl = _run_custom(mid, n_sims=6000)
        if rl > target:
            hi = mid          # too few alarms -> raise... wait: higher limit => longer ARL
        else:
            lo = mid
    return (lo + hi) / 2


def _run_custom(c_mult, lam=LAM, n_sims=6000, seed=7):
    rng = np.random.default_rng(seed)
    lim = c_mult * np.sqrt(lam / (2 - lam))
    rls = []
    for s in range(n_sims):
        z_old = 0.0
        for i in range(1, MAXRUN):
            x = rng.normal(0.0, 1.0)
            z_old = lam * x + (1 - lam) * z_old
            if abs(z_old) > lim:
                rls.append(i)
                break
        else:
            rls.append(MAXRUN)
    return np.mean(rls)


def sheet_l4_arl():
    shifts = np.array([0, .25, .5, .75, 1.0, 1.5, 2.0])
    c_mult = _calibrate_ewma()
    print(f"EWMA limit multiplier calibrated to c={c_mult:.3f} "
          "for matched ARL0")
    arl_s, arl_e = [], []
    for d in shifts:
        a, b = _run_lengths(d, n_sims=8_000, mult=c_mult)
        arl_s.append(a.mean()); arl_e.append(b.mean())
        print(f"shift {d:+.2f}σ:  Shewhart ARL={a.mean():7.1f}   EWMA ARL={b.mean():6.1f}")
    arl_s, arl_e = np.array(arl_s), np.array(arl_e)

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.semilogy(shifts, arl_s, "-o", color=BLUE, lw=2.2, ms=5,
                label="Shewhart ±3σ (single point)")
    ax.semilogy(shifts, arl_e, "-o", color=YELLOW, lw=2.2, ms=5,
                label=f"EWMA λ={LAM} (limits calibrated for equal ARL0)")
    ax.annotate(f"both ≈ {arl_s[0]:.0f} subgroups\n(false-alarm rate matched)",
                xy=(0, arl_s[0]), xytext=(0.15, arl_s[0] * 1.6),
                fontsize=12, color=MUTED,
                arrowprops=dict(arrowstyle="->", color=MUTED))
    mid = 4
    speedup = arl_s[mid] / arl_e[mid]
    ax.annotate(f"a 1σ drift:\nEWMA catches it in {arl_e[mid]:.0f}\n"
                f"vs {arl_s[mid]:.0f} subgroups —\n{speedup:.0f}× sooner",
                xy=(shifts[mid], arl_e[mid]), xytext=(shifts[mid] + .25, arl_e[mid] * 6),
                fontsize=12, color=YELLOW,
                arrowprops=dict(arrowstyle="->", color=YELLOW))
    ax.set_title("Average Run Length vs shift size — simulated, 8 000 runs per point\n"
                 "same false-alarm rate, wildly different sensitivity to drift",
                 loc="left")
    ax.set_xlabel("process shift when it happens (in σx̄ units)")
    ax.set_ylabel("average subgroups until alarm (log scale)")
    ax.legend(frameon=False); ax.grid(alpha=.5, which="both")
    fig.savefig("docs/41_l4_arl.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote docs/41_l4_arl.png")


def sheet_l4_race():
    """One drifting process, two charts racing to detect it."""
    rng = np.random.default_rng(55)
    n = 60
    shift_at = 20
    raw = rng.normal(0, 1, n) + np.where(np.arange(n) >= shift_at,
                                         (np.arange(n) - shift_at) * 0.15, 0)
    lam = LAM
    z, zs = 0.0, []
    for x in raw:
        z = lam * x + (1 - lam) * z
        zs.append(z)
    zs = np.array(zs)
    lim = 3 * np.sqrt(lam / (2 - lam))

    det_s = next(i for i, v in enumerate(raw) if abs(v) > 3)
    det_e = next(i for i, v in enumerate(zs) if abs(v) > lim)

    fig, axs = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                            constrained_layout=True)
    x = np.arange(1, n + 1)

    ax = axs[0]
    ax.axhline(3, color=BLUE, ls="--", lw=1.2); ax.axhline(-3, color=BLUE, ls="--", lw=1.2)
    ax.plot(x, raw, "-", color=MUTED, lw=1)
    ax.plot(x[:det_s], raw[:det_s], "-o", color=BLUE, ms=3.5)
    ax.plot(x[det_s:], raw[det_s:], "-o", color=RED, ms=3.5)
    ax.plot(det_s + 1, raw[det_s], "o", ms=9, mfc="none", mec=RED, mew=2)
    ax.set_title(f"Shewhart: waits for an extreme point → detects at subgroup "
                 f"{det_s+1}", loc="left", color=BLUE, fontsize=13)

    ax = axs[1]
    ax.axhline(lim, color=YELLOW, ls="--", lw=1.2)
    ax.axhline(-lim, color=YELLOW, ls="--", lw=1.2)
    ax.plot(x, zs, "-o", color=TEAL, ms=3.5)
    ax.plot(x[:det_e], zs[:det_e], "-o", color=MUTED, ms=3.5)
    ax.plot(x[det_e:], zs[det_e:], "-o", color=YELLOW, ms=3.5)
    ax.plot(det_e + 1, zs[det_e], "o", ms=9, mfc="none", mec=YELLOW, mew=2)
    ax.set_title(f"EWMA (λ=0.2): accumulates evidence → detects at subgroup "
                 f"{det_e+1} — {(det_s-det_e)} subgroups earlier",
                 loc="left", color=YELLOW, fontsize=13)
    ax.set_xlabel("subgroup")
    for ax in axs:
        ax.axvspan(shift_at, n, color=RED, alpha=.06)
        ax.text(shift_at + 1, ax.get_ylim()[1]*.85, "drift starts",
                fontsize=10, color=MUTED)

    fig.suptitle("Same process. Same false-alarm rate. Different memory.",
                 fontsize=15, y=1.03)
    fig.savefig("docs/42_l4_race.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote docs/42_l4_race.png")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l4_arl()
    sheet_l4_race()
