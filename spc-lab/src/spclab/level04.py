"""LEVEL 1 — Variation is predictable.

Sheet 1: individual chaos -> collective law (dice averaging into a bell).
Sheet 2: sigma/sqrt(n) plotted as itself — the reason subgroup means are charted.

    PYTHONPATH=src .venv/bin/python -m spclab.level04
"""
from __future__ import annotations

import math
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


def _save(fig, name):
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", f"docs/{name}.png")


def phi(z):
    import scipy.stats as st  # not guaranteed; fall back to erf
    try:
        return st.norm.cdf(z)
    except Exception:
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ---------------------------------------------------------------------------
# Sheet 1 — one die vs. the average of many: from uniform to bell
# ---------------------------------------------------------------------------
def sheet_l04_dice():
    rng = np.random.default_rng(0)
    max_k = 30
    rolls = rng.integers(1, 7, size=(100_000, max_k))  # columns = dice

    fig, axs = plt.subplots(1, 4, figsize=(14, 4), sharey=True,
                            constrained_layout=True)
    titles = [
        ("one roll\nuniform chaos — nothing to predict", 1),
        ("average of 2\nedges melting away", 2),
        ("average of 5\na shape appears", 5),
        ("average of 30\nthe bell — a law, not a guess", 30),
    ]
    bins = np.linspace(1, 6, 51)
    for ax, (title, k) in zip(axs, titles):
        avg = rolls[:, :k].mean(axis=1) if k > 1 else rolls[:, 0]
        ax.hist(avg, bins=bins if k > 1 else np.arange(0.5, 7, 1),
                density=True, color=BLUE if k == 1 else TEAL, lw=0, alpha=.85)
        ax.axvline(3.5, color=MUTED, ls="--", lw=1)
        ax.set_title(title, fontsize=12, loc="left")
        ax.grid(alpha=.5, axis="y")

    # annotate the shrinking spread with real numbers
    sd1 = rolls.std()
    axs[0].text(.5, -.28, f"σ = {sd1:.2f}", transform=axs[0].transAxes,
                ha="center", fontsize=13, color=YELLOW)
    for ax, k in zip(axs[1:], [2, 5, 30]):
        pred = sd1 / math.sqrt(k)
        ax.text(.5, -.28, rf"$\sigma/\sqrt{{{k}}}$ = {pred:.3f}",
                transform=ax.transAxes, ha="center", fontsize=13, color=YELLOW)

    fig.suptitle("One die is noise. The average of many dice is a measurement.",
                 fontsize=15, y=1.06)
    _save(fig, "l04_1_dice_to_bell")


# ---------------------------------------------------------------------------
# Sheet 2 — sigma_xbar = sigma / sqrt(n): THE reason X̄ charts exist
# ---------------------------------------------------------------------------
def sheet_l04_sqrtn():
    sig = 0.08  # a plausible machining σ in mm

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)

    # left: sigma_xbar vs n — the curve itself, with the √n payoff marked
    ax = axs[0]
    ns = np.arange(1, 26)
    ax.plot(ns, sig / np.sqrt(ns), color=BLUE, lw=2.4)
    for n in (1, 4, 9, 25):
        ax.plot(n, sig / math.sqrt(n), "o", color=YELLOW, ms=6)
        ax.annotate(rf"{sig/math.sqrt(n):.3f}", xy=(n, sig/math.sqrt(n)),
                    xytext=(n + .6, sig/math.sqrt(n) + .004), fontsize=11,
                    color=YELLOW)
    ax.set_title(r"The whole trick:  $\sigma_{\bar{x}}=\sigma/\sqrt{n}$"
                 "\nuncertainty of an average shrinks with √n", loc="left")
    ax.set_xlabel("subgroup size n"); ax.set_ylabel("σ of the subgroup mean (mm)")
    ax.grid(alpha=.5)

    # right: three distributions on one axis — individuals, n=5, n=25 means
    ax = axs[1]
    xs = np.linspace(50 - 4.5 * sig, 50 + 4.5 * sig, 500)
    for n, col, lab in [(1, RED, "individual parts  σ"),
                        (5, BLUE, "means of 5  σ/√5"),
                        (25, TEAL, "means of 25  σ/√25")]:
        s = sig / math.sqrt(n)
        pdf = np.exp(-((xs - 50) ** 2) / (2 * s ** 2)) / (s * math.sqrt(2 * math.pi))
        pdf /= pdf.max()
        ax.plot(xs, pdf, color=col, lw=2, label=lab)
        ax.fill_between(xs, pdf, color=col, alpha=.12)
    ax.set_title("Same process, three lenses:\nmeans cluster far tighter than parts",
                 loc="left")
    ax.legend(frameon=False, fontsize=11)
    ax.set_yticks([]); ax.set_xlabel("measured value (mm)")

    fig.suptitle("Why we chart subgroup means, not parts:  "
                 r"averaging divides noise by $\sqrt{n}$",
                 fontsize=15, y=1.04)
    _save(fig, "l04_2_sqrt_n")


if __name__ == "__main__":
    sheet_l04_dice()
    sheet_l04_sqrtn()
