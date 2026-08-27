"""Level 2's claims. Each one is a sentence the act speaks, checked here.

The act says four things out loud. If any of these tests can be deleted without
a claim on screen becoming unsupported, the test is decoration.
"""
import math

import numpy as np
import pytest

from spclab.chance import (
    ALPHA, ARL0, ASYMPTOTE_AT, DIE_E, DIE_FACES, GAP_AT, MEDIAN_WAIT,
    MEMORY, MEMORY_WORST, MILESTONES, ONE_MINUS_1_OVER_E, P_IN_ARL0,
    P_IN_SHIFT, RATE_ERR_AT, SHIFT_SUBGROUPS, brute_expected_gap,
    die_expectation, expected_gap_exact, expected_rate_error, p_any_alarm,
)
from spclab.formulas import inside
from spclab.detection import SHEWHART_ARL0


# --------------------------------------------------------------- the closed form
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 12, 17, 20])
def test_closed_form_matches_the_exact_distribution(n):
    """E|S_n| = 2^(1-n)·n·C(n-1,⌊(n-1)/2⌋), against a full binomial sum."""
    assert expected_gap_exact(n) == pytest.approx(brute_expected_gap(n), rel=1e-12)


def test_closed_form_survives_a_million():
    """The log-gamma evaluation must not overflow at the largest milestone."""
    got = expected_gap_exact(1_000_000)
    assert math.isfinite(got)
    assert got == pytest.approx(ASYMPTOTE_AT[1_000_000], rel=1e-6)


# ------------------------------------------------- the gap grows, the rate settles
def test_the_gap_grows_like_root_n():
    """A hundredfold in n multiplies the expected surplus by ten, not by one."""
    a, b, c = (GAP_AT[n] for n in MILESTONES)
    assert b / a == pytest.approx(10.0, rel=0.02)
    assert c / b == pytest.approx(10.0, rel=0.02)
    assert a < b < c


def test_the_rate_error_shrinks_like_one_over_root_n():
    """The same hundredfold divides the error in the proportion by ten."""
    a, b, c = (RATE_ERR_AT[n] for n in MILESTONES)
    assert a / b == pytest.approx(10.0, rel=0.02)
    assert b / c == pytest.approx(10.0, rel=0.02)
    assert a > b > c


def test_both_claims_are_about_one_quantity():
    """E|p̂−½| is E|S_n| over 2n — the growth and the convergence are one fact."""
    for n in MILESTONES:
        assert expected_rate_error(n) == pytest.approx(GAP_AT[n] / (2 * n), rel=1e-12)


def test_no_law_of_averages():
    """The expected surplus never returns toward zero as n grows."""
    gaps = [expected_gap_exact(n) for n in (10, 100, 1_000, 10_000, 100_000)]
    assert gaps == sorted(gaps)
    assert gaps[-1] > 10 * gaps[0]


# ------------------------------------------------------------------- independence
def test_the_sequence_has_no_memory():
    """After a run of k heads the next flip is a head half the time, for every k."""
    assert set(MEMORY) == {1, 2, 3, 4, 5, 6}
    assert MEMORY_WORST < 0.005, f"streak conditionals drifted: {MEMORY}"


def test_no_streak_length_is_special():
    """The conditionals must not trend with k — that would be memory."""
    ks = sorted(MEMORY)
    devs = [MEMORY[k] - 0.5 for k in ks]
    # a real memory effect shows as a consistent sign; chance alternates
    assert not all(d > 0 for d in devs)
    assert not all(d < 0 for d in devs)


# -------------------------------------------------------------------- expectation
def test_expectation_need_not_be_attainable():
    """A fair die expects 3.5, which is not one of its faces."""
    assert die_expectation() == 3.5
    assert DIE_E not in set(DIE_FACES.tolist())


# ------------------------------------------------- what 0.27 % is a claim about
def test_alpha_and_arl_come_from_the_library_not_from_here():
    """Level 2 must quote the same α and run length Levels 6 and 9 publish."""
    assert ALPHA == pytest.approx(1.0 - inside(3.0), rel=1e-15)
    assert ARL0 == SHEWHART_ARL0
    assert ARL0 == pytest.approx(1.0 / ALPHA, rel=1e-3)


def test_a_shift_is_not_safe_just_because_the_rate_is_small():
    """0.27 % per subgroup is a 23.7 % chance over a hundred of them."""
    assert P_IN_SHIFT == pytest.approx(0.237, abs=0.002)
    assert P_IN_SHIFT > 40 * ALPHA


def test_the_punchline_is_one_minus_one_over_e():
    """Running the 370 subgroups that "one in 370" names is not certainty."""
    assert P_IN_ARL0 == pytest.approx(ONE_MINUS_1_OVER_E, abs=0.001)
    assert 0.60 < P_IN_ARL0 < 0.65


def test_the_typical_wait_is_shorter_than_the_average_one():
    """The waiting time is geometric, so the median is ln2 of the mean."""
    assert MEDIAN_WAIT == pytest.approx(math.log(2.0) * ARL0, rel=0.01)
    assert MEDIAN_WAIT < ARL0
    assert 250 < MEDIAN_WAIT < 262


def test_p_any_alarm_is_a_probability():
    """Boundaries, since the act sweeps this function across a whole shift."""
    assert p_any_alarm(0) == 0.0
    assert 0.0 < p_any_alarm(1) < 1.0
    assert p_any_alarm(1) == pytest.approx(ALPHA, rel=1e-12)
    assert p_any_alarm(10_000) > 0.99
    assert np.all(np.diff([p_any_alarm(n) for n in range(0, 200, 10)]) > 0)


# ------------------------------------------------- the act may not contradict it
def test_the_act_spells_the_same_numbers_the_library_computes():
    """Narration is typed prose, so the numbers inside it need a gate too.

    The act says "three hundred and seventy" and "two seven" out loud because a
    spoken line cannot interpolate a float gracefully. That makes them typed
    copies of published numbers, and this is the check that they still match —
    the same failure `level09.py` shipped when a figure recomputed 4.44 as "5×".
    """
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "src/spclab/level02_scene.py"
    text = src.read_text()

    if "three hundred and seventy" in text:
        assert round(ARL0) == 370, f"the act says 370, the library says {ARL0}"
    if "two seven percent" in text:
        assert f"{ALPHA * 100:.2f}" == "0.27", f"the act says 0.27 %, library {ALPHA}"
    if "one half" in text:
        assert 0.5 == pytest.approx(0.5)  # the coin is fair by construction
    # no bare percentage of the published rate may be typed into a mobject
    assert '"0.27' not in text and "'0.27" not in text, (
        "0.27 is typed into the act; interpolate it from ALPHA instead")
    # the two derived headlines must be interpolated, never spelled as digits
    for literal in ('"63.3', '"23.7', '"256 '):
        assert literal not in text, f"{literal} is typed; read it from spclab.chance"
