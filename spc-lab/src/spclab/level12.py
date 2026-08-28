"""LEVEL 12 — Experiments.

Sheet 1: why one factor at a time fails. The response surface with the
         one-at-a-time path walked across it, terminating at a corner the
         factorial identifies as worse; beside it the interaction plot, whose
         non-parallel lines *are* the interaction.
Sheet 2: screening and curvature. Seven factors in eight runs with the alias
         structure computed from the design rather than quoted; then the centre-
         point test, run on a curved surface and on a flat one.

Every number comes from spclab.experiments.

    PYTHONPATH=src .venv/bin/python -m spclab.level12
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.experiments import (
    ALIASES,
    BASELINE,
    CORNERS,
    CURVED,
    EFFECTS,
    FLAT,
    FULL_RUNS,
    OFAT,
    OPTIMUM,
    OPTIMUM_Y,
    PRECISION,
    SCREEN_FACTORS,
    SCREEN_RUNS,
    TRUTH,
    response,
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
# Sheet 1 — the walk, and the interaction that defeats it
# ---------------------------------------------------------------------------
def sheet_l12_why_ofat_fails():
    fig = plt.figure(figsize=(12.6, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.18, 1], wspace=.26)

    # ---- left: the surface, with the one-at-a-time path on it
    ax = fig.add_subplot(gs[0, 0])
    gx = np.linspace(-1.25, 1.25, 240)
    A, B = np.meshgrid(gx, gx)
    Z = response(A, B)
    im = ax.contourf(A, B, Z, levels=18, cmap="viridis", alpha=.85)
    cs = ax.contour(A, B, Z, levels=9, colors=[MUTED], linewidths=.6)
    ax.clabel(cs, inline=True, fontsize=8, fmt="%.0f")

    path = OFAT["visited"]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=RED, lw=2.0,
                                    shrinkA=7, shrinkB=7))
    for c in CORNERS:
        ax.plot([c[0]], [c[1]], "o", color=BG, ms=13, zorder=4)
        ax.plot([c[0]], [c[1]], "o", color=FG, ms=7, zorder=5)
        ax.annotate(f"{TRUTH[c]:.0f}", xy=c, xytext=(c[0] * 1.16, c[1] * 1.16),
                    ha="center", va="center", fontsize=12, color=FG, zorder=6)

    ax.plot([OFAT["chosen"][0]], [OFAT["chosen"][1]], "o", color=RED, ms=13,
            mfc="none", mew=2.4, zorder=7)
    ax.plot([OPTIMUM[0]], [OPTIMUM[1]], "o", color=TEAL, ms=13, mfc="none",
            mew=2.4, zorder=7)
    # clear of the vertical leg of the path, which runs through x = chosen[0]
    ax.text(OFAT["chosen"][0] + 0.22, OFAT["chosen"][1] - 0.34,
            f"one-at-a-time\nstops here — {OFAT['chosen_y']:.0f}", ha="left",
            fontsize=11, color=RED,
            bbox=dict(facecolor=BG, edgecolor="none", alpha=.85, pad=2.4))
    ax.text(OPTIMUM[0], OPTIMUM[1] + 0.40,
            f"the optimum\n{OPTIMUM_Y:.0f}", ha="center", fontsize=11, color=TEAL,
            bbox=dict(facecolor=BG, edgecolor="none", alpha=.85, pad=2.4))

    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.45)
    ax.set_xlabel("hold pressure (coded)")
    ax.set_ylabel("melt temperature (coded)")
    ax.set_title(f"starts at {BASELINE}, visits three corners of four",
                 loc="left", fontsize=12.5, color=FG)

    # ---- right: the interaction plot
    axi = fig.add_subplot(gs[0, 1])
    for a, colour, name in ((-1, BLUE, "pressure low"), (1, YELLOW, "pressure high")):
        ys = [TRUTH[(a, b)] for b in (-1, 1)]
        axi.plot([-1, 1], ys, "-o", color=colour, lw=2.4, ms=8, label=name)
        for b, yv in zip((-1, 1), ys):
            axi.annotate(f"{yv:.0f}", (b, yv), textcoords="offset points",
                         xytext=(0, 12 if a > 0 else -18), ha="center",
                         fontsize=11, color=colour)
    axi.set_xticks([-1, 1])
    axi.set_xticklabels(["temperature low", "temperature high"])
    axi.set_ylim(4, 18)
    axi.set_ylabel("shrinkage (thousandths)")
    axi.set_title("non-parallel lines are the interaction", loc="left",
                  fontsize=12.5, color=FG)
    axi.grid(alpha=.30)
    axi.legend(frameon=False, fontsize=11, loc="upper center")
    axi.text(.5, .04, f"effect A {EFFECTS['A']:+.0f}    effect B {EFFECTS['B']:+.0f}"
                      f"    interaction {EFFECTS['AB']:+.0f}",
             transform=axi.transAxes, ha="center", fontsize=11.5, color=FG)

    fig.suptitle(
        "One factor at a time does not merely take longer — with an interaction "
        "present it stops at the wrong setting\n"
        f"and this walk was run with no measurement noise at all: it lands on "
        f"{OFAT['chosen_y']:.0f} when {OPTIMUM_Y:.0f} was available, "
        f"{100 * OFAT['shortfall'] / OPTIMUM_Y:.0f} % worse, because it never "
        f"visits the corner where both factors are high together.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l12_1_why_ofat_fails")


# ---------------------------------------------------------------------------
# Sheet 2 — screening, and what a two-level design cannot see
# ---------------------------------------------------------------------------
def sheet_l12_screening_and_curvature():
    fig = plt.figure(figsize=(12.6, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1], wspace=.24)

    # ---- left: the alias table
    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    ax.set_title(f"seven factors in {SCREEN_RUNS} runs, not {FULL_RUNS}",
                 loc="left", fontsize=12.5, color=FG)
    rows = [(L, ", ".join(ALIASES[L])) for L in SCREEN_FACTORS]
    y = 0.90
    ax.text(0.02, y + .07, "main effect", fontsize=11, color=MUTED)
    ax.text(0.30, y + .07, "confounded with", fontsize=11, color=MUTED)
    for letter, partners in rows:
        ax.text(0.06, y, letter, fontsize=15, color=YELLOW, va="center")
        ax.text(0.30, y, partners, fontsize=13, color=FG, va="center",
                family="monospace")
        y -= 0.115
    ax.text(0.02, y - .02,
            "computed from the design, not read from a table:\n"
            "two columns are aliased when they are identical\n"
            "across all eight runs — knowable before any run",
            fontsize=10.5, color=MUTED, va="top")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)

    # ---- right: the centre-point test, one axes per surface
    # Stacked axes rather than manual y offsets: the first version put both
    # pairs on one axis and the captions drifted away from the bars they
    # described, with the upper one colliding with the suptitle.
    inner = gs[0, 1].subgridspec(2, 1, hspace=.52)
    for i, (d, colour, name) in enumerate((
            (CURVED, RED, "a curved surface"),
            (FLAT, TEAL, "a flat one"))):
        axc = fig.add_subplot(inner[i, 0])
        axc.barh([1], [d["factorial_mean"]], height=.52, color=BLUE, alpha=.85)
        axc.barh([0], [d["centre_mean"]], height=.52, color=colour, alpha=.85)
        top = max(CURVED["factorial_mean"], FLAT["factorial_mean"],
                  CURVED["centre_mean"], FLAT["centre_mean"]) * 1.42
        axc.text(d["factorial_mean"] + top * .015, 1, f"corners {d['factorial_mean']:.2f}",
                 va="center", fontsize=11, color=BLUE)
        axc.text(d["centre_mean"] + top * .015, 0, f"centre {d['centre_mean']:.2f}",
                 va="center", fontsize=11, color=colour)
        axc.set_xlim(0, top)
        axc.set_ylim(-0.62, 1.62)
        axc.set_yticks([])
        axc.set_title(f"{name} — gap {d['gap']:+.2f},  F {d['f']:.1f},  "
                      f"p {d['p']:.4f}", loc="left", fontsize=11.5, color=FG)
        axc.grid(alpha=.25, axis="x")
        if i == 1:
            axc.set_xlabel("mean shrinkage")

    fig.suptitle(
        "A fraction studies many factors at once, and the price is written down "
        "before the first run\n"
        f"then curvature: a two-level design shifts every corner by the same "
        f"amount, so no contrast among corners can see a bend — add centre "
        f"points and it becomes a test (p {CURVED['p']:.4f} against "
        f"p {FLAT['p']:.2f} when the surface really is flat).",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l12_2_screening_and_curvature")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l12_why_ofat_fails()
    sheet_l12_screening_and_curvature()
