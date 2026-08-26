"""Three embedded acts, one per formula family, played inside the level pages.

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 5. Each
of the three had a number on screen that nothing on screen produced:

- **ConstantsAct** typed `n = 5 → A₂ = 0.577 ✓ matches AIAG Table B` and
  described the Monte Carlo in a parenthesis. Now d₂ is *derived by motion* —
  the mean range of simulated subgroups walks up a log scale and settles on
  2.33 — and A₂ comes out of `spclab.control_limit_constants(5)`, so the act
  cannot drift from the library the tests check.
- **EWMAMemory** claimed "drift detected ~2× sooner" while Level IV claimed
  four. Both now read the same simulation in `spclab.detection`: 43.6 subgroups
  against 9.8, at a matched false-alarm rate. Its λ is also a knob you watch:
  a tracker sweeps it and the weight bars and memory half-life follow.
- **WERules** hard-coded the four flagged subgroups — and flagged a Rule 3 that
  `western_electric_violations` does not detect on that data. The flags now
  come from the library's own output, so a rule is only claimed where the
  function fires.

Pacing lives in the narration script — see narration.py.

    PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes2.py ConstantsAct
    PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes2.py EWMAMemory
    PYTHONPATH=src .venv/bin/manim -qh src/spclab/scenes2.py WERules

Narrated: prefix any of the above with SPCLAB_VOICE=1.
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, Line, MathTex, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, GrowFromEdge, LaggedStart, ReplacementTransform,
    Restore, TransformMatchingTex, Write,
    always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.detection import ARL1_EWMA, ARL1_SHEW, EWMA_LIMIT, LAM, SIGMA_Z, SPEEDUP
from spclab.formulas import control_limit_constants
from spclab.formulas import western_electric_violations
from spclab.narration import NarratedCameraScene


def act_title(text: str) -> object:
    return prose(text, 30, GREY).to_edge(UP, buff=0.38)


# ===========================================================================
# ACT A — d2 and A2: why dividing by this constant works
# ===========================================================================
N_PARTS = 5
SUBGROUPS = 20_000
CONST = control_limit_constants(N_PARTS)


class ConstantsAct(NarratedCameraScene):
    def construct(self):
        title = act_title("1 · where does A₂ come from?")
        with self.say("Every constant on a control chart is derived, not "
                      "decreed. Here is the one that sets the limits."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        # ---- one subgroup of five, and the only spread you can measure ----
        rng = np.random.default_rng(11)
        vals = np.sort(rng.normal(0, 1, N_PARTS))
        line = Line(LEFT * 4.2, RIGHT * 4.2, stroke_color=GREY, stroke_width=2)
        line.shift(UP * 1.5)
        lab_n = micro("A SUBGROUP OF n = 5 PARTS").next_to(line, UP, buff=0.35)
        dots = VGroup(*[
            Dot(np.array([float(v) * 1.5, 1.5, 0.0]), radius=0.09, color=BLUE)
            for v in vals
        ])
        with self.say("Take five parts off the process. Each one lands "
                      "somewhere, and sigma — the thing you actually want — is "
                      "not one of the numbers you have."):
            self.play(Create(line), FadeIn(lab_n),
                      run_time=0.8, rate_func=rf.ease_in_out_sine)
            self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots],
                                  lag_ratio=0.4),
                      run_time=1.4, rate_func=rf.linear)

        span = Line(np.array([float(vals[0]) * 1.5, 1.15, 0.0]),
                    np.array([float(vals[-1]) * 1.5, 1.15, 0.0]),
                    stroke_color=YELLOW, stroke_width=3)
        span_tag = gauge(f"R = {float(vals[-1] - vals[0]):.2f} σ", 24, YELLOW)
        span_tag.next_to(span, DOWN, buff=0.16)
        with self.say("The range you can measure: largest minus smallest."):
            self.play(Create(span), FadeIn(span_tag),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        # ---- d2 derived by motion: the mean range settles ----
        ranges = np.ptp(np.random.default_rng(42).standard_normal(
            (SUBGROUPS, N_PARTS)), axis=1)
        running = np.cumsum(ranges) / np.arange(1, SUBGROUPS + 1)

        lg = ValueTracker(0.0)

        def done() -> int:
            return int(np.clip(round(10 ** lg.get_value()), 1, SUBGROUPS))

        axes = Axes(x_range=[0, 4, 1], y_range=[1.6, 3.0, 0.4],
                    x_length=8.6, y_length=2.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.9 + DOWN * 1.85)
        xlab = micro("SUBGROUPS SIMULATED (POWERS OF TEN)").next_to(
            axes, DOWN, buff=0.24)
        target = DashedLine(axes.c2p(0, CONST["d2"]), axes.c2p(4, CONST["d2"]),
                            dash_length=0.12, stroke_color=TEAL, stroke_width=2)
        target_tag = micro(f"d₂ = {CONST['d2']:.4f}", 18, TEAL).next_to(
            axes.c2p(4, CONST["d2"]), RIGHT, buff=0.12)

        traced = always_redraw(lambda: axes.plot_line_graph(
            np.log10(np.arange(1, done() + 1)), running[:done()],
            add_vertex_dots=False, line_color=YELLOW, stroke_width=3
        )["line_graph"] if done() > 1 else VGroup())

        lab_m = at_panel(micro("SUBGROUPS"), 0, value=False)
        val_m = always_redraw(lambda: at_panel(
            gauge(f"{done():>6,}", 26, INK), 0))
        lab_r = at_panel(micro("MEAN RANGE, R̄"), 1, value=False)
        val_r = always_redraw(lambda: at_panel(
            gauge(f"{running[done() - 1]:.4f}", 26, YELLOW), 1))

        with self.say("Now do that again, and again. Twenty thousand subgroups "
                      "of five, and watch their mean range.") as tr:
            self.play(Create(axes), FadeIn(xlab),
                      run_time=0.8, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(traced), FadeIn(lab_m), FadeIn(val_m),
                      FadeIn(lab_r), FadeIn(val_r),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(lg.animate.set_value(np.log10(SUBGROUPS)),
                      run_time=max(3.4, tr.duration * 0.7), rate_func=rf.ease_in_out_sine)

        with self.say("It settles. The mean range of n standard normals is a "
                      "fixed multiple of sigma, and that multiple has a name: "
                      "d two."):
            self.play(Create(target), FadeIn(target_tag),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)

        # ---- and therefore A2, from the library, not from a table ----
        self.play(FadeOut(Group(line, lab_n, dots, span, span_tag)),
                  run_time=0.6, rate_func=rf.ease_in_sine)

        eq1 = MathTex(r"\hat{\sigma}", "=", r"\frac{\bar{R}}{d_2}",
                      font_size=40, color=INK).move_to([-3.3, 2.1, 0])
        with self.say("So R bar over d two estimates sigma, out of ranges you "
                      "genuinely measured."):
            self.play(Write(eq1), run_time=1.1, rate_func=rf.linear)

        eq2 = MathTex(r"A_2", "=", r"\frac{3}{d_2\sqrt{n}}",
                      font_size=40, color=INK).move_to([0.4, 2.1, 0])
        with self.say("Feed it into three sigma limits, divide by root n because "
                      "you are charting subgroup means, and gather the "
                      "constants. That is A two."):
            self.play(Write(eq2), run_time=1.2, rate_func=rf.linear)

        eq3 = MathTex(r"A_2", "=", f"{CONST['A2']:.4f}",
                      font_size=40, color=INK).move_to([0.4, 2.1, 0])
        with self.say(f"At n of five, {CONST['A2']:.4f} — the number in the AIAG "
                      "table, computed here from the simulation rather than "
                      "copied out of it."):
            self.play(TransformMatchingTex(eq2, eq3),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        self.beat(0.8)


# ===========================================================================
# ACT B — EWMA: memory buys sensitivity
# ===========================================================================
class EWMAMemory(NarratedCameraScene):
    def construct(self):
        self.weights_act()
        self.limits_act()

    def weights_act(self):
        title = act_title("2 · EWMA — a filter with one knob")
        head = MathTex(r"z_i", "=", r"\lambda x_i + (1-\lambda) z_{i-1}",
                       font_size=38, color=INK).move_to([-1.4, 2.2, 0])
        with self.say("An EWMA chart has exactly one knob, and everything else "
                      "follows from it. Each new subgroup is blended with "
                      "everything that came before."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Write(head), run_time=1.3, rate_func=rf.linear)

        # the knob, swept: bars are the weights, and the half-life follows
        lam = ValueTracker(0.5)
        K, BW, GAP = 14, 0.42, 0.13
        total = K * BW + (K - 1) * GAP
        x0 = -total / 2 - 0.8
        base = Line(np.array([x0 - 0.15, -1.85, 0.0]),
                    np.array([x0 + total + 0.15, -1.85, 0.0]),
                    stroke_color=GREY, stroke_width=1.5)
        base_tag = micro("HOW MUCH EACH PAST SUBGROUP STILL COUNTS").next_to(
            base, DOWN, buff=0.24)

        def bars() -> VGroup:
            lv = lam.get_value()
            w = np.array([lv * (1 - lv) ** i for i in range(K)])
            grp = VGroup()
            for i, wi in enumerate(w):
                h = max(2.6 * wi / w[0], 0.02)
                grp.add(Rectangle(width=BW, height=h, fill_color=BLUE,
                                  fill_opacity=0.85, stroke_width=0)
                        .move_to(np.array([x0 + i * (BW + GAP) + BW / 2,
                                           -1.85 + h / 2, 0.0])))
            return grp

        def half_life(lv: float) -> float:
            """Subgroups back before a weight has halved: ln½ / ln(1−λ)."""
            return float(np.log(0.5) / np.log(1 - lv))

        live_bars = always_redraw(bars)
        lab_l = at_panel(micro("λ, THE ONE KNOB"), 0, value=False)
        val_l = always_redraw(lambda: at_panel(
            gauge(f"{lam.get_value():.2f}", 26, YELLOW), 0))
        lab_h = at_panel(micro("MEMORY HALF-LIFE"), 1, value=False)
        val_h = always_redraw(lambda: at_panel(
            gauge(f"{half_life(lam.get_value()):.1f} sub", 26, TEAL), 1))

        with self.say("Unroll the recursion and the weights fall away "
                      "geometrically. At lambda one half the chart has almost "
                      "no memory: one subgroup back already counts for half.") as tr:
            self.play(GrowFromEdge(base, LEFT), FadeIn(base_tag),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(FadeIn(live_bars), FadeIn(lab_l), FadeIn(val_l),
                      FadeIn(lab_h), FadeIn(val_h),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(lam.animate.set_value(0.05),
                      run_time=max(2.6, tr.duration * 0.45), rate_func=rf.ease_in_out_sine)

        with self.say("Turn it down and the tail grows: the chart starts "
                      "remembering a dozen subgroups at a time, and reacts to "
                      "none of them quickly.") as tr:
            self.play(lam.animate.set_value(LAM),
                      run_time=max(2.0, tr.duration * 0.5), rate_func=rf.ease_in_out_sine)

        with self.say(f"Zero point two is the usual compromise: half the weight "
                      f"is gone by {half_life(LAM):.1f} subgroups back."):
            self.beat(0.6)

        self.beat(0.4)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)

    def limits_act(self):
        title = act_title("…so its limits tighten, and drift cannot hide")
        n = 40
        i = np.arange(1, n + 1)
        f = np.sqrt(LAM / (2 - LAM) * (1 - (1 - LAM) ** (2 * i)))

        axes = Axes(x_range=[1, n, 10], y_range=[-3.4, 3.4, 1],
                    x_length=9.2, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.7 + DOWN * 0.4)
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        shew = VGroup(*[
            DashedLine(axes.c2p(1, v), axes.c2p(n, v), dash_length=0.12,
                       stroke_color=GREY, stroke_width=1.6)
            for v in (3, -3)
        ])
        shew_tag = micro("SHEWHART ±3σ", 18).next_to(shew[0], UP, buff=0.10)

        with self.say("That memory changes the limits themselves. A Shewhart "
                      "chart holds the same three sigma either side, forever."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(Create(shew), FadeIn(shew_tag),
                      run_time=0.7, rate_func=rf.ease_in_out_sine)

        up = axes.plot_line_graph(i, 3 * f, add_vertex_dots=False,
                                  line_color=YELLOW, stroke_width=3)["line_graph"]
        lo = axes.plot_line_graph(i, -3 * f, add_vertex_dots=False,
                                  line_color=YELLOW, stroke_width=3)["line_graph"]
        asym = 3 * SIGMA_Z
        asym_tag = micro(f"ASYMPTOTE ±{asym:.2f}σ", 18, YELLOW).next_to(
            axes.c2p(n, asym), RIGHT, buff=0.10)
        with self.say("The EWMA limits start wide, because at subgroup one there "
                      "is no accumulated evidence, then close as the weighted "
                      "history builds."):
            self.play(Create(up), Create(lo),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
        with self.say(f"They settle near one third of a sigma times three — a "
                      f"band {3 / asym:.1f} times narrower than the Shewhart one."):
            self.play(FadeIn(asym_tag), run_time=0.7, rate_func=rf.ease_out_sine)

        eq_a = MathTex(r"\sigma_z", "=",
                       r"\sigma\sqrt{\frac{\lambda}{2-\lambda}}",
                       font_size=36, color=INK).move_to([2.3, 2.55, 0])
        eq_b = MathTex(r"\sigma_z", "=", f"{SIGMA_Z:.3f}\\,\\sigma",
                       font_size=36, color=INK).move_to([2.3, 2.55, 0])
        with self.say("The width comes from one expression, and at lambda zero "
                      "point two it is a third of a sigma."):
            self.play(Write(eq_a), run_time=1.2, rate_func=rf.linear)
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        # the payoff, from the same simulation Level IV reads
        lab_s = at_panel(micro("SHEWHART · 1σ SHIFT"), 0, value=False)
        val_s = at_panel(gauge(f"{ARL1_SHEW:.1f} subgroups", 24, GREY), 0)
        lab_e = at_panel(micro("EWMA · 1σ SHIFT"), 1, value=False)
        val_e = at_panel(gauge(f"{ARL1_EWMA:.1f} subgroups", 24, YELLOW), 1)
        with self.say("Tighter limits on smoothed data catch a small shift much "
                      f"earlier. Simulated at a matched false alarm rate: "
                      f"{ARL1_SHEW:.0f} subgroups against {ARL1_EWMA:.0f}."):
            self.play(FadeIn(lab_s), FadeIn(val_s), FadeIn(lab_e), FadeIn(val_e),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        ratio = gauge(f"{SPEEDUP:.1f}× sooner, same false alarm rate", 26, YELLOW)
        ratio.move_to(DOWN * 3.45)
        with self.say(f"{SPEEDUP:.1f} times sooner, and lambda is the knob that "
                      "decides how much of the past the chart keeps."):
            self.play(ReplacementTransform(VGroup(val_s.copy(), val_e.copy()), ratio),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        self.beat(0.8)


# ===========================================================================
# ACT C — Western Electric rules: pattern detection
# ===========================================================================
def we_series() -> np.ndarray:
    """Forty subgroups built to trip all four rules — and checked, not assumed.

    The old act flagged four hard-coded indices, one of which
    `western_electric_violations` never detected on its data. This series is
    only used with the library's own findings.
    """
    rng = np.random.default_rng(23)
    z = (list(rng.normal(0, 0.45, 10))
         + [3.3]                                  # rule 1
         + list(rng.normal(0, 0.45, 3))
         + [2.25, 2.45]                           # rule 2
         + list(rng.normal(0, 0.45, 3))
         + [1.4, 1.6, 0.5, 1.35, 1.5]             # rule 3
         + list(rng.normal(0, 0.45, 3))
         + [-0.55] * 8                            # rule 4
         + list(rng.normal(0, 0.45, 5)))
    return np.round(np.array(z[:40]), 3)


class WERules(NarratedCameraScene):
    def construct(self):
        z = we_series()
        n = len(z)

        # first firing of each rule, from the library the tests check
        found: dict[str, int] = {}
        for idx, desc in western_electric_violations(z, 0.0, 1.0):
            found.setdefault(desc, idx)

        title = act_title("3 · the rules read the run, not the point")
        axes = Axes(x_range=[0, n, 10], y_range=[-3.6, 3.6, 1],
                    x_length=9.4, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(LEFT * 0.6 + DOWN * 0.55)
        xlab = micro("SUBGROUP").next_to(axes, DOWN, buff=0.26)
        zones = VGroup()
        for v, col in ((3, RED), (-3, RED), (2, GREY), (-2, GREY),
                       (1, GREY), (-1, GREY)):
            zones.add(DashedLine(axes.c2p(0, v), axes.c2p(n, v),
                                 dash_length=0.10, stroke_color=col,
                                 stroke_width=1.6 if abs(v) == 3 else 1.0))
        # tags on the left: the right-hand end of every zone line runs into the
        # readout column, and a '3σ' tag there lands on top of a readout
        zone_tags = VGroup(
            micro("3σ", 16, RED).next_to(axes.c2p(0, 3), LEFT, buff=0.12),
            micro("2σ", 16).next_to(axes.c2p(0, 2), LEFT, buff=0.12),
            micro("1σ", 16).next_to(axes.c2p(0, 1), LEFT, buff=0.12),
        )
        cl = Line(axes.c2p(0, 0), axes.c2p(n, 0), stroke_color=GREY, stroke_width=2)

        with self.say("A control limit sees one point at a time. The Western "
                      "Electric rules read the run, so the chart is divided into "
                      "one, two and three sigma zones."):
            self.play(FadeIn(title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(axes), FadeIn(xlab), Create(cl),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.play(Create(zones), FadeIn(zone_tags),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)

        dots = VGroup(*[
            Dot(axes.c2p(k + 1, float(v)), radius=0.05,
                color=RED if abs(v) > 3 else BLUE)
            for k, v in enumerate(z)
        ])
        i = ValueTracker(0.0)

        def seen() -> int:
            return int(np.clip(np.floor(i.get_value() + 1e-9), 0, n))

        live_dots = always_redraw(lambda: VGroup(*[dots[k] for k in range(seen())]))
        lab_k = at_panel(micro("SUBGROUP"), 0, value=False)
        val_k = always_redraw(lambda: at_panel(gauge(f"{seen():>2}", 26, INK), 0))
        lab_f = at_panel(micro("RULES FIRED"), 1, value=False)
        val_f = always_redraw(lambda: at_panel(gauge(
            f"{sum(1 for v in found.values() if v < seen()):>1} of 4", 26, YELLOW), 1))

        self.add(live_dots)
        with self.say("Forty subgroups from a process that looks calm at a "
                      "glance. Only one point ever leaves the limits.") as tr:
            self.play(FadeIn(lab_k), FadeIn(val_k), FadeIn(lab_f), FadeIn(val_f),
                      run_time=0.5, rate_func=rf.ease_out_sine)
            self.play(i.animate.set_value(float(n)),
                      run_time=max(3.0, tr.duration * 0.7), rate_func=rf.linear)

        # each flag is placed where the library says the rule fired
        palette = {"Rule 1": RED, "Rule 2": YELLOW, "Rule 3": TEAL, "Rule 4": BLUE}
        rows = VGroup()
        marks = VGroup()
        for desc, idx in sorted(found.items(), key=lambda kv: kv[1]):
            rule = desc.split(":")[0]
            col = palette.get(rule, INK)
            rows.add(gauge(f"{desc}   at {idx + 1}", 16, col))
        rows.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        # below the title, not centred on it: a four-row group positioned by its
        # centre puts its first row straight through the headline
        rows.next_to(title, DOWN, buff=0.30).to_edge(LEFT, buff=0.45)

        for row, (desc, idx) in zip(rows, sorted(found.items(), key=lambda kv: kv[1])):
            rule = desc.split(":")[0]
            col = palette.get(rule, INK)
            ring = Dot(axes.c2p(idx + 1, float(z[idx])), radius=0.13, color=col,
                       fill_opacity=0.0, stroke_width=3)
            marks.add(ring)
            spoken = desc.replace("Rule 1:", "Rule one:") \
                         .replace("Rule 2:", "Rule two:") \
                         .replace("Rule 3:", "Rule three:") \
                         .replace("Rule 4:", "Rule four:") \
                         .replace("σ", " sigma")
            with self.say(f"{spoken}. Subgroup {idx + 1}."):
                self.play(FadeIn(ring, scale=1.6), FadeIn(row),
                          run_time=0.8, rate_func=rf.ease_out_back)

        # one camera push, on the eight-in-a-row: the pattern no point shows
        rule4 = next((v for k, v in found.items() if k.startswith("Rule 4")), None)
        if rule4 is not None:
            zoom = 0.45
            chrome = Group(title, xlab, rows, zone_tags, lab_k, val_k, lab_f, val_f)
            self.camera.frame.save_state()
            tag = gauge("eight in a row, none of them out of limits", 24, BLUE)
            tag.scale(zoom).move_to(axes.c2p(rule4 - 2, -1.55))
            with self.say("The last one is the point of the whole idea. Eight "
                          "subgroups in a row on one side of centre, and not one "
                          "of them anywhere near a limit."):
                for m in (val_k, val_f):
                    m.clear_updaters()
                self.play(FadeOut(chrome), run_time=0.5, rate_func=rf.ease_in_sine)
                self.play(self.camera.frame.animate.scale(zoom).move_to(
                          axes.c2p(rule4 - 3, -0.55)),
                          run_time=1.4, rate_func=rf.ease_in_out_sine)
                self.play(FadeIn(tag), run_time=0.7, rate_func=rf.ease_out_sine)

            verdict = prose("a shift too small to breach a limit still shows in "
                            "the pattern", 26, TEAL).move_to(DOWN * 3.45)
            with self.say("A shift too small to breach a limit still shows up in "
                          "the pattern, which is what the rules are for."):
                self.play(Restore(self.camera.frame), FadeOut(tag),
                          run_time=1.3, rate_func=rf.ease_in_out_sine)
                self.play(FadeIn(Group(title, xlab, rows, zone_tags)),
                          FadeIn(verdict, shift=UP * 0.1),
                          run_time=1.0, rate_func=rf.ease_out_sine)

        self.beat(0.8)
