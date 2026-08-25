"""Three more 3b1b-style acts, one per formula family.

Render each:
    .venv/bin/manim -qh src/spclab/scenes2.py ConstantsAct
    .venv/bin/manim -qh src/spclab/scenes2.py EWMAMemory
    .venv/bin/manim -qh src/spclab/scenes2.py WERules
"""
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Text, VGroup, Group, Rectangle, DashedLine,
    Create, Write, FadeIn, FadeOut, Unwrite, GrowFromEdge, Indicate,
    Circumscribe, LaggedStart, ITALIC, UP, DOWN, RIGHT, LEFT, config,
)

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


def title(text, color=GREY):
    return Text(text, font_size=30, color=color).to_edge(UP, buff=0.4)


def clear(self, *mobs, rt=0.6):
    g = Group(*mobs)
    self.play(g.animate.scale(0.001).set_opacity(0), run_time=rt)
    self.remove(g)


# ===========================================================================
# ACT A — d2 and A2: why dividing by this constant works
# ===========================================================================
class ConstantsAct(Scene):
    def construct(self):
        rng = np.random.default_rng(11)
        self.camera.background_color = BG

        t = title("1 · Where does A₂ come from?")
        self.play(FadeIn(t))

        # --- part 1: take 5 parts, look at their range
        line = Line(LEFT * 4.5, RIGHT * 4.5).shift(UP * 1.8)
        lab_n = Text("subgroup of n = 5 parts", font_size=24, color=GREY)
        lab_n.next_to(line, UP, buff=0.35)
        self.play(Create(line), FadeIn(lab_n))

        vals = rng.normal(0, 1, 5)
        dots = VGroup()
        for v in sorted(vals):
            d = Dot(np.array([v * 1.6, 1.8, 0]), radius=0.09, color=BLUE)
            dots.add(d)
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.15),
                  run_time=1.0)

        lo, hi = min(vals) * 1.6, max(vals) * 1.6
        brace_line = Line(np.array([lo, 1.55, 0]), np.array([hi, 1.55, 0]),
                          stroke_color=YELLOW, stroke_width=3)
        r_lab = Text("R", font_size=28, slant=ITALIC, color=YELLOW)
        r_lab.next_to(brace_line, DOWN, buff=0.12)
        self.play(Create(brace_line), FadeIn(r_lab), run_time=0.7)
        self.wait(0.8)

        # --- part 2: repeat many times -> average range is stable
        q = Text("repeat forever →  E(R) = d₂ · σ", font_size=30, color=TEAL)
        q.shift(DOWN * 0.4)
        self.play(Write(q), run_time=1.0)

        sim = Text("(spc-lab computes d₂ by Monte Carlo: mean range of\n"
                   "400 000 subgroups of n standard normals)",
                   font_size=20, color=GREY).next_to(q, DOWN, buff=0.4)
        self.play(FadeIn(sim))
        self.wait(1.2)

        # --- part 3: therefore limits = grand mean ± 3σ, σ = R̄ / d2 / √n
        f1 = Text("σ̂ = R̄ / d₂", font_size=32, color=YELLOW).shift(DOWN * 2.0 + LEFT * 3)
        arrow1 = Text("→", font_size=32, color=GREY).shift(DOWN * 2.0)
        f2 = Text("UCL = x̄̄ + 3·R̄/d₂   …per subgroup-mean:", font_size=26).next_to(arrow1, RIGHT)
        f3 = Text("A₂ = 3 / (d₂ √n)", font_size=34, color=YELLOW).next_to(f2, DOWN, aligned_edge=LEFT, buff=0.25)
        val = Text("n = 5  →  A₂ = 0.577   ✓ matches AIAG Table B",
                   font_size=22, color=TEAL).next_to(f3, DOWN, aligned_edge=LEFT, buff=0.25)
        clear(self, t, line, lab_n, dots, brace_line, r_lab, sim)
        self.play(Write(f1), run_time=0.7)
        self.play(FadeIn(arrow1), Write(f2), run_time=0.9)
        self.play(Write(f3), run_time=0.9)
        self.play(Write(val), run_time=0.8)
        self.wait(1.6)
        clear(self, q, f1, arrow1, f2, f3, val)


