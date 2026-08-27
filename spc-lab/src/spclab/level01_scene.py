"""LEVEL 1 act — 'Variation: nothing repeats, and the order matters.'

Written 2026-08-27 against specs/spc-manim-craft-contract.md and
specs/curriculum-arc-contract.md. What this act has to earn, since the five
existing levels already summarise variation with a mean and a sigma:

- **The span is produced by arrival.** A tracker admits parts one at a time and
  the readout is the range of the parts admitted so far, evaluated per frame.
  Nothing about "twelve parts cover forty-seven microns" is typed.
- **The histogram is shown to be a setting, not a fact.** A second tracker
  sweeps the bin width across the same 240 measurements and the shape changes
  from one lump to a comb. The instrument has a knob and the knob changes the
  answer.
- **The claim of the level is proved by a movement that leaves one thing still.**
  The same measurements are re-ordered from arrival order into sorted order —
  the run chart transforms, the histogram beside it cannot move, because it is
  the same numbers. Mean and spread readouts hold to two decimals while the
  longest-run readout goes 7 to 121. That is the argument for plotting in time
  order, made visually rather than asserted.
- **Tampering is derived, not stated.** Both funnel series are drawn from the
  same draws by a tracker walking the part number, with live sigma readouts that
  land on the exact √2 penalty.

Numbers come from spclab.variation, so this act, its two figure sheets, the page
and the test suite cannot disagree.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level01_scene.py Level01
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level01_scene.py Level01
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Dot, Group, Line, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Indicate, ReplacementTransform, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.narration import NarratedCameraScene
from spclab.variation import (
    ADJUST_EVERY, LEAVE_IT, TAMPER_SIGMA_RATIO_EXACT,
    TWELVE_CLOSEST_UM, TWELVE_DEV_UM, TWELVE_SPAN_UM,
    funnel, run_of_same_side, same_histogram_pair,
)

# The twelve parts are shared with Level 3, which puts a mean and a sigma on them.
# An earlier draft of this act invented its own twelve and claimed a 26 µm span
# while Level 3 claimed 47 µm about the same parts.
TWELVE = TWELVE_DEV_UM
GAUGE_STEP = TWELVE_CLOSEST_UM      # the gauge says nothing below this


class Level01(NarratedCameraScene):
    def construct(self):
        self.part1_nothing_repeats()
        self.part2_histogram_is_a_setting()
        self.part3_same_numbers_two_orders()
        self.part4_the_funnel()

    # ------------- part 1: the span is produced by arrival ----------------
    def part1_nothing_repeats(self):
        title = prose("Level 1 · nothing repeats", 30, GREY).to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-24, 32, 8], y_range=[0, 1, 1],
                    x_length=9.0, y_length=0.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5},
                    y_axis_config={"stroke_opacity": 0}).shift(LEFT * 1.2 + DOWN * 0.6)
        xlab = micro("DEVIATION FROM NOMINAL (µm)").next_to(axes, DOWN, buff=0.3)

        with self.say("Take twelve parts off one machine. Same tool, same operator, "
                      "same gauge, one after another."):
            self.play(Create(axes), FadeIn(xlab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        # a tracker admits parts; every readout below is a function of it
        k = ValueTracker(0.0)

        def admitted() -> np.ndarray:
            return TWELVE[:int(np.clip(np.floor(k.get_value() + 1e-9), 0, len(TWELVE)))]

        dots = always_redraw(lambda: VGroup(*[
            Dot(axes.c2p(v, 0.5), radius=0.075, color=BLUE) for v in admitted()]))
        lab_n = at_panel(micro("PARTS MEASURED"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(gauge(f"{len(admitted()):d} of 12", 26, INK), 0))
        lab_sp = at_panel(micro("SPAN, WORST TO BEST"), 1, value=False)

        def span_text() -> str:
            a = admitted()
            return f"{(a.max() - a.min()):.0f} µm" if len(a) > 1 else "—"

        val_sp = always_redraw(lambda: at_panel(gauge(span_text(), 26, TEAL), 1))
        self.add(dots, val_n, val_sp)
        self.play(FadeIn(lab_n), FadeIn(lab_sp), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say(f"Every reading is different, and nothing is broken. Watch the span "
                      f"open up as the parts arrive — twelve of them cover "
                      f"{TWELVE_SPAN_UM:.0f} microns, and the closest pair differs by "
                      f"{TWELVE_CLOSEST_UM:.0f} micron, which is exactly where this gauge stops."):
            self.play(k.animate.set_value(len(TWELVE) - 1),
                      run_time=max(3.4, 4.0), rate_func=rf.ease_in_out_sine)

        closest = at_panel(gauge(f"{GAUGE_STEP:.0f} µm", 26, YELLOW), 2)
        lab_res = at_panel(micro("GAUGE RESOLUTION"), 2, value=False)
        with self.say("Below that it has nothing to say."):
            self.play(FadeIn(lab_res), FadeIn(closest), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        verdict = prose("Spread is not a defect. It is what every process does.", 26, INK)
        verdict.next_to(axes, UP, buff=0.9).shift(LEFT * 0.1)
        with self.say("Spread is not a defect. It is what every real process does, and "
                      "the job is to describe it."):
            self.play(Write(verdict), run_time=1.3, rate_func=rf.linear)

        self.beat(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 2: the instrument has a knob ----------------------
    def part2_histogram_is_a_setting(self):
        title = prose("Level 1 · a histogram is an instrument", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        stable, _ = same_histogram_pair()
        lo, hi = float(stable.min()), float(stable.max())

        # y_range holds the tallest bar the sweep can produce (4 bins peaks at 98),
        # so no bar can leave the chart and collide with the title.
        axes = Axes(x_range=[-3.2, 3.2, 1], y_range=[0, 105, 25],
                    x_length=8.4, y_length=4.2, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 1.3 + DOWN * 0.45)
        xlab = micro("MEASUREMENT (σ)").next_to(axes, DOWN, buff=0.3)
        ylab = micro("COUNT").next_to(axes.y_axis.get_top(), RIGHT, buff=0.18)

        with self.say("Two hundred and forty measurements off one stable process, "
                      "piled into bins."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)

        nb = ValueTracker(14.0)

        def bars() -> VGroup:
            bins = int(np.clip(round(nb.get_value()), 3, 60))
            counts, edges = np.histogram(stable, bins=bins, range=(lo, hi))
            g = VGroup()
            for c, left_edge, right_edge in zip(counts, edges[:-1], edges[1:]):
                if c == 0:
                    continue
                p0 = axes.c2p(left_edge, 0)
                p1 = axes.c2p(right_edge, c)
                r = Rectangle(width=abs(p1[0] - p0[0]), height=abs(p1[1] - p0[1]),
                              stroke_width=1.0, stroke_color=GREY,
                              fill_color=TEAL, fill_opacity=0.72)
                r.move_to((p0 + p1) / 2)
                g.add(r)
            return g

        hist = always_redraw(bars)
        lab_b = at_panel(micro("BINS"), 0, value=False)
        val_b = always_redraw(lambda: at_panel(
            gauge(f"{int(np.clip(round(nb.get_value()), 3, 60)):d}", 26, YELLOW), 0))
        lab_w = at_panel(micro("BIN WIDTH"), 1, value=False)
        val_w = always_redraw(lambda: at_panel(gauge(
            f"{(hi - lo) / int(np.clip(round(nb.get_value()), 3, 60)):.2f} σ", 26, INK), 1))
        self.add(hist, val_b, val_w)
        self.play(FadeIn(lab_b), FadeIn(lab_w), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("The shape looks like a fact about the process. It is not. Bin "
                      "width is a setting on the instrument, and here is the same data "
                      "again with the knob turned down."):
            self.play(nb.animate.set_value(4.0), run_time=2.2, rate_func=rf.ease_in_out_sine)

        with self.say("Four bins says the process is a lump. Turn it the other way."):
            self.play(nb.animate.set_value(52.0), run_time=2.4, rate_func=rf.ease_in_out_sine)

        with self.say("Fifty two says it is a comb of spikes. Neither is the process. "
                      "Somewhere in between is a picture you can read."):
            self.play(nb.animate.set_value(14.0), run_time=1.8, rate_func=rf.ease_in_out_sine)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 3: the claim, proved by leaving one thing still ---
    def part3_same_numbers_two_orders(self):
        title = prose("Level 1 · the histogram throws away the order", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        stable, drifting = same_histogram_pair()
        n = len(stable)
        lo, hi = float(stable.min()), float(stable.max())

        run_ax = Axes(x_range=[0, n, 60], y_range=[-3.2, 3.2, 2],
                      x_length=6.3, y_length=2.5, tips=False,
                      axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                      ).shift(LEFT * 2.75 + UP * 1.15)
        run_lab = micro("PART NUMBER, IN THE ORDER MADE").next_to(run_ax, DOWN, buff=0.26)

        hist_ax = Axes(x_range=[-3.2, 3.2, 2], y_range=[0, 46, 20],
                       x_length=6.3, y_length=1.9, tips=False,
                       axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                       ).shift(LEFT * 2.75 + DOWN * 2.25)
        hist_lab = micro("THE SAME NUMBERS, IN BINS").next_to(hist_ax, DOWN, buff=0.26)

        counts, edges = np.histogram(stable, bins=14, range=(lo, hi))
        hist = VGroup()
        for c, le, re_ in zip(counts, edges[:-1], edges[1:]):
            if c == 0:
                continue
            p0, p1 = hist_ax.c2p(le, 0), hist_ax.c2p(re_, c)
            r = Rectangle(width=abs(p1[0] - p0[0]), height=abs(p1[1] - p0[1]),
                          stroke_width=1.0, stroke_color=GREY,
                          fill_color=TEAL, fill_opacity=0.72)
            r.move_to((p0 + p1) / 2)
            hist.add(r)

        dots = VGroup(*[Dot(run_ax.c2p(i + 1, v), radius=0.032, color=TEAL)
                        for i, v in enumerate(stable)])

        with self.say("Here are the measurements in the order they were made, and "
                      "underneath, the same measurements in bins."):
            self.play(Create(run_ax), Create(hist_ax), FadeIn(run_lab), FadeIn(hist_lab),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(dots, lag_ratio=0.004), run_time=1.1, rate_func=rf.ease_out_sine)
            self.play(FadeIn(hist), run_time=0.8, rate_func=rf.ease_out_sine)

        rows = [("MEAN", f"{stable.mean():+.2f} σ", INK),
                ("SPREAD", f"{stable.std(ddof=1):.2f} σ", INK),
                ("LONGEST RUN", f"{run_of_same_side(stable):d}", TEAL)]
        labels = VGroup(*[at_panel(micro(t), i, value=False) for i, (t, _, _) in enumerate(rows)])
        values = VGroup(*[at_panel(gauge(v, 26, c), i) for i, (_, v, c) in enumerate(rows)])
        with self.say("Three readouts: the mean, the spread, and the longest run on one "
                      "side of the mean."):
            self.play(FadeIn(labels), FadeIn(values), run_time=0.8, rate_func=rf.ease_out_sine)

        # the movement that proves the claim: re-order the same values
        with self.say("Now keep every single number and change nothing but the order "
                      "they arrived in. This is what a slow drift looks like written "
                      "down as it happened."):
            self.play(*[d.animate.move_to(run_ax.c2p(i + 1, v))
                        for d, (i, v) in zip(dots, enumerate(drifting))],
                      run_time=2.6, rate_func=rf.ease_in_out_sine)

        new_run = at_panel(gauge(f"{run_of_same_side(drifting):d}", 26, RED), 2)
        with self.say("The mean has not moved. The spread has not moved. The histogram "
                      "cannot move, because it is the same numbers. Only the run "
                      "readout changes, from seven to a hundred and twenty one."):
            self.play(ReplacementTransform(values[2], new_run), run_time=1.0,
                      rate_func=rf.ease_out_sine)
            self.play(Indicate(hist, scale_factor=1.03, color=TEAL), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)

        verdict = prose("Same histogram. One of these needs an engineer today.", 26, INK)
        # under the title is the only free band on this frame; shifted left so it
        # clears the readout column, which owns everything right of PANEL
        verdict.next_to(title, DOWN, buff=0.34).shift(LEFT * 1.15)
        with self.say("Same histogram, and one of those two processes needs an engineer "
                      "today. That is why every chart after this one is drawn in time "
                      "order."):
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 4: reacting to the wrong kind ---------------------
    def part4_the_funnel(self):
        title = prose("Level 1 · reacting to noise makes it worse", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        n = 140
        left = funnel(LEAVE_IT, n=n, seed=4)
        adjusted = funnel(ADJUST_EVERY, n=n, seed=4)
        lim = 4.6

        def panel(shift_y: float, label: str) -> tuple[Axes, VGroup]:
            ax = Axes(x_range=[0, n, 40], y_range=[-lim, lim, 2],
                      x_length=6.4, y_length=2.15, tips=False,
                      axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                      ).shift(LEFT * 2.7 + UP * shift_y)
            cap = micro(label).next_to(ax, UP, buff=0.2).align_to(ax, LEFT)
            return ax, VGroup(ax, cap)

        ax_a, grp_a = panel(1.55, "LEAVE THE STABLE PROCESS ALONE")
        ax_b, grp_b = panel(-1.85, "ADJUST AFTER EVERY PART")

        with self.say("Two runs of the same process, from the same random draws. The "
                      "only difference is what the operator does."):
            self.play(Create(grp_a), Create(grp_b), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        m = ValueTracker(1.0)

        def upto(series: np.ndarray) -> np.ndarray:
            return series[:int(np.clip(np.floor(m.get_value()), 1, n))]

        def line_for(series: np.ndarray, ax: Axes, colour: str):
            return always_redraw(lambda: VGroup(*[
                Line(ax.c2p(i + 1, v), ax.c2p(i + 2, w), stroke_width=1.8, stroke_color=colour)
                for i, (v, w) in enumerate(zip(upto(series)[:-1], upto(series)[1:]))]))

        self.add(line_for(left, ax_a, TEAL), line_for(adjusted, ax_b, RED))

        lab_a = at_panel(micro("SPREAD, LEFT ALONE"), 0, value=False)
        val_a = always_redraw(lambda: at_panel(
            gauge(f"{upto(left).std(ddof=1):.2f} σ" if len(upto(left)) > 1 else "—", 26, TEAL), 0))
        lab_b = at_panel(micro("SPREAD, ADJUSTED"), 1, value=False)
        val_b = always_redraw(lambda: at_panel(
            gauge(f"{upto(adjusted).std(ddof=1):.2f} σ" if len(upto(adjusted)) > 1 else "—",
                  26, RED), 1))
        self.add(val_a, val_b)
        self.play(FadeIn(lab_a), FadeIn(lab_b), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("The operator on the bottom chart corrects after every part, by "
                      "exactly what the last part was out by. It is the most reasonable "
                      "thing in the world, and watch the two spreads separate."):
            self.play(m.animate.set_value(float(n)), run_time=max(3.6, 4.2),
                      rate_func=rf.ease_in_out_sine)

        ratio = at_panel(gauge(f"×{TAMPER_SIGMA_RATIO_EXACT:.3f}", 26, YELLOW), 2)
        lab_r = at_panel(micro("PENALTY, FOR FREE"), 2, value=False)
        with self.say("Every correction adds the last part's noise to this one's. The "
                      "variance is exactly doubled, so the spread is root two times "
                      "wider — and the operator has been working hard all shift."):
            self.play(FadeIn(lab_r), FadeIn(ratio), run_time=0.8, rate_func=rf.ease_out_sine)

        verdict = prose("Noise is not a signal. Answering it adds variation.", 26, INK)
        # placed absolutely rather than relative to a chart: next_to(ax_b, DOWN) put it
        # off the bottom of the frame, and next_to(title, DOWN) put it on the upper
        # chart's caption. The charts span x -5.9 to 0.5, so this centres under them.
        verdict.move_to([-1.7, -3.52, 0])
        with self.say("Noise is not a signal, and answering it is how you add variation "
                      "rather than remove it. Telling the two apart is what the rest of "
                      "this curriculum is for."):
            self.play(Write(verdict), run_time=1.5, rate_func=rf.linear)

        self.beat(1.0)
