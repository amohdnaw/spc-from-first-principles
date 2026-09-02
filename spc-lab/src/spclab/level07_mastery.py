"""LEVEL 7 — Which rule set earns its false alarms on *this* line.

`evidence` priced the trade in the abstract: every rule added shortens the wait
for a real shift and shortens the wait for a false one too. It stops there on
purpose, because the arithmetic cannot say which side matters until a line says
what each side costs it. This module is that last step, and it exists so the
challenge after Act B can be answered only by pricing the case in front of you.

Three claims, none asserted:

1. **A rule set has a price, not a rank.** Expected cost is the money the chart
   is expected to burn under one set of rules: the false alarms it will raise
   before it catches the shift, plus the minutes of drift it will let through
   first. Both halves come from the same run length, so neither can be tuned
   without the other.

2. **The winner belongs to the line.** Change nothing but the expected shift
   size and the cheapest rule set changes with it, because the sensitivity the
   extra rules buy depends on the shift while the false alarms they cost do not.
   That is the counterexample Act B renders, and `neutral_case` is how a test
   proves each case really turns on the field it claims.

3. **No number here is typed twice.** Every run length is read from
   `evidence.TRADE` or from `evidence.average_run_length`; the blueprints below
   type only what a plant would tell you — a masked story, a shift to watch for,
   two costs and a cadence. Winners, costs and feedback values are computed.

Units, since the two costs have different shapes and mixing them silently would
be undetectable:

    expected_shift_size   sigma of the plotted statistic  (an entry of SHIFT_GRID)
    false_alarm_cost      money per false alarm event
    missed_shift_cost     money per minute of undetected drift
    sampling_cadence      minutes per subgroup
    detection_delay       subgroups until the alarm  (an average run length)
    false alarms          delay / arl0, a count over that same delay

    PYTHONPATH=src .venv/bin/python -m spclab.level07_mastery
"""
from __future__ import annotations

from collections.abc import Sequence

from spclab.evidence import (
    ALL_RULES,
    ARL_BIG_ALL,
    ARL_BIG_ONE,
    BIG_SHIFT,
    SHIFT,
    TRADE,
    average_run_length,
)

# The three sets the learner chooses between, in the order the page lists them.
# Not every cumulative set: three options fit on one screen and (1,2,3) teaches
# nothing that (1,2) does not.
RULE_OPTIONS: dict[str, tuple[int, ...]] = {
    "rule-1": (1,),
    "rules-1-2": (1, 2),
    "all-four": (1, 2, 3, 4),
}

# Learner-visible wording, fixed by the pilot contract. The page renders these
# rather than its own copies, so the words cannot drift away from the numbers.
OPTION_LABELS: dict[str, str] = {
    "rule-1": "Rule 1 only",
    "rules-1-2": "Rules 1 + 2",
    "all-four": "All four Western Electric rules",
}

# The four facts a case states, in the labels the challenge and its feedback use.
CASE_FIELDS: tuple[str, ...] = (
    "expected shift size",
    "false-alarm cost",
    "missed-shift cost",
    "sampling cadence",
)
_FIELD_INPUTS: dict[str, str] = {
    "expected shift size": "expected_shift_size",
    "false-alarm cost": "false_alarm_cost",
    "missed-shift cost": "missed_shift_cost",
    "sampling cadence": "sampling_cadence",
}

# The small shift the one-point rule is nearly blind to, and the big one it sees
# unaided. Read from `evidence` so this act cannot quietly price a third shift.
SHIFT_GRID: tuple[float, float] = (SHIFT, BIG_SHIFT)

CASE_SEEDS: tuple[int, ...] = tuple(range(701, 713))

# The page prints money to the cent, so two answers within a cent of each other
# are the same answer as far as the learner can see.
PRINTED_DECIMALS = 2
MIN_MARGIN = 10.0 ** -PRINTED_DECIMALS


def _rule_key(rules: Sequence[int]) -> tuple[int, ...]:
    """The rule set as a hashable key, or a refusal.

    JSON has no tuples, so the page hands rules back as a list. Anything that is
    not one of the three priced sets is refused rather than guessed: a run length
    for `(1, 3)` was never simulated and inventing one would be undetectable.
    """
    key = tuple(rules)
    if key not in RULE_OPTIONS.values():
        raise ValueError(f"unknown rule set: {key}")
    return key


