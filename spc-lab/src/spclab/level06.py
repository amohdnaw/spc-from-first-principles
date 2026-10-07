"""LEVEL 2 — Control limits are a hypothesis test.

Sheet 1: the sampling distribution of x̄ with the ±3σ envelope and its
         exact tail area — the origin of '99.73%' and ARL ≈ 370.
Sheet 2: the plumbing — how well does R̄/d₂ estimate σ? (simulated).
Sheet 3: a worked X̄–R chart — 25 subgroups of 5, limits from A₂, D₃, D₄.

    PYTHONPATH=src .venv/bin/python -m spclab.level06
"""
from __future__ import annotations

import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab import figstyle

from spclab.formulas import _d2_d3, xbar_r_limits

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
figstyle.apply()


def _save(fig, name):
    figstyle.finish(fig)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", f"docs/{name}.png")


def _norm_pdf(xs, mu=0, sg=1):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * math.sqrt(2 * math.pi))


# ---------------------------------------------------------------------------
# Sheet 1 — the null distribution and its 0.27% tail
# ---------------------------------------------------------------------------
def sheet_l06_null():
    sig = 1.0
    fig, ax = plt.subplots(figsize=(11, 5.4))
    xs = np.linspace(-4.2, 4.2, 600)
    pdf = _norm_pdf(xs)

    inside = np.abs(xs) <= 3
    ax.fill_between(xs, pdf, where=inside, color=TEAL, alpha=.35, lw=0)
    ax.fill_between(xs, pdf, where=~inside, color=RED, alpha=.6, lw=0)
    ax.plot(xs, pdf, color=TEAL, lw=2)

    # area annotation with the exact integral
    area_in = math.erf(3 / math.sqrt(2))
    ax.text(.985, .92,
            r"$P(-3\sigma_{\bar{x}}<\bar{x}<+3\sigma_{\bar{x}}\,|\,\mathrm{stable})$"
            f"\n$= \\Phi(3)-\\Phi(-3) = {area_in:.4f}$",
            transform=ax.transAxes, ha="right", va="top", fontsize=13)
    ax.annotate(f"tail: {(1-area_in)/2*100:.2f}% each\n"
                "→ false alarm rate 0.27%\n"
                "→ one false alarm every ≈ 370 subgroups",
                xy=(3.05, 0.008), xytext=(2.15, 0.16), fontsize=12, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))

    for z in (-3, 3):
        ax.axvline(z, color=YELLOW, ls="--", lw=1.5)
        ax.text(z, pdf.max() * 1.04, f"{z:+d}σx̄", color=YELLOW,
                ha="center", fontsize=12)
    ax.axvline(0, color=FG, lw=1)
    ax.set_yticks([]); ax.set_xlabel("subgroup mean x̄ (in units of σx̄)")
    ax.set_title("If the process is stable, THIS is the distribution of every "
                 "plotted point.\nA point outside is not proof of change — it's "
                 "a bet at 370:1 odds.", loc="left")
    _save(fig, "l06_1_null_distribution")


# ---------------------------------------------------------------------------
# Sheet 2 — the plumbing: quality of σ̂ = R̄/d₂
# ---------------------------------------------------------------------------
def sheet_l06_plumbing():
    """Simulate 5000 processes; compare R̄/d₂ against the true σ."""
    rng = np.random.default_rng(9)
    n, subs, sims = 5, 25, 4000
    d2, _ = _d2_d3(n)
    ratios = []
    for _ in range(sims):
        data = rng.normal(0, 1, size=(subs, n))
        ratios.append(np.ptp(data, axis=1).mean() / d2)
    ratios = np.array(ratios)  # should cluster around 1.0

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(ratios, bins=70, density=True, color=BLUE, alpha=.8, lw=0)
    ax.axvline(1.0, color=YELLOW, lw=2)
    ax.annotate(f"unbiased: mean = {ratios.mean():.3f}\n"
                f"(true σ = 1.000)\nspread: ±{ratios.std():.3f} with only "
                f"{subs} subgroups",
                xy=(1.0, ax.get_ylim()[1] * .9),
                xytext=(1.06, ax.get_ylim()[1] * .82),
                fontsize=13, color=YELLOW,
                arrowprops=dict(arrowstyle="->", color=YELLOW))
    ax.axvspan(1 - 3 * ratios.std(), 1 + 3 * ratios.std(),
               color=TEAL, alpha=.12)
    ax.set_title(r"How good is $\hat{\sigma}=\bar{R}/d_2$?   "
                 f"({sims:,} simulated stable processes, {subs} subgroups of {n})"
                 "\nUnbiased on average — but few subgroups means fuzzy limits.",
                 loc="left")
    ax.set_xlabel(r"$\hat{\sigma}/\sigma$"); ax.set_ylabel("density")
    ax.grid(alpha=.5, axis="y")
    _save(fig, "l06_2_rbar_plumbing")


