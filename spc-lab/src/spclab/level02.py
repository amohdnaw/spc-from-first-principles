"""LEVEL 2 — Chance.

Sheet 1: one sequence of fair flips, read two ways. The surplus of heads over
         tails grows without limit while the proportion settles on one half.
         Both panels are the same flips, which is what makes the law of averages
         indefensible rather than merely unfashionable.
Sheet 2: what "0.27 %" is a claim about. The chance of at least one false alarm
         against the number of subgroups run, and the geometric waiting time
         underneath it — whose median is well short of its mean.

Every number comes from spclab.chance, which in turn quotes α and the average
run length from the modules that publish them, so the sheets, the act and the
page cannot disagree.

    PYTHONPATH=src .venv/bin/python -m spclab.level02
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.chance import (
    ALPHA,
    ARL0,
    FLIPS,
    MEDIAN_WAIT,
    MILESTONES,
    ONE_MINUS_1_OVER_E,
    P_IN_ARL0,
    P_IN_SHIFT,
    SHIFT_SUBGROUPS,
    expected_gap_asymptote,
    expected_gap_exact,
    expected_rate_error,
    flips,
    gap_trace,
    p_any_alarm,
    rate_trace,
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
# Sheet 1 — the gap grows, the rate settles, one sequence
# ---------------------------------------------------------------------------
def sheet_l02_long_run():
    """Two stacked panels on a shared log-n axis.

    The x axis is logarithmic because the claim spans three orders of magnitude
    and is invisible on a linear one: at n = 10,000 the interesting part of the
    convergence has already happened inside the first pixel column.
    """
    seq = flips(FLIPS)
    n_axis = np.arange(1, FLIPS + 1)
    gap = gap_trace(seq)
    rate = rate_trace(seq)

    grid = np.unique(np.geomspace(1, FLIPS, 400).astype(int))
    envelope = np.array([expected_gap_exact(int(n)) for n in grid])
    err = np.array([expected_rate_error(int(n)) for n in grid])

    fig = plt.figure(figsize=(12.5, 6.8))
    gs = fig.add_gridspec(2, 1, hspace=.30)

    # ---- top: the surplus, which has no reason to come back
    ax = fig.add_subplot(gs[0, 0])
    ax.axhline(0, color=MUTED, lw=1.1, ls="--")
    ax.plot(n_axis, gap, color=BLUE, lw=1.0, label="this sequence")
    ax.plot(grid, envelope, color=YELLOW, lw=1.8,
            label=r"$\mathbb{E}|S_n| = 2^{1-n}\,n\,\binom{n-1}{\lfloor (n-1)/2\rfloor}$")
    ax.plot(grid, np.sqrt(2 * grid / np.pi), color=RED, lw=1.2, ls=":",
            label=r"$\sqrt{2n/\pi}$")
    ax.set_xscale("log")
    ax.set_xlim(1, FLIPS)
    ax.set_ylabel("| heads − tails |")
    ax.set_title("the surplus grows — a deficit is never repaid",
                 loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.35)
    ax.legend(frameon=False, fontsize=10.5, loc="upper left")

    # ---- bottom: the proportion, converging on the same flips
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.axhline(0.5, color=MUTED, lw=1.1, ls="--")
    ax2.plot(n_axis, rate, color=BLUE, lw=1.0)
    ax2.fill_between(grid, 0.5 - err, 0.5 + err, color=TEAL, alpha=.20,
                     label=r"$\pm\,\mathbb{E}|\hat{p}-\frac{1}{2}| = \mathbb{E}|S_n|\,/\,2n$")
    ax2.set_xscale("log")
    ax2.set_xlim(1, FLIPS)
    ax2.set_ylim(0.5 - 0.62, 0.5 + 0.62)
    ax2.set_xlabel("flips, n (log scale)")
    ax2.set_ylabel("proportion of heads")
    ax2.set_title("the rate settles — the same sequence, divided by n",
                  loc="left", fontsize=12.5, color=FG)
    ax2.grid(alpha=.35)
    ax2.legend(frameon=False, fontsize=10.5, loc="upper right")

    rows = "   ".join(
        f"n={n:,}: gap {expected_gap_exact(n):.0f}, "
        f"error {expected_rate_error(n):.5f}" for n in MILESTONES)
    fig.suptitle(
        "One sequence of fair flips, read two ways — the numerator grows like "
        r"$\sqrt{n}$ and the denominator like $n$" "\n" + rows,
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l02_1_long_run")


# ---------------------------------------------------------------------------
# Sheet 2 — what a rate of 0.27 % actually costs over a shift
# ---------------------------------------------------------------------------
def sheet_l02_what_a_rate_claims():
    """The cumulative chance of a false alarm, and the wait that produces it."""
    n = np.arange(0, 1201)
    p = p_any_alarm(n)

    fig = plt.figure(figsize=(12.5, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.62, 1], wspace=.24)

    # ---- left: it is a rate, and rates accumulate
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(n, p, color=TEAL, lw=2.0)
    ax.plot(n, np.minimum(1.0, ALPHA * n), color=RED, lw=1.2, ls=":",
            label="what adding the rate up would give")
    ax.axhline(ONE_MINUS_1_OVER_E, color=YELLOW, lw=1.2, ls="--")
    ax.text(1195, ONE_MINUS_1_OVER_E + .022, r"$1 - 1/e$", ha="right",
            fontsize=12, color=YELLOW)

    for x, y, txt in ((SHIFT_SUBGROUPS, P_IN_SHIFT,
                       f"a shift of {SHIFT_SUBGROUPS}\n{P_IN_SHIFT*100:.1f} %"),
                      (ARL0, P_IN_ARL0, f"the {ARL0:.0f} in “1 in {ARL0:.0f}”\n"
                                        f"{P_IN_ARL0*100:.1f} %")):
        ax.plot([x], [y], "o", color=BLUE, ms=7, zorder=5)
        ax.annotate(txt, xy=(x, y), xytext=(x + 70, y - .17),
                    fontsize=11.5, color=FG,
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.1))

    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("subgroups plotted, nothing having changed")
    ax.set_ylabel("chance of at least one false alarm")
    ax.set_title(r"$1-(1-\alpha)^n$ — the chart's own rate, accumulated",
                 loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.35)
    ax.legend(frameon=False, fontsize=10.5, loc="lower right")

    # ---- right: the wait, whose median is not its mean
    axw = fig.add_subplot(gs[0, 1])
    k = np.arange(1, 1201)
    pmf = ALPHA * (1 - ALPHA) ** (k - 1)
    axw.fill_between(k, pmf, color=BLUE, alpha=.55, lw=0)
    axw.axvline(MEDIAN_WAIT, color=TEAL, lw=1.6)
    axw.axvline(ARL0, color=YELLOW, lw=1.6, ls="--")
    top = pmf.max()
    axw.text(MEDIAN_WAIT - 26, top * .92, f"median\n{MEDIAN_WAIT:.0f}",
             fontsize=11.5, color=TEAL, ha="right")
    axw.text(ARL0 + 30, top * .62, f"mean\n{ARL0:.0f}", fontsize=11.5, color=YELLOW)
    axw.set_xlim(0, 1200)
    axw.set_ylim(0, top * 1.12)
    axw.set_xlabel("subgroups until the first false alarm")
    axw.set_ylabel("probability")
    axw.set_title("geometric — half arrive before the median",
                  loc="left", fontsize=12.5, color=FG)
    axw.grid(alpha=.30)

    fig.suptitle(
        f"“0.27 % per subgroup” is a rate, not a per-part risk — α = {ALPHA:.4f}, "
        f"one alarm in {ARL0:.1f} subgroups on average\n"
        f"over {SHIFT_SUBGROUPS} subgroups the chance of at least one is "
        f"{P_IN_SHIFT*100:.1f} %; over {ARL0:.0f} it is {P_IN_ARL0*100:.1f} %, "
        f"not 100 % — an average is not a deadline",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l02_2_what_a_rate_claims")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l02_long_run()
    sheet_l02_what_a_rate_claims()