def false_alarm_run_length(rules: Sequence[int]) -> float:
    """Subgroups between false alarms on a process that never moved: ARL0.

    Read from `evidence.TRADE`, which simulated it, so the rate the act charges
    for is the rate Act A drew.
    """
    return TRADE[_rule_key(rules)]["arl0"]


# `evidence` already simulated the one-rule and all-four charts at BIG_SHIFT
# while it was imported. Re-running them here would spend seconds reproducing
# numbers already in memory, so those two are seeded and only the middle set is
# ever simulated — once, on first use, and then cached, because a run length
# that changed between two calls in one session would make the act's before and
# after frames disagree.
_BIG_SHIFT_DELAY: dict[tuple[int, ...], float] = {
    (1,): ARL_BIG_ONE,
    ALL_RULES: ARL_BIG_ALL,
}


def detection_delay(rules: Sequence[int], expected_shift_size: float) -> float:
    """Subgroups the chart waits before flagging a shift of that size: ARL1.

    This is the whole benefit side of the trade. It is read at 1 sigma from the
    table `evidence` published and computed once at 3 sigma, because the point
    of the level is that the same rule set is worth very different amounts at
    those two shifts.
    """
    key = _rule_key(rules)
    if expected_shift_size == SHIFT:
        return TRADE[key]["arl1"]
    if expected_shift_size == BIG_SHIFT:
        if key not in _BIG_SHIFT_DELAY:
            _BIG_SHIFT_DELAY[key] = average_run_length(key, shift=BIG_SHIFT)[0]
        return _BIG_SHIFT_DELAY[key]
    raise ValueError(f"shift off the grid {SHIFT_GRID}: {expected_shift_size}")


def expected_cost(rules: Sequence[int], *, expected_shift_size: float,
                  false_alarm_cost: float, missed_shift_cost: float,
                  sampling_cadence: float) -> float:
    """What running this rule set on this line is expected to cost, per shift caught.

    Two terms, one run length. The chart raises `delay / arl0` false alarms while
    it waits, each charged once, and it lets `delay x cadence` minutes of drift
    through, charged by the minute. Adding rules pulls the delay down and the
    false-alarm rate up, which is why the sum has a minimum somewhere and why
    where that minimum sits is a fact about the line rather than about the rules.
    """
    key = _rule_key(rules)
    delay = detection_delay(key, expected_shift_size)
    expected_false_alarms = delay / false_alarm_run_length(key)
    delay_minutes = delay * sampling_cadence
    return expected_false_alarms * false_alarm_cost + delay_minutes * missed_shift_cost