# ---------------------------------------------------------------------------
# Sheet 3 — a worked X̄–R chart: the constants of 6.6 put to work
# ---------------------------------------------------------------------------
XR_SUBS, XR_N, XR_MU, XR_SIGMA, XR_SEED = 25, 5, 50.000, 0.012, 61


def xbar_r_example() -> dict:
    """One stable process, 25 subgroups of 5, in mm. The page quotes these."""
    data = np.random.default_rng(XR_SEED).normal(XR_MU, XR_SIGMA, (XR_SUBS, XR_N))
    lim = xbar_r_limits(data)
    lim["means"] = data.mean(axis=1)
    lim["ranges"] = np.ptp(data, axis=1)
    lim["sigma_hat"] = lim["rbar"] / lim["d2"]
    return lim


def sheet_l06_xbar_r():
    """X̄ chart over R chart, every limit labelled with its arithmetic."""
    e = xbar_r_example()
    x = np.arange(1, XR_SUBS + 1)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7, 7.6), sharex=True,
                                 gridspec_kw={"hspace": .35})

    def chart(ax, ys, centre, lo, hi, names, col):
        ax.plot(x, ys, "-o", color=col, ms=4, lw=1.4)
        for v, lab, c in ((hi, names[0], YELLOW), (centre, names[1], MUTED),
                          (lo, names[2], YELLOW)):
            ax.axhline(v, color=c, ls="--", lw=1.2)
            # labels live in a gutter right of the plot, where no data runs
            ax.text(1.02, v, lab, color=c, fontsize=10.5, va="center",
                    transform=ax.get_yaxis_transform())
        ax.grid(alpha=.4, axis="y")

    chart(a1, e["means"], e["xbarbar"], e["lcl_xbar"], e["ucl_xbar"],
          (f"UCL {e['ucl_xbar']:.4f}", r"$\bar{\bar{x}}$ " + f"{e['xbarbar']:.4f}",
           f"LCL {e['lcl_xbar']:.4f}"), BLUE)
    a1.set_title(r"$\bar{x}$ chart · subgroup means, mm", loc="left")
    chart(a2, e["ranges"], e["rbar"], e["lcl_r"], e["ucl_r"],
          (f"UCL {e['ucl_r']:.4f}", r"$\bar{R}$ " + f"{e['rbar']:.4f}",
           f"LCL {e['lcl_r']:.0f}"), TEAL)
    a2.set_title("R chart · subgroup ranges, mm", loc="left")
    a2.set_xlabel("subgroup")
    a2.set_xlim(0, XR_SUBS + 1)
    pad = (e["ucl_xbar"] - e["xbarbar"]) * .25
    a1.set_ylim(e["lcl_xbar"] - pad, e["ucl_xbar"] + pad)
    a2.set_ylim(-e["rbar"] * .12, e["ucl_r"] * 1.12)
    hits = figstyle.collisions(fig)
    assert not hits, hits
    _save(fig, "l06_3_xbar_r")


if __name__ == "__main__":
    sheet_l06_null()
    sheet_l06_plumbing()
    sheet_l06_xbar_r()
