"""LEVEL 3 act — 'Capability is comparing two distributions.'

Pacing lives in the narration script: every beat is held for as long as its
line takes to speak, whether or not the audio is rendered. See narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level3_scene.py Level3
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level3_scene.py Level3
"""
import numpy as np

from spclab.formulas import ppm_from_cpk
from spclab.narration import NarratedScene
from manim import (
    Axes, Dot, Line, Text, VGroup, Group, Rectangle, Polygon,
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


class Level3(NarratedScene):
    def construct(self):
        self.two_voices()
        self.cpk_promises()

    # ---------------- part 1: two voices on one axis --------------------
    def two_voices(self):
        lsl, usl, mu0, sg = 49.7, 50.3, 50.0, 0.075
        t = Text("Level 3 · Two voices: the customer's and the process's",
                 font_size=28, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Capability compares two distributions. One is the "
                      "customer's. One is the process's."):
            self.play(FadeIn(t))

        axes = Axes(x_range=[49.55, 50.45, .2], y_range=[0, 6.2, 1],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        with self.say("One dimension, one axis, millimetres."):
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

        with self.say("The customer speaks in limits. Anything between these "
                      "lines is accepted."):
            self.play(Create(spec_lines), FadeIn(lab_c), run_time=0.8)
        with self.say("The process answers with its own spread. It never read "
                      "the drawing."):
            self.play(Create(curve_grp[0]), FadeIn(lab_p), run_time=1.1)

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
        with self.say("Tolerance is zero point six millimetres wide. Six sigma "
                      "of process is zero point four five."):
            self.play(Create(dim1), FadeIn(d1t), Create(dim2), FadeIn(d2t),
                      run_time=1.2)
        with self.say("Cp is those two widths divided. One point three three. "
                      "Pure geometry, assuming a centred mean."):
            self.play(Write(cp_lab), run_time=1.2)

        # drift the mean: same spread, new gaps -> Cpk
        shift_note = Text("…now let the mean drift +0.12 mm",
                          font_size=24, color=GREY).to_edge(DOWN, buff=0.42)
        with self.say("Now drift the mean. The spread does not change."):
            self.play(FadeOut(lab_p), FadeOut(lab_c), FadeIn(shift_note),
                      run_time=0.6)
        new_curve = axes.plot_line_graph(
            xs, pdf(xs, mu0+0.12, sg), add_vertex_dots=False,
            line_color=TEAL, stroke_width=3)["line_graph"]
        with self.say("One gap shrinks. The other opens. Cp cannot tell."):
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
        with self.say("The near side leaks. That is where parts fail."):
            self.play(FadeIn(tail), run_time=0.7)

        cpu = (usl - (mu0+0.12)) / (3*sg)
        cpl = ((mu0+0.12) - lsl) / (3*sg)
        cpk_lab = Text(f"Cpk = min({cpu:.2f}, {cpl:.2f}) = {min(cpu,cpl):.2f}"
                       " — the near gap decides",
                       font_size=26, color=RED).next_to(cp_lab, DOWN, aligned_edge=RIGHT,
                                                         buff=0.35)
        with self.say("Cpk takes the smaller one sided ratio. Zero point eight "
                      "nine. The near gap decides."):
            self.play(Write(cpk_lab), run_time=1)

        self.beat(0.7)

        everything = Group(t, axes, curve_grp, spec_lines, dim1, d1t, dim2, d2t,
                           cp_lab, shift_note, tail, cpk_lab)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # --------------- part 2: what a Cpk number promises -----------------
    def cpk_promises(self):
        t = Text("…and every Cpk value is a defect promise",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Every Cpk value is a promise about defect rate."):
            self.play(FadeIn(t))

        # Computed, never typed. Every row is the same one-sided near-tail
        # integral, so the table cannot drift out of agreement with the tests
        # or with the calculator on the web page.
        rows = []
        for cpk, col in ((0.80, RED), (1.00, YELLOW), (1.33, TEAL), (1.67, BLUE)):
            ppm = ppm_from_cpk(cpk)
            ppm_s = f"{ppm:,.0f}" if ppm >= 100 else (f"{ppm:.1f}" if ppm >= 1 else f"{ppm:.2f}")
            one_in = f"1 in {round(1e6 / ppm):,}"
            rows.append((f"Cpk {cpk:.2f}", f"{ppm_s} ppm", f"{one_in} parts fails", col))

        table = VGroup()
        for name, ppm, plain, col in rows:
            r = Text(f"{name}   →   {ppm}   ({plain})",
                     font_size=27, color=col)
            table.add(r)
        table.arrange(DOWN, aligned_edge=LEFT, buff=0.42).shift(UP * 0.4)
        from manim import LaggedStart
        with self.say("Each row: a Cpk, the parts per million expected outside "
                      "the limit, and the same number in plain counting."):
            self.play(LaggedStart(*[Write(r) for r in table], lag_ratio=0.35),
                      run_time=3)
        note = Text("near-tail integrals of the normal curve, computed at render "
                    "time\nby spclab.ppm_from_cpk — the same function the tests check",
                    font_size=22, slant=ITALIC, color=GREY
                    ).to_edge(DOWN, buff=0.4)
        with self.say("These are near tail figures, computed at render time by "
                      "the same function the test suite checks."):
            self.play(Write(note), run_time=1)
        with self.say("Nothing is read off a table. Change the formula and this "
                      "slide changes."):
            pass
