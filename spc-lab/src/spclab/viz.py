"""3b1b-flavored static visualizations of spc-lab formulas.

Palette follows the Manim/3Blue1Brown convention:
    BLUE #58C4DD  TEAL #5CD0B3  YELLOW #FFD54F  RED #FC6255
on a near-black blue-gray canvas. Math is set in a serif italic.
"""
from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab import (
    control_limit_constants, xbar_r_limits, capability_indices,
    defects_per_million, ewma_limits,
)

BG      = "#0e1116"
FG      = "#e8e8e8"
MUTED   = "#8a939f"
BLUE    = "#58C4DD"
TEAL    = "#5CD0B3"
YELLOW  = "#FFD54F"
RED     = "#FC6255"

def style():
    mpl.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG, "text.color": FG,
        "axes.edgecolor": MUTED, "axes.labelcolor": FG,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "grid.color": "#232a33", "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.spines.top": False, "axes.spines.right": False,
    })

def demo_data(seed=7, subgroups=30, n=5):
    rng = np.random.default_rng(seed)
    return rng.normal(50, 0.08, size=(subgroups, n))


def panel_xbar(ax, data):
    """Panel 1 — X̄ chart whose limits are *derived* from d2/A2."""
    lim = xbar_r_limits(data)
    means = data.mean(axis=1)
    x = np.arange(1, len(means) + 1)
    ax.axhspan(lim["lcl_xbar"], lim["ucl_xbar"], color=BLUE, alpha=0.06)
    ax.plot(x, means, "-o", color=BLUE, ms=4, lw=1.6)
    ax.axhline(lim["xbarbar"], color=MUTED, lw=1, ls="--")
    for v, lab in [(lim["ucl_xbar"], "UCL"), (lim["lcl_xbar"], "LCL")]:
        ax.axhline(v, color=YELLOW, lw=1.4, ls="--")
        ax.text(len(x) * 1.01, v, lab, color=YELLOW, fontsize=9, va="center")
    ax.set_title("X̄-R chart   ·   "
                 r"$\mathrm{UCL}=\bar{\bar{x}}+A_2\bar{R},\ \ A_2="
                 rf"{lim['A2']:.3f}$",
                 fontsize=11, loc="left")
    ax.set_ylabel("subgroup mean (mm)")


def panel_constants(ax):
    """Panel 2 — where A2 comes from: 3/(d2·√n), plotted vs table values."""
    ns = np.arange(2, 11)
    a2 = [control_limit_constants(int(n))["A2"] for n in ns]
    aiag = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483,
            7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
    ax.plot(ns, a2, "-", color=BLUE, lw=2, label="computed (Monte Carlo)")
    ax.plot(ns, [aiag[n] for n in ns], "o", ms=5, color=YELLOW, label="AIAG Table B")
    ax.set_title(r"$A_2=\dfrac{3}{d_2\sqrt{n}}$ — derived vs. published",
                 fontsize=11, loc="left")
    ax.set_xlabel("subgroup size n")
    ax.legend(frameon=False, fontsize=9)


def panel_cpk(ax, values, lsl=49.7, usl=50.3):
    """Panel 3 — capability geometry: the gap between voice of process & customer."""
    cap = capability_indices(values, lsl, usl)
    xs = np.linspace(lsl - 0.25, usl + 0.25, 400)
    pdf = np.exp(-((xs - cap["mean"]) ** 2) / (2 * cap["sigma"] ** 2))
    pdf /= pdf.max() * 1.05
    inside = (xs >= lsl) & (xs <= usl)
    ax.fill_between(xs, 0, pdf, where=inside, color=TEAL, alpha=0.35, lw=0)
    ax.fill_between(xs, 0, pdf, where=~inside, color=RED, alpha=0.55, lw=0)
    ax.plot(xs, pdf, color=TEAL, lw=2)
    for v, lab in [(lsl, "LSL"), (usl, "USL")]:
        ax.axvline(v, color=YELLOW, ls="--", lw=1.4)
        ax.text(v, pdf.max() * 1.04, lab, color=YELLOW, ha="center", fontsize=10)
    ppm = defects_per_million(cap["mean"], cap["sigma"], lsl, usl, shift=0)
    ax.text(0.02, 0.92,
            f"$C_p={cap['Cp']:.2f}$   $C_{{pk}}={cap['Cpk']:.2f}$\n"
            f"$\\approx {ppm}$ defects / million",
            transform=ax.transAxes, fontsize=10, va="top")
    ax.set_title("Capability — red area is predicted scrap", fontsize=11, loc="left")
    ax.set_yticks([])


def panel_ewma(ax, lam=0.2, k=40):
    """Panel 4 — EWMA limits tighten over time: memory buys sensitivity."""
    up, lo = ewma_limits(lam, k)
    x = np.arange(1, k + 1)
    ax.fill_between(x, lo, up, color=BLUE, alpha=0.15)
    ax.plot(x, up, color=BLUE, lw=1.8)
    ax.plot(x, lo, color=BLUE, lw=1.8)
    ax.axhline(3, color=MUTED, ls="--", lw=1)
    ax.text(k, 3.08, r"Shewhart $\pm3\sigma$", color=MUTED, ha="right", fontsize=9)
    ax.set_title(r"EWMA limits: $\pm L\sigma\sqrt{\frac{\lambda}{2-\lambda}"
                 r"(1-(1-\lambda)^{2i})}$,  $\lambda=0.2$",
                 fontsize=11, loc="left")
    ax.set_xlabel("observation i")


def gallery(out="gallery.png"):
    style()
    data = demo_data()
    individuals = data.ravel()
    fig, axs = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    panel_xbar(axs[0, 0], data)
    panel_constants(axs[0, 1])
    panel_cpk(axs[1, 0], individuals)
    panel_ewma(axs[1, 1])
    fig.suptitle("spc-lab — every formula, drawn",
                 fontsize=16, family="serif", y=1.02)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    gallery()
