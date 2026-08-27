"""LEVEL 4 act — 'Detection theory: charts as evidence accumulators.'

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 4.

The old act's punchline was a typed caption: "(ARL: ~4× faster detection of 1σ
drift)", with the spoken line naming "about ten subgroups instead of forty
four". Nothing on screen produced those numbers. Now:

- **The EWMA limit is calibrated at render time**, by bisection on a simulated
  in-control run length, so the claim "same false-alarm rate" is a computed
  result rather than an assertion. Both charts are shown with their ARL0.
- **The speed-up is simulated, not typed.** Thousands of 1σ shifts are run
  through both rules at render time; the two average run lengths and their
  ratio are read off that simulation, and the ratio arrives by morph from the
  two numbers it divides.
- **Evidence accumulating is drawn as accumulation**: a tracker walks the
  subgroup index while the EWMA path is traced behind a rider and a live
  readout carries the statistic, so the crossing is watched, not announced.
- One camera push, on the crossing, where the raw point still looks innocent.
- Every play carries a deliberate rate_func; strings are in the site's two
  voices; the recursion is Computer Modern maths and morphs term into term.

Pacing still lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level09_scene.py Level09
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level09_scene.py Level09
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, Line, MathTex, Rectangle, ValueTracker, VGroup,
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
from spclab.detection import (
    ARL0_EWMA, ARL0_SHEW, ARL1_EWMA, ARL1_SHEW, EWMA_LIMIT, LAM,
    SHEWHART_ARL0, SPEEDUP,
)
from spclab.narration import NarratedCameraScene

# The demonstration process: 80 subgroups, quiet until 20, then a ramp of
# 0.06 σ per subgroup. The old act ramped at 0.15 σ, which reaches 6 σ inside
# the window — on that data the Shewhart chart caught the drift one subgroup
# after the EWMA, so the single realisation contradicted the averages it was
# supposed to illustrate. This ramp is slow enough to be the failure mode the
# act is about, and seed 35 is a run whose lead matches the simulated ARLs.
N_SUB, SHIFT_AT, DRIFT, SEED = 80, 20, 0.06, 35


def drifting_process():
    """One process: quiet, then a slow ramp. Same data for both charts."""
    rng = np.random.default_rng(SEED)
    raw = rng.normal(0, 1, N_SUB) + np.where(
        np.arange(N_SUB) >= SHIFT_AT, (np.arange(N_SUB) - SHIFT_AT) * DRIFT, 0.0)
    z, zs = 0.0, []
    for v in raw:
        z = LAM * v + (1 - LAM) * z
        zs.append(z)
    return raw, np.array(zs)


RAW, ZS = drifting_process()
# where each rule fires on this run, and how far the mean had already moved
DET_SHEW = int(next(k for k, v in enumerate(RAW) if abs(v) > 3.0))
DET_EWMA = int(next(k for k, v in enumerate(ZS) if abs(v) > EWMA_LIMIT))
OFF_SHEW = (DET_SHEW - SHIFT_AT) * DRIFT
OFF_EWMA = (DET_EWMA - SHIFT_AT) * DRIFT


class Level09(NarratedCameraScene):
    def construct(self):
        self.part1_blind_spot()
        self.part2_memory_wins()

    # --------------- part 1: single points cannot see slow drift ------------
    def part1_blind_spot(self):
        raw, _ = drifting_process()
        title = prose("Level 9 · the blind spot: drift hides inside noise",
                      30, GREY).to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0, N_SUB, 10], y_range=[-3.8, 3.8, 1],
                    x_length=9.6, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.5 + DOWN * 0.35)
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        cl = Line(axes.c2p(0, 0), axes.c2p(N_SUB, 0), stroke_color=GREY, stroke_width=2)

        with self.say("Slow drift is the most expensive failure mode in "
                      "manufacturing, because every single measurement of it "
                      "looks acceptable."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), Create(cl),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        limits = VGroup(*[
            DashedLine(axes.c2p(0, v), axes.c2p(N_SUB, v), dash_length=0.13,
                       stroke_color=YELLOW, stroke_width=2.4)
            for v in (3, -3)
        ])
        tags = VGroup(
            micro("UCL", 18, YELLOW).next_to(limits[0], RIGHT, buff=0.14),
            micro("LCL", 18, YELLOW).next_to(limits[1], RIGHT, buff=0.14),
        )
        lab_arl = at_panel(micro("FALSE ALARM, 1 IN"), 0, value=False)
        val_arl = at_panel(gauge(f"{SHEWHART_ARL0:,.0f}", 26, YELLOW), 0)
        with self.say("A Shewhart chart, limits at plus and minus three sigma, "
                      "which buys one false alarm in three hundred and seventy "
                      "subgroups."):
            self.play(Create(limits), FadeIn(tags),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(lab_arl), FadeIn(val_arl),
                      run_time=0.5, rate_func=rf.ease_out_sine)

        # the walk: points arrive under the tracker, and the readout carries the
        # worst point seen so far, so "no point breaches" is measured live
        i = ValueTracker(0.0)
        dots = VGroup(*[
            Dot(axes.c2p(k + 1, min(v, 3.7)), radius=0.055,
                color=RED if abs(v) > 3 else BLUE)
            for k, v in enumerate(raw)
        ])

        def seen() -> int:
            return int(np.clip(np.floor(i.get_value() + 1e-9), 0, N_SUB))

        live_dots = always_redraw(lambda: VGroup(*[dots[k] for k in range(seen())]))
        lab_k = at_panel(micro("SUBGROUP"), 1, value=False)
        val_k = always_redraw(lambda: at_panel(
            gauge(f"{seen():>2}", 26, INK), 1))
        lab_worst = at_panel(micro("WORST POINT SO FAR"), 2, value=False)
        val_worst = always_redraw(lambda: at_panel(
            gauge(f"{(np.abs(raw[:max(seen(), 1)]).max()):.2f} σ", 26, BLUE), 2))

        self.add(live_dots)
        with self.say("The first twenty subgroups are noise around the target.") as tr:
            self.play(FadeIn(lab_k), FadeIn(val_k), FadeIn(lab_worst), FadeIn(val_worst),
                      run_time=0.5, rate_func=rf.ease_out_sine)
            self.play(i.animate.set_value(float(SHIFT_AT)),
                      run_time=max(1.8, tr.duration * 0.55), rate_func=rf.linear)

        drift_mark = DashedLine(axes.c2p(SHIFT_AT, -3.8), axes.c2p(SHIFT_AT, 3.8),
                                dash_length=0.1, stroke_color=RED, stroke_width=2)
        drift_tag = micro("DRIFT STARTS", 18, RED).next_to(
            axes.c2p(SHIFT_AT, 3.8), UP, buff=0.12)
        with self.say(f"Then the mean starts walking, {DRIFT} sigma per subgroup. "
                      "Slow enough that no single measurement looks wrong, and "
                      "the chart carries on saying nothing.") as tr:
            self.play(Create(drift_mark), FadeIn(drift_tag),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(i.animate.set_value(float(DET_SHEW + 1)),
                      run_time=max(3.0, tr.duration * 0.7), rate_func=rf.linear)

        ring = Dot(axes.c2p(DET_SHEW + 1, min(RAW[DET_SHEW], 3.7)),
                   radius=0.16, color=RED, fill_opacity=0.0, stroke_width=3)
        verdict = prose(f"first violation at subgroup {DET_SHEW + 1} — "
                        f"{DET_SHEW - SHIFT_AT} subgroups of drift, unreported",
                        26, RED).move_to(DOWN * 3.45)
        with self.say(f"The first violation lands at subgroup {DET_SHEW + 1}. "
                      f"That is {DET_SHEW - SHIFT_AT} subgroups after the drift "
                      f"began, by which time the mean has moved "
                      f"{OFF_SHEW:.1f} sigma and every part in between was made "
                      "by a process nobody knew had changed."):
            self.play(FadeIn(ring, scale=1.6), run_time=0.6, rate_func=rf.ease_out_back)
            self.play(FadeIn(verdict, shift=UP * 0.12),
                      run_time=1.1, rate_func=rf.ease_out_sine)

        with self.say("Each point was judged on its own and then forgotten. "
                      "That is the whole weakness: the chart has no memory."):
            self.play(i.animate.set_value(float(N_SUB)),
                      run_time=1.6, rate_func=rf.linear)

        self.beat(0.6)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    # ------------------ part 2: a chart that accumulates evidence -----------
    def part2_memory_wins(self):
        raw, zs = RAW, ZS
        det = DET_EWMA

        title = prose("…but a chart with memory accumulates evidence", 30, GREY)
        title.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[0, N_SUB, 10], y_range=[-3.8, 3.8, 1],
                    x_length=9.6, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.5 + DOWN * 0.35)
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        cl = Line(axes.c2p(0, 0), axes.c2p(N_SUB, 0), stroke_color=GREY, stroke_width=2)
        ghost = VGroup(*[
            Dot(axes.c2p(k + 1, min(v, 3.7)), radius=0.035, color=BLUE,
                fill_opacity=0.28)
            for k, v in enumerate(raw)
        ])

        with self.say("Same process, same data, same false alarm budget — and a "
                      "statistic that remembers. The faint points are the raw "
                      "measurements from before."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), Create(cl), FadeIn(ghost),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        eq_a = MathTex(r"z_i", "=", r"\lambda x_i + (1-\lambda) z_{i-1}",
                       font_size=36, color=INK).move_to([1.6, 2.75, 0])
        eq_b = MathTex(r"z_i", "=", r"0.2\,x_i + 0.8\,z_{i-1}",
                       font_size=36, color=INK).move_to([1.6, 2.75, 0])
        with self.say("Each new subgroup gets a fifth of the weight and the "
                      "running statistic keeps the rest."):
            self.play(Write(eq_a), run_time=1.2, rate_func=rf.linear)
        with self.say("With lambda at zero point two, that is one part new and "
                      "four parts memory."):
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        limits = VGroup(*[
            DashedLine(axes.c2p(0, v), axes.c2p(N_SUB, v), dash_length=0.13,
                       stroke_color=YELLOW, stroke_width=2.4)
            for v in (EWMA_LIMIT, -EWMA_LIMIT)
        ])
        lab_lim = at_panel(micro("EWMA LIMIT"), 0, value=False)
        val_lim = at_panel(gauge(f"± {EWMA_LIMIT:.2f} σ", 26, YELLOW), 0)
        lab_a0 = at_panel(micro("FALSE ALARM, 1 IN"), 1, value=False)
        val_a0 = at_panel(gauge(f"{ARL0_EWMA:,.0f}", 26, YELLOW), 1)

        with self.say(f"Its limits are not plus and minus three. They are "
                      f"calibrated by simulation until this chart cries wolf as "
                      f"rarely as the last one: one alarm in "
                      f"{ARL0_EWMA:,.0f} quiet subgroups against "
                      f"{SHEWHART_ARL0:,.0f}."):
            self.play(Create(limits), run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(lab_lim), FadeIn(val_lim), FadeIn(lab_a0), FadeIn(val_a0),
                      run_time=0.6, rate_func=rf.ease_out_sine)

        # the accumulation, traced
        i = ValueTracker(0.0)

        def seen() -> int:
            return int(np.clip(np.floor(i.get_value() + 1e-9), 1, N_SUB))

        def path() -> VGroup:
            """The statistic so far, segment by segment, red past the limit."""
            k = seen()
            pts = [axes.c2p(m + 1, float(np.clip(zs[m], -3.7, 3.7))) for m in range(k)]
            if len(pts) < 2:
                return VGroup(Dot(pts[0], radius=0.05, color=TEAL))
            segs = VGroup()
            for m in range(k - 1):
                breached = abs(zs[m + 1]) > EWMA_LIMIT
                segs.add(Line(pts[m], pts[m + 1],
                              stroke_color=RED if breached else TEAL,
                              stroke_width=3.5))
            return segs

        live_path = always_redraw(path)
        rider = always_redraw(lambda: Dot(
            axes.c2p(seen(), float(np.clip(zs[seen() - 1], -3.7, 3.7))),
            radius=0.08, color=YELLOW))
        lab_z = at_panel(micro("EVIDENCE  z"), 2, value=False)
        val_z = always_redraw(lambda: at_panel(
            gauge(f"{zs[seen() - 1]:+.2f} σ", 26, TEAL), 2))

        with self.say(f"Watch the same {N_SUB} subgroups again. While the process "
                      "is quiet the statistic wanders near zero, because new "
                      "noise keeps cancelling old noise.") as tr:
            self.play(FadeIn(live_path), FadeIn(rider), FadeIn(lab_z), FadeIn(val_z),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(i.animate.set_value(float(SHIFT_AT)),
                      run_time=max(2.0, tr.duration * 0.55), rate_func=rf.linear)

        with self.say("Once the drift starts, the noise still cancels but the "
                      "drift does not. It is the same direction every time, so "
                      "it adds up.") as tr:
            self.play(i.animate.set_value(float(det + 1)),
                      run_time=max(2.0, tr.duration * 0.6), rate_func=rf.linear)

        # camera push on the crossing: the raw point there is unremarkable
        zoom = 0.5
        chrome = Group(title, xlab, eq_b, lab_lim, val_lim, lab_a0, val_a0,
                       lab_z, val_z)
        self.camera.frame.save_state()
        cross_tag = gauge(f"z = {zs[det]:+.2f} σ    raw point = {raw[det]:+.2f} σ",
                          24, YELLOW).scale(zoom)
        cross_tag.next_to(axes.c2p(det + 1, zs[det]), UP, buff=0.45 * zoom)
        with self.say(f"It crosses the limit at subgroup {det + 1}, with the mean "
                      f"only {OFF_EWMA:.1f} sigma off, and the raw measurement "
                      f"there sitting at {raw[det]:+.2f} sigma — a number no "
                      "Shewhart chart would ever look at twice. The other chart "
                      f"waited until subgroup {DET_SHEW + 1}, "
                      f"{DET_SHEW - det} subgroups later."):
            for m in (val_z,):
                m.clear_updaters()
            self.play(FadeOut(chrome), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(self.camera.frame.animate.scale(zoom).move_to(
                      axes.c2p(det + 1, zs[det] + 0.4)),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(cross_tag), run_time=0.7, rate_func=rf.ease_out_sine)

        # the speed-up, simulated at render time and restated by morph
        lab_s = at_panel(micro("SHEWHART · 1σ SHIFT"), 0, value=False)
        val_s = at_panel(gauge(f"{ARL1_SHEW:.1f} subgroups", 24, BLUE), 0)
        lab_e = at_panel(micro("EWMA · 1σ SHIFT"), 1, value=False)
        val_e = at_panel(gauge(f"{ARL1_EWMA:.1f} subgroups", 24, YELLOW), 1)
        with self.say("That is one drift. Run thousands of them and the average "
                      "wait to detect a one sigma shift comes out at "
                      f"{ARL1_SHEW:.0f} subgroups for the Shewhart rule and "
                      f"{ARL1_EWMA:.0f} for this one."):
            self.play(Restore(self.camera.frame), FadeOut(cross_tag),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(Group(title, xlab)),
                      FadeIn(lab_s), FadeIn(val_s), FadeIn(lab_e), FadeIn(val_e),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        ratio = gauge(f"{SPEEDUP:.1f}× sooner, at the same false alarm rate",
                      28, YELLOW).move_to(DOWN * 3.45)
        with self.say(f"Divide them: {SPEEDUP:.1f} times sooner, bought with no "
                      "extra false alarms at all. That trade is the whole of "
                      "detection theory."):
            self.play(ReplacementTransform(VGroup(val_s.copy(), val_e.copy()), ratio),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        self.beat(1.0)
