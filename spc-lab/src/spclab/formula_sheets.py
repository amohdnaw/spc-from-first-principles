"""Formula sheets — one exact figure per formula.

Unlike the manim scenes (which tell the story), these plots ARE the
formulas: inputs on the x-axis, outputs on the y-axis, every number
computed live by spclab and annotated on the drawing.

    PYTHONPATH=src .venv/bin/python -m spclab.formula_sheets
"""
from __future__ import annotations

import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from spclab.formulas import (
    _d2_d3, control_limit_constants, capability_indices,
    defects_per_million, ewma_limits, _phi,
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
# 1. d2 — the sampling distribution of the range itself
# ---------------------------------------------------------------------------
def sheet_d2():
    """d2 = E(R). Show the ACTUAL distribution of R for n=5, mark its mean."""
    rng = np.random.default_rng(42)
    n, samples = 5, 200_000
    R = np.ptp(rng.standard_normal((samples, n)), axis=1)
    d2 = R.mean()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(R, bins=160, density=True, color=BLUE, alpha=0.75, lw=0)
    ax.axvline(d2, color=YELLOW, lw=2)
    ax.annotate(f"$d_2=E(R)={d2:.4f}$\n(AIAG table: 2.326)",
                xy=(d2, ax.get_ylim()[1] * 0.85),
                xytext=(d2 + 0.7, ax.get_ylim()[1] * 0.82),
                fontsize=13, color=YELLOW,
                arrowprops=dict(arrowstyle="->", color=YELLOW))
    # overlay the theoretical Rayleigh-ish shape? No — keep it honest: empirical only.
    ax.set_title(r"The range $R=x_{max}-x_{min}$ of $n=5$ standard normals"
                 "\n" r"$\sigma$ estimate:  $\hat{\sigma}=R/d_2$", loc="left")
    ax.set_xlabel("R"); ax.set_ylabel("density")
    ax.grid(True, axis="y", alpha=.6)
    _save(fig, "01_d2")


# ---------------------------------------------------------------------------
# 2. A2 — the function itself, plus D3/D4
# ---------------------------------------------------------------------------
def sheet_A2():
    """A2(n)=3/(d2(n)·sqrt(n)) plotted as the continuous function it is."""
    ns = np.arange(2, 16)
    d2s = np.array([_d2_d3(int(n))[0] for n in ns])
    A2 = 3 / (d2s * np.sqrt(ns))
    D3 = np.maximum(0, 1 - 3 * np.array([_d2_d3(int(n))[1] for n in ns]) / d2s)
    D4 = 1 + 3 * np.array([_d2_d3(int(n))[1] for n in ns]) / d2s

    aiag = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483,
            7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    ax = axs[0]
    nn = np.linspace(2, 15, 300)
    d2f = np.interp(nn, ns, d2s)
    ax.plot(nn, 3 / (d2f * np.sqrt(nn)), color=BLUE, lw=2.2)
    ax.plot(list(aiag), list(aiag.values()), "o", ms=6, color=YELLOW,
            label="AIAG Table B")
    for n in (2, 3, 5, 10):
        ax.annotate(f"{3/(d2s[ns.searchsorted(n)]*np.sqrt(n)):.3f}",
                    xy=(n, 3/(d2s[ns.searchsorted(n)]*np.sqrt(n))),
                    xytext=(n + .3, 3/(d2s[ns.searchsorted(n)]*np.sqrt(n)) + .06),
                    fontsize=11, color=BLUE)
    ax.set_title(r"$A_2(n)=\dfrac{3}{d_2(n)\sqrt{n}}$", loc="left")
    ax.set_xlabel("subgroup size  n"); ax.legend(frameon=False); ax.grid(alpha=.6)

    ax = axs[1]
    ax.plot(ns, D4, "-o", color=TEAL, ms=4, label=r"$D_4=1+3d_3/d_2$")
    ax.plot(ns, D3, "-o", color=RED, ms=4, label=r"$D_3=\max(0,\,1-3d_3/d_2)$")
    ax.axhline(1, color=MUTED, lw=.8, ls="--")
    ax.set_title("R-chart factors: limits collapse to $\\bar{R}$ as $n$ grows",
                 loc="left")
    ax.set_xlabel("subgroup size  n"); ax.legend(frameon=False); ax.grid(alpha=.6)
    _save(fig, "02_A2_D3_D4")


# ---------------------------------------------------------------------------
# 3. Control limits — the arithmetic drawn on the chart itself
# ---------------------------------------------------------------------------
def sheet_limits():
    """X̄ chart where UCL/LCL lines carry their computed numbers."""
    rng = np.random.default_rng(7)
    data = rng.normal(50, 0.08, size=(30, 5))
    c = control_limit_constants(5)
    means = data.mean(axis=1)
    xbb, Rbar = data.mean(), np.ptp(data, axis=1).mean()
    ucl, lcl = xbb + c["A2"] * Rbar, xbb - c["A2"] * Rbar

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(1, 31)
    ax.fill_between([0, 31], [lcl]*2, [ucl]*2, color=BLUE, alpha=.07)
    ax.plot(x, means, "-o", color=BLUE, ms=4.5, lw=1.6)

    def hline(v, lab, col):
        ax.axhline(v, color=col, ls="--", lw=1.4)
        ax.text(31.2, v, lab, color=col, fontsize=12, va="center")
    hline(ucl, f"UCL = {ucl:.3f}", YELLOW)
    hline(xbb, f"x̄̄ = {xbb:.3f}", MUTED)
    hline(lcl, f"LCL = {lcl:.3f}", YELLOW)
    ax.text(31.2, lcl - .028,
            f"$A_2\\bar{{R}} = {c['A2']:.3f}×{Rbar:.3f} = {c['A2']*Rbar:.3f}$",
            color=MUTED, fontsize=11)
    ax.set_xlim(0, 38)
    ax.set_title("Limits are one multiplication away:\n"
                 r"$\mathrm{UCL/LCL}=\bar{\bar{x}}\pm A_2\bar{R}$   "
                 rf"($\bar{{\bar{{x}}}}={xbb:.3f}$, $\bar{{R}}={Rbar:.3f}$, "
                 rf"$A_2={c['A2']:.3f}$)", loc="left")
    ax.set_xlabel("subgroup")
    _save(fig, "03_control_limits")


# ---------------------------------------------------------------------------
# 4. Cp / Cpk — measured distances, not vibes
# ---------------------------------------------------------------------------
def sheet_cpk():
    """Dimension-drawing style: μ, σ bracket, both spec distances."""
    rng = np.random.default_rng(3)
    v = rng.normal(50.03, 0.09, 500)
    cap = capability_indices(v, lsl=49.7, usl=50.3)
    mu, sg = cap["mean"], cap["sigma"]
    cpu, cpl = cap["Cpu"], cap["Cpl"]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    xs = np.linspace(mu - 4.6 * sg, mu + 4.6 * sg, 400)
    pdf = np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * math.sqrt(2 * math.pi))
    inside = (xs >= 49.7) & (xs <= 50.3)
    ax.fill_between(xs, pdf, where=inside, color=TEAL, alpha=.35, lw=0)
    ax.fill_between(xs, pdf, where=~inside, color=RED, alpha=.55, lw=0)
    ax.plot(xs, pdf, color=TEAL, lw=2)

    ymax = pdf.max() * 1.22
    ax.set_ylim(0, ymax); ax.set_yticks([])

    # spec lines + target
    for xv, lab in [(49.7, "LSL"), (50.3, "USL")]:
        ax.axvline(xv, color=YELLOW, ls="--", lw=1.5)
        ax.text(xv, ymax * .98, lab, color=YELLOW, ha="center", fontsize=12)
    ax.axvline(mu, color=FG, lw=1.2)
    ax.text(mu, ymax * .98, f"μ = {mu:.3f}", color=FG, ha="right",
            fontsize=12, style="italic")

    def dim(y, a, b, txt, col):
        ax.annotate("", xy=(a, y), xytext=(b, y),
                    arrowprops=dict(arrowstyle="<->", color=col, lw=1.4))
        ax.text((a + b) / 2, y + .004, txt, color=col, ha="center", fontsize=12)

    dim(pdf.max() * .55, mu, 50.3, f"CPU distance = {(50.3-mu):.3f} = {cpu:.2f}×3σ", TEAL)
    dim(pdf.max() * .40, 49.7, mu, f"CPL distance = {(mu-49.7):.3f} = {cpl:.2f}×3σ", TEAL)
    dim(pdf.max() * .18, mu - sg, mu + sg, f"σ = {sg:.4f}", BLUE)

    ax.text(.985, .95,
            f"$C_p={cap['Cp']:.2f}$   $C_{{pk}}=\\min({cpu:.2f},\\,{cpl:.2f})"
            f"=\\mathbf{{{cap['Cpk']:.2f}}}$\n"
            f"DPMO = {defects_per_million(mu, sg, 49.7, 50.3, shift=0):,}",
            transform=ax.transAxes, ha="right", va="top", fontsize=13)
    ax.set_title("Cpk is literally the smaller of two measured gaps, divided by 3σ",
                 loc="left")
    _save(fig, "04_cpk")


