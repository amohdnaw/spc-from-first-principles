"""Level 7's claims, and the fast path that makes them affordable.

An average run length needs millions of plotted points, so `evidence` has a
vectorised twin of the canonical rule checker. The first test is the one that
matters: if the twin drifts from `formulas.western_electric_violations`, every
number in this level is measuring a rule the site does not actually apply.
"""
import math

import numpy as np
import pytest

from spclab.detection import ARL1_SHEW, SHEWHART_ARL0
from spclab.evidence import (
    ALPHA_1, ARL0_ALL, ARL0_ONE_RULE, ARL1_ALL, ARL1_FROM_POWER, ARL1_ONE_RULE,
    ARL_BIG_ALL, ARL_BIG_ONE, BETA_AT, BIG_SHIFT, CHAMP_WOODALL_ARL0,
    FALSE_ALARM_COST, LIMIT, MAX_LEN, POWER_AT, P_AT_2_5, P_AT_3, RULES,
    SENSITIVITY_GAIN, SHIFT, SHIFTS, TRADE, alpha_one_point, average_run_length,
    beta_one_point, cumulative_sets, first_violation, p_value, power_one_point,
)
from spclab.formulas import inside, western_electric_violations


# ------------------------------------------- the fast path must be the same rule
@pytest.mark.parametrize("rules", cumulative_sets())
def test_first_violation_matches_the_canonical_rules(rules):
    """Same answer as the definition, on 300 random series, index for index."""
    rng = np.random.default_rng(31)
    series = rng.normal(0.0, 1.0, size=(300, 60))
    fast = first_violation(series, rules)
    for row, got in zip(series, fast):
        hits = [i for i, desc in western_electric_violations(row, 0.0, 1.0)
                if int(desc.split(":")[0].split()[-1]) in rules]
        want = min(hits) if hits else -1
        assert got == want, (rules, want, got, row[:12])


def test_first_violation_finds_planted_patterns():
    """A hand-built series for each rule, so the twin is not only self-consistent."""
    planted = {
        (1,): [0.1, 0.2, 3.5],
        (2,): [0.1, 2.5, 0.2, 2.5],
        (3,): [0.1, 1.5, 0.2, 1.5, 1.5, 1.5],
        (4,): [0.1] + [0.3] * 8,
    }
    for rules, row in planted.items():
        z = np.array([row], dtype=float)
        assert first_violation(z, rules)[0] >= 0, rules


# ------------------------------------------- claim 1: two ways to be wrong
def test_alpha_is_the_number_level_six_priced():
    assert ALPHA_1 == pytest.approx(1.0 - inside(LIMIT), rel=1e-15)
    assert ALPHA_1 == pytest.approx(0.0027, abs=1e-5)


def test_power_and_beta_are_complements():
    for s in SHIFTS:
        assert POWER_AT[s] + BETA_AT[s] == pytest.approx(1.0, abs=1e-12)
        assert 0.0 < POWER_AT[s] < 1.0


def test_power_rises_with_the_shift():
    vals = [POWER_AT[s] for s in SHIFTS]
    assert vals == sorted(vals)
    # with no shift at all, "power" is just the false-alarm rate
    assert POWER_AT[0.0] == pytest.approx(ALPHA_1, rel=1e-12)


def test_a_shift_onto_the_limit_is_a_coin_toss():
    """At δ = 3 the mean sits on the limit, so the next point is 50/50."""
    assert power_one_point(LIMIT) == pytest.approx(0.5, abs=1e-9)


# ------------------- claim 2: one point is nearly blind to a small shift
def test_one_point_is_almost_blind_to_a_one_sigma_shift():
    assert POWER_AT[SHIFT] < 0.03
    assert beta_one_point(SHIFT) > 0.97


def test_the_analytic_run_length_agrees_with_detection():
    """1/power must land on the ARL that module publishes — two routes, one number."""
    assert ARL1_FROM_POWER == pytest.approx(ARL1_SHEW, rel=0.02)


# ------------------------------- claim 3: the chart discards evidence
def test_a_point_inside_the_limits_can_still_be_surprising():
    assert P_AT_2_5 == pytest.approx(0.0124, abs=0.0005)
    assert P_AT_2_5 < 0.05          # would be "significant" anywhere else
    assert 2.5 < LIMIT              # and yet the chart calls it in


def test_the_p_value_at_the_limit_is_alpha():
    """The same number wearing two hats, which is why the chart is a test."""
    assert P_AT_3 == pytest.approx(ALPHA_1, rel=1e-12)
    assert p_value(0.0) == pytest.approx(1.0, abs=1e-12)


# --------------------------- claim 4: the trade, against published values
def test_the_one_rule_chart_reproduces_the_published_run_length():
    assert ARL0_ONE_RULE == pytest.approx(SHEWHART_ARL0, rel=0.03)


def test_all_four_rules_reproduce_champ_and_woodall():
    """External corroboration: 91.75, published 1987, not derived here."""
    assert ARL0_ALL == pytest.approx(CHAMP_WOODALL_ARL0, rel=0.03)


def test_every_added_rule_costs_false_alarms():
    arl0 = [TRADE[rs]["arl0"] for rs in cumulative_sets()]
    assert arl0 == sorted(arl0, reverse=True), arl0
    assert FALSE_ALARM_COST > 3.0


def test_every_added_rule_buys_sensitivity():
    arl1 = [TRADE[rs]["arl1"] for rs in cumulative_sets()]
    assert arl1 == sorted(arl1, reverse=True), arl1
    assert SENSITIVITY_GAIN > 3.0


def test_the_benefit_depends_on_the_shift_but_the_cost_does_not():
    """The level's thesis, as an inequality.

    At a shift the single-point rule already catches, the extra rules buy almost
    nothing — while the false-alarm cost is exactly the same as it was.
    """
    gain_small = ARL1_ONE_RULE / ARL1_ALL
    gain_big = ARL_BIG_ONE / ARL_BIG_ALL
    assert gain_small > 3.0
    assert gain_big < 1.5
    assert gain_small > 3.0 * gain_big


def test_nothing_was_censored_at_the_simulated_length():
    """A run length quoted from a truncated simulation is not a run length."""
    for rs in cumulative_sets():
        assert TRADE[rs]["censored0"] < 0.002, rs
        assert TRADE[rs]["censored1"] < 0.002, rs


def test_a_short_simulation_would_have_been_censored():
    """Proof the length was chosen, not guessed: 200 points is far too few."""
    _, censored = average_run_length((1,), shift=0.0, runs=400, max_len=200)
    assert censored > 0.3
