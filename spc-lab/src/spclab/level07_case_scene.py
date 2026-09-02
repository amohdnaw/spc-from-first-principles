"""LEVEL 7 act B — 'Which rule set earns its false alarms is a property of the
line, not of the rules.'

Built 2026-09-02 against `storyboards/spc-level-07-act-b.html` and
`specs/spc-visual-depth-pilot-contract.md`. The storyboard is authoritative for
shot order, per-shot transformation and exit state.

Five shots on **one** line strip. The strip and its four-row case card are
created in B1 and are still the same Mobjects in B5. Money is never introduced
as a number: every cost bar in B3 is carried out of the blocks that came off
that strip, and B4 re-prices the same blocks without rebuilding them.

- **B1** builds each of the four case fields as a physical thing and labels it
  second. No rule set is mentioned.
- **B2** adds the three option plates and replays the one recorded run once per
  plate, lighting where each rule set first alarms. The totals stay off screen,
  which is what makes the shot a test.
- **B3** slides the strip's amber block and red stack into one two-segment bar
  per plate, then writes the expected-cost expression under the finished bars.
- **B4** moves exactly one case row to the other entry of `SHIFT_GRID`, holds
  the other three still, and lets the winner marker walk.
- **B5** clears everything but the strip, applies the winning rule set, and ends
  on a stopped line with a logged reason and no expression on screen.

Every value on screen is computed here from `spclab.level07_mastery` and
`spclab.evidence`. No total, run length, delay, rate or winner is typed into
this file.

Two corrections to the locked storyboard, both forced by the landed model and
both recorded in `implementation-notes.html`:

1. B3's surprise as written ("the tallest amber segment and the tallest red
   segment belong to different plates") is false — `rule-1` carries both. The
   surprise rendered instead is true and makes the same point: the plate with
   the *smallest* false-alarm bill is not the winner.
2. B4 as written expects the amber halves to be "identical, frame for frame".
   They are not: expected false alarms are `delay / arl0`, and `delay` moves
   with the shift, so every amber segment moves and their order even inverts.
   The object held frame-for-frame still is the per-plate **alarm rate**, which
   is what "the purchase price did not move" actually refers to.

Pacing lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_case_scene.py Level07Case
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level07_case_scene.py Level07Case
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Dot, Line, Rectangle, ValueTracker, VGroup,
    Create, FadeIn, FadeOut, Indicate, Restore, Transform, Write, always_redraw,
    DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, RED, TEAL, YELLOW,
    gauge, micro, norm_pdf, prose, within_frame,
)
from spclab.evidence import RULE_TEXT, RULES, first_violation
from spclab.level07_mastery import (
    CASE_FIELDS, CASE_SEEDS, OPTION_LABELS, PRINTED_DECIMALS, RULE_OPTIONS,
    SHIFT_GRID, challenge_case, detection_delay, false_alarm_run_length,
    neutral_case,
)
from spclab.narration import NarratedCameraScene

# ---------------------------------------------------------------------------
# The one case, priced, and its counterexample
# ---------------------------------------------------------------------------
CASE = challenge_case(CASE_SEEDS[0])
NEUTRAL = neutral_case(CASE)

# The order the page lists the options in. Read from the model so the plates
# cannot be re-ordered here without re-ordering the challenge.
OPTION_IDS = tuple(RULE_OPTIONS)


def cost_segments(option_id: str, expected_shift_size: float) -> tuple[float, float]:
    """The two halves of one option's expected cost, in the model's own terms.

    `expected_cost` sums them; a bar has to show them apart. Recomputing the
    split here would be a second source for one number, so the split is
    asserted against `expected_cost` at import (see below) and the render fails
    rather than drawing a bar whose segments do not add up to its total.
    """
    rules = RULE_OPTIONS[option_id]
    delay = detection_delay(rules, expected_shift_size)
    alarm_half = (delay / false_alarm_run_length(rules)) * CASE["false_alarm_cost"]
    wait_half = delay * CASE["sampling_cadence"] * CASE["missed_shift_cost"]
    return alarm_half, wait_half


def _priced_pairs(case: dict) -> dict[str, tuple[float, float]]:
    pairs = {}
    for option in case["options"]:
        halves = cost_segments(option["id"], case["expected_shift_size"])
        if abs(sum(halves) - option["expected_cost"]) > 10.0 ** -PRINTED_DECIMALS:
            raise AssertionError(
                f"segment split disagrees with expected_cost for {option['id']}: "
                f"{sum(halves)} vs {option['expected_cost']}")
        pairs[option["id"]] = halves
    return pairs


SMALL = _priced_pairs(CASE)
BIG = _priced_pairs(NEUTRAL)

TOTALS = {opt: option["expected_cost"]
          for option in CASE["options"] for opt in [option["id"]]}
FULL_SCALE = max(TOTALS.values())
FULL_SCALE_BIG = max(option["expected_cost"] for option in NEUTRAL["options"])

# The four field values, in the units the case states them in. The labels
# themselves are `CASE_FIELDS`, character for character.
FIELD_VALUES = {
    "expected shift size": f"{CASE['expected_shift_size']:.1f} sigma",
    "false-alarm cost": f"{CASE['false_alarm_cost']:.2f} per event",
    "missed-shift cost": f"{CASE['missed_shift_cost']:.2f} per minute",
    "sampling cadence": f"{CASE['sampling_cadence']:.0f} min per subgroup",
}

# ---------------------------------------------------------------------------
# Geometry of the one strip
# ---------------------------------------------------------------------------
# 32 slots rather than a longer run: the stack in B1 gets one block per waiting
# subgroup, and the band between the strip and the option plates is 0.9 frame
# units, so 20 waiting subgroups is the most that can be drawn as a column of
# separately readable blocks instead of one solid bar.
N_SLOTS = 32
DRIFT = 12                        # the subgroup the mean really moves at
STRIP_LEFT = -6.85
SLOT_PITCH = 0.27
SLOT_W, SLOT_H = 0.22, 0.34
STRIP_Y = 1.85

BLOCK_W = 0.38                    # a cost block is wider than a slot, and
BLOCK_H = 0.045                   # alternating opacity keeps the blocks apart
STACK_FLOOR = 0.76                # the stack may not reach the option plates

CURVE_LEFT, CURVE_RIGHT = -6.95, -3.55
CURVE_BASE, CURVE_TOP = 2.95, 3.85
CURVE_SIGMA = (-3.5, 4.5)

CARD_X = 2.95
CARD_ROWS = (3.50, 2.77, 2.04, 1.31)

# The three plates take the whole width rather than the left half: the longest
# option label is "All four Western Electric rules", and on a narrower pitch it
# either wraps into the waiting stack above or runs into its neighbour.
PLATE_X = (-4.6, 0.0, 4.6)
PLATE_TOP, PLATE_BOTTOM = 0.78, 0.05
BAR_W = 1.45
RAIL_Y = -0.10
BAR_DEPTH = 3.05                  # frame units for a full-scale bar
MARKER_Y = -0.02                  # the winner marker underlines its plate
TOTAL_Y = -3.42
EXPR_Y = -3.80
SCALE_X, SCALE_PANEL_Y = -6.90, -0.60

# The stack is the one object whose height is set by the strip's length rather
# than by a layout choice, so it is the one that silently grows into the option
# plates if the run gets longer. Fail at import instead.
_STACK_BOTTOM = STRIP_Y - 0.5 * SLOT_H - (N_SLOTS - DRIFT) * BLOCK_H
if _STACK_BOTTOM < STACK_FLOOR:
    raise AssertionError(
        f"the waiting stack reaches {_STACK_BOTTOM:.2f}, below the option "
        f"plates at {STACK_FLOOR:.2f}: shorten the run or the blocks")


def _strip_run() -> tuple[np.ndarray, int, dict[str, int]]:
    """One recorded run the whole act replays, and where each option flags it.

    The strip has to carry four things at once: a false alarm during the quiet
    stretch and clear of the drift, and three *distinct* flag slots after the
    mean moves, earliest from the four-rule set and latest from the one-point
    rule. A run drawn at random carries them only sometimes, so the seed is
    searched rather than typed, and the search conditions are the storyboard's
    own words. `first_violation` decides every slot; nothing about which slot
    lights is chosen by hand.

    Two conditions are about legibility rather than about the model. The false
    alarm must sit at least four slots clear of the drift, or a viewer reads it
    as part of the drift; and the three flags must be distinct, or B2 stacks two
    markers on one slot and the exit state cannot show three.
    """
    shift = CASE["expected_shift_size"]
    for seed in range(1, 20000):
        z = np.random.default_rng(seed).normal(0.0, 1.0, N_SLOTS)
        z[DRIFT:] += shift
        quiet = int(first_violation(z[:DRIFT], RULE_OPTIONS["all-four"])[0])
        if not 7 <= quiet <= DRIFT - 4:
            continue
        after = {opt: int(first_violation(z[DRIFT:], rules)[0])
                 for opt, rules in RULE_OPTIONS.items()}
        if min(after.values()) < 0:
            continue
        if not after["all-four"] < after["rules-1-2"] < after["rule-1"]:
            continue
        if after["rule-1"] - after["all-four"] < 8:
            continue
        return z, quiet, {opt: DRIFT + i for opt, i in after.items()}
    raise RuntimeError("no run carries all four of the storyboard's conditions")


Z_RUN, FALSE_ALARM_SLOT, ALARM_SLOT = _strip_run()


def _firing_rule(slot: int) -> int:
    """Which of the four rules actually fires at `slot`, lowest first.

    B5 logs the pattern the operator is now reading. Naming it by hand would let
    the card describe a rule that did not fire, so each rule is asked on its own
    and the strip decides.
    """
    for rule in RULES:
        if int(first_violation(Z_RUN[DRIFT:], (rule,))[0]) == slot - DRIFT:
            return rule
    raise RuntimeError(f"no single rule fires at slot {slot}")


class Level07Case(NarratedCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        self.b1_four_facts()
        self.b2_commit_before_the_prices()
        self.b3_three_prices_one_case()
        self.b4_move_one_line()
        self.b5_what_the_next_shift_does()

    # -- shared -----------------------------------------------------------
    def _slot_x(self, i: int) -> float:
        return STRIP_LEFT + i * SLOT_PITCH

    def _ask(self, question: str) -> VGroup:
        """A prediction, on screen as a question rather than only in the voice."""
        tag = micro("PREDICT", 15, YELLOW)
        line = prose(question, 25, INK)
        grp = VGroup(tag, line).arrange(DOWN, buff=0.16)
        grp.move_to([-1.5, -2.30, 0])
        within_frame(grp, "prediction")
        return grp

    # ---------------- B1 · four facts, built before they are named --------
    def b1_four_facts(self):
        rail = Line([STRIP_LEFT - 0.16, STRIP_Y, 0],
                    [self._slot_x(N_SLOTS - 1) + 0.16, STRIP_Y, 0],
                    stroke_color=GREY, stroke_width=1.6)
        slots = VGroup(*[
            Rectangle(width=SLOT_W, height=SLOT_H, stroke_color=GREY,
                      stroke_width=1.2, fill_opacity=0.0)
            .move_to([self._slot_x(i), STRIP_Y, 0])
            for i in range(N_SLOTS)])
        self.rail, self.slots = rail, slots
        self.strip = VGroup(rail, slots)

        # Above the strip, not below it: the waiting stack hangs below and would
        # otherwise sit on top of the label for the rest of the act.
        strip_tag = within_frame(
            micro("ONE SUBGROUP PER SAMPLING INTERVAL", 15, GREY)
            .move_to([STRIP_LEFT, STRIP_Y + 0.86, 0], aligned_edge=LEFT),
            "B1 strip label")
        self.strip_tag = strip_tag

        with self.say("One masked line. It plots one subgroup of film thickness "
                      "every sampling interval, and nothing else about it matters "
                      "yet."):
            self.play(Create(rail), FadeIn(strip_tag), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(slots, lag_ratio=0.04), run_time=1.4,
                      rate_func=rf.ease_out_sine)

        # -- fact one: the mean moves, and stays moved --------------------
        axes = Axes(x_range=[CURVE_SIGMA[0], CURVE_SIGMA[1], 1], y_range=[0, 0.44, 0.1],
                    x_length=CURVE_RIGHT - CURVE_LEFT, y_length=CURVE_TOP - CURVE_BASE,
                    tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.2,
                                 "include_ticks": False},
                    y_axis_config={"stroke_opacity": 0})
        axes.shift(np.array([0.5 * (CURVE_LEFT + CURVE_RIGHT), CURVE_BASE, 0.0])
                   - axes.c2p(0.5 * sum(CURVE_SIGMA), 0))
        self.curve_axes = axes
        self.shift_t = ValueTracker(0.0)
        curve = always_redraw(self._process_curve)
        centre = Line(axes.c2p(0, 0), axes.c2p(0, 0.40),
                      stroke_color=GREY, stroke_width=1.2)
        self.process_curve = curve
        self.curve_centre = centre

        with self.say("This is the same process Act A was looking at, drawn above "
                      "the line it is running on."):
            self.play(Create(axes.x_axis), Create(centre), run_time=0.7,
                      rate_func=rf.ease_in_out_sine)
            self.add(curve)
            self.play(FadeIn(curve), run_time=0.9, rate_func=rf.ease_out_sine)

        drift_mark = Line([self._slot_x(DRIFT) - 0.5 * SLOT_PITCH, STRIP_Y - 0.30, 0],
                          [self._slot_x(DRIFT) - 0.5 * SLOT_PITCH, STRIP_Y + 0.30, 0],
                          stroke_color=BLUE, stroke_width=2.2)
        with self.say("Somewhere along this run the mean really moves, and then it "
                      "stays moved. Watch how little the picture changes."):
            self.play(Create(drift_mark), run_time=0.5, rate_func=rf.ease_out_sine)
            self.play(self.shift_t.animate.set_value(CASE["expected_shift_size"]),
                      run_time=2.2, rate_func=rf.ease_in_out_sine)
        self.drift_mark = drift_mark

        # -- fact two: one measured interval ------------------------------
        # In the quiet stretch, at the left end: on the drift side it competes
        # with the three alarm markers B2 lights on those same slots.
        caliper = self._caliper(1, 2)
        with self.say("The line is sampled on a clock. One step along the strip is "
                      "one interval, and every interval is the same length."):
            self.play(Create(caliper), run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(caliper.animate.shift(RIGHT * SLOT_PITCH), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
            self.play(caliper.animate.shift(RIGHT * SLOT_PITCH), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
        self.caliper = caliper

        # -- fact three: one block, once, per false alarm -----------------
        fa_slot = self.slots[FALSE_ALARM_SLOT]
        fa_block = Rectangle(width=BLOCK_W, height=BLOCK_H * 8,
                            fill_color=YELLOW, fill_opacity=0.92,
                            stroke_color=YELLOW, stroke_width=1.0)
        fa_block.move_to([self._slot_x(FALSE_ALARM_SLOT), STRIP_Y + 0.5 * SLOT_H, 0],
                         aligned_edge=DOWN)
        self.fa_block = fa_block
        with self.say("Sometimes the chart alarms and nothing has changed. The line "
                      "stops for one check, and that is charged once."):
            self.play(fa_slot.animate.set_fill(YELLOW, opacity=0.55),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(FadeIn(fa_block, shift=UP * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_back)
        with self.say("Once. It does not keep costing anything after the check."):
            self.beat(1.0)

        # -- fact four: the stack that keeps growing ----------------------
        stack = VGroup()
        self.stack = stack
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.62).move_to([-4.4, 1.55, 0]),
                  run_time=1.4, rate_func=rf.ease_in_out_sine)

        n_red = N_SLOTS - DRIFT
        with self.say("And while nobody has noticed, every subgroup after the move "
                      "is produced against a mean that is already wrong. That is "
                      "reworked at the next step, and it is charged by the minute."):
            for k in range(n_red):
                i = DRIFT + k
                # Alternating opacity, not a gap: at this block height a gap is
                # under a pixel at 1080p and the column renders as one solid bar,
                # which is the one thing this fact must not look like.
                block = Rectangle(width=BLOCK_W, height=BLOCK_H,
                                  fill_color=RED,
                                  fill_opacity=0.92 if k % 2 == 0 else 0.62,
                                  stroke_color=RED, stroke_width=0.5)
                block.move_to([self._slot_x(DRIFT),
                               STRIP_Y - 0.5 * SLOT_H - k * BLOCK_H, 0],
                              aligned_edge=UP)
                stack.add(block)
                self.play(self.slots[i].animate.set_fill(RED, opacity=0.50),
                          FadeIn(block), run_time=0.13,
                          rate_func=rf.ease_out_sine)
                if k == n_red // 2:
                    self.play(self.camera.frame.animate.move_to([-1.6, 1.55, 0]),
                              run_time=0.9, rate_func=rf.linear)

        with self.say("Nobody has to be told which of those two is the expensive "
                      "one. One block stopped. The other one is still going."):
            self.play(Restore(self.camera.frame), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.8)

        # -- only now are the four facts named ----------------------------
        card = VGroup()
        for row, field in enumerate(CASE_FIELDS):
            label = micro(field, 15, GREY)
            value = gauge(FIELD_VALUES[field], 21, INK)
            grp = VGroup(label, value).arrange(DOWN, buff=0.10, aligned_edge=LEFT)
            grp.move_to([CARD_X, CARD_ROWS[row], 0], aligned_edge=LEFT)
            within_frame(grp, f"B1 case row {field!r}")
            card.add(grp)
        self.card = card

        with self.say("Four facts about one line. Everything after this is "
                      "arithmetic on those four."):
            self.play(FadeIn(card, lag_ratio=0.25, shift=LEFT * 0.12),
                      run_time=2.0, rate_func=rf.ease_out_sine)
        self.beat(1.2)

    def _process_curve(self):
        return self.curve_axes.plot(
            lambda x: float(norm_pdf(np.asarray(x, dtype=float),
                                     mu=self.shift_t.get_value())),
            x_range=[CURVE_SIGMA[0], CURVE_SIGMA[1], 0.08],
            stroke_color=BLUE, stroke_width=2.6)

    def _caliper(self, i: int, j: int) -> VGroup:
        y = STRIP_Y - 0.5 * SLOT_H - 0.16
        xa, xb = self._slot_x(i), self._slot_x(j)
        span = Line([xa, y, 0], [xb, y, 0], stroke_color=TEAL, stroke_width=1.8)
        ends = VGroup(*[Line([x, y - 0.07, 0], [x, y + 0.07, 0],
                             stroke_color=TEAL, stroke_width=1.8)
                        for x in (xa, xb)])
        return VGroup(span, ends)

    # ---------------- B2 · commit before the prices -----------------------
    def b2_commit_before_the_prices(self):
        plates, empty_rows = VGroup(), VGroup()
        self.rate_rows = VGroup()
        for i, opt in enumerate(OPTION_IDS):
            # The contract fixes these three strings character for character. The
            # only change made here is one space becoming a line break, because
            # the longest of them does not fit a plate on one line.
            wrapped = OPTION_LABELS[opt].replace(" Electric", "\nElectric")
            label = gauge(wrapped, 17, INK)
            # The rate carries its own unit rather than deferring to a shared
            # legend: it is the number B4 holds still, and a reader should not
            # have to look somewhere else to know what it counts.
            rate = gauge(
                f"1 FALSE ALARM IN {false_alarm_run_length(RULE_OPTIONS[opt]):.0f}",
                14, YELLOW)
            grp = VGroup(label, rate).arrange(DOWN, buff=0.10)
            grp.move_to([PLATE_X[i], 0.5 * (PLATE_TOP + PLATE_BOTTOM), 0])
            within_frame(grp, f"B2 plate {opt}")
            plates.add(grp)
            self.rate_rows.add(rate)
            empty_rows.add(
                Rectangle(width=BAR_W, height=0.30, stroke_color=GREY,
                          stroke_width=1.2, fill_opacity=0.0)
                .move_to([PLATE_X[i], RAIL_Y, 0], aligned_edge=UP))
        self.plates, self.empty_rows = plates, empty_rows

        with self.say("Three rule sets are on offer for this line. Not every "
                      "combination — these three, in the order the page lists "
                      "them."):
            self.play(FadeIn(plates, lag_ratio=0.3, shift=UP * 0.10),
                      run_time=1.6, rate_func=rf.ease_out_sine)

        with self.say("Each one buys its alarms at a rate that never changes. That "
                      "rate is the price. What it buys is what we are about to "
                      "look at."):
            self.beat(1.0)

        # One playhead, three replays of the same recorded run.
        head_t = ValueTracker(STRIP_LEFT - 0.16)
        head = always_redraw(lambda: Line(
            [head_t.get_value(), STRIP_Y - 0.5 * SLOT_H - 0.05, 0],
            [head_t.get_value(), STRIP_Y + 0.5 * SLOT_H + 0.05, 0],
            stroke_color=TEAL, stroke_width=2.0))
        self.add(head)

        lit = VGroup()
        lines = {
            "rule-1": "One point beyond three sigma, and nothing else. It waits.",
            "rules-1-2": "Add the two-of-three rule and the same run is flagged "
                         "sooner.",
            "all-four": "All four, and the same run is flagged sooner again — and "
                        "flagged back there, in the stretch where nothing had "
                        "changed.",
        }
        for opt in OPTION_IDS:
            with self.say(lines[opt]):
                head_t.set_value(STRIP_LEFT - 0.16)
                self.play(head_t.animate.set_value(
                    self._slot_x(ALARM_SLOT[opt])), run_time=1.5,
                    rate_func=rf.ease_in_out_sine)
                mark = Rectangle(width=SLOT_W + 0.10, height=SLOT_H + 0.10,
                                 stroke_color=TEAL, stroke_width=2.4,
                                 fill_opacity=0.0)
                mark.move_to([self._slot_x(ALARM_SLOT[opt]), STRIP_Y, 0])
                # The first word of two of the three labels is "Rule"/"Rules",
                # which puts two near-identical tags on the strip. The rule count
                # comes off the option's own tuple and is unambiguous.
                n_rules = len(RULE_OPTIONS[opt])
                tag = micro(f"{n_rules} RULE" + ("" if n_rules == 1 else "S"),
                            13, TEAL)
                tag.next_to(mark, UP, buff=0.06)
                lit.add(VGroup(mark, tag))
                self.play(Create(mark), FadeIn(tag), run_time=0.5,
                          rate_func=rf.ease_out_sine)
                if opt == "all-four":
                    self.play(Indicate(
                        VGroup(self.slots[FALSE_ALARM_SLOT], self.fa_block),
                        color=YELLOW, scale_factor=1.14), run_time=1.1)
        self.remove(head)
        self.lit = lit

        with self.say("So the plate that alarms earliest is the same plate that "
                      "alarms when nothing happened. Both halves of the purchase "
                      "are on the strip, and neither of them has a price yet."):
            self.play(FadeIn(self.empty_rows, lag_ratio=0.2), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        ask = self._ask("Which of the three would you run on this line?")
        with self.say("Pick one now. The prices are off screen on purpose."):
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.beat(2.2)
        self.play(FadeOut(ask), run_time=0.5, rate_func=rf.ease_in_sine)

    # ---------------- B3 · three prices out of one case -------------------
    def b3_three_prices_one_case(self):
        self.scale_t = ValueTracker(FULL_SCALE)
        self.alarm_t = {opt: ValueTracker(0.0) for opt in OPTION_IDS}
        self.wait_t = {opt: ValueTracker(0.0) for opt in OPTION_IDS}

        bars = VGroup(*[always_redraw(self._bar(i, opt))
                        for i, opt in enumerate(OPTION_IDS)])
        totals = VGroup(*[always_redraw(self._total(i, opt))
                          for i, opt in enumerate(OPTION_IDS)])
        self.bars, self.totals = bars, totals
        self.add(bars, totals)

        # The whole panel is one always_redraw, not a static group holding a
        # redrawn value: an updater inside an arranged VGroup rebuilds its
        # mobject at the origin every frame and ignores the arrangement, which
        # put a second copy of the scale figure on top of the middle bar.
        scale_panel = always_redraw(self._scale_panel)
        self.scale_panel = scale_panel

        with self.say("Now the prices, and every one of them is carried out of that "
                      "strip rather than typed onto the screen."):
            self.play(FadeIn(scale_panel), run_time=0.7, rate_func=rf.ease_out_sine)

        lines = {
            "rule-1": "One point beyond three sigma waits the longest, so its stack "
                      "of wasted minutes is the tallest thing on the board.",
            "rules-1-2": "Two rules cut the waiting by more than half, and buy "
                         "fewer alarms doing it.",
            "all-four": "All four cut the waiting again, and this time the alarm "
                        "half goes up rather than down.",
        }
        for i, opt in enumerate(OPTION_IDS):
            alarm_half, wait_half = SMALL[opt]
            travel = VGroup(self.fa_block.copy(), self.stack.copy())
            targets = self._segment_targets(i, alarm_half, wait_half)
            with self.say(lines[opt]):
                self.play(FadeOut(self.empty_rows[i]),
                          Transform(travel[0], targets[0]),
                          Transform(travel[1], targets[1]),
                          run_time=1.8, rate_func=rf.ease_in_out_sine)
                self.alarm_t[opt].set_value(alarm_half)
                self.wait_t[opt].set_value(wait_half)
                # `Transform` adds each transformed mobject to the scene on its
                # own, so removing the group they were built in leaves both
                # copies on screen. They sit exactly on the bar at this scale
                # and only appear when B4 rescales it, as a ghost of the old bar.
                self.remove(travel, *travel)

        cheapest_alarm = min(OPTION_IDS, key=lambda opt: SMALL[opt][0])
        with self.say("Three prices, one case. And the plate that bought the "
                      "fewest false alarms is not the one that won."):
            self.play(Indicate(self.bars[OPTION_IDS.index(cheapest_alarm)][0],
                               color=YELLOW, scale_factor=1.06), run_time=1.3)

        # An underline rather than a box around the plate: a box tall enough to
        # frame the two plate rows reaches the waiting stack when it walks past
        # the drift column in B4.
        marker = Rectangle(width=BAR_W + 0.40, height=0.07,
                           fill_color=TEAL, fill_opacity=1.0,
                           stroke_color=TEAL, stroke_width=0.0)
        marker.move_to([PLATE_X[OPTION_IDS.index(CASE["answer"])], MARKER_Y, 0])
        self.marker = marker
        with self.say("Same four facts, three prices. One is smaller, and that is "
                      "arithmetic rather than taste."):
            self.play(Create(marker), run_time=0.9, rate_func=rf.ease_out_sine)

        # The expression is a caption on two stacks that already exist.
        expr = VGroup(
            gauge("expected false alarms x false-alarm cost", 19, YELLOW),
            gauge("+", 19, INK),
            gauge("delay minutes x missed-shift cost", 19, RED),
        ).arrange(RIGHT, buff=0.24)
        expr.move_to([0.0, EXPR_Y, 0])
        within_frame(expr, "B3 expected-cost expression")
        self.expr = expr
        with self.say("Two terms, in the colours of the two stacks they were built "
                      "from. Nothing else is in the arithmetic."):
            self.play(Write(expr), run_time=2.0, rate_func=rf.linear)

        winner = OPTION_IDS.index(CASE["answer"])
        with self.say("The cheapest one on this line, priced from this line's own "
                      "four facts."):
            self.play(self.camera.frame.animate.scale(0.88)
                      .move_to([0.5 * PLATE_X[winner], -1.30, 0]),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)
            self.beat(0.9)
            self.play(Restore(self.camera.frame), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)

    def _scale_panel(self) -> VGroup:
        """What a full-depth bar is worth, so a rescale is announced not hidden."""
        grp = VGroup(micro("FULL SCALE", 14, GREY),
                     gauge(f"{self.scale_t.get_value():.2f}", 19, INK))
        grp.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        return grp.move_to([SCALE_X, SCALE_PANEL_Y, 0], aligned_edge=LEFT)

    def _bar(self, i: int, opt: str):
        def build() -> VGroup:
            full = self.scale_t.get_value()
            grp, y = VGroup(), RAIL_Y
            for tracker, color in ((self.alarm_t[opt], YELLOW),
                                   (self.wait_t[opt], RED)):
                depth = max(tracker.get_value() / full * BAR_DEPTH, 1e-4)
                seg = Rectangle(width=BAR_W, height=depth, fill_color=color,
                                fill_opacity=0.92, stroke_color=color,
                                stroke_width=1.0)
                seg.move_to([PLATE_X[i], y, 0], aligned_edge=UP)
                grp.add(seg)
                y -= depth
            return grp
        return build

    def _total(self, i: int, opt: str):
        def build():
            value = self.alarm_t[opt].get_value() + self.wait_t[opt].get_value()
            txt = gauge(f"{value:.{PRINTED_DECIMALS}f}", 19, INK)
            return txt.move_to([PLATE_X[i], TOTAL_Y, 0])
        return build

    def _segment_targets(self, i: int, alarm_half: float,
                         wait_half: float) -> VGroup:
        """Where the strip's two block groups land when they become a bar."""
        full = self.scale_t.get_value()
        grp, y = VGroup(), RAIL_Y
        for value, color in ((alarm_half, YELLOW), (wait_half, RED)):
            depth = max(value / full * BAR_DEPTH, 1e-4)
            seg = Rectangle(width=BAR_W, height=depth, fill_color=color,
                            fill_opacity=0.92, stroke_color=color,
                            stroke_width=1.0)
            seg.move_to([PLATE_X[i], y, 0], aligned_edge=UP)
            grp.add(seg)
            y -= depth
        return grp

    # ---------------- B4 · move one line of the case ----------------------
    def b4_move_one_line(self):
        field = CASE["deciding_field"]
        row = CASE_FIELDS.index(field)
        others = [self.card[k] for k in range(len(CASE_FIELDS)) if k != row]

        with self.say("Three of those four facts are about to be held completely "
                      "still."):
            self.play(*[grp.animate.set_opacity(0.28) for grp in others],
                      Indicate(self.card[row], color=YELLOW, scale_factor=1.06),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        ask = self._ask("If only this row moves, does the answer move with it?")
        with self.say("One row is still lit. Before I touch it: decide whether "
                      "moving it can change which rule set is correct."):
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.beat(1.8)
        self.play(FadeOut(ask), run_time=0.5, rate_func=rf.ease_in_sine)

        big = NEUTRAL["expected_shift_size"]
        new_value = gauge(f"{big:.1f} sigma", 21, INK)
        new_value.move_to(self.card[row][1].get_left(), aligned_edge=LEFT)

        with self.say(f"The line now expects a {big:.0f} sigma move rather than a "
                      f"{CASE['expected_shift_size']:.0f} sigma one. That is the "
                      f"only edit."):
            self.play(Transform(self.card[row][1], new_value),
                      self.shift_t.animate.set_value(big),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)

        with self.say("Every rule set now sees it in about two subgroups, so the "
                      "waiting collapses for all three of them at once."):
            self.play(*[self.alarm_t[opt].animate.set_value(BIG[opt][0])
                        for opt in OPTION_IDS],
                      *[self.wait_t[opt].animate.set_value(BIG[opt][1])
                        for opt in OPTION_IDS],
                      run_time=2.6, rate_func=rf.ease_in_out_sine)

        with self.say("The rates the plates buy their alarms at did not move at "
                      "all. The purchase price is exactly what it was."):
            self.play(Indicate(self.rate_rows, color=YELLOW, scale_factor=1.10),
                      run_time=1.4)

        with self.say("At this scale all three are nearly nothing, so the board "
                      "rescales to what is left."):
            self.play(self.scale_t.animate.set_value(FULL_SCALE_BIG),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)

        winner = OPTION_IDS.index(NEUTRAL["answer"])
        with self.say("I changed one line of the case. The rules did not change. "
                      "The answer did."):
            self.play(self.marker.animate.move_to([PLATE_X[winner], MARKER_Y, 0]),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)
            self.beat(1.4)

        with self.say("The extra rules still cost what they always cost. Against a "
                      "move this size they simply have nothing left to buy."):
            self.beat(1.2)

    # ---------------- B5 · what the next shift does -----------------------
    def b5_what_the_next_shift_does(self):
        gone = VGroup(self.bars, self.totals, self.plates, self.marker, self.expr,
                      self.card, self.scale_panel, self.lit,
                      self.caliper, self.stack, self.fa_block,
                      self.curve_axes, self.process_curve, self.curve_centre,
                      self.strip_tag)
        with self.say("Put the arithmetic away. It has already done its job."):
            self.play(FadeOut(gone), run_time=1.6, rate_func=rf.ease_in_sine)
            # The slots stop being cost evidence and go back to being the time
            # axis of a chart, so their fills clear and their outlines recede.
            self.play(*[slot.animate.set_fill(GREY, opacity=0.0)
                        .set_stroke(GREY, opacity=0.30)
                        for slot in self.slots],
                      run_time=0.8, rate_func=rf.ease_in_out_sine)

        with self.say("What is left is the line, back at full width, running the "
                      "rule set this case actually chose."):
            self.play(self.strip.animate.scale(1.52).move_to([0.0, -0.15, 0]),
                      self.drift_mark.animate.scale(1.52),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)
            self.remove(self.drift_mark)

        pitch = SLOT_PITCH * 1.52
        left = float(self.slots[0].get_center()[0])
        base = float(self.slots[0].get_center()[1])

        def slot_x(i: int) -> float:
            return left + i * pitch

        # 0.30 frame units per sigma: at the 0.20 the strip's own slot height
        # suggested, a one-sigma drift is smaller than the scatter around it and
        # the series reads as confetti rather than as a mean that moved.
        centre = Line([slot_x(0) - 0.20, base, 0],
                      [slot_x(N_SLOTS - 1) + 0.20, base, 0],
                      stroke_color=GREY, stroke_width=1.0)
        dots = VGroup(*[
            Dot([slot_x(i), base + 0.30 * float(Z_RUN[i]), 0], radius=0.040,
                color=TEAL if i < DRIFT else BLUE)
            for i in range(N_SLOTS)])
        with self.say("Every subgroup it plotted, in the order it plotted them."):
            self.play(Create(centre), run_time=0.5, rate_func=rf.ease_out_sine)
            self.play(FadeIn(dots, lag_ratio=0.03), run_time=1.8,
                      rate_func=rf.ease_out_sine)

        won = CASE["answer"]
        slot = ALARM_SLOT[won]
        rule = _firing_rule(slot)
        alarm = Rectangle(width=SLOT_W * 1.52 + 0.12, height=SLOT_H * 1.52 + 0.12,
                          stroke_color=RED, stroke_width=2.6, fill_opacity=0.0)
        alarm.move_to([slot_x(slot), base, 0])
        with self.say("It alarms here."):
            self.play(Create(alarm), run_time=0.8, rate_func=rf.ease_out_sine)

        held = self._span(slot_x(slot), slot_x(N_SLOTS - 1), base + 1.85,
                          "held at the next step", RED)
        with self.say("Everything from that subgroup on is held at the next step "
                      "instead of shipped."):
            self.play(Create(held[0]), FadeIn(held[1]), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        pulled = self._span(slot_x(DRIFT), slot_x(slot), base - 1.55,
                            "pulled back onto the chart", YELLOW)
        with self.say("Everything between the move and the alarm is pulled back "
                      "and looked at again."):
            self.play(Create(pulled[0]), FadeIn(pulled[1]), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        log = VGroup(
            micro("LOGGED", 15, GREY),
            gauge(RULE_TEXT[rule], 19, INK),
            gauge(f"bought to catch {CASE['expected_shift_size']:.1f} sigma", 17, GREY),
        ).arrange(DOWN, buff=0.10, aligned_edge=LEFT)
        log.move_to([slot_x(0), base + 2.55, 0], aligned_edge=LEFT)
        within_frame(log, "B5 log card")
        with self.say("And the reason is written down against the size of move it "
                      "was bought to catch."):
            self.play(FadeIn(log, shift=DOWN * 0.10), run_time=1.4,
                      rate_func=rf.ease_out_sine)

        with self.say("You are not choosing a rule set. You are choosing what the "
                      "next shift does when the chart alarms."):
            self.play(self.camera.frame.animate.scale(1.06), run_time=2.2,
                      rate_func=rf.ease_in_out_sine)
            self.beat(2.0)

    def _span(self, xa: float, xb: float, y: float, text: str,
              color: str) -> tuple[VGroup, VGroup]:
        bar = Line([xa, y, 0], [xb, y, 0], stroke_color=color, stroke_width=2.2)
        ends = VGroup(*[Line([x, y - 0.09, 0], [x, y + 0.09, 0],
                             stroke_color=color, stroke_width=2.2)
                        for x in (xa, xb)])
        label = gauge(text, 17, color)
        label.next_to(bar, UP if y > 0 else DOWN, buff=0.12)
        within_frame(label, f"B5 span {text!r}")
        return VGroup(bar, ends), VGroup(label)
