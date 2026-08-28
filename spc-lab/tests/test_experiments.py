"""Level 12's claims. The last level, and the one with a falsifiable headline.

"One factor at a time finds the wrong answer" is a strong claim, so the test for
it runs the procedure with no noise at all: if it still stops at the wrong
corner, the failure cannot be attributed to measurement error.
"""
import math

import numpy as np
import pytest

from spclab.experiments import (
    ALIASES, BASELINE, CORNERS, CURVATURE, CURVED, EFFECTS, EFFECTS_OBSERVED,
    FLAT, FULL_RUNS, GENERATORS, NOISE_SD, OFAT, OFAT_SEES_INTERACTION,
    OPTIMUM, OPTIMUM_Y, PRECISION, SCREEN_FACTORS, SCREEN_RUNS, TRUTH,
    alias_pairs, best_corner, centre_point_test, factorial_effects,
    full_factorial_runs, ofat, ofat_can_estimate_interaction, response,
    response_curved, screening_design, truth_table,
)


# ---------------- claim 1: OFAT stops at the wrong corner, noise or not
def test_one_factor_at_a_time_does_not_find_the_optimum():
    assert OFAT["found_optimum"] is False
    assert OFAT["chosen"] != OPTIMUM
    assert OFAT["shortfall"] > 0.0


def test_the_failure_is_not_a_noise_problem():
    """`ofat` is evaluated on the true response, so nothing is sampled."""
    assert OFAT["chosen_y"] == pytest.approx(response(*OFAT["chosen"]), rel=1e-15)
    assert OFAT["optimum_y"] == pytest.approx(response(*OPTIMUM), rel=1e-15)


def test_the_shortfall_is_worth_caring_about():
    assert OFAT["shortfall"] / OPTIMUM_Y > 0.20


def test_it_fails_from_either_starting_corner_on_one_axis():
    """Not a lucky baseline: starting low on both factors is the usual choice,
    and the trap is the interaction rather than the start."""
    assert ofat((-1, -1))["found_optimum"] is False


def test_the_optimum_really_is_where_the_truth_says():
    t = truth_table()
    assert min(t, key=t.get) == OPTIMUM
    assert len(t) == 4
    assert all(t[c] == pytest.approx(response(*c), rel=1e-15) for c in CORNERS)


# ------------- claim 2: the interaction is unidentifiable, not just noisy
def test_ofat_never_visits_the_fourth_corner():
    assert OFAT_SEES_INTERACTION is False
    assert len(set(OFAT["visited"])) == 3


def test_the_interaction_is_larger_than_a_main_effect():
    """The condition under which one-at-a-time is not merely slower."""
    assert abs(EFFECTS["AB"]) > abs(EFFECTS["B"])


def test_the_factorial_recovers_every_effect_from_the_truth():
    """Effects are differences of averages, so on noiseless data they are exact."""
    assert EFFECTS["A"] == pytest.approx(-4.0, rel=1e-12)
    assert EFFECTS["B"] == pytest.approx(-2.0, rel=1e-12)
    assert EFFECTS["AB"] == pytest.approx(6.0, rel=1e-12)


def test_effects_are_recovered_from_noisy_runs_too():
    for key in ("A", "B", "AB"):
        assert EFFECTS_OBSERVED[key] == pytest.approx(EFFECTS[key], abs=4 * NOISE_SD)


def test_effect_contrasts_use_every_run():
    """Hidden replication: swap any single response and all three effects move."""
    y = dict(TRUTH)
    base = factorial_effects(y)
    y[CORNERS[0]] += 1.0
    moved = factorial_effects(y)
    for key in ("A", "B", "AB"):
        assert moved[key] != base[key], key


# --------------------- claim 3: the same budget, spent better
def test_the_factorial_estimate_is_more_precise_on_the_same_runs():
    assert PRECISION["ratio"] > 1.2


def test_the_precision_gain_is_the_root_two_theory_predicts():
    """Half the runs behind each one-at-a-time comparison, so √2."""
    assert PRECISION["ratio"] == pytest.approx(math.sqrt(2.0), rel=0.05)


