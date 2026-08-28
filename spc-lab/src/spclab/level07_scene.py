"""LEVEL 7 act — 'Evidence: adding rules is arithmetic, not opinion.'

Written 2026-08-28 against specs/spc-manim-craft-contract.md and
specs/curriculum-arc-contract.md, and it absorbs the standalone `WERules` scene
per §1 of the arc contract. What this act has to earn: Level 6 priced one
decision rule and never mentioned the other way to be wrong, and the Western
Electric rules are usually taught as a list to memorise rather than as a trade
with a price.

- **The blind spot is shown before it is named.** A shifted curve slides in
  under the same limits and the readout for the chance of catching it barely
  moves off the false-alarm rate. β arrives as the area the reader can see.
- **Power is swept, not tabulated.** One tracker walks the shift size while the
  curve slides and a live readout follows; the 50 % point lands exactly where
  the mean reaches the limit, which is the moment the number explains itself.
- **The p-value is what the chart throws away.** A point at 2.5σ is inside the
  limits and still surprising; the verdict and the evidence are separated on
  screen, and only then do the extra rules have a reason to exist.
- **Each rule is switched on and priced.** Four rules arrive one at a time and
  two run-length readouts move in the same direction — one good, one bad. The
  final frame is the comparison that decides it: the cost is fixed, the benefit
  is whatever shift you are trying to catch.

Numbers come from spclab.evidence, which quotes α from formulas and the
single-point run length from detection. The rules themselves are defined once in
formulas.western_electric_violations.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_scene.py Level07
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_scene.py Level07
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Dot, Group, Line, MathTex, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Indicate, Restore, TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, norm_pdf, prose, within_frame,
)
from spclab.evidence import (
    ALPHA_1, ARL0_ALL, ARL0_ONE_RULE, ARL1_ALL, ARL1_ONE_RULE, ARL_BIG_ALL,
    ARL_BIG_ONE, BIG_SHIFT, CHAMP_WOODALL_ARL0, FALSE_ALARM_COST, LIMIT,
    POWER_AT, RULE_TEXT, RULES, SHIFT, TRADE, cumulative_sets, p_value,
    power_one_point,
)
from spclab.narration import NarratedCameraScene

SETS = cumulative_sets()


class Level07(NarratedCameraScene):
    def construct(self):
        self.part1_the_other_error()
        self.part2_power_swept()
        self.part3_what_the_chart_discards()
        self.part4_switching_rules_on()
        self.part5_the_trade()

    # ---------- part 1: the error Level 6 never mentioned ----------------
    def part1_the_other_error(self):
        title = prose("Level 7 · the other way to be wrong", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-5.0, 6.2, 1], y_range=[0, 0.46, 0.2],
                    x_length=9.2, y_length=3.5, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(LEFT * 1.15 + DOWN * 0.55)
        xlab = within_frame(micro("PLOTTED STATISTIC, IN ITS OWN SIGMA")
                            .next_to(axes, DOWN, buff=0.3), "part 1 x-label")

        xs = np.linspace(-5.0, 6.2, 420)
        stable = axes.plot_line_graph(xs, norm_pdf(xs), add_vertex_dots=False,
                                      line_color=TEAL, stroke_width=3)["line_graph"]

        lims = VGroup(*[Line(axes.c2p(v, 0), axes.c2p(v, 0.44),
                             stroke_color=GREY, stroke_width=1.6)
                        for v in (-LIMIT, LIMIT)])
        tags = VGroup(
            micro(f"+{LIMIT:.0f}σ", 16, GREY).next_to(axes.c2p(LIMIT, 0), DOWN, buff=0.1),
            micro(f"−{LIMIT:.0f}σ", 16, GREY).next_to(axes.c2p(-LIMIT, 0), DOWN, buff=0.1))

        with self.say("Level 6 priced one decision: a point outside three sigma. "
                      "Nought point two seven percent of the time the process is "
                      "fine and the chart shouts anyway."):
            self.play(Create(axes), FadeIn(xlab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(stable), Create(lims), FadeIn(tags), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        lab_a = at_panel(micro("CRYING WOLF, α"), 0, value=False)
        val_a = at_panel(gauge(f"{ALPHA_1 * 100:.2f} %", 26, RED), 0)
        self.play(FadeIn(lab_a), FadeIn(val_a), run_time=0.6, rate_func=rf.ease_out_sine)

        # the shift slides in under the same limits
        d = ValueTracker(0.0)
        shifted = always_redraw(lambda: axes.plot_line_graph(
            xs, norm_pdf(xs, mu=d.get_value()), add_vertex_dots=False,
            line_color=YELLOW, stroke_width=3)["line_graph"])
        lab_b = at_panel(micro("STAYING SILENT, β"), 1, value=False)
        val_b = always_redraw(lambda: at_panel(gauge(
            f"{1 - power_one_point(d.get_value()):.3f}", 26, YELLOW), 1))
        lab_s = at_panel(micro("SHIFT, IN SIGMA"), 2, value=False)
        val_s = always_redraw(lambda: at_panel(
            gauge(f"{d.get_value():.2f}", 26, INK), 2))

        self.add(shifted, val_b, val_s)
        self.play(FadeIn(lab_b), FadeIn(lab_s), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say(f"Now move the process. A real shift of one sigma — and watch "
                      f"where it goes. Almost the whole curve is still inside the "
                      f"limits."):
            self.play(d.animate.set_value(SHIFT), run_time=2.6,
                      rate_func=rf.ease_in_out_sine)

        verdict = prose("The chart misses it 98 % of the time it looks.", 26, INK)
        verdict.next_to(axes, UP, buff=0.62).shift(LEFT * 0.1)
        with self.say(f"Which means the chance of catching it on the next point is "
                      f"about two percent. Beta — the chance of staying silent — is "
                      f"nought point nine seven seven. That is the error Level 6 "
                      f"never mentioned, and it is the bigger one."):
            self.play(Write(verdict), run_time=1.5, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 2: power, swept rather than tabulated -------------
    def part2_power_swept(self):
        title = prose("Level 7 · power", 30, GREY).to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, 4.2, 1], y_range=[0, 1.02, 0.25],
                    x_length=8.4, y_length=3.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 0.55)
        xlab = within_frame(micro("SIZE OF THE SHIFT, IN SIGMA")
                            .next_to(axes, DOWN, buff=0.3), "part 2 x-label")
        ylab = within_frame(micro("CHANCE IT SIGNALS")
                            .next_to(axes.y_axis, UP, buff=0.16), "part 2 y-label")

        with self.say("Put that on an axis. How big does a shift have to be before "
                      "one point is likely to see it?"):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        k = ValueTracker(0.02)
        grid = np.linspace(0, 4.2, 260)

        curve = always_redraw(lambda: _poly(
            axes, grid[grid <= k.get_value()],
            np.array([power_one_point(float(v)) for v in grid[grid <= k.get_value()]]),
            BLUE))

        lab_d = at_panel(micro("SHIFT"), 0, value=False)
        val_d = always_redraw(lambda: at_panel(
            gauge(f"{k.get_value():.2f} σ", 26, INK), 0))
        lab_p = at_panel(micro("POWER"), 1, value=False)
        val_p = always_redraw(lambda: at_panel(gauge(
            f"{power_one_point(k.get_value()) * 100:.1f} %", 26, TEAL), 1))
        self.add(curve, val_d, val_p)
        self.play(FadeIn(lab_d), FadeIn(lab_p), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("At one sigma, two percent. At two sigma, sixteen. The chart is "
                      "not broken — a small shift simply looks like ordinary noise to "
                      "a test that sees one point at a time."):
            self.play(k.animate.set_value(2.0), run_time=3.0, rate_func=rf.linear)

        half = axes.plot(lambda _: 0.5, x_range=[0, 4.2],
                         stroke_color=YELLOW, stroke_width=1.6)
        with self.say(f"It takes a shift of three full sigma — the mean landing "
                      f"exactly on the limit — before the next point is even a coin "
                      f"toss."):
            self.play(k.animate.set_value(4.2), run_time=2.2,
                      rate_func=rf.ease_out_sine)
            self.play(Create(half), run_time=0.7, rate_func=rf.ease_out_sine)

        mark = Dot(axes.c2p(LIMIT, 0.5), radius=0.075, color=YELLOW)
        eq = MathTex(r"\text{power}(3\sigma) = \tfrac{1}{2}", color=YELLOW, font_size=32)
        # clear of the half line and of the curve crossing it
        eq.next_to(axes.c2p(LIMIT, 0.5), UP, buff=0.52).shift(LEFT * 1.55)
        with self.say("And that is not a coincidence: when the mean sits on the limit, "
                      "half the distribution is on each side of it."):
            self.play(FadeIn(mark, scale=1.6), run_time=0.5, rate_func=rf.ease_out_back)
            self.play(Write(eq), run_time=1.1, rate_func=rf.linear)

        verdict = prose("One point, one chance. That is the whole limitation.", 26, INK)
        verdict.next_to(axes, UP, buff=0.52).shift(LEFT * 0.1)
        with self.say("One point, one chance. Everything the rules do next is an "
                      "attempt to get around that."):
            self.play(FadeOut(title), run_time=0.35, rate_func=rf.ease_in_sine)
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # -------- part 3: the evidence the in-or-out verdict throws away ------
    def part3_what_the_chart_discards(self):
        title = prose("Level 7 · the chart throws evidence away", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, 14, 2], y_range=[-3.6, 3.6, 1],
                    x_length=8.6, y_length=3.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 0.35)
        xlab = within_frame(micro("SUBGROUP").next_to(axes, DOWN, buff=0.28),
                            "part 3 x-label")

        cl = Line(axes.c2p(0, 0), axes.c2p(14, 0), stroke_color=GREY, stroke_width=2)
        lim = VGroup(*[Line(axes.c2p(0, v), axes.c2p(14, v), stroke_color=YELLOW,
                            stroke_width=2.0) for v in (LIMIT, -LIMIT)])
        two = VGroup(*[Line(axes.c2p(0, v), axes.c2p(14, v), stroke_color=GREY,
                            stroke_width=1.0) for v in (2, -2)])

        rng = np.random.default_rng(4)
        z = rng.normal(0, 1, 13)
        z[8] = 2.5                      # inside the limits, and surprising

        with self.say("Here is a chart doing its job. Every point inside the limits, "
                      "so every point is a pass."):
            self.play(Create(axes), FadeIn(xlab), Create(cl), Create(lim),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        dots = VGroup(*[Dot(axes.c2p(i + 1, v), radius=0.062, color=BLUE)
                        for i, v in enumerate(z)])
        self.play(FadeIn(dots, lag_ratio=0.12), run_time=1.6, rate_func=rf.ease_out_sine)

        hot = dots[8]
        lab_v = at_panel(micro("THE CHART SAYS"), 0, value=False)
        val_v = at_panel(gauge("in control", 26, TEAL), 0)
        lab_p = at_panel(micro("ITS P-VALUE"), 1, value=False)
        val_p = at_panel(gauge(f"{p_value(2.5):.4f}", 26, RED), 1)

        with self.say("Except this one. Two point five sigma — inside the limits, so "
                      "the chart calls it in control."):
            self.play(Create(two), run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(hot.animate.set_color(RED).scale(1.5), run_time=0.6,
                      rate_func=rf.ease_out_back)
            self.play(FadeIn(lab_v), FadeIn(val_v), run_time=0.6,
                      rate_func=rf.ease_out_sine)

        with self.say(f"But ask how surprising it is and the answer is one in eighty. "
                      f"Anywhere else in statistics that is a finding. Here it is "
                      f"filed as a pass and forgotten."):
            self.play(FadeIn(lab_p), FadeIn(val_p), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.play(Indicate(val_p, color=RED, scale_factor=1.12), run_time=0.9,
                      rate_func=rf.there_and_back)

        verdict = prose("A verdict is not the same as the evidence.", 26, INK)
        verdict.next_to(axes, UP, buff=0.52).shift(LEFT * 0.1)
        with self.say("A verdict is not the same as the evidence. The extra rules "
                      "exist to spend what a single point cannot hold."):
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------ part 4: the four rules, switched on one at a time -------
    def part4_switching_rules_on(self):
        title = prose("Level 7 · four rules, one at a time", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        rows = VGroup()
        for r in RULES:
            rows.add(prose(f"Rule {r} — {RULE_TEXT[r]}", 25, GREY))
        rows.arrange(DOWN, buff=0.40, aligned_edge=LEFT)
        rows.shift(UP * 0.75 + LEFT * 1.45)

        lab_0 = at_panel(micro("FALSE ALARM EVERY"), 0, value=False)
        lab_1 = at_panel(micro(f"CATCHES {SHIFT:.0f}σ IN"), 1, value=False)

        shown = ValueTracker(1.0)

        def cur() -> dict:
            i = int(np.clip(round(shown.get_value()), 1, len(SETS)))
            return TRADE[SETS[i - 1]]

        val_0 = always_redraw(lambda: at_panel(
            gauge(f"{cur()['arl0']:.0f}", 26, RED), 0))
        val_1 = always_redraw(lambda: at_panel(
            gauge(f"{cur()['arl1']:.1f}", 26, TEAL), 1))

        with self.say("So here are the four Western Electric rules. Usually taught as "
                      "a list to memorise. They are not a list — they are four "
                      "purchases, and each one has a price."):
            self.play(Write(rows[0]), run_time=0.9, rate_func=rf.linear)
            self.add(val_0, val_1)
            self.play(FadeIn(lab_0), FadeIn(lab_1), run_time=0.5,
                      rate_func=rf.ease_out_sine)
            self.play(rows[0].animate.set_color(INK), run_time=0.4,
                      rate_func=rf.ease_out_sine)

        with self.say(f"Rule one alone: a false alarm every "
                      f"{ARL0_ONE_RULE:.0f} subgroups, and a one sigma shift caught "
                      f"in {ARL1_ONE_RULE:.0f}."):
            self.beat(0.6)

        for i in (2, 3, 4):
            spoken = {
                2: "Add rule two — two of three points beyond two sigma on the same "
                   "side. Both numbers fall.",
                3: "Rule three, four of five beyond one sigma. They fall again.",
                4: "And rule four: eight in a row on one side of the line, no matter "
                   "how close.",
            }[i]
            with self.say(spoken):
                self.play(Write(rows[i - 1]), run_time=0.8, rate_func=rf.linear)
                self.play(rows[i - 1].animate.set_color(INK),
                          shown.animate.set_value(float(i)), run_time=1.3,
                          rate_func=rf.ease_in_out_sine)

        pub = at_panel(micro("PUBLISHED, 1987"), 2, value=False)
        pub_v = at_panel(gauge(f"{CHAMP_WOODALL_ARL0:.1f}", 26, YELLOW), 2)
        with self.say(f"All four together: a false alarm every {ARL0_ALL:.0f} "
                      f"subgroups. That number was published in 1987 as ninety-one "
                      f"point seven five, and this simulation was not told about it."):
            self.play(FadeIn(pub), FadeIn(pub_v), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 5: the trade, and who it is good for --------------
    def part5_the_trade(self):
        title = prose("Level 7 · so is it worth it", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, 3, 1], y_range=[0, 5.4, 1],
                    x_length=7.4, y_length=4.0, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.5 + DOWN * 0.5)
        ylab = within_frame(micro("TIMES SOONER")
                            .next_to(axes.y_axis, UP, buff=0.16), "part 5 y-label")

        cost = axes.plot(lambda _: FALSE_ALARM_COST, x_range=[0, 3],
                         stroke_color=RED, stroke_width=2.6)
        cost_tag = micro(f"THE COST — ×{FALSE_ALARM_COST:.1f} FALSE ALARMS", 16, RED)
        cost_tag.next_to(axes.c2p(3, FALSE_ALARM_COST), UP, buff=0.30)
        cost_tag.align_to(axes.c2p(3, 0), RIGHT)
        within_frame(cost_tag, "part 5 cost tag")

        with self.say("Line up what it cost against what it bought. The cost is one "
                      "number and it never changes: four times the false alarms."):
            self.play(Create(axes), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(cost), FadeIn(cost_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        gains = [(SHIFT, ARL1_ONE_RULE / ARL1_ALL, TEAL),
                 (BIG_SHIFT, ARL_BIG_ONE / ARL_BIG_ALL, BLUE)]
        grow = ValueTracker(0.0)
        bars, tags = VGroup(), VGroup()
        for j, (sh, g, col) in enumerate(gains):
            base = axes.c2p(j + 0.7, 0)
            w = abs(axes.c2p(1, 0)[0] - axes.c2p(0, 0)[0]) * 0.42

            def mk(base=base, g=g, col=col, w=w):
                h = abs(axes.c2p(0, g * grow.get_value())[1] - axes.c2p(0, 0)[1])
                r = Rectangle(width=w, height=max(h, 1e-4), stroke_width=0,
                              fill_color=col, fill_opacity=0.85)
                r.move_to([base[0], base[1] + h / 2.0, 0])
                return r

            bars.add(always_redraw(mk))
            tags.add(micro(f"{sh:.0f}σ SHIFT", 16, GREY).move_to(
                [base[0], base[1] - 0.3, 0]))

        lab_g = at_panel(micro("BOUGHT AT 1σ"), 0, value=False)
        val_g = at_panel(gauge(f"×{ARL1_ONE_RULE / ARL1_ALL:.1f}", 26, TEAL), 0)
        lab_h = at_panel(micro(f"BOUGHT AT {BIG_SHIFT:.0f}σ"), 1, value=False)
        val_h = at_panel(gauge(f"×{ARL_BIG_ONE / ARL_BIG_ALL:.1f}", 26, BLUE), 1)

        self.add(bars)
        self.play(FadeIn(tags), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say(f"Against a one sigma drift the rules catch it four and a half "
                      f"times sooner. That is above the cost line, and it is a good "
                      f"trade."):
            self.play(grow.animate.set_value(1.0), run_time=2.2,
                      rate_func=rf.ease_out_back)
            self.play(FadeIn(lab_g), FadeIn(val_g), run_time=0.6,
                      rate_func=rf.ease_out_sine)

        with self.say(f"Against a three sigma jump, they catch it barely sooner at "
                      f"all — because rule one already sees it on the next point. "
                      f"Same cost, almost nothing bought."):
            self.play(FadeIn(lab_h), FadeIn(val_h), run_time=0.6,
                      rate_func=rf.ease_out_sine)
            self.play(Indicate(bars[1], color=BLUE, scale_factor=1.06), run_time=1.0,
                      rate_func=rf.there_and_back)

        verdict = prose("The cost is fixed. The benefit is the shift you fear.",
                        26, INK)
        verdict.next_to(axes, UP, buff=0.46).shift(LEFT * 0.1)
        with self.say("So the rules are not good or bad. The cost is fixed and the "
                      "benefit is whatever shift you are actually afraid of — which "
                      "is a question about your process, and the arithmetic is only "
                      "here to make it answerable."):
            self.play(FadeOut(title), run_time=0.35, rate_func=rf.ease_in_sine)
            self.play(Write(verdict), run_time=1.6, rate_func=rf.linear)

        self.beat(1.0)


def _poly(axes: Axes, xs: np.ndarray, ys: np.ndarray, colour: str) -> VGroup:
    """A polyline through (xs, ys); `plot_line_graph` returns a dict."""
    if len(xs) < 2:
        return VGroup()
    return axes.plot_line_graph(xs, ys, add_vertex_dots=False,
                                line_color=colour, stroke_width=3)["line_graph"]