# ---------------------------------------------------------------------------
# The case bank
# ---------------------------------------------------------------------------
# A blueprint types only what a plant states: a masked story, the shift worth
# watching for, the two costs, the cadence, and which of the four fields the
# answer turns on. That last claim is not trusted — `neutral_case` re-prices the
# case with the field switched off and a test insists the winner moves.
_BLUEPRINTS: dict[int, dict[str, object]] = {
    701: {
        "surface_story": (
            "A masked deposition line plots one film-thickness subgroup every "
            "sampling interval. When the mean really drifts, everything produced "
            "between the drift and the alarm is reworked at the next step, so the "
            "damage is charged per minute the drift goes unseen. When the chart "
            "alarms and nothing has changed, the line stops for one check, so that "
            "damage is charged once per event."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 4500.0,
        "missed_shift_cost": 1.5,
        "sampling_cadence": 20.0,
        "deciding_field": "expected shift size",
    },
    702: {
        "surface_story": (
            "A masked wire-bond cell plots one pull-strength subgroup per interval. "
            "A drift keeps laying down weak joints that are screened and re-run "
            "downstream, charged for every minute it goes unseen. A false alarm "
            "pulls the operator off the cell for one verification run, charged once."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 800.0,
        "missed_shift_cost": 2.0,
        "sampling_cadence": 10.0,
        "deciding_field": "missed-shift cost",
    },
    703: {
        "surface_story": (
            "A masked plating line plots one coating-weight subgroup per interval. "
            "Unseen drift keeps plating parts that must be stripped and plated "
            "again, charged by the minute. A false alarm costs one bath check, "
            "charged once each time, and the line samples slowly."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 2400.0,
        "missed_shift_cost": 1.0,
        "sampling_cadence": 60.0,
        "deciding_field": "sampling cadence",
    },
    704: {
        "surface_story": (
            "A masked furnace anneal plots one sheet-resistance subgroup per "
            "interval. A false alarm cools the tube and buys a full requalification "
            "before the next load. Drift is caught again at the electrical test "
            "downstream, so the minutes it survives are cheap."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 9000.0,
        "missed_shift_cost": 0.5,
        "sampling_cadence": 20.0,
        "deciding_field": "false-alarm cost",
    },
    705: {
        "surface_story": (
            "A masked press shop plots one stamped-height subgroup per interval. "
            "When the tool moves it moves hard, so the shift worth planning for is "
            "a large one. A false alarm empties the press for a die inspection, and "
            "the parts made during a drift are sorted cheaply by the minute."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 6000.0,
        "missed_shift_cost": 0.8,
        "sampling_cadence": 15.0,
        "deciding_field": "expected shift size",
    },
    706: {
        "surface_story": (
            "A masked fill line plots one net-weight subgroup per interval. The "
            "failure it plans for is a large step when a valve sticks. Product given "
            "away during an unseen drift is charged by the minute, and a false alarm "
            "halts filling for one scale check."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 300.0,
        "missed_shift_cost": 1.0,
        "sampling_cadence": 20.0,
        "deciding_field": "missed-shift cost",
    },
    707: {
        "surface_story": (
            "A masked etch chamber plots one critical-dimension subgroup per "
            "interval, and a chamber fault moves the mean a long way at once. Every "
            "minute of unseen drift feeds wafers that cannot be reworked at all, "
            "while a false alarm costs one short chamber check. Subgroups are "
            "twenty minutes apart."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 100.0,
        "missed_shift_cost": 50.0,
        "sampling_cadence": 20.0,
        "deciding_field": "sampling cadence",
    },
    708: {
        "surface_story": (
            "A masked paint booth plots one film-build subgroup per interval, and "
            "the drift it fears is a large one from a blocked feed. A false alarm "
            "empties and purges the booth, which is the expensive event here. "
            "Panels made during a drift are corrected at the touch-up bay by the "
            "minute."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 12000.0,
        "missed_shift_cost": 2.0,
        "sampling_cadence": 30.0,
        "deciding_field": "false-alarm cost",
    },
    709: {
        "surface_story": (
            "A masked grinding cell plots one bore-diameter subgroup per interval. "
            "Wheel wear moves the mean slowly, so the shift worth catching is small. "
            "Parts made during an unseen drift are re-ground later, charged by the "
            "minute, and a false alarm costs one wheel-dress check."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 1500.0,
        "missed_shift_cost": 1.0,
        "sampling_cadence": 25.0,
        "deciding_field": "expected shift size",
    },
    710: {
        "surface_story": (
            "A masked reflow oven plots one peak-temperature subgroup per interval, "
            "and a heater fault moves it far in one step. Boards baked during a "
            "drift are reworked joint by joint, charged by the minute, while a false "
            "alarm holds the conveyor for one profile check. The oven is sampled "
            "rarely."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 1000.0,
        "missed_shift_cost": 1.0,
        "sampling_cadence": 40.0,
        "deciding_field": "sampling cadence",
    },
    711: {
        "surface_story": (
            "A masked injection cell plots one shot-weight subgroup per interval, "
            "and the drift it plans for is a slow one as the screw wears. A false "
            "alarm purges the barrel, which is charged once and is not cheap. Unseen "
            "drift only adds trim work, charged by the minute."),
        "expected_shift_size": SHIFT,
        "false_alarm_cost": 20000.0,
        "missed_shift_cost": 1.0,
        "sampling_cadence": 20.0,
        "deciding_field": "expected shift size",
    },
    712: {
        "surface_story": (
            "A masked polish step plots one removal-rate subgroup per interval, and "
            "a pad failure moves the mean a long way at once. Every minute of unseen "
            "drift polishes wafers past target with no recovery, while a false alarm "
            "costs one pad-conditioning check."),
        "expected_shift_size": BIG_SHIFT,
        "false_alarm_cost": 150.0,
        "missed_shift_cost": 30.0,
        "sampling_cadence": 25.0,
        "deciding_field": "missed-shift cost",
    },
}

# Switching a field off has to mean something specific, or "this field decides"
# is a claim nobody can check. A cost that is zero is a cost the line does not
# care about. A cadence of one minute is the cadence that stops amplifying: a
# subgroup of delay is then a minute of delay. Zero cadence would delete the
# whole term instead, which tests the missed-shift cost rather than the cadence.
# The neutral expected shift size is the other entry of the grid, which is the
# counterexample Act B renders on screen.
_NEUTRAL_COSTS: dict[str, float] = {
    "false-alarm cost": 0.0,
    "missed-shift cost": 0.0,
    "sampling cadence": 1.0,
}


def _priced(seed: int, surface_story: str, deciding_field: str, *,
            expected_shift_size: float, false_alarm_cost: float,
            missed_shift_cost: float, sampling_cadence: float) -> dict:
    """One case with all three options priced and the cheapest one marked."""
    options = []
    for option_id, rules in RULE_OPTIONS.items():
        options.append({
            "id": option_id,
            "label": OPTION_LABELS[option_id],
            "rules": list(rules),
            "expected_cost": expected_cost(
                rules,
                expected_shift_size=expected_shift_size,
                false_alarm_cost=false_alarm_cost,
                missed_shift_cost=missed_shift_cost,
                sampling_cadence=sampling_cadence),
        })
    return {
        "seed": seed,
        "surface_story": surface_story,
        "expected_shift_size": expected_shift_size,
        "false_alarm_cost": false_alarm_cost,
        "missed_shift_cost": missed_shift_cost,
        "sampling_cadence": sampling_cadence,
        "deciding_field": deciding_field,
        "options": options,
        "answer": min(options, key=lambda option: option["expected_cost"])["id"],
    }


def challenge_case(seed: int) -> dict:
    """The unseen-data case the page serves, priced and JSON-safe.

    The seed selects a case from the bank rather than driving a generator: the
    learner needs a story that reads like a plant wrote it, and a retry has to
    land on a case whose winner and deciding field are both known to be checkable.
    The same seed always returns the same case, so the page, the act and the tests
    can each quote it without agreeing on anything but the number.
    """
    if seed not in _BLUEPRINTS:
        raise ValueError(f"no case for seed {seed}; the bank is {CASE_SEEDS}")
    blueprint = dict(_BLUEPRINTS[seed])
    return _priced(seed, blueprint.pop("surface_story"),
                   blueprint.pop("deciding_field"), **blueprint)


def neutral_case(case: dict) -> dict:
    """The same case with its deciding field switched off, re-priced.

    This is the operational meaning of `deciding_field`: if neutralising the
    named field leaves the same winner by the same margin, the case did not turn
    on that field and the wrong-answer feedback would be pointing at the wrong
    row. Act B shot B4 is this function run on the first case.
    """
    field = case["deciding_field"]
    inputs = {name: case[name] for name in _FIELD_INPUTS.values()}
    if field == "expected shift size":
        other = SHIFT_GRID[1] if case["expected_shift_size"] == SHIFT_GRID[0] else SHIFT_GRID[0]
        inputs["expected_shift_size"] = other
    else:
        inputs[_FIELD_INPUTS[field]] = _NEUTRAL_COSTS[field]
    return _priced(case["seed"], case["surface_story"], field, **inputs)


if __name__ == "__main__":
    print(f"shift grid {SHIFT_GRID}   printed to {PRINTED_DECIMALS} decimals\n")
    for _seed in CASE_SEEDS:
        _case = challenge_case(_seed)
        _costs = sorted(o["expected_cost"] for o in _case["options"])
        print(f"{_seed}  shift {_case['expected_shift_size']:.0f}  "
              f"winner {_case['answer']:<9}  margin {_costs[1] - _costs[0]:10.2f}  "
              f"decided by {_case['deciding_field']:<19} "
              f"-> neutral winner {neutral_case(_case)['answer']}")
