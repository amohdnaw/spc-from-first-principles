"""LEVEL 2 act — 'Control limits are a hypothesis test.'

Pacing lives in the narration script: every beat is held for as long as its
line takes to speak, whether or not the audio is rendered. See narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level2_scene.py Level2
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level2_scene.py Level2
"""
import numpy as np
from manim import (
    Axes, Dot, Line, Text, VGroup, Group, Rectangle, DashedLine, Polygon,
    Create, Write, FadeIn, GrowFromEdge, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

from spclab.narration import NarratedScene

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


def norm_pdf(xs, mu=0.0, sg=1.0):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


class Level2(NarratedScene):
    def construct(self):
        self.part1_null()
        self.part2_chart()

    # ------------------- part 1: the bell IS the hypothesis -------------
    def part1_null(self):
        t = Text("Level 2 · ±3σ is not taste — it's a bet",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Three sigma is not a matter of taste. It is a bet, and "
                      "we can price it exactly."):
            self.play(FadeIn(t))

        axes = Axes(x_range=[-4.2, 4.2, 1], y_range=[0, 0.48, 0.2],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        xl = axes.get_axis_labels(
            Text("subgroup mean (units of σx̄)", font_size=20),
            Text("density", font_size=20))
        with self.say("Level one told us which distribution every subgroup mean "
                      "is drawn from, assuming nothing has changed."):
            self.play(Create(axes), FadeIn(xl), run_time=0.8)

        xs = np.linspace(-4.2, 4.2, 300)
        pdf = norm_pdf(xs)
        curve = axes.plot_line_graph(xs, pdf, add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]
        with self.say("This curve is the null hypothesis. Not an assumption about "
                      "the parts, but a claim about the process: it is unchanged."):
            self.play(Create(curve), run_time=1.4)
            hyp = Text("H₀: process unchanged — every x̄ comes from THIS distribution",
                       font_size=24, color=TEAL).to_edge(DOWN, buff=0.45)
            self.play(Write(hyp), run_time=1.2)

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
        with self.say("Put limits at plus and minus three sigma of that curve, "
                      "and you have drawn a boundary around ninety nine point "
                      "seven three percent of everything the process should ever do."):
            self.play(FadeIn(poly), run_time=0.9)

            lab_in = Text("99.73%", font_size=34, color=TEAL)
            lab_in.move_to(axes.c2p(0, 0.12))
            self.play(FadeIn(lab_in), FadeIn(tail_l), FadeIn(tail_r), run_time=0.9)

        with self.say("That leaves zero point two seven percent outside. Roughly "
                      "one false alarm every three hundred and seventy subgroups. "
                      "So a point beyond the limit is a bet at three hundred and "
                      "seventy to one that something really did change."):
            odds = Text("outside: 0.27% → false alarm ≈ once per 370 subgroups",
                        font_size=24, color=RED).next_to(hyp, UP, buff=0.22)
            self.play(Write(odds), run_time=1.2)

        self.beat(0.7)

        everything = Group(t, axes, xl, curve, hyp, poly, lab_in,
                           tail_l, tail_r, odds)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # ------------- part 2: the same picture wearing a chart's clothes ----
    def part2_chart(self):
        rng = np.random.default_rng(31)
        t = Text("…so the control chart is that test, running forever",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("A control chart is simply that same test, run again on "
                      "every subgroup, forever."):
            self.play(FadeIn(t))

        axes = Axes(x_range=[0, 40, 10], y_range=[-3.8, 3.8, 1],
                    x_length=10.5, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        with self.say("The limits are the boundary we just drew, turned on its side."):
            for v in (-3, 3):
                ln = Line(axes.c2p(0, v), axes.c2p(40, v),
                          stroke_color=YELLOW, stroke_width=2.2)
                lab = Text(f"{'UCL' if v > 0 else 'LCL'}", font_size=22, color=YELLOW)
                lab.next_to(ln, RIGHT, buff=0.12)
                self.play(Create(ln), FadeIn(lab), run_time=0.5)
            cl = Line(axes.c2p(0, 0), axes.c2p(40, 0), stroke_color=GREY, stroke_width=2)
            self.play(Create(cl), run_time=0.6)

        # in-control points, then ONE genuine shift at the end
        pts = list(rng.normal(0, 1, 36)) + [4.1]
        dots = VGroup(*[
            Dot(axes.c2p(i + 1, min(v, 3.75)), radius=0.055,
                color=RED if abs(v) > 3 else BLUE)
            for i, v in enumerate(pts)
        ])
        with self.say("Every point inside is the process agreeing with the null. "
                      "This is what boring looks like, and boring is the goal."):
            for i in range(0, 30, 6):
                self.play(FadeIn(dots[i:i + 6]), run_time=0.45)

        with self.say("Then one point steps outside."):
            self.play(FadeIn(dots[30:]), run_time=0.6)

        alarm = Text("not 'bad part' — evidence against H₀\n"
                     "act: find what changed", font_size=24, color=RED)
        alarm.next_to(dots[-1], DOWN, buff=0.5).shift(LEFT * 2.2)
        with self.say("That point is not a bad part. It is evidence against the "
                      "hypothesis that nothing changed. The correct response is "
                      "not to scrap it. It is to go and find what changed."):
            self.play(FadeIn(alarm), run_time=1.2)

        self.beat(1.0)
