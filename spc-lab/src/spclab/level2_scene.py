"""LEVEL 2 act — 'Control limits are a hypothesis test.'

    .venv/bin/manim -qh src/spclab/level2_scene.py Level2
"""
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Text, VGroup, Group, Rectangle, DashedLine, Polygon,
    Create, Write, FadeIn, GrowFromEdge, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


def norm_pdf(xs, mu=0.0, sg=1.0):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


class Level2(Scene):
    def construct(self):
        self.part1_null()
        self.part2_chart()

    # ------------------- part 1: the bell IS the hypothesis -------------
    def part1_null(self):
        t = Text("Level 2 · ±3σ is not taste — it's a bet",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[-4.2, 4.2, 1], y_range=[0, 0.48, 0.2],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        xl = axes.get_axis_labels(
            Text("subgroup mean (units of σx̄)", font_size=20),
            Text("density", font_size=20))
        self.play(Create(axes), FadeIn(xl), run_time=0.8)

        xs = np.linspace(-4.2, 4.2, 300)
        pdf = norm_pdf(xs)
        curve = axes.plot_line_graph(xs, pdf, add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]
        self.play(Create(curve), run_time=1.2)
        hyp = Text("H₀: process unchanged — every x̄ comes from THIS distribution",
                   font_size=24, color=TEAL).to_edge(DOWN, buff=0.45)
        self.play(Write(hyp), run_time=1)

        # fill ±3σ region
        poly = Polygon(
            *[axes.c2p(a, b) for a, b in zip(xs[np.abs(xs) <= 3], pdf[np.abs(xs) <= 3])],
            axes.c2p(3, 0), axes.c2p(-3, 0),
            fill_color=TEAL, fill_opacity=0.35, stroke_width=0)
        tail_l = Polygon(
            *[axes.c2p(a, b) for a, b in zip(xs[xs <= -3], pdf[xs <= -3])],
            axes.c2p(-3, 0), axes.c2p(float(xs[0]), 0),
            fill_color=RED, fill_opacity=0.65, stroke_width=0)
        tail_r = Polygon(
            *[axes.c2p(a, b) for a, b in zip(xs[xs >= 3], pdf[xs >= 3])],
            axes.c2p(3, 0), axes.c2p(float(xs[-1]), 0),
            fill_color=RED, fill_opacity=0.65, stroke_width=0)
        self.play(FadeIn(poly), run_time=0.7)

        lab_in = Text("99.73%", font_size=34, color=TEAL)
        lab_in.move_to(axes.c2p(0, 0.12))
        self.play(FadeIn(lab_in), FadeIn(tail_l), FadeIn(tail_r), run_time=0.8)

        odds = Text("outside: 0.27% → false alarm ≈ once per 370 subgroups",
                    font_size=24, color=RED).next_to(hyp, UP, buff=0.22)
        self.play(Write(odds), run_time=1)
        self.wait(1.6)

        everything = Group(t, axes, xl, curve, hyp, poly, lab_in,
                           tail_l, tail_r, odds)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # ------------- part 2: the same picture wearing a chart's clothes ----
    def part2_chart(self):
        rng = np.random.default_rng(31)
        t = Text("…so the control chart is that test, running forever",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[0, 40, 10], y_range=[-3.8, 3.8, 1],
                    x_length=10.5, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        for v in (-3, 3):
            ln = Line(axes.c2p(0, v), axes.c2p(40, v),
                      stroke_color=YELLOW, stroke_width=2.2)
            lab = Text(f"{'UCL' if v > 0 else 'LCL'}", font_size=22, color=YELLOW)
            lab.next_to(ln, RIGHT, buff=0.12)
            self.play(Create(ln), FadeIn(lab), run_time=0.4)
        cl = Line(axes.c2p(0, 0), axes.c2p(40, 0), stroke_color=GREY, stroke_width=2)
        self.play(Create(cl))

        # in-control points, then ONE genuine shift at the end
        pts = list(rng.normal(0, 1, 36)) + [4.1]
        dots = VGroup(*[
            Dot(axes.c2p(i + 1, min(v, 3.75)), radius=0.055,
                color=RED if abs(v) > 3 else BLUE)
            for i, v in enumerate(pts)
        ])
        verdicts = []
        for i in range(0, 37, 6):
            self.play(FadeIn(dots[i:i + 6]), run_time=0.25)

        alarm = Text("not 'bad part' — evidence against H₀\n"
                     "act: find what changed", font_size=24, color=RED)
        alarm.next_to(dots[-1], DOWN, buff=0.5).shift(LEFT * 2.2)
        self.play(FadeIn(alarm), run_time=1)
        self.wait(1.8)