# ===========================================================================
# ACT B — EWMA: memory buys sensitivity
# ===========================================================================
class EWMAMemory(Scene):
    def construct(self):
        lam = 0.2
        t = title("2 · EWMA — a filter with just one knob")
        self.play(FadeIn(t))

        # --- weight decay bars: z_new = λx + (1-λ)z_old
        head = Text("zᵢ = λ·xᵢ + (1−λ)·zᵢ₋₁      →  old points fade geometrically",
                    font_size=26, color=GREY)
        head.shift(UP * 0.9)
        self.play(Write(head), run_time=1)

        k = 14
        weights = [lam * (1 - lam) ** i for i in range(k)]
        maxw = max(weights)
        bars = VGroup()
        bw, gap = 0.42, 0.13
        total_w = k * bw + (k - 1) * gap
        x0 = -total_w / 2
        for i, w in enumerate(weights):
            h = 2.2 * w / maxw
            b = Rectangle(width=bw, height=max(h, 0.02),
                          fill_color=BLUE, fill_opacity=0.85, stroke_width=0)
            b.move_to(np.array([x0 + i * (bw + gap) + bw / 2, -0.6 - h / 2, 0]))
            bars.add(b)
        base = Line(np.array([x0 - 0.1, -0.62, 0]), np.array([-x0 + 0.1, -0.62, 0]),
                    stroke_color=GREY, stroke_width=1.5)
        wlab = Text("λ = 0.2 → each step back weighs 80% of the previous",
                    font_size=22, color=BLUE).to_edge(DOWN, buff=1.6)
        self.play(GrowFromEdge(base, LEFT))
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.05),
                  run_time=1.6)
        self.play(FadeIn(wlab))
        self.wait(1.2)
        clear(self, t, head, bars, base, wlab)

        # --- consequence: limits tighten, drift is caught early
        t2 = title("…so its limits tighten, and slow drift can't hide")
        self.play(FadeIn(t2))

        kk = 40
        i = np.arange(1, kk + 1)
        f = np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))
        up, lo_ = 3 * f, -3 * f

        axes = Axes(x_range=[1, kk, 10], y_range=[-3.4, 3.4, 1],
                    x_length=10, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.4)
        self.play(Create(axes), run_time=0.8)

        shew = DashedLine(axes.c2p(1, 3), axes.c2p(kk, 3), stroke_color=GREY,
                          stroke_width=1.5)
        shew_l = DashedLine(axes.c2p(1, -3), axes.c2p(kk, -3), stroke_color=GREY,
                            stroke_width=1.5)
        s_lab = Text("Shewhart ±3σ", font_size=18, color=GREY).next_to(shew, UP, buff=0.08)
        self.play(Create(shew), Create(shew_l), FadeIn(s_lab), run_time=0.6)

        ucl_curve = axes.plot_line_graph(i, up, add_vertex_dots=False,
                                         line_color=YELLOW, stroke_width=3)["line_graph"]
        lcl_curve = axes.plot_line_graph(i, lo_, add_vertex_dots=False,
                                         line_color=YELLOW, stroke_width=3)["line_graph"]
        asym = 3 * np.sqrt(lam / (2 - lam))
        a_lab = Text(f"asymptote ±{asym:.2f}σ", font_size=18, color=YELLOW)
        a_lab.next_to(axes.c2p(kk, asym), RIGHT, buff=0.1)
        self.play(Create(ucl_curve), Create(lcl_curve), run_time=1.2)
        self.play(FadeIn(a_lab))

        note = Text("tight limits + smoothed data = drift detected ~2× sooner",
                    font_size=24, slant=ITALIC, color=TEAL).to_edge(DOWN, buff=0.35)
        self.play(Write(note), run_time=1)
        self.wait(1.5)
        clear(self, t2, axes, shew, shew_l, s_lab, ucl_curve, lcl_curve, a_lab, note)


# ===========================================================================
# ACT C — Western Electric rules: pattern detection
# ===========================================================================
class WERules(Scene):
    def construct(self):
        rng = np.random.default_rng(23)
        t = title("3 · Western Electric rules — catching patterns, not just points")
        self.play(FadeIn(t))

        n = 40
        z = list(rng.normal(0, 0.45, 16)) \
          + [2.3, 2.5] + list(rng.normal(0.4, 0.45, 6)) \
          + list(rng.normal(0, 0.45, 4)) \
          + [0.6] * 8 + list(rng.normal(0, 0.45, 2))
        z[16] = 3.3                      # guaranteed Rule-1 breach
        z = np.array(z[:len(z)])[:40]

        axes = Axes(x_range=[0, n, 10], y_range=[-3.6, 3.6, 1],
                    x_length=10.5, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.4)
        for v, lab, col in [(3, "+3σ", RED), (-3, "−3σ", RED),
                            (1, "+1σ", GREY), (-1, "−1σ", GREY)]:
            ln_cls = Line if abs(v) >= 3 else DashedLine
            ln = ln_cls(axes.c2p(0, v), axes.c2p(n, v),
                        stroke_color=col, stroke_width=1.1)
            self.add(ln)
        cl = Line(axes.c2p(0, 0), axes.c2p(n, 0), stroke_color=GREY, stroke_width=2)
        self.play(Create(axes), Create(cl), run_time=0.8)

        dots = VGroup(*[
            Dot(axes.c2p(i + 1, float(v)), radius=0.05,
                color=RED if abs(v) > 3 else BLUE)
            for i, v in enumerate(z)
        ])
        for i in range(0, n, 8):
            self.play(FadeIn(dots[i:i + 8]), run_time=0.2)

        flags = [
            (16, "Rule 1 · 1 point beyond 3σ", RED),
            (18, "Rule 2 · 2 of 3 beyond 2σ, same side", YELLOW),
            (27, "Rule 3 · 4 of 5 beyond 1σ, same side", TEAL),
            (34, "Rule 4 · 8 in a row, same side", BLUE),
        ]
        y_off = 1.9
        for idx, desc, col in flags:
            hl = Dot(axes.c2p(idx + 1, float(z[idx])), radius=0.09,
                     color=col, fill_opacity=0.35)
            ft = Text(desc, font_size=19, color=col)
            ft.move_to(np.array([axes.c2p(20, 0)[0], y_off, 0]))
            y_off -= 0.52
            self.play(FadeIn(hl), Circumscribe(dots[idx], color=col, run_time=0.01),
                      Write(ft), run_time=0.75)
            self.wait(0.5)
        self.wait(1.4)
