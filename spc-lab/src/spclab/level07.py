"""LEVEL 7 — Evidence and decisions.

Sheet 1: the two ways to be wrong. The in-control curve and the same process
         shifted by one sigma, drawn against the same ±3σ limits, so the reader
         can see that almost the whole shifted curve is still inside them — then
         the power curve that puts a number on it at every shift size.
Sheet 2: the trade, as arithmetic. What each added Western Electric rule does to
         the in-control run length and to the time to catch a one-sigma shift,
         beside the published value for all four — and then the comparison that
         matters: the cost is fixed, the benefit is not.

Every number comes from spclab.evidence, which quotes α from formulas and the
single-point run length from detection.

    PYTHONPATH=src .venv/bin/python -m spclab.level07
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.evidence import (
    ALPHA_1,
    ARL0_ALL,
    ARL0_ONE_RULE,
    ARL1_ALL,
    ARL1_ONE_RULE,
    ARL_BIG_ALL,
    ARL_BIG_ONE,
    BIG_SHIFT,
    CHAMP_WOODALL_ARL0,
    FALSE_ALARM_COST,
    LIMIT,
    POWER_AT,
    RULE_TEXT,
    SHIFT,
    TRADE,
    cumulative_sets,
    p_value,
    power_one_point,
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


def _pdf(xs, mu=0.0):
    return np.exp(-((xs - mu) ** 2) / 2.0) / np.sqrt(2.0 * np.pi)


# ---------------------------------------------------------------------------
# Sheet 1 — alpha, beta, and the power curve
# ---------------------------------------------------------------------------
def sheet_l07_two_errors():
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=.22)

    # ---- left: both curves against the same limits
    ax = fig.add_subplot(gs[0, 0])
    xs = np.linspace(-5.2, 6.4, 1400)
    p0, p1 = _pdf(xs), _pdf(xs, SHIFT)

    out = np.abs(xs) > LIMIT
    ax.fill_between(xs, p0, where=out, color=RED, alpha=.75, lw=0)
    ax.plot(xs, p0, color=TEAL, lw=2.0, label="nothing has changed")

    ins = np.abs(xs) <= LIMIT
    ax.fill_between(xs, p1, where=ins, color=YELLOW, alpha=.20, lw=0)
    ax.plot(xs, p1, color=YELLOW, lw=2.0, ls="--",
            label=f"the mean has moved by {SHIFT:.0f}σ")

    for v in (-LIMIT, LIMIT):
        ax.axvline(v, color=MUTED, lw=1.3, ls=":")
    # low, not at the top: at 0.425 these sat inside the legend box
    ax.text(LIMIT + 0.12, 0.013, f"+{LIMIT:.0f}σ", color=MUTED, fontsize=11, ha="left")
    ax.text(-LIMIT - 0.12, 0.013, f"−{LIMIT:.0f}σ", color=MUTED, fontsize=11, ha="right")

    ax.annotate(f"α = {ALPHA_1*100:.2f} %\ncrying wolf",
                xy=(LIMIT + 0.28, 0.004), xytext=(LIMIT + 0.75, 0.10),
                fontsize=11.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    # inside the region it names, on a ground of its own — the previous position
    # put the text across the −3σ line
    ax.text(0.55, 0.105, f"β = {1 - POWER_AT[SHIFT]:.3f}\nthe shift stays inside",
            color=YELLOW, fontsize=11.5, ha="center",
            bbox=dict(facecolor=BG, edgecolor="none", alpha=.86, pad=3.0))

    ax.set_xlim(-5.2, 6.4)
    ax.set_ylim(0, 0.47)
    ax.set_xlabel("plotted statistic, in σ of itself")
    ax.set_ylabel("density")
    ax.set_title("a one-sigma shift is almost entirely inside the limits",
                 loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.30)
    ax.legend(frameon=False, fontsize=10.5, loc="upper right")

    # ---- right: the power curve
    axp = fig.add_subplot(gs[0, 1])
    ds = np.linspace(0, 4.2, 500)
    axp.plot(ds, [power_one_point(d) for d in ds], color=BLUE, lw=2.2)
    axp.axhline(0.5, color=MUTED, lw=1.0, ls=":")
    for d, c in ((SHIFT, YELLOW), (BIG_SHIFT, TEAL)):
        pw = power_one_point(d)
        axp.plot([d], [pw], "o", color=c, ms=7, zorder=5)
        axp.annotate(f"{d:.0f}σ → {pw*100:.1f} %", xy=(d, pw),
                     xytext=(d + 0.18, pw + 0.07), fontsize=11.5, color=c,
                     arrowprops=dict(arrowstyle="->", color=c, lw=1.1))
    axp.set_xlim(0, 4.2)
    axp.set_ylim(0, 1.02)
    axp.set_xlabel("size of the shift, in σ")
    axp.set_ylabel("chance the next point signals")
    axp.set_title("power — one point, one chance", loc="left",
                  fontsize=12.5, color=FG)
    axp.grid(alpha=.35)

    fig.suptitle(
        "Two ways to be wrong: α is crying wolf, β is staying silent — and the "
        "second one is the bigger problem\n"
        f"with limits at ±{LIMIT:.0f}σ a {SHIFT:.0f}σ shift moves the next point "
        f"outside them only {POWER_AT[SHIFT]*100:.1f} % of the time, so the chart "
        f"misses it {(1-POWER_AT[SHIFT])*100:.0f} % of the time it looks.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l07_1_two_errors")


# ---------------------------------------------------------------------------
# Sheet 2 — what each rule costs and what it buys
# ---------------------------------------------------------------------------
def sheet_l07_the_trade():
    sets = cumulative_sets()
    labels = ["+".join(str(r) for r in rs) for rs in sets]
    arl0 = [TRADE[rs]["arl0"] for rs in sets]
    arl1 = [TRADE[rs]["arl1"] for rs in sets]

    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=.26)

    # ---- left: both run lengths, log scale, as rules accumulate
    ax = fig.add_subplot(gs[0, 0])
    xs = np.arange(len(sets))
    ax.plot(xs, arl0, "-o", color=RED, lw=2.0, ms=7,
            label="false alarms — subgroups between them")
    ax.plot(xs, arl1, "-o", color=TEAL, lw=2.0, ms=7,
            label=f"real {SHIFT:.0f}σ shift — subgroups to catch it")
    ax.axhline(CHAMP_WOODALL_ARL0, color=YELLOW, lw=1.3, ls="--")
    # at the right-hand end this ran into the final data label
    ax.text(0.04, CHAMP_WOODALL_ARL0 * 1.12,
            f"published {CHAMP_WOODALL_ARL0} for all four (Champ & Woodall 1987)",
            color=YELLOW, fontsize=10.5, ha="left")
    for i, (a, b) in enumerate(zip(arl0, arl1)):
        ax.annotate(f"{a:.0f}", (i, a), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=10.5, color=RED)
        ax.annotate(f"{b:.1f}", (i, b), textcoords="offset points",
                    xytext=(0, -16), ha="center", fontsize=10.5, color=TEAL)
    ax.set_yscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"rule {l}" for l in labels])
    ax.set_ylim(5, 700)
    ax.set_ylabel("average run length (log scale)")
    ax.set_title("every rule added moves both lines down", loc="left",
                 fontsize=12.5, color=FG)
    ax.grid(alpha=.32, which="both")
    ax.legend(frameon=False, fontsize=10.5, loc="lower left")

    # ---- right: the cost is fixed, the benefit is not
    axc = fig.add_subplot(gs[0, 1])
    gains = [ARL1_ONE_RULE / ARL1_ALL, ARL_BIG_ONE / ARL_BIG_ALL]
    names = [f"{SHIFT:.0f}σ shift", f"{BIG_SHIFT:.0f}σ shift"]
    bars = axc.bar([0, 1], gains, width=.52, color=[TEAL, BLUE], alpha=.85)
    axc.axhline(FALSE_ALARM_COST, color=RED, lw=1.8)
    axc.text(1.42, FALSE_ALARM_COST + .12,
             f"the cost, always\n×{FALSE_ALARM_COST:.1f} more false alarms",
             color=RED, fontsize=11, ha="right")
    for b, g in zip(bars, gains):
        axc.text(b.get_x() + b.get_width() / 2, g + .12, f"×{g:.1f}",
                 ha="center", fontsize=12.5, color=FG)
    axc.set_xticks([0, 1])
    axc.set_xticklabels(names)
    axc.set_ylim(0, max(gains + [FALSE_ALARM_COST]) * 1.34)
    axc.set_ylabel("times sooner the shift is caught")
    axc.set_title("worth it, or not, depending on the shift", loc="left",
                  fontsize=12.5, color=FG)
    axc.grid(alpha=.30, axis="y")

    fig.suptitle(
        f"Turning on all four rules costs ×{FALSE_ALARM_COST:.1f} the false alarms "
        f"— {ARL0_ONE_RULE:.0f} subgroups between them becomes {ARL0_ALL:.0f}\n"
        f"it buys ×{ARL1_ONE_RULE/ARL1_ALL:.1f} at a {SHIFT:.0f}σ shift and only "
        f"×{ARL_BIG_ONE/ARL_BIG_ALL:.1f} at {BIG_SHIFT:.0f}σ. The cost is fixed; the "
        f"benefit is whatever shift you are actually trying to catch.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l07_2_the_trade")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l07_two_errors()
    sheet_l07_the_trade()
