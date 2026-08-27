"""LEVEL 3 act — 'Capability is comparing two distributions.'

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 3.

The old act stated its indices. Cp appeared as `Write(Text("Cp = ... = 1.33"))`
and Cpk as another typed line, which is the same defect the contract found in
Level II: the number is asserted, and a curriculum whose claim is *derived, not
asserted* cannot afford that. What replaces it:

- **Cp is derived by motion.** A ValueTracker shrinks the process spread while
  the curve, the 6σ dimension bar and a live `Cp = tolerance / 6σ` readout all
  follow it. Cp arrives as the value the movement stops on.
- **Cpk is derived by the drift.** A second tracker walks the mean off centre.
  The spread never changes, so Cp holds still at 1.33 while CPU, CPL and Cpk
  fall continuously — the whole point of the index, watched rather than stated.
- **The leak is revealed by exaggeration**, the pattern Level II proved: the
  vertical axis stretches so a 6,000 ppm tail stops being an invisible sliver.
  The peak leaves frame on purpose.
- **ppm is restated by morph** into '1 in N parts', and every figure comes from
  `spclab.ppm_from_cpk` at render time — the same function the tests check.
- Part 2 replaces the four-row typed table with a swept curve: Cpk walks from
  0.60 to 2.00 and the ppm it implies is plotted as it goes, so the table's
  four rows become four dots on a curve the viewer watched being drawn.

Pacing still lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level08_scene.py Level08
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level08_scene.py Level08
"""
from __future__ import annotations

import math

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, Line, MathTex, Polygon, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, ReplacementTransform, TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.formulas import ppm_from_cpk
from spclab.narration import NarratedCameraScene

LSL, USL = 49.7, 50.3
CENTRE = 50.0
TOL = USL - LSL
SG_END = 0.075          # the spread the sweep settles on: Cp = 0.6/0.45 = 1.33
DRIFT_END = 0.12        # how far the mean walks off centre


def pdf(xs, mu, sg):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


def ppm_words(ppm: float) -> str:
    """ppm as a count of parts, without pretending to precision it lacks."""
    if ppm <= 0:
        return "never"
    one_in = 1e6 / ppm
    if one_in >= 1e6:
        return f"1 in {one_in / 1e6:.1f} million parts"
    return f"1 in {round(one_in):,} parts"


def ppm_compact(ppm: float) -> str:
    """The same fact as ppm_words, short enough for the readout column.

    The verbose form ran off the right edge of the frame at Cpk 2.0, where
    one part in a billion needs eleven characters it does not have.
    """
    if ppm <= 0:
        return "never"
    one_in = 1e6 / ppm
    if one_in >= 1e9:
        return f"1 in {one_in / 1e9:.1f} B"
    if one_in >= 1e6:
        return f"1 in {one_in / 1e6:.1f} M"
    if one_in >= 1e4:
        return f"1 in {one_in / 1e3:.0f} k"
    return f"1 in {round(one_in):,}"


