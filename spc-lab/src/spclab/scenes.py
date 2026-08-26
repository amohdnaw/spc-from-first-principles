"""SPCGallery — the overview act the landing page plays first.

It assumes nothing and carries two ideas: control limits are learned from the
process, and capability is what happens when you hold that process against a
specification.

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 5:

- **The limits are derived by motion.** σ̂ is computed from the plotted means,
  then a tracker sweeps a candidate band outward from ±0σ̂ to ±3σ̂ while a live
  readout counts how many of the thirty six points still fall outside it. The
  band stops where the count reaches zero and stays there — which is what
  "learned from the process" means, watched rather than asserted.
- **The scrap figure is computed**, by `spclab.ppm_from_cpk` at render time.
  The old act typed "≈ 1 000+ defects per million" beside a Cpk it had also
  typed; both now come from the geometry on screen.
- One `TransformMatchingTex` on the limit definition, one camera push into the
  tail, every play with a deliberate rate_func, and all in-frame text in the
  site's two voices.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes.py SPCGallery
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes.py SPCGallery
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
    at_panel, gauge, micro, prose,
)
from spclab.formulas import ppm_from_cpk
from spclab.narration import NarratedCameraScene

N_SUB = 36


class SPCGallery(NarratedCameraScene):
    def construct(self):
        self.intro()
        self.chart_act()
        self.capability_act()

    # ------------------------------------------------------------- intro
    def intro(self):
        t1 = prose("Every SPC formula,", 46, INK)
        t2 = prose("drawn.", 46, TEAL)
        VGroup(t1, t2).arrange(DOWN, aligned_edge=LEFT).shift(UP * 0.4)
        with self.say("Statistical process control is a handful of formulas, and "
                      "every one of them is a picture."):
            self.play(Write(t1), run_time=1.2, rate_func=rf.linear)
        with self.say("Two of those pictures carry the rest."):
            self.play(Write(t2), run_time=0.8, rate_func=rf.linear)
        self.play(FadeOut(VGroup(t1, t2), shift=UP * 0.2),
                  run_time=0.7, rate_func=rf.ease_in_sine)

    # ---------------------------------------------- act 1: the X̄ chart
    def chart_act(self):
        # seed 2 because σ̂ is estimated in-sample: on seed 7 the largest of the
        # 36 means sat at 3.03 σ̂, so the band never emptied and the act would
        # have narrated "nothing outside" over a readout saying "1 of 36".
        rng = np.random.default_rng(2)
        means = np.array([rng.normal(0.0, 0.09) for _ in range(N_SUB)])
        # σ̂ from the plotted points themselves, which is the whole claim
        sigma_hat = float(means.std(ddof=1))

        title = prose("1 · control limits come from the process", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0, 40, 10], y_range=[-0.42, 0.42, 0.2],
                    x_length=9.4, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.6 + DOWN * 0.35)
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        cl = Line(axes.c2p(0, 0), axes.c2p(40, 0), stroke_color=GREY, stroke_width=2)
        cl_tag = micro("CL", 18).next_to(cl, RIGHT, buff=0.14)

        with self.say("First idea. A control chart plots subgroup averages in "
                      "the order they were made, and its centre line is simply "
                      "their average."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), Create(cl), FadeIn(cl_tag),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        dots = VGroup(*[
            Dot(axes.c2p(i + 1, float(m)), radius=0.05, color=BLUE)
            for i, m in enumerate(means)
        ])
        lab_sd = at_panel(micro("σ̂ FROM THESE POINTS"), 0, value=False)
        val_sd = at_panel(gauge(f"{sigma_hat:.4f}", 26, BLUE), 0)
        with self.say("Let the process talk: thirty six subgroup means, and the "
                      "spread they happen to have.") as tr:
            self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d in dots],
                                  lag_ratio=0.5),
                      run_time=max(2.0, tr.duration * 0.6), rate_func=rf.linear)
            self.play(FadeIn(lab_sd), FadeIn(val_sd),
                      run_time=0.5, rate_func=rf.ease_out_sine)

        # ---- the band is swept outward and the count of outsiders falls ----
        k = ValueTracker(0.0)

        def band() -> VGroup:
            w = k.get_value() * sigma_hat
            return VGroup(*[
                DashedLine(axes.c2p(0, s * w), axes.c2p(40, s * w),
                           dash_length=0.13, stroke_color=YELLOW, stroke_width=2.6)
                for s in (1, -1)
            ])

        def outside() -> int:
            return int(np.count_nonzero(np.abs(means) > k.get_value() * sigma_hat))

        live_band = always_redraw(band)
        lab_k = at_panel(micro("BAND WIDTH"), 1, value=False)
        val_k = always_redraw(lambda: at_panel(
            gauge(f"± {k.get_value():.2f} σ̂", 26, YELLOW), 1))
        lab_out = at_panel(micro("POINTS OUTSIDE IT"), 2, value=False)
        val_out = always_redraw(lambda: at_panel(
            gauge(f"{outside():>2} of {N_SUB}", 26, RED), 2))

        with self.say("Now widen a band around that centre line and count what "
                      "falls outside. By three of those sigmas nothing is, with "
                      "room to spare — and that is where the control limits go.") as tr:
            self.play(FadeIn(live_band), FadeIn(lab_k), FadeIn(val_k),
                      FadeIn(lab_out), FadeIn(val_out),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(k.animate.set_value(3.0),
                      run_time=max(3.0, tr.duration * 0.7), rate_func=rf.ease_out_cubic)

        eq_a = MathTex(r"\mathrm{UCL}", "=", r"\bar{\bar{x}} + 3\hat{\sigma}",
                       font_size=36, color=INK).move_to([1.5, 2.85, 0])
        eq_b = MathTex(r"\mathrm{UCL}", "=", f"+{3 * sigma_hat:.3f}",
                       font_size=36, color=INK).move_to([1.5, 2.85, 0])
        with self.say("Written out, the upper limit is the grand mean plus three "
                      "sigma hat."):
            self.play(Write(eq_a), run_time=1.2, rate_func=rf.linear)
        with self.say("Which for this process is a number the process itself "
                      "chose."):
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        note = prose("limits are learned from the data — specs are dictated by "
                     "the customer", 26, TEAL).move_to(DOWN * 3.45)
        with self.say("Limits come from the data. Specifications come from the "
                      "customer. Confusing those two is the most common mistake "
                      "on a shop floor."):
            self.play(FadeIn(note, shift=UP * 0.12),
                      run_time=1.2, rate_func=rf.ease_out_sine)

        self.beat(0.5)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # --------------------------------------- act 2: capability geometry
    def capability_act(self):
        mu, sg, lsl, usl = 50.03, 0.09, 49.7, 50.3
        cpk = min(usl - mu, mu - lsl) / (3 * sg)
        ppm = ppm_from_cpk(cpk)

        title = prose("2 · capability — where the scrap hides", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[lsl - 0.28, usl + 0.28, 0.2], y_range=[0, 1.25, 0.25],
                    x_length=9.4, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.6 + DOWN * 0.5)
        xlab = micro("MEASURED SIZE (mm)").next_to(axes, DOWN, buff=0.26)

        xs = np.linspace(lsl - 0.28, usl + 0.28, 301)
        pdf = np.exp(-((xs - mu) ** 2) / (2 * sg ** 2))
        curve = axes.plot_line_graph(xs, pdf, add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]

        with self.say("Second idea. Take the same process and plot it against "
                      "the measurement itself. This is where parts land."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(Create(curve), run_time=1.3, rate_func=rf.ease_in_out_sine)

        specs = VGroup(*[
            DashedLine(axes.c2p(v, 0), axes.c2p(v, 1.18), dash_length=0.13,
                       stroke_color=YELLOW, stroke_width=2.6)
            for v in (lsl, usl)
        ])
        spec_tags = VGroup(
            micro("LSL", 18, YELLOW).next_to(axes.c2p(lsl, 0), DOWN, buff=0.30),
            micro("USL", 18, YELLOW).next_to(axes.c2p(usl, 0), DOWN, buff=0.30),
        )
        with self.say("Then the customer's two limits. These were not calculated "
                      "from anything. They were dictated."):
            self.play(Create(specs), FadeIn(spec_tags),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)

        def tail(lo: float, hi: float) -> Polygon:
            m = (xs >= lo) & (xs <= hi)
            return Polygon(*[axes.c2p(a, b) for a, b in zip(xs[m], pdf[m])],
                           axes.c2p(hi, 0), axes.c2p(lo, 0),
                           fill_color=RED, fill_opacity=0.85, stroke_width=0)

        tails = VGroup(tail(float(xs[0]), lsl), tail(usl, float(xs[-1])))
        lab_cpk = at_panel(micro("Cpk, NEAR GAP / 3σ"), 0, value=False)
        val_cpk = at_panel(gauge(f"{cpk:.2f}", 26, RED), 0)
        lab_ppm = at_panel(micro("EXPECTED SCRAP"), 1, value=False)
        val_ppm = at_panel(gauge(f"{ppm:,.0f} ppm", 26, RED), 1)
        with self.say("Everything past them is scrap, and the near gap decides "
                      "how much. Distance to the nearest limit, over three "
                      "sigma, is Cpk."):
            self.play(FadeIn(tails), run_time=0.9, rate_func=rf.ease_out_sine)
            self.play(FadeIn(lab_cpk), FadeIn(val_cpk),
                      FadeIn(lab_ppm), FadeIn(val_ppm),
                      run_time=0.7, rate_func=rf.ease_out_sine)

        # one camera push: the tail is a sliver at this scale, and it is the
        # whole subject. Chrome sized for the wide frame leaves first.
        zoom = 0.42
        chrome = Group(title, xlab, spec_tags, lab_cpk, val_cpk, lab_ppm, val_ppm)
        self.camera.frame.save_state()
        one_in = gauge(f"1 in {round(1e6 / ppm):,} parts", 26, RED).scale(zoom)
        one_in.move_to(axes.c2p(usl + 0.10, 0.22))
        with self.say(f"At this scale the red is a sliver. It is "
                      f"{ppm:,.0f} parts per million — one in "
                      f"{round(1e6 / ppm):,}."):
            self.play(FadeOut(chrome), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(self.camera.frame.animate.scale(zoom).move_to(
                      axes.c2p(usl + 0.02, 0.16)),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(ReplacementTransform(val_ppm.copy().scale(zoom), one_in),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        # one line, not two: stacked at the bottom edge the pair sat on the
        # LSL/USL tags and the axis label
        closing = prose("steady is the chart's question — good enough is "
                        "capability's", 26, TEAL).move_to(DOWN * 3.55)
        with self.say("So the chart tells you whether the process is steady, and "
                      "capability tells you whether steady is good enough."):
            self.play(Restore(self.camera.frame), FadeOut(one_in),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(Group(title, xlab, spec_tags, lab_cpk, val_cpk,
                                   lab_ppm, val_ppm)),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(FadeIn(closing, shift=UP * 0.1),
                      run_time=1.1, rate_func=rf.ease_out_sine)

        self.beat(1.0)