# ---------------------------------------------------------------------------
# 5. DPMO — the sigma-level curve the whole industry quotes
# ---------------------------------------------------------------------------
def sheet_dpmo():
    """PPM defect rate as a function of sigma level, shift=1.5 convention."""
    zs = np.linspace(2, 8, 400)
    ppm = (1 - np.vectorize(_phi)(zs - 1.5)) * 1e6          # worst-side tail after 1.5σ drift
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.semilogy(zs, ppm, color=BLUE, lw=2.4)
    marks = [(3, 66_807, "3σ"), (4, 6_210, "4σ"), (5, 233, "5σ"), (6, 3.4, "6σ")]
    for z_, p_, lab in marks:
        p_exact = (1 - _phi(z_ - 1.5)) * 1e6
        ax.plot(z_, p_exact, "o", color=RED, ms=6)
        ax.annotate(f"{lab}\n{p_exact:,.1f} DPMO" if p_exact < 100
                    else f"{lab}\n{p_exact:,.0f} DPMO",
                    xy=(z_, p_exact), xytext=(z_ + .15, p_exact * 2.4),
                    fontsize=11, color=YELLOW)
    ax.set_title(r"DPMO$(z)=\left[1-\Phi(z-1.5)\right]\times10^6$ — "
                 "why 'Six Sigma' means 3.4 defects per million", loc="left")
    ax.set_xlabel(r"sigma level  $z$  (short-term)")
    ax.set_ylabel("defective parts per million")
    ax.grid(alpha=.5, which="both")
    _save(fig, "05_dpmo")