class Level08(NarratedCameraScene):
    def construct(self):
        self.part1_two_voices()
        self.part2_promise()

    # ------------- part 1: two voices, then Cp, then the drift --------------
    def part1_two_voices(self):
        title = prose("Level 8 · two voices, one axis", 28, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[49.55, 50.45, 0.2], y_range=[0, 7.0, 2],
                    x_length=9.4, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.55 + DOWN * 0.55)
        xlab = micro("MILLIMETRES").next_to(axes, DOWN, buff=0.26)

        with self.say("Capability compares two distributions. One belongs to the "
                      "customer, one belongs to the process, and they are drawn "
                      "on the same axis in millimetres."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)

        specs = VGroup(*[
            DashedLine(axes.c2p(v, 0), axes.c2p(v, 6.6), dash_length=0.13,
                       stroke_color=YELLOW, stroke_width=2.6)
            for v in (LSL, USL)
        ])
        # below the axis, not above the lines: the row above the spec tops is
        # where the tolerance dimension bar goes
        spec_tags = VGroup(
            micro("LSL", 18, YELLOW).next_to(axes.c2p(LSL, 0), DOWN, buff=0.30),
            micro("USL", 18, YELLOW).next_to(axes.c2p(USL, 0), DOWN, buff=0.30),
        )
        voice_c = prose("the customer: “anything between these lines”", 24, YELLOW)
        voice_c.move_to(DOWN * 3.62)
        with self.say("The customer speaks in limits. Anything between these two "
                      "lines is accepted, and nothing outside them is."):
            self.play(Create(specs), FadeIn(spec_tags), FadeIn(voice_c),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        # ---- Cp derived by motion: the spread shrinks, the ratio follows ----
        sg = ValueTracker(0.155)      # starts barely capable: Cp = 0.65
        xs = np.linspace(49.55, 50.45, 241)

        def curve_at(mu: float, s: float, colour=TEAL):
            return axes.plot_line_graph(xs, pdf(xs, mu, s), add_vertex_dots=False,
                                        line_color=colour, stroke_width=3)["line_graph"]

        live_curve = always_redraw(lambda: curve_at(CENTRE, sg.get_value()))
        six_bar = always_redraw(lambda: Line(
            axes.c2p(CENTRE - 3 * sg.get_value(), 6.0),
            axes.c2p(CENTRE + 3 * sg.get_value(), 6.0),
            stroke_color=BLUE, stroke_width=3))
        tol_bar = Line(axes.c2p(LSL, 6.9), axes.c2p(USL, 6.9),
                       stroke_color=YELLOW, stroke_width=3)

        lab_tol = at_panel(micro("TOLERANCE"), 0, value=False)
        val_tol = at_panel(gauge(f"{TOL:.2f} mm", 26, YELLOW), 0)
        lab_six = at_panel(micro("6σ OF PROCESS"), 1, value=False)
        val_six = always_redraw(lambda: at_panel(
            gauge(f"{6 * sg.get_value():.2f} mm", 26, BLUE), 1))
        lab_cp = at_panel(micro("Cp = TOL / 6σ"), 2, value=False)
        val_cp = always_redraw(lambda: at_panel(
            gauge(f"{TOL / (6 * sg.get_value()):.2f}", 26, INK), 2))

        voice_p = prose("the process: “this is my natural spread”", 24, TEAL)
        voice_p.move_to(DOWN * 3.62)
        with self.say("The process answers with a spread. It never read the "
                      "drawing, and at this width it does not fit."):
            self.play(FadeOut(voice_c, shift=DOWN * 0.2),
                      run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(FadeIn(live_curve), FadeIn(six_bar), Create(tol_bar),
                      FadeIn(voice_p),
                      run_time=1.1, rate_func=rf.ease_out_sine)
            self.play(FadeIn(lab_tol), FadeIn(val_tol), FadeIn(lab_six),
                      FadeIn(val_six), FadeIn(lab_cp), FadeIn(val_cp),
                      run_time=0.7, rate_func=rf.ease_out_sine)

        with self.say("Now improve the process and watch the only number that "
                      "matters here: the tolerance divided by six sigma. That "
                      "ratio is Cp, and it is pure geometry.") as tr:
            self.play(sg.animate.set_value(0.0855),
                      run_time=max(2.2, tr.duration * 0.5), rate_func=rf.ease_in_out_sine)
            self.play(sg.animate.set_value(SG_END),
                      run_time=max(1.2, tr.duration * 0.28), rate_func=rf.ease_out_sine)

        filed_cp = gauge("Cp = 1.33 centred", 22, INK)
        filed_cp.move_to([-6.1, 2.95, 0], aligned_edge=LEFT)
        with self.say("One point three three. The natural spread is now three "
                      "quarters of the tolerance, and there is room on both sides."):
            travelling = val_cp.copy().clear_updaters()
            self.remove(val_cp)
            self.play(ReplacementTransform(travelling, filed_cp),
                      FadeOut(lab_cp, shift=RIGHT * 0.2),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        # ---- Cpk derived by the drift: same spread, worse process ----------
        drift = ValueTracker(0.0)
        self.remove(live_curve, six_bar)
        live_curve = always_redraw(lambda: curve_at(CENTRE + drift.get_value(), SG_END))
        live_six = always_redraw(lambda: Line(
            axes.c2p(CENTRE + drift.get_value() - 3 * SG_END, 6.0),
            axes.c2p(CENTRE + drift.get_value() + 3 * SG_END, 6.0),
            stroke_color=BLUE, stroke_width=3))
        self.add(live_curve, live_six)

        def cpu() -> float:
            return (USL - (CENTRE + drift.get_value())) / (3 * SG_END)

        def cpl() -> float:
            return ((CENTRE + drift.get_value()) - LSL) / (3 * SG_END)

        lab_cpu = at_panel(micro("CPU  (near USL)"), 1, value=False)
        val_cpu = always_redraw(lambda: at_panel(gauge(f"{cpu():.2f}", 26, RED), 1))
        lab_cpk = at_panel(micro("Cpk = min(CPU, CPL)"), 2, value=False)
        val_cpk = always_redraw(lambda: at_panel(
            gauge(f"{min(cpu(), cpl()):.2f}", 26, RED), 2))

        drift_note = prose("the spread has not changed — only the centring has",
                           24, GREY).move_to(DOWN * 3.62)
        with self.say("Now let the mean drift, and change nothing else. The "
                      "spread stays exactly where it was.") as tr:
            self.play(FadeOut(voice_p, shift=DOWN * 0.2), FadeIn(drift_note),
                      FadeOut(lab_six), FadeOut(val_six),
                      run_time=0.6, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(lab_cpu), FadeIn(val_cpu),
                      FadeIn(lab_cpk), FadeIn(val_cpk),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(drift.animate.set_value(DRIFT_END),
                      run_time=max(2.6, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)

        # the leaking tail: real, and invisible at this scale
        stretch = ValueTracker(1.0)
        mu_end = CENTRE + DRIFT_END
        xs_tail = xs[xs >= USL]
        tail = Polygon(*[axes.c2p(a, b) for a, b in zip(xs_tail, pdf(xs_tail, mu_end, SG_END))],
                       axes.c2p(float(xs_tail[-1]), 0), axes.c2p(USL, 0),
                       fill_color=RED, fill_opacity=0.85, stroke_width=0)
        base_curve = curve_at(mu_end, SG_END)

        def stretched(base):
            return always_redraw(lambda: base.copy().stretch(
                max(stretch.get_value(), 1e-4), dim=1, about_point=axes.c2p(CENTRE, 0)))

        cpk_end = min((USL - mu_end) / (3 * SG_END), (mu_end - LSL) / (3 * SG_END))
        ppm_end = ppm_from_cpk(cpk_end)

        lab_ppm = at_panel(micro("PARTS PAST USL"), 0, value=False)
        val_ppm = at_panel(gauge(f"{ppm_end:,.0f} ppm", 26, RED), 0)
        lab_x = at_panel(micro("VERTICAL AXIS"), 1, value=False)
        val_x = always_redraw(lambda: at_panel(
            gauge(f"× {stretch.get_value():.0f}", 26, GREY), 1))

        # The spoken figures are interpolated, not typed: the old act said
        # "zero point eight nine" while its own label computed 0.80, which is
        # exactly the failure this rebuild exists to remove.
        with self.say("Cpk keeps the smaller of the two one sided ratios, because "
                      f"the near limit is the one you fail first. {cpk_end:.2f}, "
                      "and the near side is now leaking parts."):
            self.play(FadeOut(lab_cpu), FadeOut(val_cpu), FadeOut(lab_tol),
                      FadeOut(val_tol), FadeOut(drift_note),
                      run_time=0.6, rate_func=rf.ease_in_sine)
            self.remove(live_curve)
            self.add(stretched(base_curve), stretched(tail))
            self.play(FadeIn(lab_ppm), FadeIn(val_ppm),
                      run_time=0.7, rate_func=rf.ease_out_sine)

        # x20 puts the tail's tallest point near the top of the axis; the peak
        # is 5.3 density units and goes 90 units up, which is the intention.
        with self.say(f"That leak is {ppm_end:,.0f} parts per million, and at this "
                      "scale you cannot see it. So stretch the vertical axis "
                      "until it is visible. The peak leaves the frame; the tail "
                      "is what we came for.") as tr:
            self.play(FadeIn(lab_x), FadeIn(val_x),
                      run_time=0.5, rate_func=rf.ease_out_sine)
            self.play(stretch.animate.set_value(20.0),
                      run_time=max(2.4, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)

        # ppm restated as parts, by morph — no new number written
        as_parts = gauge(ppm_words(ppm_end), 30, RED).move_to(DOWN * 3.55)
        with self.say(f"{ppm_end:,.0f} parts per million is the same sentence as "
                      f"{ppm_words(ppm_end)}."):
            self.play(ReplacementTransform(val_ppm.copy(), as_parts),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        eq_a = MathTex(r"C_{pk}", "=",
                       r"\frac{\mathrm{USL}-\mu}{3\sigma}",
                       font_size=38, color=INK).move_to(UP * 2.35)
        eq_b = MathTex(r"C_{pk}", "=", f"{cpk_end:.2f}",
                       font_size=38, color=INK).move_to(UP * 2.35)
        with self.say("And the index itself is only the near gap measured in "
                      "three sigmas."):
            self.play(Write(eq_a), run_time=1.3, rate_func=rf.linear)
        with self.say(f"Which for this drifted process is {cpk_end:.2f}."):
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        self.beat(0.7)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ---------------- part 2: every Cpk is a defect promise -----------------
    def part2_promise(self):
        title = prose("…and every Cpk is a promise about defect rate", 30, GREY)
        title.to_edge(UP, buff=0.38)

        # log ppm on the y axis, because the interesting range spans five
        # decades: Cpk 0.6 is 36,000 ppm and Cpk 2.0 is one part in a billion.
        axes = Axes(x_range=[0.6, 2.0, 0.2], y_range=[-3, 5, 1],
                    x_length=9.0, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.7 + DOWN * 0.35)
        xlab = micro("Cpk").next_to(axes, DOWN, buff=0.26)
        ylab = micro("ppm OUTSIDE THE NEAR LIMIT (log)").next_to(
            axes.y_axis.get_top(), RIGHT, buff=0.18)

        def log_ppm(c: float) -> float:
            return math.log10(max(ppm_from_cpk(c), 1e-4))


        c = ValueTracker(0.6)
        traced = always_redraw(lambda: axes.plot(
            log_ppm, x_range=[0.6, max(c.get_value(), 0.605), 0.01],
            color=TEAL, stroke_width=3))
        rider = always_redraw(lambda: Dot(
            axes.c2p(c.get_value(), log_ppm(c.get_value())), radius=0.075, color=YELLOW))

        lab_c = at_panel(micro("Cpk"), 0, value=False)
        val_c = always_redraw(lambda: at_panel(
            gauge(f"{c.get_value():.2f}", 26, INK), 0))
        lab_p = at_panel(micro("EXPECTED DEFECTS"), 1, value=False)

        def ppm_text() -> str:
            p = ppm_from_cpk(c.get_value())
            return f"{p:,.0f} ppm" if p >= 100 else (f"{p:.1f} ppm" if p >= 1 else f"{p:.2f} ppm")

        val_p = always_redraw(lambda: at_panel(gauge(ppm_text(), 26, RED), 1))
        lab_w = at_panel(micro("IN PLAIN COUNTING"), 2, value=False)
        val_w = always_redraw(lambda: at_panel(
            gauge(ppm_compact(ppm_from_cpk(c.get_value())), 24, RED), 2))

        # the axes, the rider and all three readouts land inside the opening
        # line: axes alone under a twelve-second sentence is dead air
        with self.say("Every Cpk value is a promise about defect rate, and the "
                      "promise is steep. Parts per million up the side, on a "
                      "logarithmic scale, because it spans five decades."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(rider), FadeIn(lab_c), FadeIn(val_c),
                      FadeIn(lab_p), FadeIn(val_p), FadeIn(lab_w), FadeIn(val_w),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        # the walk starts inside this line: a ten-second sentence over a frozen
        # readout is the same dead air as an empty axis
        with self.say("Walk Cpk upward from zero point six. Every figure here is "
                      "computed at render time by the same function the test "
                      "suite checks — nothing is read off a table.") as tr:
            self.play(FadeIn(traced), run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(c.animate.set_value(0.80),
                      run_time=max(1.8, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)

        # each milestone is marked when the sweep arrives on it, and the spoken
        # figure is the computed one, so the words cannot drift from the curve
        marks = VGroup()
        for target, colour, tail_line in (
            (1.00, YELLOW, "the number that means the limit sits three sigma out"),
            (1.33, TEAL, "the number most customers ask for"),
            (1.67, BLUE, "and the curve is falling off a cliff"),
        ):
            ppm_t = ppm_from_cpk(target)
            shown = f"{ppm_t:,.0f}" if ppm_t >= 100 else f"{ppm_t:.2f}"
            with self.say(f"Cpk {target:.2f}, {tail_line}: {shown} parts per "
                          f"million, or {ppm_words(ppm_t)}.") as tr:
                self.play(c.animate.set_value(target),
                          run_time=max(1.5, tr.duration * 0.5),
                          rate_func=rf.ease_in_out_sine)
                dot = Dot(axes.c2p(target, log_ppm(target)), radius=0.06, color=colour)
                tag = micro(f"{target:.2f}", 18, colour).next_to(dot, UP, buff=0.14)
                marks.add(dot, tag)
                self.play(FadeIn(dot, scale=0.5), FadeIn(tag),
                          run_time=0.5, rate_func=rf.ease_out_back)

        with self.say("Which is why the difference between one point three three "
                      "and one point six seven is not a rounding argument. It is "
                      "two orders of magnitude of scrap."):
            self.play(c.animate.set_value(2.0),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)

        verdict = prose("a capability index is a defect rate wearing a friendlier number",
                        26, TEAL).move_to(DOWN * 3.55)
        with self.say("A capability index is a defect rate wearing a friendlier "
                      "number. Change the formula and this curve changes with it."):
            self.play(FadeIn(verdict, shift=UP * 0.12),
                      run_time=1.1, rate_func=rf.ease_out_sine)

        self.beat(1.0)
