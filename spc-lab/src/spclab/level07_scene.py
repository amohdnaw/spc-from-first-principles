"""LEVEL 7 act A — 'Every added signal rule buys earlier detection by spending a
fixed stream of false alarms.'

Rebuilt 2026-09-02 against `storyboards/spc-level-07-act-a.html` and
`specs/spc-visual-depth-pilot-contract.md`. The storyboard is authoritative for
shot order, per-shot transformation and exit state; this file is its Manim
realisation and adds nothing that is not on that page.

The act is six shots on **one** stage. An in-control curve, a shifted curve and
one decision boundary are created in A1 and are still the same Mobjects in A6.
Nothing is faded out and rebuilt: every later shot transforms what surrounds
them.

- **A1** steps the boundary out in sigma widths, takes a prediction, then slides
  a copy of the curve to `SHIFT`. No symbol is allowed on screen.
- **A2** fills the two errors as areas *first* — the in-control tail beyond the
  boundary, and the body of the shifted curve inside it — and only then morphs
  the plain-language labels into α and β.
- **A3** sweeps the shift across `SHIFTS` with a tracker while the missed-shift
  area shrinks and a power column rises, then kills the obvious escape route by
  pulling the boundary inside `LIMIT` and showing the α area fatten.
- **A4** drops one point inside the boundary and answers it twice, in two
  objects that coexist and disagree: a chart verdict, and the point's own tail
  area peeled off the board into an evidence chip.
- **A5** shrinks the board into the upper third and spends the rest of the frame
  on one cost board: two bars on a shared log axis of subgroups, three stops.
- **A6** prices the same purchase at `BIG_SHIFT`. The false-alarm bar is not
  animated at all; the catch bar collapses. The act ends on the question Act B
  opens with.

Every number on screen is computed here from `spclab.evidence` (or, for the one
middle stop at `BIG_SHIFT`, from `spclab.level07_mastery.detection_delay`, which
reads the same table). No alpha, beta, power, p-value, run length, ratio or
published figure is typed into this file.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_scene.py Level07
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_scene.py Level07
"""
from __future__ import annotations

import math

import numpy as np
from manim import (
    Axes, Dot, Group, Line, MathTex, Polygon, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Indicate, ReplacementTransform, Restore, Transform,
    Write, always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, norm_pdf, prose, within_frame,
)
from spclab.evidence import (
    ALL_RULES, ALPHA_1, ARL0_ALL, ARL0_ONE_RULE, ARL1_ALL, ARL1_FROM_POWER,
    ARL1_ONE_RULE, ARL_BIG_ALL, ARL_BIG_ONE, BETA_AT, BIG_SHIFT,
    CHAMP_WOODALL_ARL0, FALSE_ALARM_COST, LIMIT, POWER_AT, P_AT_2_5, P_AT_3,
    RULES, RULE_TEXT, SENSITIVITY_GAIN, SHIFT, SHIFTS, TRADE, alpha_one_point,
    beta_one_point, cumulative_sets, first_violation, p_value, power_one_point,
)
from spclab.level07_mastery import detection_delay
from spclab.narration import NarratedCameraScene

# ---------------------------------------------------------------------------
# Geometry of the one stage
# ---------------------------------------------------------------------------
XMIN, XMAX = -4.6, 6.8            # the plotted statistic, in its own sigma
STEP = 0.08                       # sampling of every redrawn curve
BOARD_ORIGIN = np.array([-2.30, -1.90, 0.0])   # frame point of data (0, 0), A1-A4
CURVE_TOP = 0.42                  # data height the boundary verticals reach

# A3's counterexample: the escape route a viewer reaches for before the rules
# are offered. Not a result — it is a limit *position*, and every number read
# off it comes back through `alpha_one_point` and `power_one_point`.
TIGHT_LIMIT = 2.0

# A5 layout: the board shrinks and the cost board takes the rest of the frame.
BOARD_SCALE = 0.60
BOARD_ORIGIN_A5 = np.array([-2.20, 2.05, 0.0])
LANE_FIRST = 0.20                 # frame units below the axis for subgroup 1
LANE_STEP = 0.155
LANE_DEPTH = 1.45

COST_LEFT, COST_RIGHT = -5.85, 5.10
Y_BAR_A, Y_BAR_B = -0.35, -2.05   # false-alarm bar, catch bar
Y_TRAVEL_A, Y_TRAVEL_B = -0.92, -2.55
Y_TRAVEL_LAID = -2.84             # the cost length laid alongside the benefit
Y_COST_AXIS = -3.25
BAR_H = 0.42

SETS = cumulative_sets()
# rule 1, rules 1+2, all four — the storyboard's three stops, taken from the
# cumulative order rather than retyped.
STOPS = (SETS[0], SETS[1], SETS[-1])


def _pdf(mu: float):
    """The in-control density, moved to `mu`. One shape for both curves."""
    return lambda x: float(norm_pdf(np.asarray(x, dtype=float), mu=mu))


def _z_of(p: float) -> float:
    """The sigma position whose two-sided p-value is `p`.

    A4 plots a point and prices it. Typing the position and reading the price
    from `evidence` would be two sources for one point, so the position is
    recovered from the symbol instead: the dot cannot end up somewhere the chip
    is not describing.
    """
    lo, hi = 0.0, 12.0
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if p_value(mid) > p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


Z_INSIDE = _z_of(P_AT_2_5)        # inside the boundary, and still surprising
Z_EDGE = _z_of(P_AT_3)            # on the boundary, where the two answers agree


def _pattern(rule: int, n: int, seed: int) -> np.ndarray:
    """`n` subgroups that `rule` flags on the last one and no earlier rule flags.

    Drawn rather than typed: the pattern on screen is certified by the same
    `first_violation` the run lengths were simulated with, so a shot cannot show
    a run that the priced rule would not actually have caught.
    """
    earlier = tuple(r for r in RULES if r < rule)
    rng = np.random.default_rng(seed)
    for _ in range(400):
        z = rng.normal(0.0, 1.0, size=(4096, n))
        ok = first_violation(z, (rule,)) == n - 1
        if earlier:
            ok &= first_violation(z, earlier) < 0
        found = np.flatnonzero(ok)
        if found.size:
            return z[found[0]]
    raise RuntimeError(f"no clean pattern found for rule {rule}")


