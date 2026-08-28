"""Level 10's claims. Attribute charts, where the mean fixes the spread.

Check 9 of the arc contract: pytest covers any new library function, and the
lab computes its numbers from these same formulas. `test_lab_matches_python`
in the page sweep is the other half of that promise.
"""
import math

import numpy as np
import pytest

from spclab.counting import (
    C_AT, C_BAR, DISPERSION_BATCHED, DISPERSION_CLEAN, K, LIMITS_BY_N, MISCLASS,
    NP_AT_CONST, NP_THRESHOLD, N_CONST, N_FOR_LCL, N_VARY, P_AT_CONST, P_BAR,
    TAIL, UNIT_DEFECT, UNIT_ITEM, binomial_sigma, binomial_tail, c_limits,
    chart_for, dispersion_ratio, n_for_positive_lcl, normal_tail_approx,
    np_limits, p_limits, poisson_sigma, simulate_batch_effect,
    simulate_binomial, u_limits,
)


# ------------------------------- claim 1: the mean fixes the spread
def test_the_binomial_sigma_is_a_function_of_the_mean():
    """Nothing is estimated separately, which is the whole difference."""
    assert binomial_sigma(N_CONST, P_BAR) == pytest.approx(
        math.sqrt(P_BAR * (1 - P_BAR) / N_CONST), rel=1e-15)
    # halving n widens the proportion's spread by root two
    assert binomial_sigma(100, P_BAR) / binomial_sigma(200, P_BAR) == pytest.approx(
        math.sqrt(2.0), rel=1e-12)


def test_the_poisson_variance_is_its_mean():
    assert poisson_sigma(C_BAR) == pytest.approx(math.sqrt(C_BAR), rel=1e-15)
    assert poisson_sigma(C_BAR) ** 2 == pytest.approx(C_BAR, rel=1e-12)


def test_simulated_spread_matches_the_formula():
    """The claim, checked against data rather than against itself."""
    counts = simulate_binomial(subgroups=4000)
    props = counts / N_CONST
    assert props.std(ddof=1) == pytest.approx(binomial_sigma(N_CONST, P_BAR), rel=0.06)
    rng = np.random.default_rng(1)
    pois = rng.poisson(C_BAR, size=20_000)
    assert pois.std(ddof=1) == pytest.approx(poisson_sigma(C_BAR), rel=0.04)
    assert pois.mean() == pytest.approx(pois.var(ddof=1), rel=0.05)


def test_np_is_the_p_chart_in_counts():
    """Same chart, different units — so the limits must scale by n exactly."""
    assert NP_AT_CONST["ucl"] == pytest.approx(N_CONST * P_AT_CONST["ucl"], rel=1e-12)
    assert NP_AT_CONST["cl"] == pytest.approx(N_CONST * P_BAR, rel=1e-12)


def test_u_limits_reduce_to_c_limits_at_one_unit():
    """A u-chart inspecting exactly one unit is a c-chart."""
    u = u_limits(C_BAR, 1.0)
    c = c_limits(C_BAR)
    for key in ("cl", "ucl", "lcl_raw"):
        assert u[key] == pytest.approx(c[key], rel=1e-12)


# --------------------- claim 2: a disagreement is information
def test_a_true_binomial_process_has_a_dispersion_ratio_of_one():
    assert DISPERSION_CLEAN == pytest.approx(1.0, abs=0.15)


def test_a_drifting_rate_shows_up_as_overdispersion():
    """The mean is untouched; only the scatter gives it away."""
    assert DISPERSION_BATCHED > 1.35
    assert DISPERSION_BATCHED > DISPERSION_CLEAN
    clean, batched = simulate_binomial(), simulate_batch_effect()
    assert clean.mean() / N_CONST == pytest.approx(P_BAR, abs=0.006)
    assert batched.mean() / N_CONST == pytest.approx(P_BAR, abs=0.006)


def test_dispersion_ratio_is_scale_free():
    """A ratio, so doubling the subgroup count must not move it systematically."""
    a = dispersion_ratio(simulate_binomial(subgroups=2000, seed=5), N_CONST)
    b = dispersion_ratio(simulate_binomial(subgroups=4000, seed=6), N_CONST)
    assert a == pytest.approx(b, abs=0.12)


# ------------------------------ claim 3: two questions, four charts
@pytest.mark.parametrize("unit,const,want", [
    (UNIT_ITEM, True, "np"), (UNIT_ITEM, False, "p"),
    (UNIT_DEFECT, True, "c"), (UNIT_DEFECT, False, "u"),
])
def test_chart_selection_is_two_binary_questions(unit, const, want):
    assert chart_for(unit, const) == want


