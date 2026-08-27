"""LEVEL 2 act — 'Chance: what a probability is a statement about.'

Written 2026-08-28 against specs/spc-manim-craft-contract.md and
specs/curriculum-arc-contract.md. What this act has to earn: Level 6 will price
±3σ at 99.73 %, and almost every misuse of a control chart is a misreading of
what such a percentage claims. So this level is about the claim, not the curve.

- **The proportion arrives by arrival.** A tracker admits flips one at a time and
  the rate readout is the heads-so-far over flips-so-far, evaluated per frame.
  Nothing about "one half" is typed; it is where the readout stops moving.
- **The law of averages is refuted by one sequence read twice.** The same flips
  drive two panels at once: the surplus of heads over tails, which grows along
  its exact envelope, and the proportion, which converges. One tracker feeds
  both, so the two readings cannot be accused of being two experiments.
- **The exact form morphs into its asymptote**, rather than a second equation
  being typed beside the first.
- **Independence is shown as an absence.** Six bars, one per streak length, all
  landing on one half — the interesting thing is that nothing happens.
- **Expectation is a balance point that is not a face.** A fulcrum slides under
  six equal weights and settles at 3.5, which no die can show.
- **The punchline is derived, not stated.** A tracker walks the subgroup count
  while the accumulated false-alarm chance follows it, and stops at the very
  number the phrase "one alarm in 370" contains — 63 %, not 100 %.

Numbers come from spclab.chance, which quotes α and the average run length from
the modules that already publish them, so this act, its two figure sheets, the
page and the test suite cannot disagree.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level02_scene.py Level02
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level02_scene.py Level02
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Dot, Group, Line, MathTex, Rectangle, Triangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Indicate, Restore, TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.chance import (
    ALPHA, ARL0, DIE_FACES, MEDIAN_WAIT, MEMORY, MEMORY_WORST, MILESTONES,
    ONE_MINUS_1_OVER_E, P_IN_ARL0, P_IN_SHIFT, SHIFT_SUBGROUPS, STREAKS,
    die_expectation, expected_gap_exact, expected_rate_error, flips,
    p_any_alarm,
)
from spclab.narration import NarratedCameraScene

# The act reads the same sequence the sheets draw.
SEQ_N = 10_000
LOG_MAX = np.log10(SEQ_N)

# A per-frame redraw of ten thousand points costs five times the render for no
# visible gain; the curves are sampled on a log grid instead. The craft contract
# measured that cost, so this is a rule rather than a preference.
GRID = np.unique(np.geomspace(1, SEQ_N, 220).astype(int))


class Level02(NarratedCameraScene):
    def construct(self):
        self.part1_long_run()
        self.part2_gap_and_rate()
        self.part3_no_memory()
        self.part4_expectation()
        self.part5_what_the_rate_claims()

    # --------- part 1: a proportion is a long-run frequency ---------------
    def part1_long_run(self):
        title = prose("Level 2 · a probability is not a property of a part", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        seq = flips(320, seed=11)
        n_show = len(seq)

        axes = Axes(x_range=[0, n_show, 80], y_range=[0, 1, 0.25],
                    x_length=9.0, y_length=3.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.2 + DOWN * 0.55)
        xlab = micro("FLIPS").next_to(axes, DOWN, buff=0.28)
        ylab = micro("PROPORTION HEADS").next_to(axes.y_axis, UP, buff=0.18)
        half = axes.plot(lambda _: 0.5, x_range=[0, n_show], stroke_color=YELLOW,
                         stroke_width=2.0)
        half_tag = micro("ONE HALF", 16, YELLOW).next_to(
            axes.c2p(n_show, 0.5), RIGHT, buff=0.12)

        with self.say("A fair coin. Not a claim about any one flip — no single flip "
                      "is ever half a head."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        k = ValueTracker(1.0)

        def upto() -> np.ndarray:
            return seq[:max(1, int(k.get_value()))]

        def rate() -> float:
            s = upto()
            return float((s > 0).sum()) / len(s)

        trace = always_redraw(lambda: axes.plot_line_graph(
            np.arange(1, len(upto()) + 1),
            np.cumsum(upto() > 0) / np.arange(1, len(upto()) + 1),
            add_vertex_dots=False, line_color=BLUE, stroke_width=3)["line_graph"])

        lab_n = at_panel(micro("FLIPS SEEN"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(gauge(f"{len(upto()):d}", 26, INK), 0))
        lab_r = at_panel(micro("HEADS SO FAR"), 1, value=False)
        val_r = always_redraw(lambda: at_panel(
            gauge(f"{(upto() > 0).sum():d}", 26, INK), 1))
        lab_p = at_panel(micro("PROPORTION"), 2, value=False)
        val_p = always_redraw(lambda: at_panel(gauge(f"{rate():.3f}", 26, TEAL), 2))

        self.add(trace, val_n, val_r, val_p)
        self.play(FadeIn(lab_n), FadeIn(lab_r), FadeIn(lab_p), run_time=0.5,
                  rate_func=rf.ease_out_sine)

        with self.say("Flip it once and the proportion of heads is nought or one. "
                      "Flip it again and again, and the proportion goes wherever "
                      "the flips send it."):
            self.play(k.animate.set_value(40), run_time=2.6, rate_func=rf.linear)

        with self.say("Keep going. It stops wandering, and it settles."):
            self.play(Create(half), FadeIn(half_tag), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.play(k.animate.set_value(n_show), run_time=3.4,
                      rate_func=rf.ease_out_sine)

        verdict = prose("A probability is a long-run frequency.", 26, INK)
        verdict.next_to(axes, UP, buff=0.62).shift(LEFT * 0.1)
        with self.say("That settling is the whole definition. A probability is a "
                      "long-run frequency — a statement about what a repeated "
                      "process does, and never about the next flip."):
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------- part 2: one sequence, two readings — the law of averages -----
    def part2_gap_and_rate(self):
        title = prose("Level 2 · the gap grows, the rate settles", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        seq = flips(SEQ_N)
        gap_all = np.abs(np.cumsum(seq))
        rate_all = np.cumsum(seq > 0) / np.arange(1, SEQ_N + 1)

        top = Axes(x_range=[0, LOG_MAX, 1], y_range=[0, 120, 40],
                   x_length=8.4, y_length=2.15, tips=False,
                   axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        top.shift(LEFT * 1.35 + UP * 1.42)
        bot = Axes(x_range=[0, LOG_MAX, 1], y_range=[0, 1, 0.5],
                   x_length=8.4, y_length=2.15, tips=False,
                   axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        bot.shift(LEFT * 1.35 + DOWN * 1.52)

        t_lab = micro("| HEADS − TAILS |").next_to(top.y_axis, UP, buff=0.14)
        b_lab = micro("PROPORTION HEADS").next_to(bot.y_axis, UP, buff=0.14)
        x_lab = micro("FLIPS — 1, 10, 100, 1 000, 10 000").next_to(bot, DOWN, buff=0.26)
        half = bot.plot(lambda _: 0.5, x_range=[0, LOG_MAX], stroke_color=YELLOW,
                        stroke_width=1.8)

        with self.say("Now the same sequence, read two ways at once. Above, the "
                      "surplus of heads over tails. Below, the proportion. One set "
                      "of flips feeds both."):
            self.play(Create(top), Create(bot), FadeIn(t_lab), FadeIn(b_lab),
                      FadeIn(x_lab), Create(half), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        k = ValueTracker(1.0)

        def grid_upto() -> np.ndarray:
            return GRID[GRID <= max(1, int(k.get_value()))]

        gap_curve = always_redraw(lambda: _poly(
            top, np.log10(grid_upto()), gap_all[grid_upto() - 1], BLUE))
        rate_curve = always_redraw(lambda: _poly(
            bot, np.log10(grid_upto()), rate_all[grid_upto() - 1], BLUE))

        envelope = _poly(top, np.log10(GRID),
                         np.array([expected_gap_exact(int(n)) for n in GRID]), YELLOW)
        err_hi = _poly(bot, np.log10(GRID),
                       0.5 + np.array([expected_rate_error(int(n)) for n in GRID]), TEAL)
        err_lo = _poly(bot, np.log10(GRID),
                       0.5 - np.array([expected_rate_error(int(n)) for n in GRID]), TEAL)

        lab_g = at_panel(micro("SURPLUS"), 0, value=False)
        val_g = always_redraw(lambda: at_panel(
            gauge(f"{int(gap_all[max(1, int(k.get_value())) - 1]):d}", 26, BLUE), 0))
        lab_e = at_panel(micro("RATE ERROR"), 1, value=False)
        val_e = always_redraw(lambda: at_panel(gauge(
            f"{abs(rate_all[max(1, int(k.get_value())) - 1] - 0.5):.4f}", 26, TEAL), 1))
        lab_n = at_panel(micro("FLIPS"), 2, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{max(1, int(k.get_value())):,d}", 26, INK), 2))

        self.add(gap_curve, rate_curve, val_g, val_e, val_n)
        self.play(FadeIn(lab_g), FadeIn(lab_e), FadeIn(lab_n), run_time=0.5,
                  rate_func=rf.ease_out_sine)

        with self.say("Watch the two readouts move in opposite directions. The "
                      "surplus climbs and never comes back. The error in the rate "
                      "falls the whole way."):
            self.play(k.animate.set_value(SEQ_N), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        with self.say("Neither is an accident. The surplus has an exact expected "
                      "size, and the proportion's error is that same quantity "
                      "divided by the number of flips."):
            self.play(Create(envelope), run_time=1.1, rate_func=rf.ease_out_sine)
            self.play(Create(err_hi), Create(err_lo), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # the exact form becomes its asymptote by morph, not by a second line
        exact = MathTex(r"\mathbb{E}|S_n|", "=",
                        r"2^{1-n}\,n\,\binom{n-1}{\lfloor (n-1)/2\rfloor}",
                        color=INK, font_size=34)
        exact.next_to(top, UP, buff=0.34).shift(LEFT * 0.15)
        asymp = MathTex(r"\mathbb{E}|S_n|", r"\approx", r"\sqrt{2n/\pi}",
                        color=INK, font_size=34)
        asymp.move_to(exact)

        with self.say("Two to the one minus n, times n, times a binomial "
                      "coefficient — which for any n worth plotting is the square "
                      "root of two n over pi."):
            self.play(FadeOut(title), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(Write(exact), run_time=1.5, rate_func=rf.linear)
            self.play(TransformMatchingTex(exact, asymp), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        # a camera move, at native type size: the band closing is the point
        self.camera.frame.save_state()
        with self.say("Root n in the numerator, n in the denominator. That is the "
                      "whole reason a deficit is never repaid and the proportion "
                      "converges anyway."):
            self.play(FadeOut(t_lab), FadeOut(b_lab), run_time=0.3,
                      rate_func=rf.ease_in_sine)
            self.play(self.camera.frame.animate.scale(0.58).move_to(
                bot.c2p(LOG_MAX * 0.74, 0.5)), run_time=1.6,
                rate_func=rf.ease_in_out_sine)
            self.beat(0.5)
            self.play(Restore(self.camera.frame), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(t_lab), FadeIn(b_lab), run_time=0.3,
                      rate_func=rf.ease_out_sine)

        verdict = prose("Nothing is owed. The denominator does the work.", 26, INK)
        verdict.next_to(bot, DOWN, buff=0.66).shift(LEFT * 0.1)
        with self.say("There is no law of averages. Nothing is owed and nothing is "
                      "repaid. The denominator does all the work."):
            self.play(FadeOut(x_lab), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # --------------- part 3: independence, shown as an absence -----------
    def part3_no_memory(self):
        title = prose("Level 2 · the coin has no memory", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        ks = sorted(MEMORY)
        axes = Axes(x_range=[0, len(ks) + 1, 1], y_range=[0, 1, 0.25],
                    x_length=8.2, y_length=3.5, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 0.5)
        xlab = micro("LENGTH OF THE RUN JUST SEEN").next_to(axes, DOWN, buff=0.3)
        ylab = micro("NEXT FLIP IS A HEAD").next_to(axes.y_axis, UP, buff=0.16)
        half = axes.plot(lambda _: 0.5, x_range=[0, len(ks) + 1],
                         stroke_color=YELLOW, stroke_width=2.0)

        with self.say("Here is the belief worth killing. After a run of heads, is a "
                      "tail due?"):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        grow = ValueTracker(0.0)
        bars, tags = VGroup(), VGroup()
        for i, kk in enumerate(ks, start=1):
            target = MEMORY[kk]
            base = axes.c2p(i, 0)
            width = abs(axes.c2p(1, 0)[0] - axes.c2p(0, 0)[0]) * 0.46

            def make(i=i, target=target, base=base, width=width):
                h = abs(axes.c2p(0, target * grow.get_value())[1] - axes.c2p(0, 0)[1])
                r = Rectangle(width=width, height=max(h, 1e-4),
                              stroke_width=0, fill_color=BLUE, fill_opacity=0.85)
                r.move_to([base[0], base[1] + h / 2.0, 0])
                return r

            bars.add(always_redraw(make))
            tags.add(micro(f"{kk}", 16, GREY).move_to(
                [base[0], base[1] - 0.28, 0]))

        lab_w = at_panel(micro("WORST DEPARTURE"), 0, value=False)
        val_w = always_redraw(lambda: at_panel(gauge(
            f"{MEMORY_WORST * grow.get_value():.4f}", 26,
            TEAL if grow.get_value() > 0.99 else INK), 0))
        lab_s = at_panel(micro("FROM ONE HALF"), 1, value=False)
        val_s = at_panel(gauge("0.5000", 26, YELLOW), 1)

        self.add(bars, val_w)
        self.play(FadeIn(tags), FadeIn(lab_w), FadeIn(lab_s), FadeIn(val_s),
                  run_time=0.6, rate_func=rf.ease_out_sine)

        with self.say("Two million flips, sorted by the run that came before each "
                      "one. After a single head, after two, after six — how often "
                      "is the next flip a head?"):
            self.play(Create(half), run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(grow.animate.set_value(1.0), run_time=2.8,
                      rate_func=rf.ease_out_back)

        with self.say("Every bar lands on one half. Nothing happens, and the fact "
                      "that nothing happens is the result."):
            self.play(Indicate(half, color=YELLOW, scale_factor=1.0), run_time=1.0,
                      rate_func=rf.there_and_back)

        verdict = prose("Independence: the sequence carries no debt.", 26, INK)
        verdict.next_to(axes, UP, buff=0.58).shift(LEFT * 0.1)
        with self.say("That is independence. The sequence carries no debt, and it is "
                      "also the assumption every control limit later rests on."):
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ----------- part 4: expectation is a balance point, not a face ------
    def part4_expectation(self):
        title = prose("Level 2 · expectation", 30, GREY).to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        beam = Line(LEFT * 4.0, RIGHT * 2.2, stroke_color=GREY, stroke_width=3.0)
        beam.shift(DOWN * 0.35)
        xs = np.linspace(-3.6, 1.8, len(DIE_FACES))
        weights, faces = VGroup(), VGroup()
        for face, x in zip(DIE_FACES, xs):
            d = Dot([x, beam.get_y() + 0.26, 0], radius=0.15, color=BLUE)
            weights.add(d)
            # clear of the fulcrum's travel: the triangle rides at -0.19 and is
            # 0.17 tall, so anything above -0.55 is under it at some point
            faces.add(micro(f"{face}", 18, GREY).move_to([x, beam.get_y() - 0.68, 0]))

        with self.say("One more idea before the chart. A fair die: six faces, each "
                      "as likely as the others."):
            self.play(Create(beam), FadeIn(weights), FadeIn(faces), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        e = die_expectation()
        pos = ValueTracker(float(DIE_FACES.min()))

        def x_of(face_value: float) -> float:
            lo, hi = float(DIE_FACES.min()), float(DIE_FACES.max())
            return float(xs[0] + (face_value - lo) / (hi - lo) * (xs[-1] - xs[0]))

        fulcrum = always_redraw(lambda: Triangle(
            color=YELLOW, fill_opacity=0.9, stroke_width=0).scale(0.17).move_to(
                [x_of(pos.get_value()), beam.get_y() - 0.19, 0]))

        lab_e = at_panel(micro("BALANCE POINT"), 0, value=False)
        val_e = always_redraw(lambda: at_panel(
            gauge(f"{pos.get_value():.2f}", 26, YELLOW), 0))
        self.add(fulcrum, val_e)
        self.play(FadeIn(lab_e), run_time=0.4, rate_func=rf.ease_out_sine)

        with self.say("Slide a fulcrum until the six weights balance. It settles "
                      "between three and four — at three point five."):
            self.play(pos.animate.set_value(e), run_time=2.4,
                      rate_func=rf.ease_in_out_sine)

        lab_x = at_panel(micro("A FACE OF THE DIE"), 1, value=False)
        val_x = at_panel(gauge("no", 26, RED), 1)
        with self.say("Three point five is not a face. The die can never show it, "
                      "and it is still the value to expect."):
            self.play(FadeIn(lab_x), FadeIn(val_x), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        verdict = prose("An expected value need not be attainable.", 26, INK)
        verdict.next_to(beam, UP, buff=1.05).shift(LEFT * 0.9)
        with self.say("An expected value is a balance point, not a prediction, and "
                      "it need not be attainable at all."):
            self.play(Write(verdict), run_time=1.3, rate_func=rf.linear)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # --------- part 5: what a rate of 0.27 % is a claim about -------------
    def part5_what_the_rate_claims(self):
        title = prose("Level 2 · what a percentage claims", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        # the rate is spelled from ALPHA, not typed: three typed copies of a
        # number the library publishes is how a page ends up disagreeing with it
        pct = f"{ALPHA * 100:.2f} %"
        claims = VGroup(
            prose(f"{pct} — the chance this part is bad", 25, GREY),
            prose(f"{pct} — the fraction of parts out of tolerance", 25, GREY),
            prose(f"{pct} — how often an unchanged process trips its own chart",
                  25, INK),
        ).arrange(DOWN, buff=0.42, aligned_edge=LEFT).shift(UP * 1.15 + LEFT * 0.5)

        with self.say("Level 6 will put a number on a pair of limits: nought point "
                      "two seven percent outside. Three readings of that number, "
                      "and only one of them is true."):
            self.play(Write(claims[0]), run_time=1.0, rate_func=rf.linear)
            self.play(Write(claims[1]), run_time=1.0, rate_func=rf.linear)
            self.play(Write(claims[2]), run_time=1.2, rate_func=rf.linear)

        strikes = VGroup(*[
            Line(c.get_left(), c.get_right(), stroke_color=RED, stroke_width=3.0)
            for c in claims[:2]])
        with self.say("Not the part — a part is never a probability. Not the parts "
                      "out of tolerance — that is capability, and it is Level 8. It "
                      "is a rate at which a chart cries wolf."):
            self.play(Create(strikes[0]), run_time=0.7, rate_func=rf.ease_in_out_sine)
            self.play(Create(strikes[1]), run_time=0.7, rate_func=rf.ease_in_out_sine)
            self.play(claims[2].animate.set_color(TEAL), run_time=0.6,
                      rate_func=rf.ease_out_sine)

        self.play(FadeOut(Group(claims[0], claims[1], strikes)), run_time=0.6,
                  rate_func=rf.ease_in_sine)
        self.play(claims[2].animate.scale(0.92).to_edge(UP, buff=1.15),
                  FadeOut(title), run_time=0.8, rate_func=rf.ease_in_out_sine)

        axes = Axes(x_range=[0, 1200, 300], y_range=[0, 1, 0.25],
                    x_length=8.2, y_length=3.1, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 1.15)
        xlab = micro("SUBGROUPS PLOTTED, NOTHING CHANGED").next_to(axes, DOWN, buff=0.28)
        ylab = micro("AT LEAST ONE ALARM").next_to(axes.y_axis, UP, buff=0.16)

        with self.say("So run the chart on a process where nothing is wrong, and "
                      "count the chance of having been alarmed at least once."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        n = ValueTracker(0.0)
        xs = np.linspace(0, 1200, 260)

        curve = always_redraw(lambda: _poly(
            axes, xs[xs <= max(1e-6, n.get_value())],
            p_any_alarm(xs[xs <= max(1e-6, n.get_value())]), TEAL)
            if (xs <= n.get_value()).sum() > 1 else VGroup())

        lab_n = at_panel(micro("SUBGROUPS"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{int(n.get_value()):,d}", 26, INK), 0))
        lab_p = at_panel(micro("ALARMED ONCE"), 1, value=False)
        val_p = always_redraw(lambda: at_panel(
            gauge(f"{p_any_alarm(n.get_value()) * 100:.1f} %", 26, TEAL), 1))
        self.add(curve, val_n, val_p)
        self.play(FadeIn(lab_n), FadeIn(lab_p), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say(f"A shift of a hundred subgroups, and it is already "
                      f"{P_IN_SHIFT * 100:.0f} percent."):
            self.play(n.animate.set_value(SHIFT_SUBGROUPS), run_time=1.8,
                      rate_func=rf.ease_out_sine)

        with self.say("Keep plotting. The phrase is one alarm in three hundred and "
                      "seventy subgroups, so run exactly that many."):
            self.play(n.animate.set_value(ARL0), run_time=2.6,
                      rate_func=rf.ease_in_out_sine)

        mark = Dot(axes.c2p(ARL0, P_IN_ARL0), radius=0.075, color=BLUE)
        line = axes.plot(lambda _: ONE_MINUS_1_OVER_E, x_range=[0, 1200],
                         stroke_color=YELLOW, stroke_width=1.8)
        with self.say(f"Not certainty — {P_IN_ARL0 * 100:.0f} percent. And that is "
                      f"not a coincidence."):
            self.play(FadeIn(mark, scale=1.6), run_time=0.6,
                      rate_func=rf.ease_out_back)
            self.play(Create(line), run_time=0.8, rate_func=rf.ease_out_sine)

        form = MathTex(r"1-(1-\alpha)^{n}", color=INK, font_size=36)
        form.next_to(claims[2], DOWN, buff=0.42).shift(LEFT * 0.2)
        at_arl = MathTex(r"1-(1-\alpha)^{1/\alpha}", color=INK, font_size=36)
        at_arl.move_to(form)
        limit = MathTex(r"1-e^{-1}", "=", f"{ONE_MINUS_1_OVER_E * 100:.1f}\\,\\%",
                        color=TEAL, font_size=36)
        limit.move_to(form)

        with self.say("Because the number of subgroups is one over the rate, the "
                      "expression collapses to one minus one over e."):
            self.play(Write(form), run_time=1.1, rate_func=rf.linear)
            self.play(TransformMatchingTex(form, at_arl), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)
            self.play(TransformMatchingTex(at_arl, limit), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        lab_m = at_panel(micro("TYPICAL WAIT"), 2, value=False)
        val_m = at_panel(gauge(f"{MEDIAN_WAIT:.0f} of {ARL0:.0f}", 26, RED), 2)
        with self.say(f"And because the waiting time is geometric, the typical wait "
                      f"is shorter than the average one: half of all first false "
                      f"alarms arrive by subgroup {MEDIAN_WAIT:.0f}."):
            self.play(FadeIn(lab_m), FadeIn(val_m), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        verdict = prose("A rate is a claim about the process, not about a part.",
                        26, INK)
        verdict.next_to(axes, UP, buff=0.52).shift(LEFT * 0.1)
        with self.say("A percentage on a control chart is a claim about a repeated "
                      "process. Never about a part. Level 6 can price the limits now."):
            self.play(Write(verdict), run_time=1.5, rate_func=rf.linear)

        self.beat(1.0)


def _poly(axes: Axes, xs: np.ndarray, ys: np.ndarray, colour: str) -> VGroup:
    """A polyline through (xs, ys) in `axes` coordinates.

    `plot_line_graph` is the only Axes helper that takes arbitrary samples, and
    it returns a dict; the act only ever wants the line out of it.
    """
    if len(xs) < 2:
        return VGroup()
    return axes.plot_line_graph(xs, ys, add_vertex_dots=False,
                                line_color=colour, stroke_width=3)["line_graph"]