# The cost board's shared axis. Subgroups, on a log scale, so a ratio is a
# length: what the purchase spends and what it buys become two lines the eye can
# lay side by side. Endpoints are decades around the data, not chosen by hand.
_BAR_VALUES = (ARL0_ONE_RULE, ARL0_ALL, ARL1_ONE_RULE, ARL1_ALL,
               ARL_BIG_ONE, ARL_BIG_ALL)
LOG_LO = 10.0 ** math.floor(math.log10(min(_BAR_VALUES)))
LOG_HI = 10.0 ** math.ceil(math.log10(max(_BAR_VALUES)))


def _cx(v: float) -> float:
    """Frame x of a run length of `v` subgroups on the cost board's axis."""
    f = (math.log10(v) - math.log10(LOG_LO)) / (math.log10(LOG_HI) - math.log10(LOG_LO))
    return COST_LEFT + f * (COST_RIGHT - COST_LEFT)


def _decades() -> list[float]:
    out, v = [], LOG_LO
    while v <= LOG_HI * 1.0001:
        out.append(v)
        v *= 10.0
    return out


def _bar(value: float, y: float, colour: str, opacity: float = 0.85) -> Rectangle:
    right = _cx(value)
    w = max(right - COST_LEFT, 1e-3)
    r = Rectangle(width=w, height=BAR_H, stroke_width=0,
                  fill_color=colour, fill_opacity=opacity)
    r.move_to([COST_LEFT + w / 2.0, y, 0])
    return r


def _travel(lo: float, hi: float, y: float, colour: str, left: float | None = None) -> VGroup:
    """A comparison length: how far a bar moved, drawn as a line with end caps."""
    span = _cx(hi) - _cx(lo)
    x0 = _cx(lo) if left is None else left
    line = Line([x0, y, 0], [x0 + span, y, 0], stroke_color=colour, stroke_width=3)
    caps = VGroup(*[Line([x, y - 0.11, 0], [x, y + 0.11, 0],
                         stroke_color=colour, stroke_width=3)
                    for x in (x0, x0 + span)])
    return VGroup(line, caps)


def _plate(head: str, body_text: str, edge: str, body_colour: str) -> VGroup:
    """A bordered readout. Two of these are what A4 refuses to collapse into one."""
    lab = micro(head, 15, edge)
    body = gauge(body_text, 27, body_colour)
    inner = VGroup(lab, body).arrange(DOWN, buff=0.17)
    box = Rectangle(width=inner.width + 0.62, height=inner.height + 0.50,
                    stroke_color=edge, stroke_width=1.7, fill_opacity=0.0)
    box.move_to(inner)
    return VGroup(box, inner)