def test_an_unknown_unit_is_refused_rather_than_guessed():
    with pytest.raises(ValueError):
        chart_for("measurements", True)


# ------------------- claim 4: varying n, and the cost of ignoring it
def test_limits_breathe_with_the_subgroup_size():
    """A bigger subgroup gives a tighter proportion, monotonically."""
    ucls = [LIMITS_BY_N[n]["ucl"] for n in sorted(N_VARY)]
    assert ucls == sorted(ucls, reverse=True)


def test_average_n_limits_disagree_at_a_computable_rate():
    assert MISCLASS["disagree"] > 0.002
    assert MISCLASS["false_signal"] > MISCLASS["missed"]


def test_pretending_n_is_constant_costs_more_false_alarms_than_the_design():
    """The design is 0.27 %; the average-n shortcut spends noticeably more."""
    design = 2 * (1 - 0.5 * (1 + math.erf(K / math.sqrt(2))))
    assert MISCLASS["false_signal"] > design


# ---------------- claim 5: the lower limit, and where it falls off
def test_the_lower_limit_is_clamped_in_the_worked_example():
    """n = 200 at p̄ = 0.04 cannot signal an improvement, and says so."""
    assert P_AT_CONST["clamped"] is True
    assert P_AT_CONST["lcl_raw"] < 0.0
    assert P_AT_CONST["lcl"] == 0.0


def test_the_threshold_for_a_positive_lower_limit_is_exact():
    """n > k²(1−p̄)/p̄, checked by evaluating the limit either side of it."""
    assert p_limits(N_FOR_LCL, P_BAR)["lcl_raw"] > 0.0
    assert p_limits(N_FOR_LCL - 1, P_BAR)["lcl_raw"] <= 0.0
    assert N_FOR_LCL == math.floor(K * K * (1 - P_BAR) / P_BAR) + 1


def test_the_count_form_of_the_threshold_beats_the_rule_of_thumb():
    """n·p̄ must exceed k²(1−p̄) ≈ 8.6, not the folklore 5."""
    assert NP_THRESHOLD == pytest.approx(K * K * (1 - P_BAR), rel=1e-12)
    assert NP_THRESHOLD > 5.0
    # and at n·p̄ = 5 the limit really is still negative
    n_at_five = int(round(5.0 / P_BAR))
    assert p_limits(n_at_five, P_BAR)["lcl_raw"] < 0.0


@pytest.mark.parametrize("p", [0.002, 0.01, 0.04, 0.2, 0.5])
def test_the_threshold_holds_across_rates(p):
    n = n_for_positive_lcl(p)
    assert p_limits(n, p)["lcl_raw"] > 0.0
    assert p_limits(n - 1, p)["lcl_raw"] <= 0.0


# ------------- annex: capability when the distribution is not normal
def test_the_normal_approximation_understates_a_count_tail():
    """And it flatters the process, which is the direction that matters."""
    assert TAIL["approx_understates"] is True
    assert TAIL["ratio"] > 2.0


def test_the_exact_tail_is_a_probability():
    assert binomial_tail(N_CONST, P_BAR, 0) == 1.0
    assert binomial_tail(N_CONST, P_BAR, N_CONST + 1) == 0.0
    vals = [binomial_tail(N_CONST, P_BAR, x) for x in (4, 8, 12, 16, 20)]
    assert vals == sorted(vals, reverse=True)


def test_the_approximation_improves_as_the_count_grows():
    """It is not useless — it is wrong where attribute data usually lives."""
    small = tail_ratio(200, 0.04, 16)
    large = tail_ratio(20_000, 0.4, 8_240)
    assert abs(math.log(large)) < abs(math.log(small))


def tail_ratio(n: int, p: float, at_least: int) -> float:
    return binomial_tail(n, p, at_least) / normal_tail_approx(n, p, at_least)


def test_the_boundary_itself_is_one_sided():
    """At n exactly k²(1−p̄)/p̄ the limit is zero, and zero cannot be crossed.

    A proportion is never negative, so a lower limit sitting at zero can never
    be violated: that chart is still one-sided. The lab's status readout is the
    teaching device for this section, and it read TWO-SIDED at the boundary
    until the predicate was widened from `< 0` to `<= 0`.
    """
    edge = N_FOR_LCL - 1
    assert p_limits(edge, P_BAR)["lcl_raw"] == 0.0
    assert p_limits(edge, P_BAR)["clamped"] is True
    assert p_limits(N_FOR_LCL, P_BAR)["lcl_raw"] > 0.0
    assert p_limits(N_FOR_LCL, P_BAR)["clamped"] is False
