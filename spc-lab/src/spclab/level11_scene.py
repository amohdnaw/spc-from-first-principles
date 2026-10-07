"""LEVEL 11 act — 'Least squares is a claim, not a name.'

Built 2026-10-07 against specs/l10-12-acts-contract.md ("after go": L11) and
the craft rules in specs/spc-manim-craft-contract.md.

- The level's one dataset (spclab.relationships): 29 speeds, roughness.
- The slope is a ValueTracker. The line pivots on the centroid, each residual is
  drawn as its square, and the live sum and a trace on the parabola of sums are
  computed from the tracker per frame, so the floor is found, not announced.
- At slope 0 the line is the mean and its squares are the total; at the floor
  they are the residual. R² is the ratio of those two, read off the same picture.
- The one camera move is the close-up on the floor of the parabola, where the
  closed form lands on the minimum, not near it.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level11_scene.py Level11
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level11_scene.py Level11
"""
from __future__ import annotations

import numpy as np
from manim import (
    Dot, Group, Line, MathTex, Polygon, TracedPath, ValueTracker, VGroup, VMobject,
    Circumscribe, Create, FadeIn, FadeOut, Restore, TransformMatchingShapes,
    always_redraw,
    DOWN, LEFT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose, within_frame,
)
from spclab.narration import NarratedCameraScene
from spclab.relationships import dataset, fit

XS, YS = dataset()
F = fit(XS, YS)
YBAR = float(YS.mean())
B_HI = 2 * F["slope"]          # the parabola is drawn symmetric about the floor
B_TOO = 1.6 * F["slope"]       # the sweep stops here: steeper, the line leaves the plot

# scatter: speed [50, 210] → [-6.2, 2.6]; roughness [0.5, 3.7] → [-2.6, 2.0]
SX0, SX1, SY0, SY1 = -6.2, 2.6, -2.6, 2.0
V0, V1, R0, R1 = 50.0, 210.0, 0.5, 3.7
# the parabola of sums, under the readouts
PX0, PX1, PY0, PY1 = PANEL, 6.85, -2.75, -0.55
S_MAX = 9.6


def sx(v):
    return SX0 + (v - V0) / (V1 - V0) * (SX1 - SX0)


def sy(r):
    return SY0 + (r - R0) / (R1 - R0) * (SY1 - SY0)


def px(b):
    return PX0 + b / B_HI * (PX1 - PX0)


def py(s):
    return PY0 + s / S_MAX * (PY1 - PY0)


def sse(b: float) -> float:
    return float(((YS - YBAR - b * (XS - F["xbar"])) ** 2).sum())


