"""LEVEL 3 act — 'Capability is comparing two distributions.'

    .venv/bin/manim -qh src/spclab/level3_scene.py Level3
"""
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Text, VGroup, Group, Rectangle, Polygon,
    Create, Write, FadeIn, FadeOut, Transform, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


def pdf(xs, mu, sg):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


class Level3(Scene):
    def construct(self):
        self.two_voices()
        self.cpk_promises()

    # ---------------- part 1: two voices on one axis --------------------
    def two_voices(self):
        lsl, usl, mu0, sg = 49.7, 50.3, 50.0, 0.075
        t = Text("Level 3 · Two voices: the customer's and the process's",
                 font_size=28, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[49.55, 50.45, .2], y_range=[0, 6.2, 1],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        self.play(Create(axes), run_time=0.8)

        # customer voice: the tolerance bracket
        xs = np.linspace(49.55, 50.45, 300)
        curve_grp = VGroup()
        for mu in (mu0,):     # built once; shifted later
            p = pdf(xs, mu, sg)
            c = axes.plot_line_graph(xs, p, add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]
            curve_grp.add(c)
        spec_lines = VGroup()
        for xv in (lsl, usl):
            ln = Line(axes.c2p(xv, 0), axes.c2p(xv, 5.8),
                      stroke_color=YELLOW, stroke_width=2.4)
            spec_lines.add(ln)
        lab_c = Text("customer: “anything between these lines”",
                     font_size=22, color=YELLOW).to_edge(DOWN, buff=0.42)
        lab_p = Text("process: “this is my natural spread”",
                     font_size=22, color=TEAL).next_to(lab_c, UP, buff=0.18)

        self.play(Create(spec_lines), FadeIn(lab_c), run_time=0.8)
        self.play(Create(curve_grp[0]), FadeIn(lab_p), run_time=1.1)
        self.wait(1.0)

        # Cp dimension line: tolerance width vs process width
        y_top = axes.c2p(0, 5.3)[1]
        dim1 = Line(axes.c2p(lsl, 5.3), axes.c2p(usl, 5.3),
                    stroke_color=YELLOW, stroke_width=2)
        d1t = Text(f"tolerance width {usl-lsl:.2f}", font_size=20, color=YELLOW)
        d1t.next_to(dim1, UP, buff=0.12)
        dim2 = Line(axes.c2p(mu0-3*sg, 4.6), axes.c2p(mu0+3*sg, 4.6),
                    stroke_color=BLUE, stroke_width=2)
        d2t = Text(f"6σ = {6*sg:.2f}", font_size=20, color=BLUE)
        d2t.next_to(dim2, DOWN, buff=0.12)
        cp_lab = Text("Cp = width ratio = 1.33", font_size=26, color=YELLOW)
        cp_lab.to_edge(RIGHT, buff=.7).shift(UP*1.4)
        self.play(Create(dim1), FadeIn(d1t), Create(dim2), FadeIn(d2t),
                  Write(cp_lab), run_time=1.2)
        self.wait(1.0)

        # drift the mean: same spread, new gaps -> Cpk
        shift_note = Text("…now let the mean drift +0.12 mm",
                          font_size=24, color=GREY).to_edge(DOWN, buff=0.42)
        self.play(FadeOut(lab_p), FadeOut(lab_c), FadeIn(shift_note), run_time=0.6)
        new_curve = axes.plot_line_graph(
            xs, pdf(xs, mu0+0.12, sg), add_vertex_dots=False,
            line_color=TEAL, stroke_width=3)["line_graph"]
        self.play(Transform(curve_grp[0], new_curve),
                  dim2.animate.shift(axes.c2p(0.12, 0) - axes.c2p(0, 0)),
                  d2t.animate.shift(axes.c2p(0.12, 0) - axes.c2p(0, 0)),
                  run_time=1.2)

        # red tail beyond USL
        xs_tail = xs[xs >= usl]
        p_tail = pdf(xs_tail, mu0+0.12, sg)
        tail = Polygon(*[axes.c2p(a, b) for a, b in zip(xs_tail, p_tail)],
                       axes.c2p(usl, 0), axes.c2p(float(xs_tail[-1]), 0),
                       fill_color=RED, fill_opacity=0.65, stroke_width=0)
        self.play(FadeIn(tail), run_time=0.7)

        cpu = (usl - (mu0+0.12)) / (3*sg)
        cpl = ((mu0+0.12) - lsl) / (3*sg)
        cpk_lab = Text(f"Cpk = min({cpu:.2f}, {cpl:.2f}) = {min(cpu,cpl):.2f}"
                       " — the near gap decides",
                       font_size=26, color=RED).next_to(cp_lab, DOWN, aligned_edge=RIGHT,
                                                         buff=0.35)
        self.play(Write(cpk_lab), run_time=1)
        self.wait(1.6)

        everything = Group(t, axes, curve_grp, spec_lines, dim1, d1t, dim2, d2t,
                           cp_lab, shift_note, tail, cpk_lab)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # --------------- part 2: what a Cpk number promises -----------------
    def cpk_promises(self):
        t = Text("…and every Cpk value is a defect promise",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        rows = [
            ("Cpk 0.80", "≈ 16 400 ppm", "1 in 61 parts fails", RED),
            ("Cpk 1.00", "≈   1 350 ppm", "1 in 740 parts fails", YELLOW),
            ("Cpk 1.33", "≈      32 ppm", "1 in 31 000 parts fails", TEAL),
            ("Cpk 1.67", "≈       0.6 ppm", "1 in 1.7 million fails", BLUE),
        ]
        table = VGroup()
        for name, ppm, plain, col in rows:
            r = Text(f"{name}   →   {ppm}   ({plain})",
                     font_size=27, color=col)
            table.add(r)
        table.arrange(DOWN, aligned_edge=LEFT, buff=0.42).shift(UP * 0.4)
        from manim import LaggedStart
        self.play(LaggedStart(*[Write(r) for r in table], lag_ratio=0.35), run_time=3)
        note = Text("these aren't rules of thumb — they're integrals of the "
                    "normal tail,\ncomputed exactly in spc-lab's tests",
                    font_size=22, slant=ITALIC, color=GREY
                    ).to_edge(DOWN, buff=0.4)
        self.play(Write(note), run_time=1)
        self.wait(1.8)
