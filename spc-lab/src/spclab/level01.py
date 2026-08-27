"""LEVEL 1 — Variation.

Sheet 1: the same measurements in two arrival orders. Identical histogram bin
         for bin, identical mean, identical spread — and one of those processes
         needs an engineer. The figure that justifies plotting in time order.
Sheet 2: Deming's funnel. Leaving a stable process alone against adjusting after
         every part, on the same random draws, with the exact factor of two.

Every number on both sheets comes from spclab.variation, so the sheets, the act
and the page cannot disagree.

    PYTHONPATH=src .venv/bin/python -m spclab.level01
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.variation import (
    ADJUST_EVERY,
    LEAVE_IT,
    PAIR_RUN_DRIFTING,
    PAIR_RUN_STABLE,
    TAMPER_SIGMA_RATIO_EXACT,
    TAMPER_VAR_RATIO,
    TAMPER_VAR_RATIO_EXACT,
    funnel,
    histograms_identical,
    same_histogram_pair,
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
# Sheet 1 — one set of numbers, two orders
# ---------------------------------------------------------------------------
def sheet_l01_time_order():
    stable, drifting = same_histogram_pair()
    n = len(stable)
    bins = 14
    lo, hi = min(stable.min(), drifting.min()), max(stable.max(), drifting.max())
    assert histograms_identical(stable, drifting, bins=bins), "the claim just broke"

    fig = plt.figure(figsize=(12.5, 6.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.35, 1], hspace=.38, wspace=.22)

    for row, (series, colour, label, run) in enumerate([
            (stable, TEAL, "as it happened", PAIR_RUN_STABLE),
            (drifting, YELLOW, "the same numbers, sorted — what a drift looks like",
             PAIR_RUN_DRIFTING)]):
        ax = fig.add_subplot(gs[row, 0])
        ax.plot(np.arange(1, n + 1), series, "-o", color=colour, lw=1.0, ms=2.6, alpha=.95)
        ax.axhline(series.mean(), color=MUTED, lw=1.1, ls="--")
        ax.set_ylim(lo - .35, hi + .35)
        ax.set_title(label, loc="left", fontsize=12, color=FG)
        ax.set_ylabel("measurement")
        ax.grid(alpha=.35)
        ax.text(.985, .06, f"longest run on one side: {run}", transform=ax.transAxes,
                ha="right", fontsize=11.5, color=colour,
                bbox=dict(facecolor=BG, edgecolor="none", alpha=.85, pad=2.5))
        if row == 1:
            ax.set_xlabel("part number, in the order it was made")

        axh = fig.add_subplot(gs[row, 1])
        axh.hist(series, bins=bins, range=(lo, hi), color=colour, alpha=.85,
                 orientation="horizontal")
        axh.set_ylim(lo - .35, hi + .35)
        axh.set_xlabel("count" if row == 1 else "")
        axh.set_title("histogram", loc="left", fontsize=11, color=MUTED)
        axh.grid(alpha=.3)

    fig.suptitle(
        f"The same {n} measurements, written down in two orders — "
        "identical histogram, identical mean, identical spread\n"
        "only the order says which process needs an engineer",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l01_1_time_order")


# ---------------------------------------------------------------------------
# Sheet 2 — Deming's funnel: the cost of adjusting a stable process
# ---------------------------------------------------------------------------
def sheet_l01_tampering():
    """Two stacked panels, same grammar as sheet 1.

    An earlier version overlaid both series on one axis, which hid the only thing
    the figure exists to show - that one of them is wider. Stacking them against a
    shared y-axis makes the penalty visible without reading the legend.
    """
    n = 160
    left = funnel(LEAVE_IT, n=n, seed=4)
    adjusted = funnel(ADJUST_EVERY, n=n, seed=4)
    lim = max(abs(adjusted).max(), abs(left).max()) * 1.08

    fig = plt.figure(figsize=(12.5, 6.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.35, 1], hspace=.38, wspace=.22)
    t_axis = np.arange(1, n + 1)

    for row, (series, colour, label) in enumerate([
            (left, TEAL, "leave the stable process alone"),
            (adjusted, RED, "adjust after every part, by what you just measured")]):
        ax = fig.add_subplot(gs[row, 0])
        ax.axhline(0, color=MUTED, lw=1.1, ls="--")
        ax.plot(t_axis, series, "-o", color=colour, lw=1.0, ms=2.6)
        ax.set_ylim(-lim, lim)
        ax.set_title(label, loc="left", fontsize=12, color=FG)
        ax.set_ylabel("deviation from\ntarget (σ)")
        ax.grid(alpha=.35)
        ax.text(.985, .06, f"σ = {series.std(ddof=1):.2f}", transform=ax.transAxes,
                ha="right", fontsize=12, color=colour,
                bbox=dict(facecolor=BG, edgecolor="none", alpha=.85, pad=2.5))
        if row == 1:
            ax.set_xlabel("part number")

        axh = fig.add_subplot(gs[row, 1])
        axh.hist(series, bins=20, range=(-lim, lim), color=colour, alpha=.85,
                 orientation="horizontal")
        axh.set_ylim(-lim, lim)
        axh.set_title("what the customer receives" if row == 0 else "",
                      loc="left", fontsize=11, color=MUTED)
        axh.set_xlabel("count" if row == 1 else "")
        axh.grid(alpha=.3)

    fig.suptitle(
        "Deming's funnel, rule 2 — the same random draws, the only difference is the operator\n"
        f"variance ×{TAMPER_VAR_RATIO:.2f} simulated against ×{TAMPER_VAR_RATIO_EXACT:.0f} exact, "
        f"so the spread is ×{TAMPER_SIGMA_RATIO_EXACT:.3f} wider for the extra work",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l01_2_tampering")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l01_time_order()
    sheet_l01_tampering()
