"""Level 7's transfer decision: the price of a rule set on one line.

The act argues that the answer is a property of the line, not of the rules. A
challenge that could be passed by remembering the video's winner would argue the
opposite, so these tests police three things: every number the learner sees is
computed from `spclab.evidence`, the bank of cases still contains all three
winners, and the field each case says is deciding really is the one that decides.

    PYTHONPATH=src .venv/bin/pytest tests/test_level07_mastery.py -q
"""
import json
import random
import re

import numpy as np
import pytest

from spclab.evidence import (
    ALL_RULES,
    ARL_BIG_ALL,
    ARL_BIG_ONE,
    BIG_SHIFT,
    SHIFT,
    TRADE,
)
from spclab.level07_mastery import (
    CASE_FIELDS,
    CASE_SEEDS,
    MIN_MARGIN,
    OPTION_LABELS,
    PRINTED_DECIMALS,
    RULE_OPTIONS,
    SHIFT_GRID,
    challenge_case,
    detection_delay,
    expected_cost,
    false_alarm_run_length,
    neutral_case,
)

BANK = [challenge_case(seed) for seed in CASE_SEEDS]


def _sorted_costs(case):
    return sorted(option["expected_cost"] for option in case["options"])


def _winner(case):
    return case["answer"]


# ------------------------------------------------- the two gates the plan fixed
def test_seed_bank_exercises_every_rule_set():
    assert {challenge_case(seed)["answer"] for seed in CASE_SEEDS} == {
        "rule-1", "rules-1-2", "all-four"
    }


def test_expected_cost_prices_delay_and_false_alarms():
    case = challenge_case(CASE_SEEDS[0])
    for option in case["options"]:
        assert option["expected_cost"] == expected_cost(
            option["rules"],
            expected_shift_size=case["expected_shift_size"],
            false_alarm_cost=case["false_alarm_cost"],
            missed_shift_cost=case["missed_shift_cost"],
            sampling_cadence=case["sampling_cadence"],
        )


# ------------------------------------------------- the API boundary
def test_a_list_and_a_tuple_name_the_same_rule_set():
    """The page will hand back JSON, which has no tuples."""
    kwargs = dict(expected_shift_size=SHIFT, false_alarm_cost=900.0,
                  missed_shift_cost=2.0, sampling_cadence=15.0)
    assert expected_cost([1, 2], **kwargs) == expected_cost((1, 2), **kwargs)


def test_a_rule_set_nobody_priced_is_refused():
    """(1, 3) is a legal thought and an unpriced one; guessing it would be a lie."""
    with pytest.raises(ValueError):
        expected_cost((1, 3), expected_shift_size=SHIFT, false_alarm_cost=1.0,
                      missed_shift_cost=1.0, sampling_cadence=1.0)


def test_a_shift_off_the_grid_is_refused():
    with pytest.raises(ValueError):
        detection_delay((1,), 2.0)


# ------------------------------------------------- nothing is copied, everything read
def test_the_options_are_rule_sets_evidence_already_simulated():
    for key in RULE_OPTIONS.values():
        assert key in TRADE, key
    assert RULE_OPTIONS["all-four"] == ALL_RULES


def test_the_shift_grid_is_the_pair_the_level_already_uses():
    """Pinned by the Act B storyboard: this act may not invent a third shift."""
    assert SHIFT_GRID == (SHIFT, BIG_SHIFT)


def test_the_run_lengths_come_from_the_evidence_table():
    for key in RULE_OPTIONS.values():
        assert false_alarm_run_length(key) == TRADE[key]["arl0"]
        assert detection_delay(key, SHIFT) == TRADE[key]["arl1"]


def test_the_big_shift_delay_is_cached_and_does_not_drift():
    """Simulated once. A second call that re-simulated could quietly disagree."""
    assert detection_delay((1,), BIG_SHIFT) == ARL_BIG_ONE
    assert detection_delay(ALL_RULES, BIG_SHIFT) == ARL_BIG_ALL
    middle = detection_delay((1, 2), BIG_SHIFT)
    assert detection_delay((1, 2), BIG_SHIFT) == middle
    assert BIG_SHIFT > SHIFT and middle < TRADE[(1, 2)]["arl1"]


# ------------------------------------------------- the cases the page will serve
def test_every_case_survives_a_json_round_trip():
    for case in BANK:
        assert json.loads(json.dumps(case)) == case


