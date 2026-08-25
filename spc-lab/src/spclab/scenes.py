"""SPCGallery — the overview act, in true 3b1b spirit.

The curriculum landing page plays this one first, so it assumes nothing: it
introduces the two ideas the whole subject rests on. Points stream onto an X̄
chart and control limits draw themselves from the data (not from a spec), then
capability geometry shows where scrap hides.

Pacing lives in the narration script: every beat is held for as long as its
line takes to speak, whether or not the audio is rendered. See narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qm src/spclab/scenes.py SPCGallery
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qm src/spclab/scenes.py SPCGallery

No LaTeX required — all math uses unicode Text().
"""
import numpy as np
from manim import (
    Axes, Dot, Line, Text, VGroup, Group, Rectangle, Polygon,
    Create, Write, FadeIn, Unwrite, GrowFromEdge, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

from spclab.narration import NarratedScene

# ---- palette (the classic 3b1b constants) --------------------------------
BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


class SPCGallery(NarratedScene):
    def construct(self):
        self.intro()
        self.chart_act()
        self.capability_act()

    # ------------------------------------------------------------- intro
    def intro(self):
        t1 = Text("Every SPC formula,", font_size=44, slant=ITALIC)
        t2 = Text("drawn.", font_size=44, slant=ITALIC, color=TEAL)
        title = VGroup(t1, t2).arrange(DOWN, aligned_edge=LEFT).shift(UP)
        with self.say("Statistical process control is a handful of formulas. "
                      "Each one is a picture."):
            self.play(Write(t1), run_time=1.2)
        with self.say("Two of those pictures carry the rest."):
            self.play(Write(t2), run_time=0.8)
        self.play(Unwrite(t1), Unwrite(t2), run_time=0.7)

    # ---------------------------------------------- act 1: the X̄ chart
    def chart_act(self):
        rng = np.random.default_rng(7)
        target = 0.0

        title = Text("1 · Control limits come FROM the process",
                     font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("First idea. Control limits are learned from the process, "
                      "not handed to you."):
            self.play(FadeIn(title))

        axes = Axes(
            x_range=[0, 40, 10], y_range=[-0.45, 0.45, 0.2],
            x_length=10, y_length=4.6,
            tips=False,
            axis_config={"stroke_color": GREY, "stroke_width": 1.5,
                         "tip_width": 0.1},
        ).shift(DOWN * 0.3)
        labels = axes.get_axis_labels(Text("subgroup", font_size=20),
                                      Text("x̄", font_size=24, slant=ITALIC))

        # CL first — it is just the grand mean
        cl_line = Line(axes.c2p(0, target), axes.c2p(40, target),
                       stroke_color=GREY, stroke_width=2)
        cl_lab = Text("CL", font_size=22, color=GREY).next_to(cl_line, RIGHT, buff=0.15)

        with self.say("This chart plots subgroup averages in sample order. "
                      "The centre line is just their average."):
            self.play(Create(axes), FadeIn(labels), run_time=1)
            self.play(Create(cl_line), FadeIn(cl_lab), run_time=0.6)

        # points stream in, six at a time
        means = [rng.normal(target, 0.09) for _ in range(36)]
        dots = VGroup(*[
            Dot(axes.c2p(i + 1, m), radius=0.045, color=BLUE)
            for i, m in enumerate(means)
        ])
        with self.say("Now let the process talk. Each dot is one subgroup mean."):
            for i in range(0, 36, 6):
                self.play(FadeIn(dots[i:i + 6]), run_time=0.18)

        # derive σ of subgroup means from the data itself → ±3σ limits
        sigma_hat = float(np.std(means[5:], ddof=1))
        ucl_v, lcl_v = 3 * sigma_hat, -3 * sigma_hat
        ucl = Line(axes.c2p(0, ucl_v), axes.c2p(40, ucl_v),
                   stroke_color=YELLOW, stroke_width=2.5)
        lcl = Line(axes.c2p(0, lcl_v), axes.c2p(40, lcl_v),
                   stroke_color=YELLOW, stroke_width=2.5)
        band = Rectangle(stroke_width=0, fill_color=BLUE, fill_opacity=0.08)
        band.stretch_to_fit_width(axes.x_length)
        band.stretch_to_fit_height(ucl.get_y() - lcl.get_y())
        band.move_to((ucl.get_center() + lcl.get_center()) / 2)

        ucl_lab = Text("UCL = x̄̄ + 3σ̂", font_size=22, color=YELLOW).next_to(ucl, RIGHT, buff=0.12)
        lcl_lab = Text("LCL = x̄̄ − 3σ̂", font_size=22, color=YELLOW).next_to(lcl, RIGHT, buff=0.12)

        with self.say("Their spread gives you sigma hat. Lines at three sigma "
                      "either side are the control limits."):
            self.play(GrowFromEdge(band, LEFT), Create(ucl), Create(lcl), run_time=1.1)
            self.play(FadeIn(ucl_lab), FadeIn(lcl_lab), run_time=0.5)

        note = Text("limits learned from data — not from the customer's spec",
                    font_size=26, slant=ITALIC, color=TEAL).to_edge(DOWN, buff=0.35)
        with self.say("Limits come from the data. Specs come from the customer. "
                      "Confusing the two is the most common mistake on a shop floor."):
            self.play(Write(note), run_time=1)

        everything = Group(title, axes, labels, cl_line, cl_lab, band,
                           ucl, lcl, ucl_lab, lcl_lab, dots, note)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.6)
        self.remove(everything)

    # --------------------------------------- act 2: capability geometry
    def capability_act(self):
        title = Text("2 · Capability — how much scrap hides in the tail",
                     font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Second idea. Capability is what happens when you compare "
                      "the process against the specification."):
            self.play(FadeIn(title))

        mu, sg, lsl, usl = 50.03, 0.09, 49.7, 50.3
        xs = np.linspace(lsl - 0.28, usl + 0.28, 300)
        pdf = np.exp(-((xs - mu) ** 2) / (2 * sg ** 2))

        axes = Axes(
            x_range=[float(xs[0]), float(xs[-1]), 0.1],
            y_range=[0, 1.25, 0.25],
            x_length=10.5, y_length=4.4, tips=False,
            axis_config={"stroke_color": GREY, "stroke_width": 1.5},
        ).shift(DOWN * 0.35)
        curve = axes.plot_line_graph(
            xs, pdf, add_vertex_dots=False, line_color=TEAL, stroke_width=3,
        )["line_graph"]

        with self.say("Same process, now plotted against the measurement itself. "
                      "This is where parts land."):
            self.play(Create(axes), run_time=0.8)
            self.play(Create(curve), run_time=1.1)

        with self.say("Now the customer's two limits. These were not calculated. "
                      "They were dictated."):
            for xv, lab in [(lsl, "LSL"), (usl, "USL")]:
                ln = Line(axes.c2p(xv, 0), axes.c2p(xv, 1.15),
                          stroke_color=YELLOW, stroke_width=2.5)
                t = Text(lab, font_size=22, color=YELLOW).next_to(ln, DOWN, buff=0.12)
                self.play(Create(ln), FadeIn(t), run_time=0.4)

        # red tails: area beyond spec = predicted scrap
        poly_l = Polygon(
            *[axes.c2p(a, b) for a, b in zip(xs[xs <= lsl], pdf[xs <= lsl])],
            axes.c2p(lsl, 0), axes.c2p(float(xs[0]), 0),
            fill_color=RED, fill_opacity=0.65, stroke_width=0)
        poly_r = Polygon(
            *[axes.c2p(a, b) for a, b in zip(xs[xs >= usl], pdf[xs >= usl])],
            axes.c2p(usl, 0), axes.c2p(float(xs[-1]), 0),
            fill_color=RED, fill_opacity=0.65, stroke_width=0)
        with self.say("Everything past them is scrap. The red area is how much "
                      "to expect."):
            self.play(FadeIn(poly_l), FadeIn(poly_r), run_time=0.9)

        cpk = min(usl - mu, mu - lsl) / (3 * sg)
        txt = Text(f"Cpk = {cpk:.2f}   →   ≈ 1 000+ defects per million",
                   font_size=28, color=RED).to_edge(DOWN, buff=0.35)
        with self.say("Nearest spec distance over three sigma is C p k. "
                      "About one, so a thousand bad parts per million."):
            self.play(Write(txt), run_time=1)

        self.beat(0.7)

        # Closing line: no new visual, the narration alone holds the last frame.
        with self.say("The chart says whether the process is steady. "
                      "Capability says whether steady is good enough."):
            pass
