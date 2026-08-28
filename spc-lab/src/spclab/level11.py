"""LEVEL 11 — Relationships.

Sheet 1: least squares as a minimisation, and what R² does not tell you. The
         residual sum of squares swept across slopes with the closed form at its
         minimum; then the same straight-line fit applied to a straight
         relationship and to a curved one, where a high R² sits beside residuals
         that arc for sixteen points in a row.
Sheet 2: the two intervals and the bridge. The fitted line with a confidence
         band for the mean response and the much wider prediction band for a
         single new reading; then the same total variation decomposed into part,
         operator, interaction and repeat — which is a Gage R&R.

Every number comes from spclab.relationships.

    PYTHONPATH=src .venv/bin/python -m spclab.level11
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.relationships import (
    CURVED_FIT,
    CURVED_RUN,
    CX,
    CY,
    FIT,
    GAUGE,
    HALF_CI,
    HALF_PI,
    R2_PLAIN,
    R2_WITH_NOISE,
    SLOPE_GRID,
    SSE_CURVE,
    STRAIGHT_RUN,
    X,
    X0,
    Y,
    interval_half_widths,
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
# Sheet 1 — the minimisation, and what the summary hides
# ---------------------------------------------------------------------------
def sheet_l11_least_squares():
    fig = plt.figure(figsize=(12.6, 6.8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1.35], hspace=.44, wspace=.24)

    # ---- left: the parabola
    ax = fig.add_subplot(gs[:, 0])
    ax.plot(SLOPE_GRID, SSE_CURVE, color=TEAL, lw=2.2)
    ax.plot([FIT["slope"]], [FIT["sse"]], "o", color=YELLOW, ms=8, zorder=5)
    ax.annotate(f"the closed form\nslope {FIT['slope']:.5f}",
                xy=(FIT["slope"], FIT["sse"]),
                # inside the mouth of the parabola, which is empty; offset to the
                # right it sat on the curve's own branch
                xytext=(FIT["slope"], FIT["sse"]
                        + float(SSE_CURVE.max() - SSE_CURVE.min()) * .72),
                ha="center", fontsize=11, color=YELLOW,
                arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.1))
    ax.set_xlabel("slope tried")
    ax.set_ylabel("residual sum of squares")
    ax.set_title("“least squares” is a claim, not a name", loc="left",
                 fontsize=12.5, color=FG)
    ax.grid(alpha=.32)

    # ---- right: two relationships, one line each
    for row, (xx, yy, f, name, colour) in enumerate([
            (X, Y, FIT, "a straight relationship", TEAL),
            (CX, CY, CURVED_FIT, "a curved one, fitted straight", RED)]):
        axf = fig.add_subplot(gs[row, 1])
        axf.plot(xx, yy, "o", color=BLUE, ms=4.2)
        line = f["intercept"] + f["slope"] * xx
        axf.plot(xx, line, color=colour, lw=2.0)
        run = STRAIGHT_RUN if row == 0 else CURVED_RUN
        axf.set_title(f"{name} — R² {f['r2']:.3f}, longest same-sign run {run}",
                      loc="left", fontsize=11.5, color=FG)
        axf.set_ylabel("roughness")
        axf.grid(alpha=.28)
        if row == 1:
            axf.set_xlabel("cutting speed (m/min)")
        # residuals, drawn beneath as sticks so the pattern is unmissable
        base = axf.get_ylim()[0]
        span = (axf.get_ylim()[1] - base)
        for xv, rv in zip(xx, f["resid"]):
            axf.plot([xv, xv], [base + span * .06,
                                base + span * .06 + rv * span * .55],
                     color=colour, lw=1.4, alpha=.8)
        axf.axhline(base + span * .06, color=MUTED, lw=.9, ls=":")

    fig.suptitle(
        "Least squares finds the line by minimising something, and R² only "
        "summarises how well it did\n"
        f"both fits below score above 0.92. The lower one is wrong, and the "
        f"residuals say so — {CURVED_RUN} in a row on the same side against "
        f"{STRAIGHT_RUN} for the honest fit. R² never mentions it.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l11_1_least_squares")


# ---------------------------------------------------------------------------
# Sheet 2 — two intervals, then the bridge
# ---------------------------------------------------------------------------
def sheet_l11_intervals_and_bridge():
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1], wspace=.26)

    # ---- left: the bands
    ax = fig.add_subplot(gs[0, 0])
    grid = np.linspace(X.min(), X.max(), 200)
    yhat = FIT["intercept"] + FIT["slope"] * grid
    hc = np.array([interval_half_widths(FIT, float(v))[0] for v in grid])
    hp = np.array([interval_half_widths(FIT, float(v))[1] for v in grid])

    ax.fill_between(grid, yhat - hp, yhat + hp, color=BLUE, alpha=.18, lw=0,
                    label="prediction band — one new reading")
    ax.fill_between(grid, yhat - hc, yhat + hc, color=TEAL, alpha=.40, lw=0,
                    label="confidence band — the mean response")
    ax.plot(grid, yhat, color=YELLOW, lw=2.0)
    ax.plot(X, Y, "o", color=BLUE, ms=4.4)
    ax.axvline(X0, color=MUTED, lw=1.0, ls=":")
    ax.annotate(f"at {X0:.0f} m/min\n±{HALF_CI:.3f} for the mean\n"
                f"±{HALF_PI:.3f} for a reading",
                xy=(X0, FIT["intercept"] + FIT["slope"] * X0),
                xytext=(X.min() + 6, Y.max() - 0.06), fontsize=11, color=FG,
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.1))
    ax.set_xlabel("cutting speed (m/min)")
    ax.set_ylabel("surface roughness (µm)")
    ax.set_title(f"one band is ×{HALF_PI / HALF_CI:.1f} the other", loc="left",
                 fontsize=12.5, color=FG)
    ax.grid(alpha=.30)
    # the data rises left to right, so the lower right is the empty corner and
    # the upper left already holds the annotation
    ax.legend(frameon=False, fontsize=10.5, loc="lower right")

    # ---- right: the same identity, two-way
    axb = fig.add_subplot(gs[0, 1])
    order = ["part", "repeat", "operator", "interaction"]
    colours = {"part": TEAL, "repeat": RED, "operator": YELLOW,
               "interaction": BLUE}
    left = 0.0
    for key in order:
        w = GAUGE["pct"][key]
        axb.barh([0], [w], left=left, color=colours[key], height=.42,
                 edgecolor=BG, linewidth=1.2)
        left += w

    ys = -0.62
    for i, key in enumerate(order):
        axb.plot([2 + i * 26], [ys], "s", color=colours[key], ms=9)
        axb.text(6 + i * 26, ys, f"{key}\n{GAUGE['pct'][key]:.2f} %",
                 va="center", fontsize=10.5, color=FG)

    axb.axvline(GAUGE["pct"]["part"], color=FG, lw=1.4, ls="--")
    axb.text(GAUGE["pct"]["part"] - 2, 0.42,
             f"parts {GAUGE['pct']['part']:.1f} %", ha="right", fontsize=11,
             color=FG)
    axb.text(GAUGE["pct"]["part"] + 2, 0.42,
             f"gauge {GAUGE['pct_gauge']:.1f} %", ha="left", fontsize=11,
             color=RED)
    axb.set_xlim(0, 100)
    axb.set_ylim(-1.0, 0.75)
    axb.set_yticks([])
    axb.set_xlabel("share of the total variance")
    axb.set_title("the same total, split four ways — a Gage R&R", loc="left",
                  fontsize=12.5, color=FG)
    axb.grid(alpha=.25, axis="x")

    fig.suptitle(
        "A confidence interval covers the mean response; a prediction interval "
        "covers the next reading, and keeps that reading's own variance\n"
        "then the same sum-of-squares identity, applied two-way, gives the "
        "variance components a gauge study reports — which is where this "
        "curriculum stops and the MSA site starts.",
        x=.008, ha="left", fontsize=13.5)
    _save(fig, "l11_2_intervals_and_bridge")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_l11_least_squares()
    sheet_l11_intervals_and_bridge()
