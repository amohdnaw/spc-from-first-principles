"""Level 5's claims, plus the distribution this repo had to write itself.

`t_quantile` is hand-rolled (scipy is not a dependency and one distribution does
not justify adding it), so it is checked against the published table before any
claim resting on it is trusted. A wrong quantile would make every coverage
number in this level agree with a wrong theory.
"""
import math

import pytest

from spclab.estimation import (
    CONF, COVER_T, COVER_Z, D2_MEAN, D2_PUBLISHED, D2_SE,
    D2_SUBGROUPS_FOR_3DP, HALVE_FROM, HALVE_N_T, HALVE_N_Z, SE_EXACT,
    SE_OBSERVED, SIZES, SUBGROUP_N, TRUE_SIGMA, T_AT, WIDTH_AT, WIDTH_AT_Z,
    Z_95, interval_width, standard_error_exact, t_cdf, t_quantile,
)
from spclab.formulas import control_limit_constants


# ------------------------------------------------- the distribution itself
# Two-sided 95 % critical values, from the standard table.
TABLE = {1: 12.706, 2: 4.303, 4: 2.776, 9: 2.262, 14: 2.145,
         24: 2.064, 29: 2.045, 99: 1.984}


@pytest.mark.parametrize("df,expected", sorted(TABLE.items()))
def test_t_quantile_matches_the_published_table(df, expected):
    """The hand-rolled quantile must agree with the table it replaces."""
    assert t_quantile(df) == pytest.approx(expected, abs=0.001)


def test_t_approaches_the_normal_quantile():
    """As df grows, t must converge on 1.96 — the sanity check on the tail."""
    assert t_quantile(10_000) == pytest.approx(Z_95, abs=0.001)
    assert t_quantile(4) > t_quantile(99) > t_quantile(10_000) >= Z_95 - 1e-6


def test_t_cdf_is_a_distribution():
    assert t_cdf(0.0, 5) == pytest.approx(0.5, abs=1e-12)
    for df in (1, 4, 30):
        assert t_cdf(-2.0, df) == pytest.approx(1.0 - t_cdf(2.0, df), abs=1e-9)
        assert 0.0 < t_cdf(-8.0, df) < t_cdf(0.0, df) < t_cdf(8.0, df) < 1.0


# ------------------------------------------- claim 1: the standard error
@pytest.mark.parametrize("n", SIZES)
def test_the_standard_error_is_the_spread_of_the_estimate(n):
    """The sample means' own spread must land on σ/√n."""
    assert SE_OBSERVED[n] == pytest.approx(SE_EXACT[n], rel=0.02)


def test_the_standard_error_is_not_the_spread_of_the_parts():
    """The distinction the level exists to make: σ/√n is smaller than σ."""
    for n in SIZES:
        if n > 1:
            assert SE_EXACT[n] < TRUE_SIGMA
    assert standard_error_exact(100) == pytest.approx(TRUE_SIGMA / 10.0, rel=1e-12)


# ------------------------------------- claims 2 and 3: coverage, and why t
def test_a_t_interval_delivers_the_coverage_it_advertises():
    """Counted, not asserted: every n within one point of 95 %."""
    for n in SIZES:
        assert COVER_T[n] == pytest.approx(CONF, abs=0.01), (n, COVER_T[n])


def test_a_normal_quantile_under_covers_at_small_n():
    """The reason t exists, as a measured gap rather than a table's authority."""
    assert COVER_Z[2] < 0.75
    assert COVER_Z[5] < 0.90
    assert COVER_Z[10] < 0.93
    # and the shortfall must shrink as n grows, or the explanation is wrong
    shortfalls = [CONF - COVER_Z[n] for n in SIZES]
    assert shortfalls == sorted(shortfalls, reverse=True)
    assert COVER_Z[100] == pytest.approx(CONF, abs=0.005)


def test_t_beats_z_at_every_small_n():
    for n in SIZES:
        if n < 100:
            assert COVER_T[n] > COVER_Z[n]


# --------------------------------- claim 4: the price of precision
def test_the_interval_narrows_as_root_n_when_the_quantile_is_fixed():
    """With σ known the width is exactly proportional to 1/√n."""
    for a, b in zip(SIZES, SIZES[1:]):
        assert WIDTH_AT_Z[a] / WIDTH_AT_Z[b] == pytest.approx(
            math.sqrt(b / a), rel=1e-12)


def test_halving_the_width_is_a_square_law_with_sigma_known():
    assert HALVE_N_Z == 4 * HALVE_FROM


def test_t_makes_precision_cheaper_than_the_square_law_at_small_n():
    """Because the quantile shrinks with df, not only the √n term."""
    assert HALVE_N_T < HALVE_N_Z
    assert HALVE_N_T > HALVE_FROM
    # the effect must vanish for large samples, where t is already ~z
    big = 4000
    assert interval_width(big) == pytest.approx(
        interval_width(big, use_t=False), rel=0.002)


def test_every_width_shrinks_with_n():
    widths = [WIDTH_AT[n] for n in SIZES]
    assert widths == sorted(widths, reverse=True)


# ------------------- claim 4b: the curriculum's own constants are estimates
def test_d2_comes_from_the_library_not_from_here():
    assert D2_PUBLISHED == control_limit_constants(SUBGROUP_N)["d2"]


def test_the_simulated_d2_agrees_with_the_published_one_within_its_own_error():
    """The replicates and the library must not disagree by more than noise."""
    se_of_mean = D2_SE / math.sqrt(60)
    assert abs(D2_MEAN - D2_PUBLISHED) < 4.0 * se_of_mean


def test_d2_has_a_standard_error_at_all():
    """A four-figure table hides this; the level's point is that it exists."""
    assert D2_SE > 0.005
    assert D2_MEAN == pytest.approx(2.326, abs=0.01)


def test_pinning_the_third_decimal_of_d2_is_expensive():
    """Simulation earns three decimals only at a subgroup count nobody runs."""
    assert D2_SUBGROUPS_FOR_3DP > 1_000_000