class Level11(NarratedCameraScene):
    def construct(self):
        self.b = ValueTracker(0.0)
        self.part1_slide()
        self.part2_ratio()

    # ---------------- pieces driven by the tracker --------------------------
    def line(self):
        b = self.b.get_value()
        y = lambda v: YBAR + b * (v - F["xbar"])
        near = abs(b - F["slope"]) < 2e-5
        return Line([sx(62), sy(y(62)), 0], [sx(198), sy(y(198)), 0],
                    stroke_color=TEAL if near else INK, stroke_width=3)

    def squares(self) -> VGroup:
        b = self.b.get_value()
        out = VGroup()
        for v, r in zip(XS, YS):
            fy = YBAR + b * (v - F["xbar"])
            x, y0, y1 = sx(v), sy(r), sy(fy)
            side = abs(y1 - y0)
            if side < 1e-3:
                continue
            # grow toward the centre of the cloud, so no square leaves the plot
            d = side if v < F["xbar"] else -side
            out.add(Polygon([x, y0, 0], [x + d, y0, 0], [x + d, y1, 0], [x, y1, 0],
                            stroke_width=0.8, stroke_color=RED, stroke_opacity=0.6,
                            fill_color=RED, fill_opacity=0.16))
        return out

    def build_plot(self):
        axes = VGroup(Line([SX0, SY0, 0], [SX1, SY0, 0], stroke_color=GREY, stroke_width=1.5),
                      Line([SX0, SY0, 0], [SX0, SY1, 0], stroke_color=GREY, stroke_width=1.5))
        ticks = VGroup(*[micro(f"{v}", 14).move_to([sx(v), SY0 - 0.28, 0])
                         for v in (60, 100, 140, 180)])
        xlab = micro("CUTTING SPEED · m/min").move_to([(SX0 + SX1) / 2, SY0 - 0.68, 0])
        ylab = micro("ROUGHNESS · µm").next_to([SX0, SY1, 0], UP, buff=0.12)
        ylab.align_to([SX0, 0, 0], LEFT)
        dots = VGroup(*[Dot([sx(v), sy(r), 0], radius=0.055, color=BLUE)
                        for v, r in zip(XS, YS)])
        return dict(axes=axes, ticks=ticks, xlab=xlab, ylab=ylab, dots=dots,
                    line=always_redraw(self.line), squares=always_redraw(self.squares))

    def build_parabola(self):
        bs = np.linspace(0, B_HI, 80)
        curve = VMobject(stroke_color=GREY, stroke_width=2).set_points_smoothly(
            [[px(b), py(sse(b)), 0] for b in bs])
        base = Line([PX0, PY0, 0], [PX1, PY0, 0], stroke_color=GREY, stroke_width=1.2)
        lab = micro("Σ RESIDUAL² BY SLOPE", 14).next_to([PX0, PY1, 0], UP, buff=0.18)
        lab.align_to([PX0, 0, 0], LEFT)
        within_frame(lab, "parabola label")
        dot = always_redraw(lambda: Dot([px(self.b.get_value()), py(sse(self.b.get_value())), 0],
                                        radius=0.07, color=INK))
        trace = TracedPath(dot.get_center, stroke_color=RED, stroke_width=3)
        return dict(curve=curve, base=base, lab=lab, dot=dot, trace=trace)

    def readouts(self):
        rows = [
            (micro("SLOPE · µm per m/min"),
             lambda: gauge(f"{self.b.get_value():.5f}", 24, INK)),
            (micro("Σ RESIDUAL²"),
             lambda: gauge(f"{sse(self.b.get_value()):.3f}", 24, RED)),
        ]
        out = []
        for i, (lab, val) in enumerate(rows):
            at_panel(lab, i, value=False)
            out += [lab, always_redraw(lambda val=val, i=i: at_panel(val(), i))]
        return out

    # ---------------- part 1: slide the line, watch the sum -----------------
    def part1_slide(self):
        title = prose("Level 11 · Relationships", 30, GREY).to_edge(UP, buff=0.38)
        g = self.build_plot()
        self.g = g
        with self.say("Twenty nine parts, each cut at a different speed, each with "
                      "its surface roughness measured. Faster cutting, rougher surface."):
            self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(g["axes"]), FadeIn(g["ticks"]),
                      FadeIn(g["xlab"]), FadeIn(g["ylab"]),
                      run_time=0.9, rate_func=rf.ease_out_sine)
            self.play(FadeIn(g["dots"], lag_ratio=0.06), run_time=2.2, rate_func=rf.ease_out_sine)

        with self.say("Which straight line describes them? Start with the laziest "
                      "one: flat, at the average roughness."):
            self.play(Create(g["line"]), run_time=1.2, rate_func=rf.ease_in_out_sine)

        with self.say("Every part misses the line by some amount. Square each miss, "
                      "and draw it as a square."):
            self.play(FadeIn(g["squares"]), run_time=1.2, rate_func=rf.ease_out_sine)

        p = self.build_parabola()
        self.p = p
        ro = self.readouts()
        self.ro = ro
        with self.say("Add up their areas. That sum is the score, and a smaller "
                      "sum is a better line."):
            self.play(*[FadeIn(m) for m in ro], run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(Create(p["base"]), FadeIn(p["lab"]), FadeIn(p["dot"]),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.add(p["trace"])

        with self.say("Now tilt the line about the centre of the cloud. The squares "
                      "shrink, and the sum falls.") as tr:
            self.play(self.b.animate.set_value(F["slope"] * 1.0),
                      run_time=max(3.0, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        with self.say("Keep tilting, past the cloud, and the squares grow again. "
                      "The sum comes back up.") as tr:
            self.play(self.b.animate.set_value(B_TOO),
                      run_time=max(3.0, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        with self.say("Every slope has a score, and the scores make a parabola. "
                      "It has exactly one floor.") as tr:
            self.play(Create(p["curve"]), run_time=max(1.6, tr.duration * 0.6),
                      rate_func=rf.ease_in_out_sine)

        with self.say("Bring the line back down to the floor.") as tr:
            self.play(self.b.animate.set_value(F["slope"]),
                      run_time=max(2.4, tr.duration * 0.9), rate_func=rf.ease_out_cubic)

        closed = MathTex(r"b", "=", r"\frac{S_{xy}}{S_{xx}}", font_size=46,
                         color=INK).move_to([-3.4, 1.4, 0])
        valued = MathTex(r"b", "=", rf"{F['slope']:.5f}", font_size=46,
                         color=TEAL).move_to(closed)
        with self.say("Nobody needs to slide anything. Set the slope of the parabola "
                      "to zero and the floor has a closed form: the cross products "
                      "over the squares of speed."):
            self.play(FadeIn(closed, shift=DOWN * 0.15), run_time=1.0, rate_func=rf.ease_out_sine)
        with self.say(f"Here that is {F['slope']:.5f} microns per metre a minute."):
            self.play(TransformMatchingShapes(closed, valued),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
        self.valued = valued

        # the one camera move: onto the floor, where the formula lands
        floor = Dot([px(F["slope"]), py(F["sse"]), 0], radius=0.05, color=YELLOW)
        self.camera.frame.save_state()
        with self.say("Look closely at the floor. The formula's slope sits at the "
                      "minimum, not near it. Any other line is worse, by an amount "
                      "you can compute.") as tr:
            self.play(self.camera.frame.animate.scale(0.38).move_to([px(F["slope"]), -1.65, 0]),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(floor, scale=1.6), run_time=0.8, rate_func=rf.ease_out_back)
            self.play(Circumscribe(floor, color=YELLOW, buff=0.06),
                      run_time=max(1.2, tr.duration * 0.3), rate_func=rf.ease_in_out_sine)
        with self.say("That is what least squares means. It is a claim about this "
                      "parabola, and you just watched it hold."):
            self.play(Restore(self.camera.frame), run_time=1.4, rate_func=rf.ease_in_out_sine)
        self.title = title

    # ---------------- part 2: the same squares give R² ----------------------
    def part2_ratio(self):
        r2 = (micro("R² · SHARE EXPLAINED"), lambda: gauge(f"{1 - sse(self.b.get_value()) / F['sst']:.3f}", 24, TEAL))
        with self.say("The flat line from the start was not wasted. Its squares are "
                      "the total variation, nine point zero three."):
            self.play(FadeOut(self.p["trace"]), self.b.animate.set_value(0.0),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)

        with self.say("The floor's squares are what the line leaves unexplained, "
                      "nought point two six.") as tr:
            self.play(self.b.animate.set_value(F["slope"]),
                      run_time=max(1.8, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        lab = at_panel(r2[0], 2, value=False)
        val = always_redraw(lambda: at_panel(r2[1](), 2))
        ratio = MathTex(r"R^2", "=", rf"1-\frac{{{F['sse']:.3f}}}{{{F['sst']:.3f}}}", "=", rf"{F['r2']:.3f}",
                        font_size=40, color=INK).move_to([-3.0, -0.2, 0]).shift(UP * 1.6)
        with self.say("One minus their ratio is R squared: the share of the total "
                      "variation the line accounts for, ninety seven per cent."):
            self.play(FadeOut(self.valued, shift=UP * 0.2), FadeIn(lab), FadeIn(val),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(FadeIn(ratio, shift=DOWN * 0.15), run_time=1.0, rate_func=rf.ease_out_sine)

        verdict = prose("the line is found, not drawn", 30, YELLOW).move_to([-1.8, 2.75, 0])
        within_frame(verdict, "verdict")
        with self.say("Regression, ANOVA, and the gauge study that comes next all "
                      "split this same total. The line is found, not drawn."):
            self.play(FadeOut(self.title, shift=UP * 0.12), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(FadeIn(verdict, shift=UP * 0.14), run_time=1.0, rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)
