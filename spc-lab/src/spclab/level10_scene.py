"""LEVEL 10 act — 'For a count, the mean fixes the spread.'

Built 2026-10-07 against specs/l10-12-acts-contract.md (pilot) and the craft
rules in specs/spc-manim-craft-contract.md.

- The σ formula for a count becomes the one for a fraction by morph: the n
  slides under the root, nothing is retyped.
- The rate is a ValueTracker. The binomial bars, the ±3σ limits and the σ
  readout are all computed from it per frame (spclab.counting), so every σ on
  screen is produced by the movement.
- The lower limit runs into zero and stops; a dim ghost keeps going to where
  the arithmetic puts it, until it leaves the axis.
- Part 2 holds the rate and moves the size. The axis rescales from a tracker
  (the data zooms, not the camera); the one camera move is the close-up on the
  floor as the lower limit lifts off at n = 217.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level10_scene.py Level10
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level10_scene.py Level10
"""
from __future__ import annotations

import math

from manim import (
    DashedLine, Group, Line, MathTex, Rectangle, ValueTracker, VGroup,
    Circumscribe, Create, FadeIn, FadeOut, Restore, TransformMatchingShapes, Write,
    always_redraw,
    DOWN, LEFT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, ROWS, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose, within_frame,
)
from spclab.counting import K, N_CONST, N_FOR_LCL, P_BAR, p_limits
from spclab.narration import NarratedCameraScene

# the plot: data x (a fraction) maps onto [X0, X0 + L]; a strip left of zero
# (NEG of the range) is where the arithmetic puts a lower limit a chart cannot draw
X0, L, NEG = -6.3, 9.6, 0.12
BASE, TOP = -2.5, 1.1          # baseline and top of the limit lines
DENS = 0.085                   # units per unit of density (area under the bars is 1)
TICK_Y = -2.82


def pmf(n: int, p: float, k: int) -> float:
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log1p(-p))