class Level07(NarratedCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        self.a1_the_line_that_will_not_move()
        self.a2_two_areas_then_two_letters()
        self.a3_sweeping_the_shift()
        self.a4_one_point_two_answers()
        self.a5_the_cost_board()
        self.a6_same_purchase_different_shift()

    # -- shared -----------------------------------------------------------
    def _ask(self, question: str) -> VGroup:
        """A prediction, on screen as a question rather than only in the voice."""
        tag = micro("PREDICT", 15, YELLOW)
        line = prose(question, 26, INK)
        grp = VGroup(tag, line).arrange(DOWN, buff=0.18)
        grp.move_to([-0.9, 2.85, 0])
        within_frame(grp, "prediction")
        return grp

    def _lane_point(self, z: float, i: int) -> np.ndarray:
        base = self.axes.c2p(z, 0)
        return np.array([base[0], base[1] - LANE_FIRST - i * LANE_STEP, 0.0])

    # ---------------- A1 · the line that will not move --------------------
    def a1_the_line_that_will_not_move(self):
        axes = Axes(x_range=[XMIN, XMAX, 1], y_range=[0, 0.44, 0.1],
                    x_length=8.6, y_length=3.2, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5,
                                 "include_ticks": False},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(BOARD_ORIGIN - axes.c2p(0, 0))
        self.axes = axes

        xlab = within_frame(micro("THE PLOTTED STATISTIC, IN ITS OWN SIGMA")
                            .next_to(axes.x_axis, DOWN, buff=0.34), "A1 x-label")
        # A5 shrinks the board into the upper third and the cost board takes the
        # rest of the frame. This label belongs to the full-size board, and left
        # on screen it ends up lying across the middle of the cost board.
        self.xlab = xlab

        stable = axes.plot(_pdf(0.0), x_range=[XMIN, XMAX, STEP],
                           stroke_color=TEAL, stroke_width=3)

        # Trackers. Everything that moves for the rest of the act moves through
        # one of these, so no shot has to destroy a Mobject to change it.
        self.shift_t = ValueTracker(0.0)
        self.lim_t = ValueTracker(LIMIT)
        self.lane_t = ValueTracker(0.0)
        self.sweep_a = ValueTracker(0.0)
        self.sweep_b = ValueTracker(0.0)
        self.alpha_op = ValueTracker(0.0)
        self.beta_op = ValueTracker(0.0)
        self.power_op = ValueTracker(0.0)
        self.curve_op = ValueTracker(1.0)
        self.sym_op = ValueTracker(0.0)
        self.dim = ValueTracker(1.0)

        self.stable = stable
        self.board_static = VGroup(axes, stable)

        with self.say("Level 6 priced one way to be wrong. Here is the other one, "
                      "in plain sight."):
            self.play(Create(axes.x_axis), FadeIn(xlab), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(stable), run_time=1.3, rate_func=rf.ease_out_sine)

        # The boundary is stepped out in equal sigma widths, so it reads as a
        # distance before it reads as a rule.
        steps = list(range(1, int(LIMIT) + 1))
        ticks, tick_tags = VGroup(), VGroup()
        with self.say("The limit is not a verdict handed down. It is a distance, "
                      "stepped out from the centre one sigma width at a time."):
            for k in steps:
                pair = VGroup(*[Line(axes.c2p(s * k, 0), axes.c2p(s * k, 0.042),
                                     stroke_color=GREY, stroke_width=1.6)
                                for s in (-1, 1)])
                tags = VGroup(*[micro(f"{k}σ", 15, GREY).next_to(
                    axes.c2p(s * k, 0), DOWN, buff=0.10) for s in (-1, 1)])
                ticks.add(pair)
                tick_tags.add(tags)
                self.play(Create(pair), FadeIn(tags), run_time=0.42,
                          rate_func=rf.ease_out_sine)
        self.sigma_marks = VGroup(ticks, tick_tags)
        self.board_static.add(ticks)

        boundary = always_redraw(self._boundary)
        self.boundary = boundary
        dist = micro(f"{LIMIT:.0f} SIGMA WIDTHS FROM CENTRE", 16, YELLOW)
        dist.next_to(axes.c2p(LIMIT, CURVE_TOP), UP, buff=0.16).shift(LEFT * 0.55)
        within_frame(dist, "A1 boundary distance")
        self.boundary_tag = dist
        with self.say("Stop at the third one and draw the line. That line does not "
                      "move again for the rest of this act."):
            self.add(boundary)
            self.play(FadeIn(dist), run_time=0.8, rate_func=rf.ease_out_sine)

        ask = self._ask("How far would the mean have to move before this chart notices?")
        with self.say("Before I move anything: decide where you would have to put "
                      "the mean before this chart starts complaining. Hold that."):
            self.play(FadeIn(ask, shift=DOWN * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.beat(1.4)
        self.play(FadeOut(ask), run_time=0.5, rate_func=rf.ease_in_sine)

        # Copy and slide. The shifted curve is added at zero shift, sitting
        # exactly on the in-control curve, so what the eye reads is one process
        # moving rather than a second process being drawn.
        shifted = always_redraw(self._shifted_curve)
        self.shifted = shifted
        self.add(shifted)
        self.bring_to_front(boundary)
        with self.say(f"Take a copy of that same curve and move the process by "
                      f"{SHIFT:.0f} sigma. Same shape, same spread. Only the mean "
                      f"has moved."):
            self.play(self.shift_t.animate.set_value(SHIFT), run_time=2.4,
                      rate_func=rf.ease_in_out_sine)

        with self.say("The process has genuinely moved, and the picture of it looks "
                      "almost exactly like the picture of a process that has not."):
            self.beat(1.4)

    def _boundary(self) -> VGroup:
        top = self.axes.c2p(0, CURVE_TOP)[1]
        base = self.axes.c2p(0, 0)[1] - self.lane_t.get_value()
        v = self.lim_t.get_value()
        return VGroup(*[Line([self.axes.c2p(s * v, 0)[0], base, 0],
                             [self.axes.c2p(s * v, 0)[0], top, 0],
                             stroke_color=YELLOW, stroke_width=2.6)
                        for s in (-1, 1)])

    def _shifted_curve(self):
        return self.axes.plot(
            _pdf(self.shift_t.get_value()), x_range=[XMIN, XMAX, STEP],
            stroke_color=BLUE, stroke_width=3,
            stroke_opacity=self.curve_op.get_value() * self.dim.get_value())

    # ---------------- A2 · two areas, then two letters --------------------
    def a2_two_areas_then_two_letters(self):
        alpha_area = always_redraw(self._alpha_area)
        beta_area = always_redraw(self._beta_area)
        self.alpha_area, self.beta_area = alpha_area, beta_area
        self.add(alpha_area, beta_area)
        self.bring_to_front(self.stable, self.shifted, self.boundary)

        self.camera.frame.save_state()
        with self.say("Both of these errors start at the same line, so let the line "
                      "cut them out. This tail is the process behaving and the chart "
                      "shouting anyway."):
            self.alpha_op.set_value(0.85)
            self.play(
                self.sweep_a.animate.set_value(1.0),
                self.camera.frame.animate.scale(0.80).move_to(
                    self.axes.c2p(LIMIT - 0.4, 0.16)),
                run_time=2.4, rate_func=rf.ease_in_out_sine)

        with self.say("And this one is the process having moved, with every point "
                      "still landing inside the line."):
            self.beta_op.set_value(0.42)
            self.play(self.sweep_b.animate.set_value(1.0), run_time=2.4,
                      rate_func=rf.ease_in_out_sine)

        with self.say("One of these is the error the limit was chosen against. The "
                      "other is the one you are paying."):
            self.play(Restore(self.camera.frame), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.5)

        # Only now, on quantities that have been filled and held, do the words
        # arrive — and only after the words do the letters.
        wolf_at = self.axes.c2p(4.55, 0.115)
        silent_at = self.axes.c2p(SHIFT, 0.155)
        wolf = prose("crying wolf", 26, RED).move_to(wolf_at)
        silent = prose("staying silent", 26, BLUE).move_to(silent_at)
        leader = Line(self.axes.c2p(4.55, 0.085), self.axes.c2p(3.55, 0.012),
                      stroke_color=RED, stroke_width=1.3)
        within_frame(wolf, "A2 alpha words")
        within_frame(silent, "A2 beta words")
        with self.say("Now they can be named. This one is crying wolf. That one is "
                      "staying silent."):
            self.play(FadeIn(wolf), Create(leader), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(silent), run_time=0.8, rate_func=rf.ease_out_sine)
            self.beat(0.6)

        a_sym = MathTex(r"\alpha", color=RED, font_size=46).move_to(wolf_at)
        b_sym = MathTex(r"\beta", color=BLUE, font_size=46).move_to(silent_at)
        with self.say("And a name that has been earned can shrink to one letter."):
            self.play(Transform(wolf, a_sym), Transform(silent, b_sym),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        self.alpha_sym, self.beta_sym = wolf, silent
        self.alpha_leader = leader
        a_val = always_redraw(self._alpha_value)
        b_val = always_redraw(self._beta_value)
        self.alpha_val, self.beta_val = a_val, b_val
        with self.say("The sliver is the rate the limit was designed to hold down. "
                      "The bulk is the rate nobody quotes."):
            self.sym_op.set_value(1.0)
            self.add(a_val, b_val)
            self.beat(1.3)

    def _alpha_area(self) -> VGroup:
        f = self.sweep_a.get_value()
        op = self.alpha_op.get_value() * self.dim.get_value()
        if f <= 0.001 or op <= 0.001:
            return VGroup()
        g = self.axes.plot(_pdf(0.0), x_range=[XMIN, XMAX, STEP])
        v = self.lim_t.get_value()
        hi = v + f * (XMAX - v)
        lo = -v - f * (-v - XMIN)
        return VGroup(
            self.axes.get_area(g, x_range=[v, hi], color=RED, opacity=op,
                               stroke_width=0),
            self.axes.get_area(g, x_range=[lo, -v], color=RED, opacity=op,
                               stroke_width=0))

    def _beta_area(self) -> VGroup:
        f = self.sweep_b.get_value()
        op = self.beta_op.get_value() * self.dim.get_value()
        if f <= 0.001 or op <= 0.001:
            return VGroup()
        g = self.axes.plot(_pdf(self.shift_t.get_value()),
                           x_range=[XMIN, XMAX, STEP])
        v = self.lim_t.get_value()
        return VGroup(self.axes.get_area(g, x_range=[v - f * 2 * v, v], color=BLUE,
                                         opacity=op, stroke_width=0))

    def _power_area(self) -> VGroup:
        op = self.power_op.get_value() * self.dim.get_value()
        if op <= 0.001:
            return VGroup()
        g = self.axes.plot(_pdf(self.shift_t.get_value()),
                           x_range=[XMIN, XMAX, STEP])
        v = self.lim_t.get_value()
        return VGroup(
            self.axes.get_area(g, x_range=[v, XMAX], color=TEAL, opacity=op,
                               stroke_width=0),
            self.axes.get_area(g, x_range=[XMIN, -v], color=TEAL, opacity=op,
                               stroke_width=0))

    def _alpha_value(self):
        t = gauge(f"{alpha_one_point(self.lim_t.get_value()):.4f}", 23, RED)
        t.next_to(self.axes.c2p(4.55, 0.115), DOWN, buff=0.30)
        return t.set_opacity(self.sym_op.get_value())

    def _beta_value(self):
        t = gauge(f"{beta_one_point(self.shift_t.get_value(), self.lim_t.get_value()):.3f}",
                  23, BLUE)
        t.next_to(self.axes.c2p(SHIFT, 0.155), DOWN, buff=0.30)
        return t.set_opacity(self.sym_op.get_value())

    # ---------------- A3 · sweeping the shift ----------------------------
    def a3_sweeping_the_shift(self):
        # The handle rides the statistic axis itself: the shift is measured in
        # the same sigma, so the handle is the shifted mean.
        handle = always_redraw(self._handle)
        stops = VGroup(*[VGroup(
            Line(self.axes.c2p(s, 0), self.axes.c2p(s, -0.022),
                 stroke_color=GREY, stroke_width=1.4),
            micro(f"{s:.1f}", 13, GREY).next_to(self.axes.c2p(s, -0.022), DOWN, buff=0.30))
            for s in SHIFTS])
        self.add(handle)

        col_frame, col = self._power_column()
        self.power_col = VGroup(col_frame, col)
        power_area = always_redraw(self._power_area)
        self.power_fill = power_area
        self.add(power_area)
        self.bring_to_front(self.stable, self.shifted, self.boundary, handle)

        lab_d = at_panel(micro("SHIFT, IN SIGMA"), 0, value=False)
        val_d = always_redraw(lambda: at_panel(
            gauge(f"{self.shift_t.get_value():.2f}", 26, INK), 0))
        lab_p = at_panel(micro("CHANCE IT SIGNALS"), 1, value=False)
        val_p = always_redraw(lambda: at_panel(gauge(
            f"{power_one_point(self.shift_t.get_value(), self.lim_t.get_value()) * 100:.1f} %",
            26, TEAL), 1))
        self.panel = VGroup(lab_d, lab_p)

        with self.say("So put a handle on the mean and let it walk."):
            self.play(FadeIn(stops), FadeIn(col_frame), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.add(col, val_d, val_p)
            self.play(FadeIn(lab_d), FadeIn(lab_p), run_time=0.5,
                      rate_func=rf.ease_out_sine)

        ask = self._ask("At which shift does the chart catch half of what it sees?")
        with self.say("Point at the shift where you think this chart catches half of "
                      "what it is shown. The handle is about to walk past it."):
            self.play(FadeIn(ask, shift=DOWN * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.beat(1.2)
        self.play(FadeOut(ask), run_time=0.45, rate_func=rf.ease_in_sine)

        self.shift_t.set_value(SHIFTS[0])
        self.power_op.set_value(0.75)
        col_ticks = VGroup(*[Line([self.col_x - 0.30, self._col_y(POWER_AT[s]), 0],
                                  [self.col_x - 0.10, self._col_y(POWER_AT[s]), 0],
                                  stroke_color=GREY, stroke_width=1.4)
                             for s in SHIFTS])
        self.play(FadeIn(col_ticks), run_time=0.5, rate_func=rf.ease_out_sine)

        with self.say("Small shifts do almost nothing. The blue bulk barely moves and "
                      "the column barely lifts, because one point at a time is a weak "
                      "test and a small move looks exactly like ordinary noise."):
            self.play(self.shift_t.animate.set_value(SHIFTS[len(SHIFTS) // 2]),
                      run_time=3.0, rate_func=rf.linear)

        with self.say("Then it wakes up. Nothing about the chart changed. The mean "
                      "simply got close enough to the line for the tail to be on the "
                      "wrong side of it."):
            self.play(self.shift_t.animate.set_value(SHIFTS[-1]), run_time=3.2,
                      rate_func=rf.linear)

        # The half-way frame: the mean lands on the boundary and the two areas
        # are the same size. The number explains itself.
        half = VGroup(
            Line([self.col_x - 0.34, self._col_y(POWER_AT[SHIFTS[-1]]), 0],
                 [self.col_x + 0.34, self._col_y(POWER_AT[SHIFTS[-1]]), 0],
                 stroke_color=YELLOW, stroke_width=2.4),
            micro("HALF", 14, YELLOW).next_to(
                [self.col_x + 0.34, self._col_y(POWER_AT[SHIFTS[-1]]), 0], RIGHT, buff=0.10))
        with self.say("The mean is sitting on the line. Half the curve is each side of "
                      "it, so the column is at half, and it had to be."):
            self.play(Create(half), run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(self.camera.frame.animate.scale(0.82).move_to(
                self.axes.c2p(LIMIT - 0.2, 0.30)), run_time=1.3,
                rate_func=rf.ease_in_out_sine)
            self.beat(0.6)
        self.play(Restore(self.camera.frame), run_time=1.1,
                  rate_func=rf.ease_in_out_sine)

        # Counterexample: buy sensitivity by moving the line instead, and watch
        # the other area pay for it.
        tight = micro(f"LIMIT PULLED IN TO {TIGHT_LIMIT:.0f} SIGMA WIDTHS", 16, YELLOW)
        tight.move_to([-0.9, 2.85, 0])
        within_frame(tight, "A3 tight limit tag")
        with self.say("There is an obvious escape route here: stop moving the process "
                      "and move the line instead. Pull it in."):
            self.play(self.shift_t.animate.set_value(SHIFTS[0]), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)
            self.play(self.lim_t.animate.set_value(TIGHT_LIMIT), FadeIn(tight),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)

        with self.say("The column does rise earlier. It also just fattened the red "
                      "sliver, and that sliver is the alarms you will chase on a "
                      "process that never moved. Sensitivity bought this way is paid "
                      "for in the same currency."):
            self.play(Indicate(self.alpha_val, color=RED, scale_factor=1.15),
                      run_time=0.9, rate_func=rf.there_and_back)
            self.play(self.shift_t.animate.set_value(SHIFTS[-1]), run_time=3.0,
                      rate_func=rf.linear)

        with self.say("So put the line back where Level 6 left it."):
            self.play(self.lim_t.animate.set_value(LIMIT),
                      self.shift_t.animate.set_value(SHIFT),
                      FadeOut(tight), run_time=1.8, rate_func=rf.ease_in_out_sine)

        # The expression arrives last, labelling areas that have been on screen
        # for the whole sweep.
        eq = MathTex(r"\text{power}(\delta)=",
                     r"\Phi(-k-\delta)", r"+", r"\Phi(-k+\delta)",
                     color=INK, font_size=34)
        eq[1].set_color(TEAL)
        eq[3].set_color(TEAL)
        eq.next_to(self.axes.x_axis, DOWN, buff=0.92).shift(LEFT * 0.4)
        knote = micro(f"k = {LIMIT:.0f} SIGMA WIDTHS", 14, GREY).next_to(eq, DOWN, buff=0.18)
        within_frame(eq, "A3 power expression")
        within_frame(knote, "A3 k note")
        self.power_eq = VGroup(eq, knote)
        with self.say("Which is all the power expression says. One term for the tail "
                      "on the far side, one for the tail on the near side, and nothing "
                      "else."):
            self.play(Write(eq[0]), run_time=0.8, rate_func=rf.linear)
            self.play(Write(eq[1]), self._flash_tail(left=True), run_time=1.0,
                      rate_func=rf.linear)
            self.play(Write(eq[2]), Write(eq[3]), self._flash_tail(left=False),
                      run_time=1.0, rate_func=rf.linear)
            self.play(FadeIn(knote), run_time=0.5, rate_func=rf.ease_out_sine)

        lab_r = at_panel(micro("POINTS PER CATCH"), 2, value=False)
        val_r = at_panel(gauge(f"{ARL1_FROM_POWER:.0f}", 26, YELLOW), 2)
        self.panel.add(lab_r, val_r)
        with self.say("One point, one chance. That is the whole limitation, and this "
                      "is its price in points waited."):
            self.play(FadeIn(lab_r), FadeIn(val_r), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.beat(0.8)

        self.a3_kit = VGroup(stops, col_frame, col, col_ticks, half, val_d, val_p)

    def _handle(self) -> VGroup:
        p = self.axes.c2p(self.shift_t.get_value(), 0)
        tri = Polygon([p[0] - 0.10, p[1] - 0.20, 0], [p[0] + 0.10, p[1] - 0.20, 0],
                      [p[0], p[1], 0], stroke_width=0, fill_color=INK, fill_opacity=1.0)
        stem = Line([p[0], p[1], 0], self.axes.c2p(self.shift_t.get_value(), 0.40),
                    stroke_color=INK, stroke_width=1.1, stroke_opacity=0.45)
        return VGroup(stem, tri)

    def _col_y(self, power: float) -> float:
        return self.col_base + self.col_h * power

    def _power_column(self):
        self.col_x = 3.52
        self.col_base = BOARD_ORIGIN[1]
        self.col_h = 2.90
        frame = Rectangle(width=0.52, height=self.col_h, stroke_color=GREY,
                          stroke_width=1.3, fill_opacity=0.0)
        frame.move_to([self.col_x, self.col_base + self.col_h / 2.0, 0])
        cap = micro("SIGNALS", 14, TEAL).next_to(frame, UP, buff=0.16)
        within_frame(cap, "A3 column cap")

        def build():
            h = max(1e-3, self.col_h * power_one_point(
                self.shift_t.get_value(), self.lim_t.get_value()))
            r = Rectangle(width=0.52, height=h, stroke_width=0,
                          fill_color=TEAL, fill_opacity=0.85)
            r.move_to([self.col_x, self.col_base + h / 2.0, 0])
            return r

        return VGroup(frame, cap), always_redraw(build)

    def _flash_tail(self, left: bool):
        g = self.axes.plot(_pdf(self.shift_t.get_value()), x_range=[XMIN, XMAX, STEP])
        v = self.lim_t.get_value()
        rng = [XMIN, -v] if left else [v, XMAX]
        area = self.axes.get_area(g, x_range=rng, color=TEAL, opacity=0.95,
                                  stroke_width=0)
        return Indicate(area, color=TEAL, scale_factor=1.0)

    # ---------------- A4 · one point, two answers ------------------------
    def a4_one_point_two_answers(self):
        with self.say("Keep the board. Drop the instruments."):
            self.play(FadeOut(self.a3_kit), FadeOut(self.panel),
                      FadeOut(self.power_eq), FadeOut(self.beta_sym),
                      FadeOut(self.beta_val),
                      self.power_op.animate.set_value(0.0),
                      self.beta_op.animate.set_value(0.10),
                      self.curve_op.animate.set_value(0.40),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)
        self.remove(self.beta_val)

        self.z_t = ValueTracker(Z_INSIDE)
        self.drop_t = ValueTracker(2.6)
        self.evid_op = ValueTracker(0.0)
        point = always_redraw(lambda: Dot(
            [self.axes.c2p(self.z_t.get_value(), 0)[0],
             self.axes.c2p(0, 0)[1] + self.drop_t.get_value(), 0],
            radius=0.09, color=INK))
        self.add(point)

        with self.say("One subgroup. It lands here, comfortably inside the line."):
            self.play(self.drop_t.animate.set_value(0.0), run_time=1.0,
                      rate_func=rf.ease_in_quad)

        ask = self._ask("In, or out?")
        with self.say("One word. In, or out."):
            self.play(FadeIn(ask, shift=DOWN * 0.10), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.beat(1.2)
        self.play(FadeOut(ask), run_time=0.45, rate_func=rf.ease_in_sine)

        verdict = _plate("THE CHART SAYS", "in control", YELLOW, TEAL)
        verdict.move_to([4.55, 2.35, 0])
        within_frame(verdict, "A4 verdict plate")
        self.verdict = verdict
        with self.say("In. The rule the chart owns is a distance, the point is inside "
                      "the distance, and that is the whole answer it is able to give."):
            self.play(FadeIn(verdict, shift=LEFT * 0.15), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        tail = always_redraw(self._evidence_tail)
        self.evidence_tail = tail
        self.evid_op.set_value(0.0)
        self.add(tail)
        self.bring_to_front(self.stable, self.shifted, self.boundary, point)

        chip_box = _plate("EVIDENCE, TWO-SIDED P", " " * 6, RED, RED)
        chip_box.move_to([4.55, 0.85, 0])
        within_frame(chip_box, "A4 evidence chip")
        
        self.evid_op.set_value(0.9)
        peel = self._evidence_tail().copy().set_opacity(0.95)
        self.evid_op.set_value(0.0)

        with self.say("But the same point carries something the verdict threw away: "
                      "how much of the in-control curve is further out than it is. "
                      "Peel that off the board."):
            self.play(self.evid_op.animate.set_value(0.9), run_time=0.6, rate_func=rf.ease_out_sine)
            self.add(peel)
            self.play(ReplacementTransform(peel, chip_box), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)
        chip_val = always_redraw(lambda: gauge(
            f"{p_value(self.z_t.get_value()):.4f}", 27, RED).move_to(
                chip_box[1][1]))
        self.chip_box, self.chip_val = chip_box, chip_val
        self.add(chip_val)

        eq = MathTex(r"p = 2\,\bigl[\,1-\Phi(|z|)\,\bigr]", color=RED, font_size=32)
        eq.next_to(self.axes.c2p(4.0, 0.0), UP, buff=1.05)
        within_frame(eq, "A4 p expression")
        self.p_eq = eq
        with self.say("Two objects now, built from one point, and they disagree. The "
                      "chart's answer is a pass. The evidence is not a pass."):
            self.play(Indicate(self.verdict, color=TEAL, scale_factor=1.05),
                      run_time=0.8, rate_func=rf.there_and_back)
            self.play(Indicate(chip_box, color=RED, scale_factor=1.05),
                      run_time=0.8, rate_func=rf.there_and_back)
            self.play(Write(eq), run_time=1.2, rate_func=rf.linear)

        # Counterexample: at the boundary the two answers agree, and the peeled
        # tail lands exactly on the alpha sliver that has been there since A2.
        fail = _plate("THE CHART SAYS", "out of control", YELLOW, RED)
        fail.move_to(verdict.get_center())
        within_frame(fail, "A4 fail plate")
        with self.say("Walk the point out to the line itself, and the two answers "
                      "agree. The peeled tail lands on the sliver from earlier and "
                      "the chip lands on its rate."):
            self.play(self.z_t.animate.set_value(Z_EDGE),
                      Transform(verdict, fail), run_time=2.2,
                      rate_func=rf.ease_in_out_sine)
            self.play(Indicate(self.alpha_val, color=RED, scale_factor=1.2),
                      Indicate(chip_val, color=RED, scale_factor=1.2),
                      run_time=1.1, rate_func=rf.there_and_back)

        pass_again = _plate("THE CHART SAYS", "in control", YELLOW, TEAL)
        pass_again.move_to(verdict.get_center())
        with self.say("So the agreement holds at exactly one place. Step back inside, "
                      "and the disagreement is a property of the rule rather than of "
                      "the drawing. The verdict is not the evidence, and the chart "
                      "keeps one and throws the other away."):
            self.play(self.z_t.animate.set_value(Z_INSIDE),
                      Transform(verdict, pass_again), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)
            self.beat(1.0)

        self.evidence_point = point

    def _evidence_tail(self):
        op = self.evid_op.get_value() * self.dim.get_value()
        if op <= 0.001:
            return VGroup()
        g = self.axes.plot(_pdf(0.0), x_range=[XMIN, XMAX, STEP])
        z = self.z_t.get_value()
        return VGroup(
            self.axes.get_area(g, x_range=[z, XMAX], color=RED, opacity=op,
                               stroke_color=INK, stroke_width=2),
            self.axes.get_area(g, x_range=[XMIN, -z], color=RED, opacity=op,
                               stroke_color=INK, stroke_width=2))

    # ---------------- A5 · the cost board, three stops -------------------
    def a5_the_cost_board(self):
        with self.say("Hold on to all of that and make room."):
            self.play(FadeOut(self.verdict), FadeOut(self.chip_box),
                      FadeOut(self.p_eq), FadeOut(self.alpha_sym),
                      FadeOut(self.alpha_leader), FadeOut(self.boundary_tag),
                      FadeOut(self.sigma_marks[1]), FadeOut(self.xlab),
                      self.evid_op.animate.set_value(0.0),
                      self.sym_op.animate.set_value(0.0),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
        self.remove(self.chip_val, self.alpha_val, self.evidence_tail,
                    self.evidence_point)

        origin = self.axes.c2p(0, 0).copy()
        with self.say("The board goes up there and stays there. Everything on it is "
                      "the same board."):
            self.play(
                self.board_static.animate.scale(BOARD_SCALE, about_point=origin)
                .shift(BOARD_ORIGIN_A5 - origin),
                self.curve_op.animate.set_value(0.9),
                self.beta_op.animate.set_value(0.34),
                run_time=1.8, rate_func=rf.ease_in_out_sine)

        # The boundary verticals grow downward and become the limits of a lane
        # that runs one subgroup per row. The same line, doing a second job.
        guides = always_redraw(self._lane_guides)
        self.add(guides)
        band_tags = VGroup(*[micro(f"{k}σ", 14, GREY).next_to(
            self.axes.c2p(k, 0), UP, buff=0.06).shift(RIGHT * 0.02)
            for k in range(1, int(LIMIT) + 1)])
        with self.say("Because a rule is a pattern in a run of subgroups, and a run "
                      "needs somewhere to fall."):
            self.play(self.lane_t.animate.set_value(LANE_DEPTH), FadeIn(band_tags),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        # ---- the cost board itself ----
        axis = Line([COST_LEFT, Y_COST_AXIS, 0], [COST_RIGHT, Y_COST_AXIS, 0],
                    stroke_color=GREY, stroke_width=1.5)
        dec = VGroup()
        for v in _decades():
            dec.add(Line([_cx(v), Y_COST_AXIS - 0.10, 0], [_cx(v), Y_COST_AXIS + 0.10, 0],
                         stroke_color=GREY, stroke_width=1.4))
            dec.add(micro(f"{v:.0f}", 14, GREY).move_to([_cx(v), Y_COST_AXIS - 0.32, 0]))
        axis_tag = micro("SUBGROUPS · EACH STEP IS TEN TIMES AS MANY", 15, GREY)
        axis_tag.move_to([COST_LEFT + 0.1, Y_COST_AXIS - 0.62, 0], aligned_edge=LEFT)
        within_frame(axis_tag, "A5 axis tag")

        lab_a = micro("SUBGROUPS BETWEEN FALSE ALARMS — WANT THIS LONG", 15, RED)
        lab_a.move_to([COST_LEFT, Y_BAR_A + 0.44, 0], aligned_edge=LEFT)
        lab_b = micro(f"SUBGROUPS TO CATCH A {SHIFT:.0f}σ SHIFT — WANT THIS SHORT", 15, TEAL)
        # A6 re-prices this same bar and needs to REPLACE this label rather than
        # fade another one in on the identical anchor, which stacked two strings
        # of caps on one line and rendered as garbled glyphs.
        self.lab_b = lab_b
        lab_b.move_to([COST_LEFT, Y_BAR_B + 0.44, 0], aligned_edge=LEFT)
        within_frame(lab_a, "A5 bar A label")
        within_frame(lab_b, "A5 bar B label")

        self.arl0_t = ValueTracker(TRADE[STOPS[0]]["arl0"])
        self.arl1_t = ValueTracker(TRADE[STOPS[0]]["arl1"])
        bar_a = always_redraw(lambda: _bar(self.arl0_t.get_value(), Y_BAR_A, RED))
        bar_b = always_redraw(lambda: _bar(self.arl1_t.get_value(), Y_BAR_B, TEAL))
        val_a = always_redraw(lambda: gauge(f"{self.arl0_t.get_value():.0f}", 25, RED)
                              .next_to([_cx(self.arl0_t.get_value()), Y_BAR_A, 0],
                                       RIGHT, buff=0.18))
        val_b = always_redraw(lambda: gauge(f"{self.arl1_t.get_value():.1f}", 25, TEAL)
                              .next_to([_cx(self.arl1_t.get_value()), Y_BAR_B, 0],
                                       RIGHT, buff=0.18))
        self.bar_b, self.val_b = bar_b, val_b

        with self.say("This is the whole purchase, on one axis of subgroups. How long "
                      "between false alarms, and how long until a real shift is "
                      "caught. Both are simulated run lengths, not opinions."):
            self.play(Create(axis), FadeIn(dec), FadeIn(axis_tag), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            self.add(bar_a, bar_b, val_a, val_b)
            self.play(FadeIn(lab_a), FadeIn(lab_b), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        ask = self._ask("Which way does each bar move when you switch a rule on?")
        ask.move_to([0.0, 0.45, 0])
        within_frame(ask, "A5 prediction")
        with self.say("Both bars are frozen at their single-rule lengths. Before I "
                      "switch anything on: which way does each one move?"):
            self.play(FadeIn(ask, shift=DOWN * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.beat(1.4)
        self.play(FadeOut(ask), run_time=0.45, rate_func=rf.ease_in_sine)

        captions = VGroup()
        ghosts = VGroup()
        spoken = {
            1: "Stop one is the rule Level 6 already bought: a single point outside "
               "the line. Those are the lengths it gives you.",
            2: "Stop two adds a pattern that no single point could hold — two of "
               "three out at two sigma on the same side. Watch both bars.",
            3: "Stop three switches the last two on, and the bars do it again.",
        }
        for i, rules in enumerate(STOPS):
            added = [r for r in rules if r not in (STOPS[i - 1] if i else ())]
            with self.say(spoken[i + 1]):
                self.play(self.dim.animate.set_value(1.0), run_time=0.2)
                for r in added:
                    cap = self._draw_pattern(r)
                    captions.add(cap)
                if i:
                    for value, y in ((self.arl0_t.get_value(), Y_BAR_A),
                                     (self.arl1_t.get_value(), Y_BAR_B)):
                        ghosts.add(Line([_cx(value), y - BAR_H / 2, 0],
                                        [_cx(value), y + BAR_H / 2, 0],
                                        stroke_color=INK, stroke_width=1.8,
                                        stroke_opacity=0.55))
                    self.add(ghosts)
                    self.play(self.arl0_t.animate.set_value(TRADE[rules]["arl0"]),
                              self.arl1_t.animate.set_value(TRADE[rules]["arl1"]),
                              run_time=2.0, rate_func=rf.ease_in_out_sine)
        captions.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        captions.move_to([1.30, 2.20, 0], aligned_edge=LEFT)
        self.rule_captions = captions

        # External corroboration, on a hold, with no camera move.
        pub = VGroup(
            Line([_cx(CHAMP_WOODALL_ARL0), Y_BAR_A - 0.42, 0],
                 [_cx(CHAMP_WOODALL_ARL0), Y_BAR_A + 0.42, 0],
                 stroke_color=YELLOW, stroke_width=2.2),
            micro("CHAMP & WOODALL, 1987", 14, YELLOW).next_to(
                [_cx(CHAMP_WOODALL_ARL0), Y_BAR_A + 0.42, 0], UP, buff=0.10))
        within_frame(pub, "A5 published tick")
        with self.say(f"That all-four false-alarm length was published in 1987 as "
                      f"{CHAMP_WOODALL_ARL0:.2f}. This simulation was never told "
                      f"about it, and it landed on the tick."):
            self.play(FadeIn(pub), run_time=0.8, rate_func=rf.ease_out_sine)
            self.beat(1.0)

        # Both quantities are already lengths on this axis, because a ratio is a
        # distance once the axis is logarithmic. So compare the lengths, and do
        # not print the factors.
        trav_a = _travel(ARL0_ALL, ARL0_ONE_RULE, Y_TRAVEL_A, RED)
        tag_a = micro("SPENT", 15, RED).next_to(trav_a, RIGHT, buff=0.16)
        trav_b = _travel(ARL1_ALL, ARL1_ONE_RULE, Y_TRAVEL_B, TEAL)
        tag_b = micro("BOUGHT", 15, TEAL).next_to(trav_b, RIGHT, buff=0.16)
        laid = _travel(ARL0_ALL, ARL0_ONE_RULE, Y_TRAVEL_LAID, RED,
                       left=_cx(ARL1_ALL))
        tag_laid = micro("SPENT", 14, RED).next_to(laid, LEFT, buff=0.16)
        self.travel_b, self.tag_b = trav_b, tag_b
        self.laid, self.tag_laid = laid, tag_laid
        for m, w in ((trav_a, "A5 travel A"), (tag_a, "A5 tag A"),
                     (trav_b, "A5 travel B"), (tag_b, "A5 tag B"),
                     (laid, "A5 laid"), (tag_laid, "A5 laid tag")):
            within_frame(m, w)

        with self.say("So measure the two moves. This is what the purchase spent, and "
                      "this is what it bought. Lay one against the other."):
            self.play(Create(trav_a), FadeIn(tag_a), run_time=1.0,
                      rate_func=rf.ease_out_sine)
            self.play(Create(trav_b), FadeIn(tag_b), run_time=1.0,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(laid), FadeIn(tag_laid), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        with self.say("Every rule you switch on buys time and spends alarms. Both "
                      "sides are simulated, not asserted, and at this shift the two "
                      "lengths are near enough to argue about."):
            self.beat(1.2)

        self.cost_board = VGroup(axis, dec, axis_tag, lab_a, lab_b, trav_a, tag_a, pub)
        self.ghosts = ghosts

    def _lane_guides(self) -> VGroup:
        d = self.lane_t.get_value()
        if d <= 0.001:
            return VGroup()
        base = self.axes.c2p(0, 0)[1]
        out = VGroup()
        for k in range(1, int(LIMIT)):
            for s in (-1, 1):
                x = self.axes.c2p(s * k, 0)[0]
                out.add(Line([x, base - d, 0], [x, base, 0], stroke_color=GREY,
                             stroke_width=1.0, stroke_opacity=0.45))
        return out

    def _draw_pattern(self, rule: int) -> VGroup:
        """Draw the run that this rule flags, in the lane, once."""
        n = {1: 3, 2: 3, 3: 5, 4: 8}[rule]
        z = _pattern(rule, n, seed=900 + rule)
        dots = VGroup(*[Dot(self._lane_point(float(v), i), radius=0.055, color=INK)
                        for i, v in enumerate(z)])
        cap = micro(f"RULE {rule} — {RULE_TEXT[rule].upper()}", 15, INK)
        self.play(FadeIn(dots, lag_ratio=0.55), run_time=1.1, rate_func=rf.linear)
        flag = dots[-1]
        self.play(flag.animate.set_color(RED).scale(1.5), run_time=0.4,
                  rate_func=rf.ease_out_back)
        cap.move_to([1.30, 2.20, 0], aligned_edge=LEFT)
        within_frame(cap, f"A5 rule {rule} caption")
        self.play(FadeIn(cap), run_time=0.4, rate_func=rf.ease_out_sine)
        self.play(FadeOut(dots), run_time=0.5, rate_func=rf.ease_in_sine)
        return cap

    # ---------------- A6 · same purchase, different shift ----------------
    def a6_same_purchase_different_shift(self):
        with self.say(f"Nothing about the board changes now. One thing changes: the "
                      f"shift this line is trying to catch goes from {SHIFT:.0f} sigma "
                      f"to {BIG_SHIFT:.0f}."):
            self.play(self.shift_t.animate.set_value(BIG_SHIFT), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)

        tag = micro(f"NOW PRICED AGAINST A {BIG_SHIFT:.0f}σ SHIFT", 15, BLUE)
        tag.move_to([COST_LEFT, Y_BAR_B + 0.44, 0], aligned_edge=LEFT)
        within_frame(tag, "A6 catch bar label")
        big_ghosts = VGroup(*[Line([_cx(TRADE[r]["arl1"]), Y_BAR_B - BAR_H / 2, 0],
                                   [_cx(TRADE[r]["arl1"]), Y_BAR_B + BAR_H / 2, 0],
                                   stroke_color=INK, stroke_width=1.8,
                                   stroke_opacity=0.4) for r in STOPS])
        self.add(big_ghosts)

        with self.say("The false-alarm bar is not going to be touched, because nothing "
                      "about a false alarm depends on a shift that did not happen. "
                      "Watch it hold still."):
            self.play(ReplacementTransform(self.lab_b, tag), run_time=0.6,
                      rate_func=rf.ease_out_sine)
            self.play(self.arl1_t.animate.set_value(
                detection_delay(STOPS[0], BIG_SHIFT)), run_time=1.8,
                rate_func=rf.ease_in_out_sine)

        with self.say("Now walk the same three stops again. Same rules, same order, "
                      "same price."):
            for rules in STOPS[1:]:
                self.play(self.arl1_t.animate.set_value(
                    detection_delay(rules, BIG_SHIFT)), run_time=1.6,
                    rate_func=rf.ease_in_out_sine)

        new_b = _travel(ARL_BIG_ALL, ARL_BIG_ONE, Y_TRAVEL_B, TEAL)
        new_laid = _travel(ARL0_ALL, ARL0_ONE_RULE, Y_TRAVEL_LAID, RED,
                           left=_cx(ARL_BIG_ALL))
        within_frame(new_b, "A6 travel B")
        within_frame(new_laid, "A6 laid")
        with self.say("There is the same measurement. Rule one already sees a jump "
                      "that big on the very next point, so the extra rules were bought "
                      "at exactly the previous price and then never used."):
            self.play(Transform(self.travel_b, new_b),
                      self.tag_b.animate.next_to(new_b, RIGHT, buff=0.16),
                      Transform(self.laid, new_laid),
                      self.tag_laid.animate.next_to(new_laid, LEFT, buff=0.16),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)

        with self.say("Same purchase. The cost did not move. The benefit nearly "
                      "vanished. The rules did not get worse — the shift you are "
                      "aiming at changed, and that alone decided it."):
            self.beat(1.0)

        # The act ends on one sentence, so everything it was built out of leaves
        # first. Written over the live board this line landed across the limit
        # line and both curves, and the closing frame read as clutter.
        #
        # Everything currently on stage goes, rather than a hand-written list of
        # objects: the first attempt at this enumerated `cost_board` and friends
        # and still left the two bars, the boundary and the sigma ticks standing,
        # because those are separate `always_redraw` mobjects. Updaters are
        # cleared first, or they keep regenerating what the fade just removed.
        question = prose("Which shift is this line actually afraid of?", 32, INK)
        question.move_to([0.0, 0.0, 0])
        within_frame(question, "A6 open question")
        with self.say("Which leaves exactly one question standing."):
            # Group, not VGroup: the stage holds at least one plain Mobject and
            # VGroup accepts only VMobjects.
            leaving = Group(*[m for m in self.mobjects
                              if m is not self.camera.frame])
            for m in leaving:
                m.clear_updaters()
            self.play(FadeOut(leaving), run_time=1.4, rate_func=rf.ease_in_sine)
            self.clear()
            self.play(Write(question), run_time=1.8, rate_func=rf.linear)
        self.beat(1.8)
