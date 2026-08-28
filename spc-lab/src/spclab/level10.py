"""LEVEL 10 — Counting, not measuring.

Sheet 1: the mean fixes the spread, and what that buys you. The binomial sigma
         as a function of the rate, then two p-charts with the same average and
         different scatter — one a genuine binomial, one with the rate drifting
         between subgroups, told apart by a ratio you get for free.
Sheet 2: the limits breathe. A p-chart where the subgroup size varies, with the
         average-n limits laid over the honest ones and the points they
         misclassify; then the lower limit against n, and where it falls off the
         bottom of the chart.

Every number comes from spclab.counting, which reuses the incomplete beta from
spclab.estimation for exact binomial tails.

    PYTHONPATH=src .venv/bin/python -m spclab.level10
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.counting import (
    C_BAR,
    DISPERSION_BATCHED,
    DISPERSION_CLEAN,
    K,
    MISCLASS,
    NP_THRESHOLD,
    N_CONST,
    N_FOR_LCL,
    N_VARY,
    P_BAR,
    TAIL,
    binomial_sigma,
    p_limits,
    simulate_batch_effect,
    simulate_binomial,
)

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


def _save(fig, name):
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", f"docs/{name}.png")


# ---------------------------------------------------------------------------
# Sheet 1 — the mean fixes the spread, and a free diagnostic
# ---------------------------------------------------------------------------
def sheet_l10_spread_is_not_free():
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.55], hspace=.42, wspace=.22)

    # ---- left: sigma as a function of the rate
    ax = fig.add_subplot(gs[:, 0])
    ps = np.linspace(0.001, 0.999, 600)
    ax.plot(ps, [binomial_sigma(N_CONST, p) for p in ps], color=TEAL, lw=2.2)
    ax.plot([P_BAR], [binomial_sigma(N_CONST, P_BAR)], "o", color=YELLOW, ms=7,
            zorder=5)
    ax.annotate(f"our rate: {P_BAR:.2f}\nσ = {binomial_sigma(N_CONST, P_BAR):.5f}",
                xy=(P_BAR, binomial_sigma(N_CONST, P_BAR)),
                xytext=(0.20, 0.0125), fontsize=11, color=YELLOW,
                arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.1))
    ax.set_xlabel("fraction defective, " + r"$\bar{p}$")
    ax.set_ylabel(r"$\sigma$ of the proportion")
    ax.set_title(r"for counts, $\sigma=\sqrt{\bar{p}(1-\bar{p})/n}$",
                 loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.32)
    # under the descending branch: centred at the top it crossed the curve
    ax.text(.97, .30, "no separate estimate,\nso no range chart\nbeside it",
            transform=ax.transAxes, ha="right", va="top", fontsize=11, color=MUTED)

    # ---- right: two processes with the same mean
    clean, batched = simulate_binomial(), simulate_batch_effect()
    show = 90
    lim = p_limits(N_CONST)
    for row, (counts, colour, name, ratio) in enumerate([
            (clean, TEAL, "one rate, every subgroup", DISPERSION_CLEAN),
            (batched, RED, "the rate drifting between subgroups", DISPERSION_BATCHED)]):
        axp = fig.add_subplot(gs[row, 1])
        props = counts[:show] / N_CONST
        axp.axhline(lim["cl"], color=MUTED, lw=1.1, ls="--")
        axp.axhline(lim["ucl"], color=YELLOW, lw=1.5)
        axp.plot(np.arange(1, show + 1), props, "-o", color=colour, lw=1.0, ms=2.8)
        axp.set_ylim(0, max(0.115, props.max() * 1.12))
        axp.set_ylabel("fraction\ndefective")
        axp.set_title(f"{name} — dispersion ratio {ratio:.2f}",
                      loc="left", fontsize=12, color=FG)
        axp.grid(alpha=.3)
        if row == 1:
            axp.set_xlabel("subgroup")
        axp.text(.985, .88, f"mean {props.mean():.4f}", transform=axp.transAxes,
                 ha="right", fontsize=11, color=colour,
                 bbox=dict(facecolor=BG, edgecolor="none", alpha=.85, pad=2.4))

    fig.suptitle(
        "Stop measuring and start counting, and the distribution hands you the "
        "spread — which makes a disagreement informative\n"
        f"both panels average {P_BAR:.2f} defective — the lower one is not wider, it "
        f"is a process whose rate moved, and the variance ratio "
        f"({DISPERSION_BATCHED:.2f} against {DISPERSION_CLEAN:.2f}) is what says so.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l10_1_spread_is_not_free")


# ---------------------------------------------------------------------------
# Sheet 2 — breathing limits, and the floor
# ---------------------------------------------------------------------------
def sheet_l10_breathing_limits():
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=.24)

    # ---- left: limits that breathe, and the average-n shortcut
    ax = fig.add_subplot(gs[0, 0])
    rng = np.random.default_rng(8)
    ns = np.array([N_VARY[i % len(N_VARY)] for i in range(34)])
    counts = rng.binomial(ns, P_BAR)
    props = counts / ns
    ucl = np.array([p_limits(int(n))["ucl"] for n in ns])
    lcl = np.array([p_limits(int(n))["lcl"] for n in ns])
    n_bar = int(round(float(ns.mean())))
    flat = p_limits(n_bar)

    xs = np.arange(1, len(ns) + 1)
    ax.step(xs, ucl, where="mid", color=YELLOW, lw=1.8, label="honest limits, per n")
    ax.step(xs, lcl, where="mid", color=YELLOW, lw=1.8)
    ax.axhline(flat["ucl"], color=RED, lw=1.5, ls=":",
               label=f"one limit at average n = {n_bar}")
    ax.axhline(P_BAR, color=MUTED, lw=1.1, ls="--")

    wrong = (props <= ucl) & (props > flat["ucl"])
    ax.plot(xs[~wrong], props[~wrong], "o", color=BLUE, ms=5.5)
    if wrong.any():
        ax.plot(xs[wrong], props[wrong], "o", color=RED, ms=8, zorder=5,
                label="called a signal only by the shortcut")

    ax.set_xlabel("subgroup (size varies 120–360)")
    ax.set_ylabel("fraction defective")
    ax.set_title("a p-chart's limits are a function of each subgroup's size",
                 loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.32)
    # outside the axes: the step limits occupy both the top and the bottom of the
    # plot, so every in-axes corner sat on data
    ax.legend(frameon=False, fontsize=10.5, loc="upper center",
              bbox_to_anchor=(0.5, -0.135), ncol=3)

    # ---- right: where the lower limit falls off
    axl = fig.add_subplot(gs[0, 1])
    n_grid = np.arange(40, 601)
    raw = np.array([p_limits(int(n))["lcl_raw"] for n in n_grid])
    axl.axhline(0, color=MUTED, lw=1.2)
    axl.plot(n_grid, raw, color=TEAL, lw=2.2)
    axl.fill_between(n_grid, raw, 0, where=raw < 0, color=RED, alpha=.30, lw=0)
    axl.axvline(N_FOR_LCL, color=YELLOW, lw=1.6, ls="--")
    axl.annotate(f"LCL clears zero\nat n = {N_FOR_LCL}",
                 xy=(N_FOR_LCL, 0), xytext=(N_FOR_LCL + 55, -0.0085),
                 fontsize=11, color=YELLOW,
                 arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.1))
    folklore = int(round(5.0 / P_BAR))
    axl.plot([folklore], [p_limits(folklore)["lcl_raw"]], "o", color=RED, ms=7)
    axl.annotate(f"the “$n\\bar{{p}}\\geq 5$” rule\nstops here — still negative",
                 xy=(folklore, p_limits(folklore)["lcl_raw"]),
                 xytext=(folklore - 20, -0.019), fontsize=10.5, color=RED,
                 arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))
    axl.set_xlabel("subgroup size, n")
    axl.set_ylabel("lower limit before clamping")
    axl.set_title("below the threshold it can only signal upward",
                  loc="left", fontsize=12.5, color=FG)
    axl.grid(alpha=.30)

    fig.suptitle(
        f"When n varies, one set of limits at the average disagrees with the honest "
        f"ones on {MISCLASS['disagree']*100:.2f} % of subgroups\n"
        f"and a lower limit needs " + r"$n\bar{p} > k^2(1-\bar{p})$" +
        f" = {NP_THRESHOLD:.2f} before it clears zero — so at "
        f"{P_BAR:.2f} defective you need n ≥ {N_FOR_LCL}, not the 125 the rule of "
        f"thumb allows.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l10_2_breathing_limits")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l10_spread_is_not_free()
    sheet_l10_breathing_limits()