def test_the_factorial_estimate_is_unbiased():
    assert PRECISION["factorial_bias"] == pytest.approx(0.0, abs=0.01)


# ------------------- claim 4: screening, and the price as a table
def test_the_fraction_is_the_size_it_claims():
    assert SCREEN_RUNS == 8
    assert FULL_RUNS == 128
    assert full_factorial_runs(3) == 8


def test_the_design_is_balanced_in_every_column():
    runs = screening_design()
    for letter in SCREEN_FACTORS:
        col = [r[letter] for r in runs]
        assert sum(col) == 0, letter
        assert set(col) == {-1, 1}, letter


def test_the_generators_hold_in_every_run():
    for r in screening_design():
        for letter, word in GENERATORS.items():
            prod = 1
            for ch in word:
                prod *= r[ch]
            assert r[letter] == prod, (letter, word, r)


def test_every_main_effect_is_aliased_and_the_table_says_with_what():
    """Resolution III: each main effect confounded with two-factor interactions."""
    assert set(ALIASES) == set(SCREEN_FACTORS)
    for letter, partners in ALIASES.items():
        assert partners, letter
        assert all(len(p) == 2 and letter not in p for p in partners), (letter, partners)


def test_the_alias_table_is_symmetric():
    """If A is aliased with BD then B is aliased with AD — same relation."""
    a = alias_pairs()
    assert "BD" in a["A"] and "AD" in a["B"]
    assert "AB" in a["D"]


# ------------------- claim 5: curvature needs centre points
def test_a_two_level_design_cannot_see_curvature_by_itself():
    """The bend is identical at every corner, so no corner contrast can see it.

    This is sharper than "the bend is zero at the corners" — it is not zero, it
    is constant, which is exactly why it is inseparable from the intercept in a
    two-level design. The decisive check is that the estimated effects come out
    unchanged.
    """
    shifts = [response_curved(*c) - response(*c) for c in CORNERS]
    assert all(s == pytest.approx(shifts[0], rel=1e-12) for s in shifts)
    assert shifts[0] == pytest.approx(2 * CURVATURE, rel=1e-12)

    flat = factorial_effects({c: response(*c) for c in CORNERS})
    bent = factorial_effects({c: response_curved(*c) for c in CORNERS})
    for key in ("A", "B", "AB"):
        assert bent[key] == pytest.approx(flat[key], rel=1e-12), key
    assert CURVATURE != 0.0


def test_centre_points_detect_the_curvature():
    assert CURVED["p"] < 0.05
    assert abs(CURVED["gap"]) > 1.0


def test_and_do_not_cry_curvature_on_a_flat_surface():
    assert FLAT["p"] > 0.20
    assert abs(FLAT["gap"]) < abs(CURVED["gap"]) / 5


def test_the_centre_is_the_only_place_the_bend_shows():
    """Zero at the centre, 2·CURVATURE at every corner — hence the gap."""
    assert response_curved(0.0, 0.0) == pytest.approx(response(0.0, 0.0), rel=1e-12)
    assert CURVED["gap"] == pytest.approx(2 * CURVATURE, abs=0.6)


def test_a_tie_for_best_is_not_a_failure():
    """Found by dragging the lab onto a tie.

    At βAB = +1 with these main effects two corners tie for best. The procedure
    lands on one of them, so it has succeeded — but comparing *coordinates*
    rather than values reported a miss with a shortfall of zero, which is a
    contradiction the status readout showed to the reader.
    """
    import spclab.experiments as ex
    saved = ex.BAB
    try:
        ex.BAB = 1.0
        o = ex.ofat()
        assert o["shortfall"] == pytest.approx(0.0, abs=1e-12)
        assert o["found_optimum"] is True, "a tie for best must count as found"
    finally:
        ex.BAB = saved


def test_the_headline_case_still_fails_after_that_change():
    """And the level's own numbers are untouched by it."""
    assert OFAT["found_optimum"] is False
    assert OFAT["shortfall"] == pytest.approx(2.0, rel=1e-12)
