"""LEVEL 5 act — 'Estimation: every number here is an estimate, including ours.'

Written 2026-08-28 against specs/spc-manim-craft-contract.md and
specs/curriculum-arc-contract.md. What this act has to earn: Level 4 gave the
sampling distribution and σ/√n, and Level 6 will build limits out of estimates
without ever saying so. This level is where an estimate gets an error bar, and
where the curriculum turns that instrument on its own constants.

- **The scatter of estimates is produced, not stated.** A tracker admits samples
  one at a time; the readout is the standard deviation of the sample means so
  far, and it walks onto σ/√n without that value ever being typed as a target.
- **Coverage is counted on screen.** Intervals arrive one per sample, the ones
  that miss the hidden mean turn red, and a live readout divides caught by built.
  The 95 % is the number the counter stops at.
- **Then the same procedure is run with the wrong quantile** and the counter
  stops somewhere else. The formula morphs z into t by
  `TransformMatchingTex` — the fix is a substitution, and it looks like one.
- **The square law is walked, not asserted.** A tracker sweeps n while the width
  readout follows; the camera closes on the point where the width has halved so
  the reader can read the cost off the axis.
- **The act ends by measuring the repo.** Sixty independent estimates of d₂ pile
  into a histogram beside the value `formulas` publishes, and the closing readout
  is how many subgroups its third decimal would actually cost.

Numbers come from spclab.estimation, which quotes d₂ from spclab.formulas.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level05_scene.py Level05
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level05_scene.py Level05
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Dot, Group, Line, MathTex, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Restore, TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose, within_frame,
)
from spclab.estimation import (
    CONF, COVER_T, COVER_Z, D2_MEAN, D2_PUBLISHED, D2_SE, D2_SUBGROUPS_FOR_3DP,
    HALVE_FROM, HALVE_N_Z, SIZES, SUBGROUP_N, TRUE_MEAN, TRUE_SIGMA, Z_95,
    d2_estimates, interval_width, samples, standard_error_exact, t_quantile,
)
from spclab.narration import NarratedCameraScene

N = SUBGROUP_N                  # the subgroup size the rest of the arc uses
SHOW = 46                       # intervals drawn on screen
T_N = t_quantile(N - 1)


class Level05(NarratedCameraScene):
    def construct(self):
        self.part1_estimates_scatter()
        self.part2_counting_coverage()
        self.part3_why_t_exists()
        self.part4_the_price_of_precision()
        self.part5_our_own_constants()

    # ------- part 1: an estimate has a spread, and it is σ/√n --------------
    def part1_estimates_scatter(self):
        title = prose("Level 5 · every number on a chart is an estimate", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        s = samples(N, trials=260, seed=3)
        means = s.mean(axis=1)

        axes = Axes(x_range=[TRUE_MEAN - 1.2, TRUE_MEAN + 1.2, 0.4],
                    y_range=[0, 44, 20], x_length=9.0, y_length=3.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(LEFT * 1.2 + DOWN * 0.55)
        xlab = within_frame(micro("ESTIMATE OF THE MEAN (MM)").next_to(axes, DOWN, buff=0.3))
        truth = Line(axes.c2p(TRUE_MEAN, 0), axes.c2p(TRUE_MEAN, 44),
                     stroke_color=YELLOW, stroke_width=2.2)
        truth_tag = micro("THE TRUTH — NEVER SEEN", 16, YELLOW)
        # left edge clear of the line, not centred on it
        truth_tag.next_to(axes.c2p(TRUE_MEAN, 44), UP, buff=0.14)
        truth_tag.align_to(truth, LEFT).shift(RIGHT * 0.16)

        with self.say("Somewhere behind this process there is a real mean. Nobody on "
                      "a shop floor has ever seen one."):
            self.play(Create(axes), FadeIn(xlab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(truth), FadeIn(truth_tag), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        k = ValueTracker(1.0)

        def taken() -> np.ndarray:
            return means[:max(1, int(k.get_value()))]

        # a histogram of estimates, built by arrival
        edges = np.linspace(TRUE_MEAN - 1.2, TRUE_MEAN + 1.2, 33)
        width = abs(axes.c2p(edges[1], 0)[0] - axes.c2p(edges[0], 0)[0]) * 0.9

        def bars() -> VGroup:
            counts, _ = np.histogram(taken(), bins=edges)
            g = VGroup()
            for c, lo, hi in zip(counts, edges[:-1], edges[1:]):
                if c == 0:
                    continue
                base = axes.c2p((lo + hi) / 2.0, 0)
                h = abs(axes.c2p(0, c)[1] - axes.c2p(0, 0)[1])
                r = Rectangle(width=width, height=h, stroke_width=0,
                              fill_color=BLUE, fill_opacity=0.8)
                r.move_to([base[0], base[1] + h / 2.0, 0])
                g.add(r)
            return g

        hist = always_redraw(bars)

        lab_n = at_panel(micro("SAMPLES OF FIVE"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{len(taken()):d}", 26, INK), 0))
        lab_sd = at_panel(micro("SPREAD OF THESE"), 1, value=False)
        val_sd = always_redraw(lambda: at_panel(gauge(
            f"{taken().std(ddof=1):.4f}" if len(taken()) > 1 else "—", 26, TEAL), 1))
        lab_se = at_panel(micro("SIGMA OVER ROOT N"), 2, value=False)
        val_se = at_panel(gauge(f"{standard_error_exact(N):.4f}", 26, YELLOW), 2)

        self.add(hist, val_n, val_sd)
        self.play(FadeIn(lab_n), FadeIn(lab_sd), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("So take five parts and average them. That average is an "
                      "estimate, and it is wrong — a little. Take another five, and "
                      "it is wrong by a different amount."):
            self.play(k.animate.set_value(24), run_time=2.6, rate_func=rf.linear)

        with self.say("Keep going, and the estimates make a shape of their own. It "
                      "is narrower than the parts, and it has a width you can "
                      "predict before you measure anything."):
            self.play(k.animate.set_value(len(means)), run_time=3.4,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(lab_se), FadeIn(val_se), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        verdict = prose("Sigma over root n is the size of being wrong.", 26, INK)
        verdict.next_to(axes, UP, buff=0.66).shift(LEFT * 0.1)
        with self.say("Sigma over root n. Level 4 derived it; here it is the size of "
                      "being wrong, and it is the thing an interval is built out of."):
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ---------- part 2: coverage is a thing you count ---------------------
    def part2_counting_coverage(self):
        title = prose("Level 5 · what “ninety-five percent” has to earn", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        s = samples(N, trials=SHOW, seed=3)
        m = s.mean(axis=1)
        sd = s.std(axis=1, ddof=1)
        half = T_N * sd / np.sqrt(N)
        caught = (m - half <= TRUE_MEAN) & (TRUE_MEAN <= m + half)

        axes = Axes(x_range=[TRUE_MEAN - 1.6, TRUE_MEAN + 1.6, 0.5],
                    y_range=[0, SHOW, SHOW], x_length=8.6, y_length=4.6, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(LEFT * 1.3 + DOWN * 0.35)
        xlab = within_frame(micro("ESTIMATE OF THE MEAN (MM)").next_to(axes, DOWN, buff=0.28))
        truth = Line(axes.c2p(TRUE_MEAN, 0), axes.c2p(TRUE_MEAN, SHOW),
                     stroke_color=YELLOW, stroke_width=2.2)

        with self.say("An interval is the estimate plus and minus a margin. Build one "
                      "from every sample and the interval is what moves — the truth "
                      "does not."):
            self.play(Create(axes), FadeIn(xlab), Create(truth), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)

        k = ValueTracker(0.0)

        def drawn() -> int:
            return int(np.clip(k.get_value(), 0, SHOW))

        def bars() -> VGroup:
            g = VGroup()
            for i in range(drawn()):
                y = axes.c2p(TRUE_MEAN, i + 0.5)[1]
                c = TEAL if caught[i] else RED
                g.add(Line([axes.c2p(m[i] - half[i], 0)[0], y, 0],
                           [axes.c2p(m[i] + half[i], 0)[0], y, 0],
                           stroke_color=c, stroke_width=2.6))
            return g

        ivals = always_redraw(bars)

        lab_b = at_panel(micro("INTERVALS BUILT"), 0, value=False)
        val_b = always_redraw(lambda: at_panel(gauge(f"{drawn():d}", 26, INK), 0))
        lab_c = at_panel(micro("CAUGHT THE TRUTH"), 1, value=False)
        val_c = always_redraw(lambda: at_panel(
            gauge(f"{int(caught[:drawn()].sum()):d}", 26, TEAL), 1))
        lab_p = at_panel(micro("SO FAR"), 2, value=False)
        val_p = always_redraw(lambda: at_panel(gauge(
            f"{100.0 * caught[:drawn()].mean():.1f} %" if drawn() else "—", 26, TEAL), 2))

        self.add(ivals, val_b, val_c, val_p)
        self.play(FadeIn(lab_b), FadeIn(lab_c), FadeIn(lab_p), run_time=0.5,
                  rate_func=rf.ease_out_sine)

        with self.say("Green caught the real mean. Red missed it entirely — and on the "
                      "shop floor you would never know which one you were holding."):
            self.play(k.animate.set_value(SHOW), run_time=5.0, rate_func=rf.linear)

        verdict = prose("Ninety-five percent is a property of the procedure.", 26, INK)
        verdict.next_to(axes, UP, buff=0.42).shift(LEFT * 0.1)
        with self.say("That is all a confidence level is: run the procedure many times "
                      "and this fraction of the intervals contain the truth. It is a "
                      "property of the procedure, not of the interval in your hand."):
            self.play(Write(verdict), run_time=1.6, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------- part 3: the wrong quantile, measured -------------------
    def part3_why_t_exists(self):
        title = prose("Level 5 · why t exists", 30, GREY).to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, len(SIZES) + 1, 1], y_range=[0.6, 1.0, 0.1],
                    x_length=8.2, y_length=3.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 0.62)
        xlab = within_frame(micro("PARTS PER SAMPLE").next_to(axes, DOWN, buff=0.3))
        ylab = within_frame(micro("CAUGHT THE TRUTH").next_to(
            axes.y_axis, UP, buff=0.16), "part 3 y-label")
        target = axes.plot(lambda _: CONF, x_range=[0, len(SIZES) + 1],
                           stroke_color=YELLOW, stroke_width=2.0)
        tag = micro("NOMINAL 95 %", 16, YELLOW).next_to(
            axes.c2p(len(SIZES) + 1, CONF), RIGHT, buff=0.1)

        ticks = VGroup(*[micro(f"{k}", 16, GREY).move_to(
            axes.c2p(i + 1, 0.6) + DOWN * 0.28) for i, k in enumerate(SIZES)])

        with self.say("Here is where the textbooks quietly cheat. Sigma is never known "
                      "either — it is estimated from the same five parts."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), FadeIn(ticks),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)
            self.play(Create(target), FadeIn(tag), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        pts_z = VGroup(*[Dot(axes.c2p(i + 1, COVER_Z[k]), radius=0.07, color=RED)
                         for i, k in enumerate(SIZES)])
        line_z = axes.plot_line_graph(
            [i + 1 for i in range(len(SIZES))], [COVER_Z[k] for k in SIZES],
            add_vertex_dots=False, line_color=RED, stroke_width=3)["line_graph"]

        lab_q = at_panel(micro("QUANTILE USED"), 0, value=False)
        val_q = at_panel(gauge(f"{Z_95:.3f}", 26, RED), 0)
        lab_c = at_panel(micro("AT FIVE PARTS"), 1, value=False)
        val_c = at_panel(gauge(f"{COVER_Z[N] * 100:.1f} %", 26, RED), 1)

        with self.say(f"Use one point nine six anyway, and count. At five parts the "
                      f"interval that says ninety-five delivers "
                      f"{COVER_Z[N] * 100:.0f}."):
            self.play(Create(line_z), FadeIn(pts_z), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(lab_q), FadeIn(val_q), FadeIn(lab_c), FadeIn(val_c),
                      run_time=0.7, rate_func=rf.ease_out_sine)

        # the fix is a substitution, and it should look like one
        form_z = MathTex(r"\bar{x} \pm", "1.96", r"\frac{s}{\sqrt{n}}",
                         color=INK, font_size=38)
        form_z.next_to(axes, UP, buff=0.46).shift(LEFT * 0.2)
        form_t = MathTex(r"\bar{x} \pm", "t_{n-1}", r"\frac{s}{\sqrt{n}}",
                         color=TEAL, font_size=38)
        form_t.move_to(form_z)

        with self.say("The margin is too narrow because s is itself uncertain. Replace "
                      "the quantile with one that knows how few parts it was built "
                      "from."):
            self.play(Write(form_z), run_time=1.2, rate_func=rf.linear)
            self.play(TransformMatchingTex(form_z, form_t), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)

        pts_t = VGroup(*[Dot(axes.c2p(i + 1, COVER_T[k]), radius=0.07, color=TEAL)
                         for i, k in enumerate(SIZES)])
        line_t = axes.plot_line_graph(
            [i + 1 for i in range(len(SIZES))], [COVER_T[k] for k in SIZES],
            add_vertex_dots=False, line_color=TEAL, stroke_width=3)["line_graph"]
        val_q2 = at_panel(gauge(f"{T_N:.3f}", 26, TEAL), 0)
        val_c2 = at_panel(gauge(f"{COVER_T[N] * 100:.1f} %", 26, TEAL), 1)

        with self.say(f"At five parts that quantile is {T_N:.2f}, not 1.96 — and the "
                      f"count lands on ninety-five where it belongs, at every sample "
                      f"size."):
            self.play(Create(line_t), FadeIn(pts_t), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeOut(val_q), FadeOut(val_c), FadeIn(val_q2), FadeIn(val_c2),
                      run_time=0.7, rate_func=rf.ease_out_sine)

        verdict = prose("t is not a correction. It is the honest quantile.", 26, INK)
        verdict.next_to(axes, DOWN, buff=0.84).shift(LEFT * 0.1)
        with self.say("t is not a correction bolted onto a normal. It is what the "
                      "arithmetic gives you when the spread is estimated too."):
            self.play(FadeOut(xlab), run_time=0.35, rate_func=rf.ease_in_sine)
            self.play(Write(verdict), run_time=1.4, rate_func=rf.linear)

        self.beat(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # -------------- part 4: the price of being sure -----------------------
    def part4_the_price_of_precision(self):
        title = prose("Level 5 · precision has a price", 30, GREY)
        title.to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, 44, 10], y_range=[0, 1.3, 0.4],
                    x_length=8.4, y_length=4.0, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5})
        axes.shift(LEFT * 1.3 + DOWN * 0.5)
        xlab = within_frame(micro("PARTS PER SAMPLE").next_to(axes, DOWN, buff=0.3))
        ylab = within_frame(micro("WIDTH — SIGMA KNOWN").next_to(axes.y_axis, UP, buff=0.16))

        with self.say("So how many parts does it take to be sure? Hold sigma known for "
                      "a moment, so the quantile stops moving and only the root n is "
                      "left. The width answers it, and the answer is expensive."):
            self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        n_t = ValueTracker(2.0)
        grid = np.arange(2, 45)
        widths = np.array([interval_width(int(v), use_t=False) for v in grid])

        curve = always_redraw(lambda: _poly(
            axes, grid[grid <= max(2, n_t.get_value())],
            widths[grid <= max(2, n_t.get_value())], BLUE))

        lab_n = at_panel(micro("PARTS"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{int(n_t.get_value()):d}", 26, INK), 0))
        lab_w = at_panel(micro("WIDTH, MM"), 1, value=False)
        val_w = always_redraw(lambda: at_panel(gauge(
            f"{interval_width(int(n_t.get_value()), use_t=False):.3f}", 26, TEAL), 1))

        self.add(curve, val_n, val_w)
        self.play(FadeIn(lab_n), FadeIn(lab_w), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("Watch the width fall as the parts arrive. It falls fast at "
                      "first, and then it stops paying."):
            self.play(n_t.animate.set_value(44), run_time=4.2,
                      rate_func=rf.ease_in_out_sine)

        base = interval_width(HALVE_FROM, use_t=False)
        mark_a = Dot(axes.c2p(HALVE_FROM, base), radius=0.075, color=YELLOW)
        mark_b = Dot(axes.c2p(HALVE_N_Z, base / 2), radius=0.075, color=YELLOW)
        drop = Line(axes.c2p(HALVE_FROM, base), axes.c2p(HALVE_FROM, base / 2),
                    stroke_color=YELLOW, stroke_width=1.6)
        across = Line(axes.c2p(HALVE_FROM, base / 2), axes.c2p(HALVE_N_Z, base / 2),
                      stroke_color=YELLOW, stroke_width=1.6)

        lab_c = at_panel(micro("TO HALVE IT"), 2, value=False)
        val_c = at_panel(gauge(f"{HALVE_FROM} to {HALVE_N_Z}", 26, YELLOW), 2)

        self.camera.frame.save_state()
        with self.say(f"Halve the width and the bill is four times the parts: five "
                      f"becomes twenty. Not ten — four times, because the error falls "
                      f"as the root."):
            self.play(FadeIn(mark_a, scale=1.5), run_time=0.5, rate_func=rf.ease_out_back)
            self.play(Create(drop), Create(across), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(mark_b, scale=1.5), FadeIn(lab_c), FadeIn(val_c),
                      run_time=0.7, rate_func=rf.ease_out_back)
            self.play(self.camera.frame.animate.scale(0.62).move_to(
                axes.c2p(HALVE_N_Z * 0.55, base * 0.62)), run_time=1.5,
                rate_func=rf.ease_in_out_sine)
            self.beat(0.5)
            self.play(Restore(self.camera.frame), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)

        verdict = prose("Certainty is bought by the square.", 26, INK)
        verdict.next_to(axes, UP, buff=0.50).shift(LEFT * 0.1)
        with self.say("Certainty is bought by the square. That is the sentence to take "
                      "to anyone who asks for a tighter number without more parts."):
            self.play(Write(verdict), run_time=1.3, rate_func=rf.linear)

        self.beat(0.7)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ---------- part 5: the instrument turned on the curriculum -----------
    def part5_our_own_constants(self):
        title = prose("Level 5 · including ours", 30, GREY).to_edge(UP, buff=0.38)
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                  rate_func=rf.ease_out_sine)

        reps = d2_estimates()
        lo, hi = 2.28, 2.38
        axes = Axes(x_range=[lo, hi, 0.02], y_range=[0, 13, 5],
                    x_length=8.4, y_length=3.5, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(LEFT * 1.3 + DOWN * 0.55)
        xlab = within_frame(micro("D2 ESTIMATED, ONCE PER RUN").next_to(axes, DOWN, buff=0.3))

        with self.say("One last place to point this. Every control chart in the rest "
                      "of this curriculum multiplies a range by a constant called "
                      "d two."):
            self.play(Create(axes), FadeIn(xlab), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        pub = Line(axes.c2p(D2_PUBLISHED, 0), axes.c2p(D2_PUBLISHED, 13),
                   stroke_color=YELLOW, stroke_width=2.2)
        pub_tag = micro(f"PUBLISHED {D2_PUBLISHED:.4f}", 16, YELLOW)
        pub_tag.next_to(axes.c2p(D2_PUBLISHED, 13), UP, buff=0.12)
        pub_tag.align_to(pub, LEFT).shift(RIGHT * 0.16)

        lab_p = at_panel(micro("THE TABLE SAYS"), 0, value=False)
        val_p = at_panel(gauge(f"{D2_PUBLISHED:.4f}", 26, YELLOW), 0)

        with self.say("This site does not look it up. It simulates it — and anything "
                      "simulated is an estimate."):
            self.play(Create(pub), FadeIn(pub_tag), FadeIn(lab_p), FadeIn(val_p),
                      run_time=0.9, rate_func=rf.ease_out_sine)

        k = ValueTracker(0.0)
        edges = np.linspace(lo, hi, 22)
        width = abs(axes.c2p(edges[1], 0)[0] - axes.c2p(edges[0], 0)[0]) * 0.9

        def bars() -> VGroup:
            taken = reps[:int(np.clip(k.get_value(), 0, len(reps)))]
            counts, _ = np.histogram(taken, bins=edges)
            g = VGroup()
            for c, a, b in zip(counts, edges[:-1], edges[1:]):
                if c == 0:
                    continue
                base = axes.c2p((a + b) / 2.0, 0)
                h = abs(axes.c2p(0, c)[1] - axes.c2p(0, 0)[1])
                r = Rectangle(width=width, height=h, stroke_width=0,
                              fill_color=BLUE, fill_opacity=0.82)
                r.move_to([base[0], base[1] + h / 2.0, 0])
                g.add(r)
            return g

        hist = always_redraw(bars)
        lab_se = at_panel(micro("ITS STD ERROR"), 1, value=False)
        val_se = always_redraw(lambda: at_panel(gauge(
            f"{reps[:int(k.get_value())].std(ddof=1):.4f}"
            if int(k.get_value()) > 1 else "—", 26, TEAL), 1))
        self.add(hist, val_se)

        with self.say("Run that simulation sixty times over and the answers scatter. "
                      "The scatter is the standard error of our own constant."):
            self.play(FadeIn(lab_se), run_time=0.4, rate_func=rf.ease_out_sine)
            self.play(k.animate.set_value(len(reps)), run_time=3.6,
                      rate_func=rf.ease_out_sine)

        lab_c = at_panel(micro("FOR 3 DECIMALS"), 2, value=False)
        val_c = at_panel(gauge(f"{D2_SUBGROUPS_FOR_3DP / 1e6:.1f} M", 26, RED), 2)
        with self.say(f"Which sets a limit on honesty. Earning the third decimal of "
                      f"that constant from simulation alone would take "
                      f"{D2_SUBGROUPS_FOR_3DP / 1e6:.0f} million subgroups. The "
                      f"fourth figure in the table is not simulated at all — it comes "
                      f"from the exact integral."):
            self.play(FadeIn(lab_c), FadeIn(val_c), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        verdict = prose("Every constant ahead is an estimate. Now you can price one.",
                        26, INK)
        verdict.next_to(axes, UP, buff=0.90).shift(LEFT * 0.1)
        with self.say("So when Level 6 builds limits and Level 8 divides by a spread, "
                      "remember what they are made of. Estimates, with a size you now "
                      "know how to work out."):
            self.play(Write(verdict), run_time=1.6, rate_func=rf.linear)

        self.beat(1.0)


def _poly(axes: Axes, xs: np.ndarray, ys: np.ndarray, colour: str) -> VGroup:
    """A polyline through (xs, ys); `plot_line_graph` returns a dict."""
    if len(xs) < 2:
        return VGroup()
    return axes.plot_line_graph(xs, ys, add_vertex_dots=False,
                                line_color=colour, stroke_width=3)["line_graph"]
