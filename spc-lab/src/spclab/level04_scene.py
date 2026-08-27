"""LEVEL 1 act — 'Variation is predictable.'

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 3, with
the patterns Level II proved:

- Flatness is **derived by motion**. The old act jumped between five static
  histograms (`with self.say(line): pass` — nothing animated at all). Now a
  ValueTracker walks the roll count from 1 to 10,000 on a log scale while the
  bars and a live `OFF FLAT` readout follow it, so the law of large numbers is
  something you watch happen rather than a caption claiming it happened.
- σx̄ = σ/√n is **derived twice and never asserted**: first as two readouts that
  agree (measured spread of k-dice averages against σ₁/√k), then as a dot
  riding the 1/√n curve with the spread read off it continuously.
- The formula arrives by **morph** from those two agreeing numbers, and the
  substitution n = 25 is a `TransformMatchingTex`, term into term.
- One camera move, on the flat end of the curve, where the point is that the
  next part buys almost nothing. Type is authored at native size and scaled.

Pacing still lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level04_scene.py Level04
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level04_scene.py Level04
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, MathTex, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, ReplacementTransform, Restore, TransformMatchingTex,
    Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.narration import NarratedCameraScene

FLAT = 1.0 / 6.0
ROLLS = 10_000


def dice_bins(k, max_bars=55):
    """Bin edges aligned to the 1/k lattice the average of k dice can land on.

    Averages of k dice are discrete — multiples of 1/k. Bins that straddle that
    lattice unevenly put a comb of false notches through the bell, so each bin
    here spans a whole number of lattice steps.
    """
    if k == 1:
        return np.arange(0.5, 7.5, 1.0)
    step = 1.0 / k
    step *= max(1, int(np.ceil(5.0 / (max_bars * step))))
    return np.arange(1.0 - step / 2, 6.0 + step, step)


def hist_bars(axes, values, bins, color):
    """Density histogram of `values`, peak-normalised, sitting on the x-axis."""
    dens, edges = np.histogram(values, bins=bins, density=True)
    peak = dens.max()
    if peak > 0:
        dens = dens / peak
    bars = VGroup()
    for d, lo, hi in zip(dens, edges[:-1], edges[1:]):
        left, right = axes.c2p(lo, 0), axes.c2p(hi, 0)
        top = axes.c2p(lo, max(float(d), 0.004))
        bar = Rectangle(width=(right[0] - left[0]) * 0.94,
                        height=max(top[1] - left[1], 0.02),
                        stroke_width=0, fill_color=color, fill_opacity=0.85)
        bar.move_to((left + right) / 2, aligned_edge=DOWN)
        bars.add(bar)
    return bars


class Level04(NarratedCameraScene):
    def construct(self):
        self.part1_dice()
        self.part2_averaging()
        self.part3_sqrtn()

    # ------------------------------------------ part 1: one die, many rolls
    def part1_dice(self):
        rng = np.random.default_rng(4)
        rolls = rng.integers(1, 7, size=ROLLS)
        onehot = np.zeros((ROLLS, 6))
        onehot[np.arange(ROLLS), rolls - 1] = 1.0
        cum = np.cumsum(onehot, axis=0)          # counts after n rolls

        def share(n: int) -> np.ndarray:
            return cum[min(max(n, 1), ROLLS) - 1] / float(min(max(n, 1), ROLLS))

        title = prose("Level 4 · one part is noise, many parts are information",
                      28, GREY).to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0.4, 6.6, 1], y_range=[0, 0.52, 0.1],
                    x_length=9.0, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.7 + DOWN * 0.45)
        xlab = micro("FACE").next_to(axes, DOWN, buff=0.26)
        flat = DashedLine(axes.c2p(0.4, FLAT), axes.c2p(6.6, FLAT),
                          dash_length=0.12, stroke_color=YELLOW, stroke_width=2)
        flat_tag = micro("1/6", 18, YELLOW).next_to(flat, LEFT, buff=0.14)

        with self.say("One part tells you almost nothing. Many parts obey a law. "
                      "Start with the simplest part there is: one die, six faces, "
                      "all equally likely."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(Create(flat), FadeIn(flat_tag),
                      run_time=0.8, rate_func=rf.ease_in_out_sine)

        # log10 of the roll count. The sweep starts at ten rolls, not one: with
        # one roll a single face holds the whole probability and its bar is
        # three times the height of the axis, which either clips (a lie about
        # the shape) or forces a y-range that makes 1/6 invisible at 10,000.
        lg = ValueTracker(1.0)

        def face_bars() -> VGroup:
            props = share(int(round(10 ** lg.get_value())))
            bars = VGroup()
            for i, p in enumerate(props):
                lo, hi = i + 0.62, i + 1.38
                left, right = axes.c2p(lo, 0), axes.c2p(hi, 0)
                top = axes.c2p(lo, max(float(p), 1e-4))
                bars.add(Rectangle(width=right[0] - left[0],
                                   height=max(top[1] - left[1], 0.012),
                                   stroke_width=0, fill_color=BLUE,
                                   fill_opacity=0.85)
                         .move_to((left + right) / 2, aligned_edge=DOWN))
            return bars

        def off_flat(n: int) -> float:
            """Worst face's distance from one sixth, as a percentage of it."""
            return float(np.max(np.abs(share(n) - FLAT)) / FLAT * 100.0)

        live_bars = always_redraw(face_bars)
        lab_rolls = at_panel(micro("ROLLS"), 0, value=False)
        val_rolls = always_redraw(lambda: at_panel(
            gauge(f"{int(round(10 ** lg.get_value())):>6,}", 26, BLUE), 0))
        lab_off = at_panel(micro("WORST FACE, OFF 1/6"), 1, value=False)
        val_off = always_redraw(lambda: at_panel(
            gauge(f"{off_flat(int(round(10 ** lg.get_value()))):5.1f} %", 26, YELLOW), 1))

        with self.say("Ten rolls tell you nothing: the worst face is out by two "
                      "hundred percent. Keep rolling, and watch that distance.") as tr:
            self.play(FadeIn(live_bars), FadeIn(lab_rolls), FadeIn(val_rolls),
                      FadeIn(lab_off), FadeIn(val_off),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(lg.animate.set_value(4.0),
                      run_time=max(4.0, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        # the readout's own last value becomes the finding, by morph
        settled = gauge(f"{off_flat(ROLLS):.1f} % off flat at 10,000 rolls",
                        24, YELLOW).move_to([-5.9, 2.95, 0], aligned_edge=LEFT)
        with self.say("Ten thousand rolls, and the worst face is within a few "
                      "percent of one sixth. Nobody arranged that. It is what "
                      "randomness does in bulk."):
            travelling = val_off.copy().clear_updaters()
            self.remove(val_off)
            self.play(ReplacementTransform(travelling, settled),
                      FadeOut(lab_off, shift=RIGHT * 0.2),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        note = prose("predictable in bulk — and still one die at a time",
                     26, TEAL).move_to(DOWN * 3.55)
        with self.say("Predictable in bulk. But this is still one die at a time, "
                      "and one die is flat. Nothing here looks like a bell."):
            self.play(FadeIn(note, shift=UP * 0.12),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        self.beat(0.6)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # -------------------------------- part 2: average k dice, twice measured
    def part2_averaging(self):
        rng = np.random.default_rng(0)
        draws = rng.integers(1, 7, size=(60_000, 30))
        sd1 = float(draws[:, 0].std())

        title = prose("…now average the dice instead of counting them", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0.5, 6.5, 1], y_range=[0, 1.06, 0.25],
                    x_length=9.0, y_length=4.0, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.7 + DOWN * 0.55)
        xlab = micro("AVERAGE OF THE SUBGROUP").next_to(axes, DOWN, buff=0.26)
        centre = DashedLine(axes.c2p(3.5, 0), axes.c2p(3.5, 1.02),
                            dash_length=0.12, stroke_color=GREY, stroke_width=1.5)

        # k is continuous only so the prediction *curve* can narrow smoothly
        # between panels. The readouts step with the panels instead of tracking
        # the tween: a subgroup size of 7.4 does not exist, and a readout that
        # says "k = 7" beside a spread computed from 7.4 is lying by rounding.
        kk = ValueTracker(1.0)
        predicted = always_redraw(lambda: axes.plot(
            lambda x: float(np.exp(-((x - 3.5) ** 2) / (2 * (sd1 / np.sqrt(kk.get_value())) ** 2))),
            x_range=[0.5, 6.5, 0.05], color=YELLOW, stroke_width=3))

        lab_k = at_panel(micro("SUBGROUP SIZE"), 0, value=False)
        lab_meas = at_panel(micro("MEASURED σ"), 1, value=False)
        # no subscript digits in a mono label: Plex Mono has no ₁ and Pango
        # falls back to another face mid-string
        lab_pred = at_panel(micro("PREDICTED  σ / √k"), 2, value=False)

        panels = [
            (1, BLUE, "One die is the baseline: every face equally likely, no "
                      "shape at all."),
            (2, TEAL, "Average two of them and the flat top is already gone."),
            (5, TEAL, "Average five, and there is a shape where there was none."),
            (30, TEAL, "Thirty, and it is a bell. Nothing about a die is bell "
                       "shaped. The averaging did this."),
        ]

        bars = val_k = val_meas = val_pred = None
        for k, colour, line in panels:
            values = draws[:, 0] if k == 1 else draws[:, :k].mean(axis=1)
            new_bars = hist_bars(axes, values, dice_bins(k), colour)
            new_k = at_panel(gauge(f"k = {k:>2}", 26, INK), 0)
            new_meas = at_panel(gauge(f"{float(values.std()):.3f}", 26, TEAL), 1)
            new_pred = at_panel(gauge(f"{sd1 / np.sqrt(k):.3f}", 26, YELLOW), 2)

            with self.say(line) as tr:
                if bars is None:
                    self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes),
                              FadeIn(xlab), FadeIn(centre),
                              run_time=0.9, rate_func=rf.ease_in_out_sine)
                    self.play(FadeIn(new_bars, shift=UP * 0.2),
                              FadeIn(lab_k), FadeIn(new_k),
                              FadeIn(lab_meas), FadeIn(new_meas),
                              run_time=1.0, rate_func=rf.ease_out_sine)
                else:
                    self.play(ReplacementTransform(bars, new_bars),
                              ReplacementTransform(val_k, new_k),
                              ReplacementTransform(val_meas, new_meas),
                              kk.animate.set_value(float(k)),
                              run_time=max(1.4, tr.duration * 0.55),
                              rate_func=rf.ease_in_out_sine)
                    if val_pred is None:
                        # the normal prediction only means anything once we are
                        # averaging, and only after k has actually moved: a bell
                        # of one die's spread over a uniform histogram claims
                        # something false about one die.
                        self.play(FadeIn(lab_pred), FadeIn(new_pred),
                                  FadeIn(predicted),
                                  run_time=0.6, rate_func=rf.ease_out_sine)
                    else:
                        self.play(ReplacementTransform(val_pred, new_pred),
                                  run_time=0.5, rate_func=rf.ease_in_out_sine)
            bars, val_k, val_meas = new_bars, new_k, new_meas
            val_pred = new_pred

        # the two agreeing readouts become the law they were agreeing with
        law = MathTex(r"\sigma_{\bar{x}}", "=", r"\frac{\sigma}{\sqrt{n}}",
                      font_size=54, color=INK).move_to(UP * 0.45)
        with self.say("Two numbers, measured separately, agreeing to three "
                      "decimals: the spread of the averages, and one die's "
                      "spread divided by the root of the count."):
            self.play(val_meas.animate.set_color(TEAL), val_pred.animate.set_color(TEAL),
                      run_time=0.8, rate_func=rf.ease_in_out_sine)
        with self.say("That agreement is the law. Sigma of x bar equals sigma "
                      "over root n."):
            self.play(FadeOut(bars, shift=DOWN * 0.3), FadeOut(centre),
                      FadeOut(predicted), FadeOut(axes), FadeOut(xlab),
                      run_time=0.8, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(VGroup(val_meas, val_pred), law),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        self.beat(0.7)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------------------------------- part 3: what √n actually buys you
    def part3_sqrtn(self):
        title = prose("…and root n is what averaging buys", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[1, 25, 4], y_range=[0, 1.06, 0.25],
                    x_length=9.0, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.7 + DOWN * 0.40)
        xlab = micro("SUBGROUP SIZE n").next_to(axes, DOWN, buff=0.26)
        ylab = micro("σ OF THE MEAN").next_to(axes.y_axis.get_top(), RIGHT, buff=0.18)
        law = MathTex(r"\sigma_{\bar{x}}", "=", r"\frac{\sigma}{\sqrt{n}}",
                      font_size=40, color=INK).move_to([4.9, 2.95, 0])

        with self.say("Put subgroup size along the bottom and the spread of the "
                      "mean up the side, with sigma set to one."):
            self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(law),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)

        # The curve is continuous because the function is. The rider and the
        # readouts snap to whole n, because a subgroup of 1.53 parts does not
        # exist — and a readout printing "n = 2" beside 1/√1.53 = 0.808 is a
        # rounding lie. So the dot hops integer to integer along a smooth curve.
        n = ValueTracker(1.0)

        def whole_n() -> int:
            return int(round(n.get_value()))

        traced = always_redraw(lambda: axes.plot(
            lambda x: 1.0 / np.sqrt(x), x_range=[1, max(n.get_value(), 1.02), 0.05],
            color=BLUE, stroke_width=3))
        rider = always_redraw(lambda: Dot(
            axes.c2p(whole_n(), 1.0 / np.sqrt(whole_n())),
            radius=0.075, color=YELLOW))
        drop = always_redraw(lambda: DashedLine(
            axes.c2p(whole_n(), 0),
            axes.c2p(whole_n(), 1.0 / np.sqrt(whole_n())),
            dash_length=0.1, stroke_color=GREY, stroke_width=1.6))

        lab_n = at_panel(micro("SUBGROUP SIZE"), 1, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"n = {whole_n():>2}", 26, INK), 1))
        lab_s = at_panel(micro("σ OF THE MEAN"), 2, value=False)
        val_s = always_redraw(lambda: at_panel(
            gauge(f"{1.0 / np.sqrt(whole_n()):.3f} σ", 26, YELLOW), 2))

        with self.say("Now walk the subgroup size up from one to twenty five and "
                      "read the spread of the mean off the curve as it goes.") as tr:
            self.play(FadeIn(traced), FadeIn(rider), FadeIn(drop),
                      FadeIn(lab_n), FadeIn(val_n), FadeIn(lab_s), FadeIn(val_s),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(n.animate.set_value(25.0),
                      run_time=max(3.4, tr.duration * 0.75), rate_func=rf.ease_in_out_sine)

        law_25 = MathTex(r"\sigma_{\bar{x}}", "=", r"\frac{\sigma}{5}",
                         font_size=40, color=INK).move_to([4.9, 2.95, 0])
        with self.say("Twenty five parts, and the spread of the mean is a fifth "
                      "of one part's spread. The root is doing all the work."):
            self.play(TransformMatchingTex(law, law_25),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        # One camera move, on the flat end, where the next part buys nothing.
        # Everything sized for the wide frame leaves first: a magnifier that
        # also magnifies the labels is just a bigger picture, and 26pt type
        # blown up 2.2x is the tell.
        zoom = 0.45
        chrome = Group(title, law_25, lab_n, val_n, lab_s, val_s, xlab, ylab)
        self.camera.frame.save_state()
        with self.say("But look at the shape of what you are buying."):
            for m in (val_n, val_s):
                m.clear_updaters()
            self.play(FadeOut(chrome), run_time=0.6, rate_func=rf.ease_in_sine)
            self.play(self.camera.frame.animate.scale(zoom).move_to(axes.c2p(20, 0.30)),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        d1 = 1.0 - 1.0 / np.sqrt(2)
        d24 = 1.0 / np.sqrt(24) - 1.0 / np.sqrt(25)
        cost = VGroup(
            gauge(f"n 1 → 2 buys  {d1:.3f} σ", 24, TEAL),
            gauge(f"n 24 → 25 buys  {d24:.3f} σ", 24, YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).scale(zoom)
        cost.move_to(axes.c2p(20, 0.52))
        with self.say("The second part halves your uncertainty. The twenty fifth "
                      "part buys four thousandths of a sigma. Averaging is "
                      "cheap at the start and almost free of value at the end."):
            self.play(FadeIn(cost, shift=UP * 0.1 * zoom),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        with self.say("Which is why subgroups of four and five are everywhere, "
                      "and subgroups of fifty are not."):
            self.play(Restore(self.camera.frame), FadeOut(cost),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(Group(title, law_25, xlab, ylab)),
                      run_time=0.6, rate_func=rf.ease_out_sine)

        payoff = prose("this is why a chart watches means, not parts", 28, TEAL)
        payoff.move_to(DOWN * 3.55)
        with self.say("And it is why a control chart plots subgroup means. A "
                      "shift that hides inside single parts moves a mean far "
                      "enough to see."):
            self.play(FadeIn(payoff, shift=UP * 0.12),
                      run_time=1.1, rate_func=rf.ease_out_sine)

        self.beat(1.0)
