"""LEVEL 3 — Capability is comparing two distributions.

Sheet 1: the two voices on one axis — customer tolerance vs process spread;
         Cp as pure geometry, Cpk as geometry + offset.
Sheet 2: from Cpk to promised defects — the exact mapping curve with
         industry thresholds marked at their real ppm values.

    PYTHONPATH=src .venv/bin/python -m spclab.level3
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


def _pdf(xs, mu, sg):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


# ---------------------------------------------------------------------------
# Sheet 1 — two voices, one axis
# ---------------------------------------------------------------------------
def sheet_l3_two_voices():
    lsl, usl = 49.7, 50.3          # customer's voice: width 0.6
    sg = 0.075                      # process voice: 6σ = 0.45

    fig, axs = plt.subplots(2, 1, figsize=(11, 8), sharex=True,
                            constrained_layout=True)
    xs = np.linspace(49.55, 50.45, 600)

    # --- top: perfectly centered -> Cp is the whole story
    ax = axs[0]
    mu = 50.0
    pdf = _pdf(xs, mu, sg)
    inside = (xs >= lsl) & (xs <= usl)
    ax.fill_between(xs, pdf, where=~inside, color=RED, alpha=.55, lw=0)
    ax.fill_between(xs, pdf, where=inside, color=TEAL, alpha=.35, lw=0)
    ax.plot(xs, pdf, color=TEAL, lw=2)
    cp = (usl - lsl) / (6 * sg)
    # dimension lines: tolerance width vs process width
    y1 = pdf.max() * 1.12
    ax.annotate("", xy=(lsl, y1), xytext=(usl, y1),
                arrowprops=dict(arrowstyle="<->", color=YELLOW, lw=1.6))
    ax.text(50, y1 + .004, f"tolerance width = {usl-lsl:.2f}", color=YELLOW,
            ha="center", fontsize=12)
    y2 = pdf.max() * .78
    ax.annotate("", xy=(mu - 3*sg, y2), xytext=(mu + 3*sg, y2),
                arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.6))
    ax.text(mu, y2 - .006, f"process width 6σ = {6*sg:.2f}", color=BLUE,
            ha="center", fontsize=12)
    for xv, lab in [(lsl, "LSL"), (usl, "USL")]:
        ax.axvline(xv, color=YELLOW, ls="--", lw=1.4)
        ax.text(xv, pdf.max()*1.22, lab, color=YELLOW, ha="center", fontsize=12)
    ax.set_title(f"Voice of the customer vs voice of the process — "
                 f"perfectly centered:\n$C_p = \\frac{{USL-LSL}}{{6\\sigma}} "
                 f"= {cp:.2f}$   (potential only — assumes perfect centering)",
                 loc="left", fontsize=13)
    ax.set_yticks([])

    # --- bottom: mean drifts; Cpk measures the nearer gap
    ax = axs[1]
    mu = 50.12
    pdf = _pdf(xs, mu, sg)
    inside = (xs >= lsl) & (xs <= usl)
    ax.fill_between(xs, pdf, where=~inside, color=RED, alpha=.55, lw=0)
    ax.fill_between(xs, pdf, where=inside, color=TEAL, alpha=.35, lw=0)
    ax.plot(xs, pdf, color=TEAL, lw=2)
    for xv in (lsl, usl):
        ax.axvline(xv, color=YELLOW, ls="--", lw=1.4)
    cpu = (usl - mu) / (3 * sg)
    cpl = (mu - lsl) / (3 * sg)
    yA = pdf.max() * .55
    ax.annotate("", xy=(mu, yA), xytext=(usl, yA),
                arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.5))
    ax.text((mu+usl)/2, yA+.004, f"{cpu:.2f}×3σ", color=BLUE, ha="center", fontsize=12)
    ax.annotate("", xy=(lsl, yA*.72), xytext=(mu, yA*.72),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=1.5))
    ax.text((lsl+mu)/2, yA*.72+.004, f"{cpl:.2f}×3σ", color=RED, ha="center",
            fontsize=12)
    ax.axvline(mu, color=FG, lw=1)
    ax.text(mu, pdf.max()*1.18, f"μ drifted to {mu:.2f}", color=FG, ha="center",
            fontsize=12, style="italic")
    ax.set_title(f"Same spread, drifted mean — now the gaps differ:\n"
                 f"$C_{{pk}}=\\min({cpu:.2f},\\,{cpl:.2f})={min(cpu,cpl):.2f}$"
                 "   and the red tail is real scrap",
                 loc="left", fontsize=13)
    ax.set_yticks([]); ax.set_xlabel("measured value (mm)")

    fig.suptitle("Cp asks “could it fit?” · Cpk asks “does it fit where it actually sits?”",
                 fontsize=15, y=1.02)
    _save(fig, "31_l3_two_voices")


# ---------------------------------------------------------------------------
# Sheet 2 — Cpk -> promised defects (the exact mapping)
# ---------------------------------------------------------------------------
def sheet_l3_cpk_to_ppm():
    import scipy.stats as st
    phi = st.norm.cdf if True else None

    cpks = np.linspace(0.4, 2.0, 400)

    def ppm_of(cpk, shift):
        z = 3 * cpk
        return (1 - phi(z - shift)) * 1e6      # worst-side tail after shift

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.semilogy(cpks, ppm_of(cpks, 0.0), color=TEAL, lw=2.2,
                label="no drift (short-term)")
    ax.semilogy(cpks, ppm_of(cpks, 1.5), color=BLUE, lw=2.2,
                label="with 1.5σ long-term drift")

    for c in (1.0, 1.33, 1.67):
        p_short = ppm_of(c, 0)[0] if False else float(ppm_of(np.array([c]), 0.0)[0])
        p_long = float(ppm_of(np.array([c]), 1.5)[0])
        ax.axvline(c, color=MUTED, ls="--", lw=.9)
        ax.annotate(f"Cpk {c:.2f}\n{p_short:,.0f} ppm short-term\n"
                    f"{'≈' if abs(p_long-p_short)>1 else ''}{p_long:,.0f} ppm long-term",
                    xy=(c, p_short), xytext=(c + .05, p_short * 3),
                    fontsize=10.5, color=YELLOW)

    ax.set_title("What a Cpk number promises — exact tail arithmetic, both conventions\n"
                 "(thresholds 1.00 / 1.33 / 1.67 are just chosen points on this curve)",
                 loc="left")
    ax.set_xlabel("Cpk"); ax.set_ylabel("predicted defective parts per million")
    ax.legend(frameon=False); ax.grid(alpha=.5, which="both")
    _save(fig, "32_l3_cpk_to_ppm")


if __name__ == "__main__":
    sheet_l3_two_voices()
    sheet_l3_cpk_to_ppm()