# ---------------------------------------------------------------------------
# 6. EWMA — weight decay + limit convergence, exact curves
# ---------------------------------------------------------------------------
def sheet_ewma():
    lam = 0.2
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)

    ax = axs[0]
    k = np.arange(0, 20)
    w = lam * (1 - lam) ** k
    ax.bar(k, w, color=BLUE, alpha=.85)
    ax.plot(k, w, "o-", color=YELLOW, ms=4, lw=1.2,
            label=r"$w_k=\lambda(1-\lambda)^k$")
    ax.set_yscale("log"); ax.set_ylim(1e-3, 1)
    ax.set_title("EWMA memory: weight of an observation\n"
                 rf"$k$ steps old ($\lambda={lam}$)", loc="left")
    ax.set_xlabel("age  k  (observations back)"); ax.legend(frameon=False)
    ax.grid(alpha=.5, which="both")

    ax = axs[1]
    i = np.arange(1, 51)
    f = np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))
    ax.plot(i, 3 * f, color=YELLOW, lw=2.2, label="EWMA limit factor")
    ax.axhline(3, color=MUTED, ls="--", lw=1)
    asym = 3 * math.sqrt(lam / (2 - lam))
    ax.axhline(asym, color=RED, ls=":", lw=1.4)
    ax.text(50, asym + .08, f"asymptote = 3√(λ/(2−λ)) = {asym:.3f}σ",
            color=RED, ha="right", fontsize=11)
    ax.set_title(r"$L_i=3\sqrt{\frac{\lambda}{2-\lambda}"
                 r"\left[1-(1-\lambda)^{2i}\right]}$", loc="left")
    ax.set_xlabel("observation  i"); ax.legend(frameon=False); ax.grid(alpha=.5)
    _save(fig, "06_ewma")


# ---------------------------------------------------------------------------
# 7. Western Electric rules — the decision zones drawn to scale
# ---------------------------------------------------------------------------
def sheet_we():
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for z, lab, col in [(3, "+3σ", RED), (2, "+2σ", YELLOW), (1, "+1σ", TEAL),
                        (-1, "−1σ", TEAL), (-2, "−2σ", YELLOW), (-3, "−3σ", RED)]:
        ax.axhline(z, color=col, lw=1.6 if abs(z) == 3 else 1.1,
                   ls="-" if abs(z) == 3 else "--", alpha=.9)
        ax.text(.99, z + .07, lab, color=col, ha="right", fontsize=11,
                transform=ax.get_yaxis_transform())

    zones = [
        (1, 3, RED, .25, "RULE 1\n1 pt beyond 3σ"),
        (2, 3, YELLOW, .14, "RULE 2\n2 of 3 beyond 2σ"),
        (1, 2, TEAL, .12, "RULE 3\n4 of 5 beyond 1σ"),
    ]
    for lo, hi, col, op, lab in zones:
        ax.axhspan(lo, hi, color=col, alpha=op)
        ax.axhspan(-hi, -lo, color=col, alpha=op)
        ax.text(1.02, (lo + hi) / 2, lab, color=col, fontsize=11, va="center")

    ax.axhline(0, color=FG, lw=1.4)
    ax.text(1.02, 0, "RULE 4\n8 in a row\none side", color=BLUE, fontsize=11,
            va="center")
    ax.set_xlim(0, 1); ax.set_xticks([])
    ax.set_ylim(-3.5, 3.5)
    ax.set_ylabel("standardized subgroup mean  z = (x̄ − x̄̄)/σ_x̄")
    ax.set_title("The WE decision map — every rule is a region of this picture",
                 loc="left")
    _save(fig, "07_western_electric")


if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    sheet_d2()
    sheet_A2()
    sheet_limits()
    sheet_cpk()
    sheet_dpmo()
    sheet_ewma()
    sheet_we()