def test_a_seed_always_returns_the_same_case():
    forward = [challenge_case(seed) for seed in CASE_SEEDS]
    backward = [challenge_case(seed) for seed in reversed(CASE_SEEDS)][::-1]
    assert forward == backward == BANK


def test_pricing_a_case_leaks_no_random_state():
    """A challenge that moved the global seed would change its neighbours."""
    before_std, before_np = random.getstate(), np.random.get_state()
    for seed in CASE_SEEDS:
        challenge_case(seed)
    assert random.getstate() == before_std
    assert all(np.array_equal(a, b)
               for a, b in zip(np.random.get_state(), before_np))


def test_no_case_is_a_tie_at_the_precision_the_page_prints():
    """Two equally correct answers would make the wrong-answer feedback a lie."""
    for case in BANK:
        best, runner_up = _sorted_costs(case)[:2]
        assert runner_up - best > MIN_MARGIN, case["seed"]
        assert round(best, PRINTED_DECIMALS) != round(runner_up, PRINTED_DECIMALS)


def test_the_bank_covers_every_winner_shift_and_deciding_field():
    """A future edit may not quietly drop a class of case from the retry bank."""
    assert {_winner(c) for c in BANK} == set(RULE_OPTIONS)
    assert {c["expected_shift_size"] for c in BANK} == set(SHIFT_GRID)
    assert {c["deciding_field"] for c in BANK} == set(CASE_FIELDS)


def test_each_case_names_the_field_that_actually_decides():
    """Neutralise the named field and the winner must move or stop being a winner."""
    for case in BANK:
        neutral = neutral_case(case)
        best, runner_up = _sorted_costs(neutral)[:2]
        moved = neutral["answer"] != case["answer"]
        assert moved or runner_up - best <= MIN_MARGIN, (
            case["seed"], case["deciding_field"], neutral["answer"])


def test_the_first_case_is_the_one_the_storyboard_rendered():
    """Act B shot B4 moves one row and the marker walks from all four to rule 1."""
    case = challenge_case(CASE_SEEDS[0])
    assert case["expected_shift_size"] == SHIFT
    assert case["deciding_field"] == "expected shift size"
    assert case["answer"] == "all-four"
    assert neutral_case(case)["answer"] == "rule-1"


# ------------------------------------------------- what the learner reads
def test_the_vocabulary_is_the_one_the_contract_fixed():
    assert list(OPTION_LABELS) == ["rule-1", "rules-1-2", "all-four"]
    assert list(OPTION_LABELS.values()) == [
        "Rule 1 only", "Rules 1 + 2", "All four Western Electric rules"]
    assert CASE_FIELDS == ("expected shift size", "false-alarm cost",
                           "missed-shift cost", "sampling cadence")
    for case in BANK:
        assert [o["id"] for o in case["options"]] == list(OPTION_LABELS)
        assert [o["label"] for o in case["options"]] == list(OPTION_LABELS.values())


def test_no_surface_story_carries_an_identifier():
    """Masked means masked: no name, no product, no tool code, no digits at all."""
    banned = ("ICOS", "BTMMN", "Nikon", "OM-X")
    for case in BANK:
        story = case["surface_story"]
        assert not any(ch.isdigit() for ch in story), case["seed"]
        assert not any(word in story for word in banned), case["seed"]
        assert not re.search(r"\b[A-Z]{2,}\b", story), case["seed"]
        # A proper noun is a capital that is not opening a sentence.
        for capital in re.finditer(r"(?<!^)(?<![.]\s)\b[A-Z][a-z]+", story):
            pytest.fail(f"{case['seed']}: proper noun {capital.group()!r}")


# ------------------------------------------------- watch the gate fail
def test_a_sabotaged_cost_model_would_change_the_winners():
    """Both terms carry the argument; dropping either one is visible in the bank."""
    real = [_winner(c) for c in BANK]

    def winners(price):
        out = []
        for case in BANK:
            costs = {opt["id"]: price(opt["rules"], case) for opt in case["options"]}
            out.append(min(costs, key=costs.get))
        return out

    def delay_only(rules, case):
        return (detection_delay(tuple(rules), case["expected_shift_size"])
                * case["sampling_cadence"] * case["missed_shift_cost"])

    def false_alarms_only(rules, case):
        key = tuple(rules)
        return (detection_delay(key, case["expected_shift_size"])
                / false_alarm_run_length(key) * case["false_alarm_cost"])

    assert winners(delay_only) != real
    assert winners(false_alarms_only) != real
