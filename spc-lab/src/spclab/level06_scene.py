"""LEVEL 2 act — 'Control limits are a hypothesis test.'

Rebuilt 2026-08-26 against specs/spc-manim-craft-contract.md. What changed and
why, because the diff alone will not say it:

- 99.73 % is **produced by a movement**, not typed. A ValueTracker sweeps the
  limits outward while the filled area and a live readout follow them; the
  readout is `erf(k/√2)` evaluated per frame, so the number arrives as the
  result of the sweep and exists nowhere in the act before it.
- The 0.27 % tail is **revealed by exaggeration** — the vertical axis stretches
  ×70 and the wings grow out of the baseline. The peak leaves the top of frame
  on purpose: clamping it draws a flat-topped box, which is a lie about a bell.
- The odds are **restated by morph**: the two wing labels converge into 0.27 %,
  which becomes 1 false alarm in 370 subgroups. Nothing already derived is
  written on screen a second time.
- Every play() carries a deliberate rate_func, and in-frame text is set in the
  site's own two voices (EB Garamond prose, IBM Plex Mono readouts). Maths is
  Computer Modern, per the contract's default 3.

Build rules carried from the style test, all of them earned:
  * type is authored at native size and .scale()d — magnifying small type with
    the camera destroys Pango's glyph metrics;
  * Transform leaves the *source* as the survivor, so replacements go through
    ReplacementTransform;
  * corners are reserved explicitly (they collide at 1920px), and no label sits
    on the mark it labels.

Pacing still lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level06_scene.py Level06
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level06_scene.py Level06
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, Line, MathTex, Polygon, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, LaggedStart, ReplacementTransform, Restore,
    TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, RED, TEAL, YELLOW,
    gauge, micro, norm_pdf, phi, prose,
)
from spclab.formulas import inside
from spclab.narration import NarratedCameraScene


class Level06(NarratedCameraScene):
    def construct(self):
        self.part1_derive()
        self.part2_chart()

    # ---------------- part 1: derive the number, then the odds -------------
    def part1_derive(self):
        title = prose("Level 6 · ±3σ is not taste, it is a bet", 30, GREY)
        title.to_edge(UP, buff=0.38)
        with self.say("Three sigma is not a matter of taste. It is a bet, and "
                      "we can price it exactly."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.9, rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-4.2, 4.2, 1], y_range=[0, 0.48, 0.2],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.55)
        # no x̄ in a mono string: Plex Mono places the combining macron badly
        # and it reads as a typo. Garamond sets it correctly, so H₀ keeps it.
        xlab = micro("SUBGROUP MEAN  (UNITS OF σ)").next_to(axes, DOWN, buff=0.28)
        ylab = micro("DENSITY").next_to(axes.y_axis.get_top(), RIGHT, buff=0.20)
        xs = np.linspace(-4.2, 4.2, 421)
        curve = axes.plot_line_graph(xs, norm_pdf(xs), add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]
        hyp = prose("H₀: the process is unchanged — every x̄ is drawn from this curve",
                    22, TEAL).move_to(DOWN * 3.62)

        # the curve is drawn inside this beat, not the next one: holding an
        # empty pair of axes for the length of a spoken line is dead air.
        with self.say("Level four told us which distribution every subgroup mean "
                      "is drawn from, assuming nothing has changed."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.play(Create(curve), run_time=2.0, rate_func=rf.ease_in_out_sine)

        with self.say("That curve is the null hypothesis. Not an assumption about "
                      "the parts, but a claim about the process: it is unchanged."):
            self.play(FadeIn(hyp, shift=UP * 0.12), run_time=1.0, rate_func=rf.ease_out_sine)

        # ---- the sweep. k drives the limits, the fill and the readout ----
        k = ValueTracker(0.55)

        # coarse grid for the per-frame fill: the contract measured per-frame
        # updaters at ~5x render cost, so the polygon is 169 points, not 421.
        xf = np.linspace(-4.2, 4.2, 169)
        pf = norm_pdf(xf)

        def region(kv: float) -> Polygon:
            m = np.abs(xf) < kv
            pts = ([axes.c2p(-kv, phi(kv))]
                   + [axes.c2p(a, b) for a, b in zip(xf[m], pf[m])]
                   + [axes.c2p(kv, phi(kv))])
            return Polygon(*pts, axes.c2p(kv, 0), axes.c2p(-kv, 0),
                           fill_color=TEAL, fill_opacity=0.35, stroke_width=0)

        def limit(sign: int) -> DashedLine:
            # full height, not up to the curve: at k = 3 the density is 0.004,
            # so a line drawn to the curve is invisible exactly when it matters.
            def build(sign=sign):
                kv = k.get_value()
                return DashedLine(axes.c2p(sign * kv, 0), axes.c2p(sign * kv, 0.44),
                                  dash_length=0.13, stroke_color=YELLOW, stroke_width=2.6)
            return always_redraw(build)

        live_fill = always_redraw(lambda: region(k.get_value()))
        lim_l, lim_r = limit(-1), limit(+1)

        lab_limit = micro("LIMIT").move_to([PANEL, 2.95, 0], aligned_edge=LEFT)
        val_limit = always_redraw(lambda: gauge(f"± {k.get_value():.2f} σ", 26, YELLOW)
                                  .move_to([PANEL, 2.52, 0], aligned_edge=LEFT))
        lab_area = micro("AREA INSIDE").move_to([PANEL, 1.92, 0], aligned_edge=LEFT)
        val_area = always_redraw(lambda: gauge(f"{100 * inside(k.get_value()):.2f} %", 26, TEAL)
                                 .move_to([PANEL, 1.49, 0], aligned_edge=LEFT))

        with self.say("So put a pair of limits on it and sweep them outward from "
                      "the centre. The readout is not a table: it is the integral "
                      "of that curve between the limits, evaluated as they move.") as tr:
            self.play(FadeIn(live_fill), FadeIn(lim_l), FadeIn(lim_r),
                      FadeIn(lab_limit), FadeIn(val_limit),
                      FadeIn(lab_area), FadeIn(val_area),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            # two stages so the last hundredths crawl: the number has to be
            # readable on the way, not just at the end.
            self.play(k.animate.set_value(2.90),
                      run_time=max(2.0, tr.duration * 0.50), rate_func=rf.ease_in_out_sine)
            self.play(k.animate.set_value(3.00),
                      run_time=max(1.2, tr.duration * 0.28), rate_func=rf.ease_out_sine)

        # the derived number leaves the readout and lands on the area it measures
        settled = gauge("99.73 %", 40, TEAL).move_to(axes.c2p(0, 0.115))
        with self.say("Ninety nine point seven three percent. Nobody chose that "
                      "number. It is what plus and minus three sigma is worth."):
            travelling = val_area.copy().clear_updaters()
            self.remove(val_area)
            self.play(ReplacementTransform(travelling, settled),
                      FadeOut(lab_area, shift=RIGHT * 0.2),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        # ---- reveal the tails by exaggeration ----
        s = ValueTracker(1.0)

        def stretched(base):
            return always_redraw(lambda: base.copy().stretch(
                max(s.get_value(), 1e-4), dim=1, about_point=axes.c2p(0, 0)))

        def wing(lo: float, hi: float) -> Polygon:
            m = (xf >= lo) & (xf <= hi)
            pts = [axes.c2p(a, b) for a, b in zip(xf[m], pf[m])]
            return Polygon(*pts, axes.c2p(hi, 0), axes.c2p(lo, 0),
                           fill_color=RED, fill_opacity=0.8, stroke_width=0)

        wing_l, wing_r = wing(-4.2, -3.0), wing(3.0, 4.2)
        live_curve = stretched(curve)
        live_wing_l, live_wing_r = stretched(wing_l), stretched(wing_r)

        filed = gauge("99.73 % inside", 22, TEAL).move_to([-5.35, 3.30, 0], aligned_edge=LEFT)
        lab_axis = micro("VERTICAL AXIS").move_to([PANEL, 1.92, 0], aligned_edge=LEFT)
        val_axis = always_redraw(lambda: gauge(f"× {s.get_value():.1f}", 26, GREY)
                                 .move_to([PANEL, 1.49, 0], aligned_edge=LEFT))

        with self.say("Everything the process should ever do lives inside. The whole "
                      "of the rest is out here in the tails, and at this scale you "
                      "cannot see it at all.") as tr:
            self.play(ReplacementTransform(settled, filed),
                      FadeOut(live_fill),
                      FadeOut(title, shift=UP * 0.2),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.remove(curve)
            self.add(live_curve, live_wing_l, live_wing_r)
            self.play(FadeIn(lab_axis), FadeIn(val_axis),
                      run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("So stretch the vertical axis and let them grow. The peak goes "
                      "straight out of frame — that is the point. The tails are "
                      "seventy times smaller than anything else on this chart.") as tr:
            self.play(s.animate.set_value(70.0),
                      run_time=max(2.4, tr.duration * 0.66), rate_func=rf.ease_in_out_sine)

        # clear of the wings and of the ±3σ limit lines: at ×70 the wing tip
        # reaches y = 0.06, so the labels sit outboard at 0.6 and touch nothing.
        w_l = gauge("0.135 %", 24, RED).move_to([-4.9, 0.6, 0])
        w_r = gauge("0.135 %", 24, RED).move_to([4.9, 0.6, 0])
        with self.say("Each wing is one tenth of one percent of everything, and there "
                      "are two of them."):
            self.play(FadeIn(w_l, shift=UP * 0.18), FadeIn(w_r, shift=UP * 0.18),
                      run_time=0.9, rate_func=rf.ease_out_sine)

        # ---- the equation, term into term ----
        eq_a = MathTex(r"P(|z|>3)", "=",
                       r"1-\operatorname{erf}\!\left(\tfrac{3}{\sqrt{2}}\right)",
                       font_size=38, color=INK).move_to(UP * 2.30)
        with self.say("Together they are the tail integral, and it has a closed form."):
            self.play(Write(eq_a), run_time=1.3, rate_func=rf.linear)

        eq_b = MathTex(r"P(|z|>3)", "=", "0.0027",
                       font_size=38, color=INK).move_to(UP * 2.30)
        with self.say("Evaluate it: zero point zero zero two seven."):
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        # ---- restate the same quantity as odds, by morph ----
        odds = gauge("0.27 %", 34, RED).move_to(DOWN * 3.55)
        with self.say("Which is the two wings added together."):
            self.play(FadeOut(hyp, shift=DOWN * 0.25),
                      run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(VGroup(w_l, w_r), odds),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        arl = gauge("1 false alarm in 370 subgroups", 28, RED).move_to(DOWN * 3.55)
        with self.say("Invert it and the bet is priced. Zero point two seven percent "
                      "is one false alarm in three hundred and seventy subgroups. A "
                      "point outside the limit is that bet, taken."):
            self.play(ReplacementTransform(odds, arl),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        self.beat(0.8)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 2: the same test wearing a chart's clothes ----------
    def part2_chart(self):
        title = prose("…so the chart is that same test, run on every subgroup", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0, 40, 10], y_range=[-3.8, 3.8, 1],
                    x_length=10.4, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        # below the whole axes, not below x_axis: with y_range ±3.8 the x-axis
        # line runs through the middle of the plot, among the points.
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        cl = Line(axes.c2p(0, 0), axes.c2p(40, 0), stroke_color=GREY, stroke_width=2)

        # centre line lands with the title, for the same reason as part 1
        with self.say("A control chart is simply that same test, run again on "
                      "every subgroup, forever."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(cl), FadeIn(xlab), run_time=1.1, rate_func=rf.ease_in_out_sine)

        with self.say("The limits are the boundary we just drew, turned on its side."):
            for v in (3, -3):
                ln = DashedLine(axes.c2p(0, v), axes.c2p(40, v), dash_length=0.13,
                                stroke_color=YELLOW, stroke_width=2.6)
                tag = micro("UCL" if v > 0 else "LCL", 18, YELLOW).next_to(ln, RIGHT, buff=0.14)
                self.play(Create(ln), FadeIn(tag), run_time=0.55, rate_func=rf.ease_out_sine)

        # 36 subgroups from a stable process, then one genuine shift
        rng = np.random.default_rng(31)
        pts = list(rng.normal(0, 1, 36)) + [4.1]
        dots = VGroup(*[
            Dot(axes.c2p(i + 1, min(v, 3.75)), radius=0.055,
                color=RED if abs(v) > 3 else BLUE)
            for i, v in enumerate(pts)
        ])
        with self.say("Every point inside is the process agreeing with the null "
                      "hypothesis. This is what boring looks like, and boring is "
                      "the goal.") as tr:
            self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots[:36]],
                                  lag_ratio=0.55),
                      run_time=max(2.2, tr.duration * 0.72), rate_func=rf.linear)

        # one camera move: in on the breach. Type is authored at native size and
        # scaled by the same factor as the frame, never magnified small type.
        zoom = 0.55
        self.camera.frame.save_state()
        with self.say("Then one point steps outside."):
            self.play(FadeIn(dots[36], scale=1.6), run_time=0.6, rate_func=rf.ease_out_back)
            self.play(self.camera.frame.animate.scale(zoom).move_to(axes.c2p(31, 1.4)),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)

        with self.say("Four point one sigma above the centre line, where the null "
                      "hypothesis allows one point in three hundred and seventy."):
            read = gauge("MEAN = +4.10 σ", 26, RED).scale(zoom)
            read.next_to(dots[36], LEFT, buff=0.18 * zoom)
            self.play(FadeIn(read, shift=RIGHT * 0.1 * zoom),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        with self.say("So this is not a bad part, and scrapping it changes nothing."):
            # the readout was sized for the zoomed frame; it goes back with it
            self.play(Restore(self.camera.frame), FadeOut(read),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        verdict = prose("evidence against H₀ — go and find what changed", 28, RED)
        verdict.move_to(DOWN * 3.45)
        with self.say("It is evidence against the hypothesis that nothing changed. "
                      "The correct response is to go and find what did."):
            self.play(FadeIn(verdict, shift=UP * 0.14), run_time=1.1, rate_func=rf.ease_out_sine)

        self.beat(1.0)