class Level10(NarratedCameraScene):
    def construct(self):
        self.p = ValueTracker(P_BAR)
        self.n = ValueTracker(N_CONST)
        self.xmax = ValueTracker(0.65)
        self.part1_rate()
        self.part2_size()

    # ---------------- shared geometry, all driven by the trackers -----------
    def X(self, v: float) -> float:
        xm = self.xmax.get_value()
        lo = -NEG * xm
        return X0 + (v - lo) / (xm - lo) * L

    def lim(self) -> dict:
        return p_limits(int(round(self.n.get_value())), self.p.get_value(), K)

    def bars(self) -> VGroup:
        n, p = int(round(self.n.get_value())), self.p.get_value()
        mu, sd = n * p, math.sqrt(n * p * (1 - p))
        w = (self.X(1 / n) - self.X(0)) * 0.78
        out = VGroup()
        for k in range(max(0, int(mu - 6 * sd)), min(n, int(mu + 6 * sd) + 2)):
            h = pmf(n, p, k) * n * DENS
            if h < 0.01:
                continue
            out.add(Rectangle(width=w, height=h, stroke_width=0, fill_color=BLUE,
                              fill_opacity=0.85).move_to([self.X(k / n), BASE + h / 2, 0]))
        return out

    def vline(self, v: float, color=YELLOW, top=TOP, dashed=True, width=2.6):
        a, b = [self.X(v), BASE, 0], [self.X(v), top, 0]
        if dashed:
            return DashedLine(a, b, dash_length=0.12, stroke_color=color, stroke_width=width)
        return Line(a, b, stroke_color=color, stroke_width=width)

    def build_plot(self):
        axis = always_redraw(lambda: Line([X0, BASE, 0], [X0 + L, BASE, 0],
                                          stroke_color=GREY, stroke_width=1.5))
        # the strip below zero: no chart can draw a fraction here
        strip = always_redraw(lambda: Rectangle(
            width=self.X(0) - X0, height=TOP - BASE, stroke_width=0,
            fill_color=GREY, fill_opacity=0.10).move_to(
                [(X0 + self.X(0)) / 2, (BASE + TOP) / 2, 0]))
        strip_lab = micro("BELOW ZERO", 13).rotate(math.pi / 2)
        strip_lab.add_updater(lambda m: m.move_to([(X0 + self.X(0)) / 2, 0.2, 0]))

        bars = always_redraw(self.bars)
        centre = always_redraw(lambda: self.vline(self.p.get_value(), GREY, TOP - 0.3,
                                                  dashed=False, width=1.6))
        ucl = always_redraw(lambda: self.vline(self.lim()["ucl"]))
        lcl = always_redraw(lambda: self.vline(self.lim()["lcl"]))
        # where the arithmetic puts the lower limit; hidden once it leaves the axis
        # or rejoins the drawn one. Low on purpose, clear of the strip's label.
        ghost = always_redraw(lambda: (
            DashedLine([self.X(self.lim()["lcl_raw"]), BASE, 0],
                       [self.X(self.lim()["lcl_raw"]), BASE + 1.2, 0],
                       dash_length=0.08, stroke_color=GREY, stroke_width=2)
            if -NEG * self.xmax.get_value() < self.lim()["lcl_raw"] < -1e-4
            else VGroup()))

        ucl_tag = micro("UCL", 16, YELLOW)
        ucl_tag.add_updater(lambda m: m.move_to([self.X(self.lim()["ucl"]), TOP + 0.24, 0]))
        lcl_tag = micro("LCL", 16, YELLOW)
        lcl_tag.add_updater(lambda m: m.move_to([self.X(self.lim()["lcl"]), TOP + 0.24, 0]))

        xlab = micro("FRACTION DEFECTIVE IN ONE SUBGROUP").move_to([X0 + L / 2, -3.28, 0])
        coarse = self.ticks([i / 10 for i in range(7)], lambda v: f"{v * 100:.0f} %")
        fine = self.ticks([i / 50 for i in range(8)], lambda v: f"{v * 100:.0f} %")
        self.fine_on = ValueTracker(0.0)
        for t in coarse:
            t.add_updater(lambda m: m.set_opacity(m.vis() * (1 - self.fine_on.get_value())))
        for t in fine:
            t.add_updater(lambda m: m.set_opacity(m.vis() * self.fine_on.get_value()))
        return dict(axis=axis, strip=strip, strip_lab=strip_lab, bars=bars, centre=centre,
                    ucl=ucl, lcl=lcl, ghost=ghost, ucl_tag=ucl_tag, lcl_tag=lcl_tag,
                    xlab=xlab, coarse=coarse, fine=fine)

    def ticks(self, values, fmt) -> VGroup:
        out = VGroup()
        for v in values:
            t = micro(fmt(v), 14)
            t.v = v
            t.vis = (lambda t=t: 1.0 if 0 <= t.v <= self.xmax.get_value() * 1.001 else 0.0)
            t.add_updater(lambda m: m.move_to([self.X(m.v), TICK_Y, 0]))
            out.add(t)
        return out

    def readouts(self):
        rows = [
            (micro("RATE · SIZE n"),
             lambda: gauge(f"{self.p.get_value() * 100:.1f} % · {int(round(self.n.get_value()))}",
                           24, INK)),
            (micro("σ OF THE FRACTION"),
             lambda: gauge(f"{self.lim()['sigma'] * 100:.2f} %", 24, TEAL)),
            (micro("LOWER LIMIT · RAW"),
             lambda: gauge(self.lcl_text(), 24, YELLOW)),
        ]
        out = []
        for i, (lab, val) in enumerate(rows):
            at_panel(lab, i, value=False)
            out += [lab, always_redraw(lambda val=val, i=i: at_panel(val(), i))]
        return out

    def lcl_text(self) -> str:
        d = self.lim()
        if d["clamped"]:
            return f"0 · {d['lcl_raw'] * 100:.2f} %".replace("-", "−")
        return f"{d['lcl'] * 100:.2f} %"

    # ---------------- part 1: the rate is the spread -------------------------
    def part1_rate(self):
        title = prose("Level 10 · Counting, not measuring", 30, GREY).to_edge(UP, buff=0.38)
        with self.say("Levels three to five spent their time estimating a spread, "
                      "because for a measurement the spread is a separate fact "
                      "about the process."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9, rate_func=rf.ease_out_sine)

        count = MathTex(r"\sigma_{\text{count}}", "=", r"\sqrt{n\,\bar p\,(1-\bar p)}",
                        font_size=52, color=INK).move_to([0, 0.4, 0])
        with self.say("Count defective items instead, and that stops being true. "
                      "Out of n items the number defective is binomial, and its "
                      "standard deviation is the square root of n, times p bar, "
                      "times one minus p bar.") as tr:
            self.play(Write(count), run_time=max(2.0, tr.duration * 0.5), rate_func=rf.linear)

        frac = MathTex(r"\sigma_{\hat p}", "=", r"\sqrt{\bar p\,(1-\bar p)\,/\,n}",
                       font_size=52, color=INK).move_to(count)
        with self.say("Divide by n to turn the count into a fraction, and the n "
                      "moves under the root."):
            self.play(TransformMatchingShapes(count, frac),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)

        with self.say("Nothing on the right is a separate spread. The rate and the "
                      "subgroup size fix it, and nobody gets to choose it."):
            self.play(Circumscribe(frac[2], color=TEAL, buff=0.08),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)

        g = self.build_plot()
        self.g = g
        with self.say("Here is a subgroup of two hundred items at four per cent "
                      "defective: how often each fraction turns up."):
            self.play(FadeIn(g["axis"]), FadeIn(g["strip"]), FadeIn(g["strip_lab"]),
                      FadeIn(g["xlab"]), FadeIn(g["coarse"]), FadeIn(g["fine"]),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(frac.animate.scale(44 / 52).move_to([-1.3, 2.2, 0]),
                      FadeIn(g["bars"], shift=UP * 0.3), FadeIn(g["centre"]),
                      run_time=1.2, rate_func=rf.ease_out_cubic)

        with self.say("Three sigma either side gives the limits."):
            self.play(Create(g["ucl"]), Create(g["lcl"]),
                      FadeIn(g["ucl_tag"]), FadeIn(g["lcl_tag"]),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)
            self.add(g["ghost"])

        ro = self.readouts()
        with self.say("Now move the rate, and only the rate. The spread follows it, "
                      "because the rate is the spread.") as tr:
            self.play(*[FadeIn(m) for m in ro], run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(self.p.animate.set_value(0.5),
                      run_time=max(3.0, tr.duration * 0.75), rate_func=rf.ease_in_out_sine)

        with self.say("At fifty per cent the scatter is as wide as it can ever get."):
            self.play(Circumscribe(ro[3], color=TEAL, buff=0.08),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        with self.say("Bring the rate down to two per cent and the band closes up. "
                      "The lower limit runs into zero and stops there.") as tr:
            self.play(self.p.animate.set_value(0.02),
                      run_time=max(3.0, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        with self.say("The arithmetic puts it below zero, at minus one per cent. "
                      "A chart cannot draw a negative fraction, so it draws zero, "
                      "and a limit at zero can never be crossed."):
            self.play(Circumscribe(ro[5], color=YELLOW, buff=0.08),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)

        with self.say("That is why a chart for counts has no range chart beside it. "
                      "There is no separate spread to chart."):
            self.play(self.p.animate.set_value(P_BAR), FadeOut(frac, shift=UP * 0.2),
                      run_time=2.2, rate_func=rf.ease_in_out_sine)
        self.title = title

    # ---------------- part 2: the size, and the floor -----------------------
    def part2_size(self):
        g = self.g
        with self.say("Now hold the rate at four per cent, and change the size of "
                      "the subgroup instead.") as tr:
            self.play(self.xmax.animate.set_value(0.14), self.fine_on.animate.set_value(1.0),
                      run_time=max(2.4, tr.duration * 0.8), rate_func=rf.ease_in_out_cubic)

        with self.say("Fifty items per subgroup, and the band opens wide.") as tr:
            self.play(self.n.animate.set_value(50),
                      run_time=max(2.4, tr.duration * 0.85), rate_func=rf.ease_in_out_sine)

        with self.say("Two hundred, and it closes. A bigger subgroup gives a "
                      "steadier fraction, so when the size changes from one "
                      "subgroup to the next, the limits have to breathe with it.") as tr:
            self.play(self.n.animate.set_value(N_CONST),
                      run_time=max(3.0, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)

        rule = MathTex(r"n\bar p \ge 5", r"\;\Rightarrow\;", r"n = 125",
                       font_size=40, color=GREY).move_to([-1.3, 2.2, 0])
        with self.say("Even at two hundred the lower limit is stuck at zero. The "
                      "rule of thumb says n p bar of five is enough, which here "
                      "is a hundred and twenty five items."):
            self.play(FadeIn(rule, shift=DOWN * 0.15), run_time=1.0, rate_func=rf.ease_out_sine)

        exact = MathTex(r"n\bar p > 9(1-\bar p)", r"\;\Rightarrow\;", rf"n = {N_FOR_LCL}",
                        font_size=40, color=YELLOW).move_to(rule)
        with self.say("The arithmetic says otherwise. The limit clears zero only "
                      f"from {N_FOR_LCL}.") as tr:
            self.play(TransformMatchingShapes(rule, exact),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)
            self.play(self.n.animate.set_value(N_FOR_LCL),
                      run_time=max(1.6, tr.duration * 0.4), rate_func=rf.ease_out_sine)

        # the one camera move: in on the floor, where the limit leaves the wall
        zoom = 0.58  # frame 4.64 tall: ticks at -2.82 and tags at 1.34 both fit
        self.camera.frame.save_state()
        floor_x = self.X(0)
        with self.say("Look closely at the floor. Above that size, every item you "
                      "add buys a real lower limit: a chart that can tell you the "
                      "process got better.") as tr:
            self.play(self.camera.frame.animate.scale(zoom).move_to([floor_x + 2.6, -0.75, 0]),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)
            self.play(self.n.animate.set_value(400),
                      run_time=max(2.6, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)

        verdict = prose("a limit at zero is not a limit", 30, YELLOW)
        verdict.move_to([0, 2.2, 0])
        within_frame(verdict, "verdict")
        with self.say("A limit at zero is not a limit. Size the subgroup so the "
                      "chart can signal both ways."):
            self.play(Restore(self.camera.frame), FadeOut(exact, shift=UP * 0.2),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(verdict, shift=UP * 0.14), run_time=1.0, rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)
