"""LEVEL 5 — Estimation and uncertainty.

Sheet 1: coverage, counted. Forty intervals from forty samples against the true
         mean nobody is allowed to see, then the coverage of a nominal 95 %
         interval against sample size — built with a normal quantile, which
         under-covers, and with t, which does not.
Sheet 2: the price of precision, and the curriculum's own constants. Interval
         width against n with the halving cost marked both ways, and the spread
         of sixty independent estimates of d₂ beside the value the library
         publishes.

Every number comes from spclab.estimation, which quotes d₂ from spclab.formulas.

    PYTHONPATH=src .venv/bin/python -m spclab.level05
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.estimation import (
    CONF,
    COVER_T,
    COVER_Z,
    D2_MEAN,
    D2_PUBLISHED,
    D2_SE,
    D2_SUBGROUPS_FOR_3DP,
    HALVE_FROM,
    HALVE_N_T,
    HALVE_N_Z,
    SIZES,
    TRUE_MEAN,
    TRUE_SIGMA,
    Z_95,
    d2_estimates,
    interval_width,
    samples,
    t_quantile,
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
# Sheet 1 — coverage is something you count
# ---------------------------------------------------------------------------
def sheet_l05_coverage():
    n = 5
    show = 40
    s = samples(n, trials=show, seed=3)
    m = s.mean(axis=1)
    sd = s.std(axis=1, ddof=1)
    half_t = t_quantile(n - 1) * sd / np.sqrt(n)
    half_z = Z_95 * sd / np.sqrt(n)

    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], wspace=.22)

    # ---- left: the intervals themselves, and the line they are trying to catch
    ax = fig.add_subplot(gs[0, 0])
    ax.axvline(TRUE_MEAN, color=YELLOW, lw=1.8)
    ax.text(TRUE_MEAN + 0.055, show + 1.4, "the true mean — never observed",
            color=YELLOW, fontsize=11, ha="left")
    for i in range(show):
        miss = not (m[i] - half_t[i] <= TRUE_MEAN <= m[i] + half_t[i])
        c = RED if miss else TEAL
        ax.plot([m[i] - half_t[i], m[i] + half_t[i]], [i, i], "-", color=c, lw=1.9,
                solid_capstyle="round")
        ax.plot([m[i]], [i], "o", color=c, ms=3.4)
    hits = sum((m - half_t <= TRUE_MEAN) & (TRUE_MEAN <= m + half_t))
    ax.set_ylim(-1.5, show + 3)
    ax.set_xlabel("estimate of the process mean (mm)")
    ax.set_ylabel("one sample of five parts per row")
    ax.set_title(f"{show} samples, {show} intervals — {show - hits} miss "
                 f"({hits}/{show} caught it)", loc="left", fontsize=12.5, color=FG)
    ax.grid(alpha=.3, axis="x")

    # ---- right: coverage against n, both quantiles
    axc = fig.add_subplot(gs[0, 1])
    xs = np.arange(len(SIZES))
    axc.axhline(CONF, color=YELLOW, lw=1.6, ls="--")
    axc.text(len(SIZES) - 0.5, CONF + .006, "nominal 95 %", color=YELLOW,
             fontsize=11, ha="right")
    axc.plot(xs, [COVER_Z[k] for k in SIZES], "-o", color=RED, lw=1.8, ms=5.5,
             label=r"built with $z = 1.96$")
    axc.plot(xs, [COVER_T[k] for k in SIZES], "-o", color=TEAL, lw=1.8, ms=5.5,
             label=r"built with $t_{n-1}$")
    for i, k in enumerate(SIZES):
        axc.annotate(f"{COVER_Z[k]*100:.0f}%", (i, COVER_Z[k]), textcoords="offset points",
                     xytext=(0, -15), ha="center", fontsize=10, color=RED)
    axc.set_xticks(xs)
    axc.set_xticklabels([str(k) for k in SIZES])
    axc.set_ylim(0.62, 1.005)
    axc.set_xlabel("parts per sample, n")
    axc.set_ylabel("intervals that contain the true mean")
    axc.set_title("what the interval actually delivers", loc="left",
                  fontsize=12.5, color=FG)
    axc.grid(alpha=.35)
    axc.legend(frameon=False, fontsize=10.5, loc="lower right")

    fig.suptitle(
        "A 95 % interval is a claim about the procedure, not about this interval — "
        "so the way to check it is to count\n"
        f"from five parts, a normal quantile delivers {COVER_Z[5]*100:.1f} %, not 95 %; "
        f"t delivers {COVER_T[5]*100:.1f} %. That gap is why t exists.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l05_1_coverage")


# ---------------------------------------------------------------------------
# Sheet 2 — the price of precision, and our own constants
# ---------------------------------------------------------------------------
def sheet_l05_price():
    fig = plt.figure(figsize=(12.6, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1], wspace=.24)

    # ---- left: width against n
    ax = fig.add_subplot(gs[0, 0])
    ns = np.arange(2, 121)
    w_t = np.array([interval_width(int(k)) for k in ns])
    w_z = np.array([interval_width(int(k), use_t=False) for k in ns])
    ax.plot(ns, w_z, color=BLUE, lw=2.0, label=r"σ known — width $\propto 1/\sqrt{n}$")
    ax.plot(ns, w_t, color=TEAL, lw=2.0, ls="--",
            label=r"σ estimated — $t_{n-1}$, wider and steeper")

    base = interval_width(HALVE_FROM, use_t=False)
    ax.plot([HALVE_FROM], [base], "o", color=YELLOW, ms=7, zorder=5)
    ax.plot([HALVE_N_Z], [base / 2], "o", color=YELLOW, ms=7, zorder=5)
    ax.annotate("", xy=(HALVE_N_Z, base / 2), xytext=(HALVE_FROM, base),
                arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.4,
                                connectionstyle="arc3,rad=-.25"))
    ax.text(HALVE_N_Z + 4, base / 2 + .05,
            f"half the width costs\n{HALVE_FROM} → {HALVE_N_Z} parts (×4)",
            color=YELLOW, fontsize=11)
    ax.set_ylim(0, 2.6)
    ax.set_xlim(2, 120)
    ax.set_xlabel("parts per sample, n")
    ax.set_ylabel("width of the 95 % interval (mm)")
    ax.set_title("precision is bought at a square-law price", loc="left",
                 fontsize=12.5, color=FG)
    ax.grid(alpha=.35)
    ax.legend(frameon=False, fontsize=10.5, loc="upper right")

    # ---- right: our own d2 is an estimate
    axd = fig.add_subplot(gs[0, 1])
    reps = d2_estimates()
    axd.hist(reps, bins=14, color=BLUE, alpha=.75, lw=0)
    axd.axvline(D2_PUBLISHED, color=YELLOW, lw=1.8)
    axd.axvline(D2_MEAN, color=TEAL, lw=1.6, ls="--")
    top = axd.get_ylim()[1]
    axd.set_ylim(0, top * 1.30)          # headroom, so no label sits on the title
    # both labels get a ground of their own: over a histogram, unbacked text is
    # unreadable, and "published" was landing on the panel title
    box = dict(facecolor=BG, edgecolor="none", alpha=.88, pad=2.2)
    axd.text(D2_PUBLISHED + 0.0015, top * 1.16, f"published {D2_PUBLISHED:.4f}",
             color=YELLOW, fontsize=11, ha="left", bbox=box)
    axd.text(0.035, 0.96, f"60 replicates\nmean {D2_MEAN:.4f}\ns.e. {D2_SE:.4f}",
             transform=axd.transAxes, color=TEAL, fontsize=10.5,
             ha="left", va="top", bbox=box)
    axd.set_xlabel(r"$d_2$ estimated from 2 000 subgroups, once per replicate")
    axd.set_ylabel("replicates")
    axd.set_title(r"the constant this curriculum uses is itself an estimate",
                  loc="left", fontsize=12.5, color=FG)
    axd.grid(alpha=.30)

    fig.suptitle(
        f"Halving an interval costs four times the parts — and the same arithmetic "
        f"applies to our own constants\n"
        f"$d_2$ is simulated, so its standard error is {D2_SE:.4f}; earning the third "
        f"decimal that way needs {D2_SUBGROUPS_FOR_3DP/1e6:.1f} million subgroups.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l05_2_price")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l05_coverage()
    sheet_l05_price()
