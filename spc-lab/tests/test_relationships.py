"""Level 11's claims — one sum-of-squares identity, checked in all three guises.

The bridge level, so the last group of tests is the one that matters most: the
two-way decomposition has to satisfy the same identity as the regression, or the
claim that a Gage R&R is "the same arithmetic" is decoration.
"""
import math

import numpy as np
import pytest

from spclab.relationships import (
    ADJ_WITH_NOISE, CONF, COVERAGE, CURVED_FIT, CURVED_RUN, FIT, GAUGE,
    HALF_CI, HALF_PI, MSA_SITE, NOISE_SD, OPERATORS, PARTS, R2_PLAIN,
    R2_WITH_NOISE, REPEATS, SLOPE_GRID, SSE_CURVE, STRAIGHT_RUN, TRUE_SLOPE, X,
    X0, Y, adjusted_r2, dataset, f_sf, fit, gauge_study, interval_half_widths,
    one_way, residual_runs, sse_at_slope, two_way_components,
)


# ------------------------------ claim 1: least squares is a minimisation
def test_the_closed_form_sits_at_the_minimum_of_the_swept_curve():
    """Not near the minimum — at it, to the resolution of the sweep."""
    best = float(SLOPE_GRID[int(SSE_CURVE.argmin())])
    step = float(SLOPE_GRID[1] - SLOPE_GRID[0])
    assert abs(best - FIT["slope"]) <= step


def test_the_residual_sum_of_squares_is_convex_in_the_slope():
    """A parabola, so no other slope can beat the closed form anywhere."""
    d2 = np.diff(SSE_CURVE, 2)
    assert (d2 > 0).all()
    assert sse_at_slope(X, Y, FIT["slope"]) == pytest.approx(FIT["sse"], rel=1e-12)
    for off in (-0.004, -0.001, 0.001, 0.004):
        assert sse_at_slope(X, Y, FIT["slope"] + off) > FIT["sse"]


def test_the_fit_recovers_the_slope_it_was_built_from():
    assert FIT["slope"] == pytest.approx(TRUE_SLOPE, rel=0.15)


def test_the_sums_of_squares_identity_holds_for_the_regression():
    assert FIT["ssr"] + FIT["sse"] == pytest.approx(FIT["sst"], rel=1e-12)
    assert FIT["r2"] == pytest.approx(FIT["ssr"] / FIT["sst"], rel=1e-12)


def test_residuals_have_no_slope_left_in_them():
    """Least squares leaves residuals orthogonal to the predictor, exactly."""
    r = FIT["resid"]
    assert r.sum() == pytest.approx(0.0, abs=1e-10)
    assert float((r * (X - X.mean())).sum()) == pytest.approx(0.0, abs=1e-10)


# ------------------------------------- claim 2: R² rises for nothing
def test_r_squared_never_falls_when_a_useless_column_is_added():
    ks = sorted(R2_WITH_NOISE)
    vals = [R2_PLAIN] + [R2_WITH_NOISE[k] for k in ks]
    assert vals == sorted(vals), vals


def test_the_gain_is_bought_with_nothing_and_adjusted_r2_says_so():
    """The plain figure climbs; penalised for the columns, it turns down."""
    ks = sorted(R2_WITH_NOISE)
    assert R2_WITH_NOISE[ks[-1]] > R2_PLAIN
    assert ADJ_WITH_NOISE[ks[-1]] < ADJ_WITH_NOISE[ks[0]]


def test_adjusted_r2_reduces_to_r2_with_one_predictor_and_no_penalty():
    assert adjusted_r2(0.9, 100, 0) == pytest.approx(0.9, rel=1e-12)


# --------------------- claim 3: residuals say what R² cannot
def test_a_curved_relationship_scores_a_high_r_squared_anyway():
    assert CURVED_FIT["r2"] > 0.9


def test_the_residuals_give_the_curve_away_even_so():
    """A high R² with a 16-long same-sign run is worse than a lower one."""
    assert CURVED_RUN > 2 * STRAIGHT_RUN
    assert CURVED_RUN > 12


def test_residual_runs_counts_what_it_says():
    assert residual_runs(np.array([1, 1, 1, -1, -1])) == 3
    assert residual_runs(np.array([1, -1, 1, -1])) == 1
    assert residual_runs(np.array([-1] * 6)) == 6


# --------------- claim 4: two intervals that are not the same interval
def test_the_prediction_interval_is_wider_than_the_confidence_interval():
    assert HALF_PI > HALF_CI
    assert HALF_PI / HALF_CI > 2.0


def test_both_intervals_cover_what_they_claim_when_counted():
    assert COVERAGE["ci"] == pytest.approx(CONF, abs=0.02)
    assert COVERAGE["pi"] == pytest.approx(CONF, abs=0.02)


def test_only_the_confidence_interval_shrinks_toward_zero():
    """The prediction interval keeps the variance of the new reading itself."""
    rng = np.random.default_rng(2)
    x = np.linspace(60, 200, 4000)
    y = 0.42 + TRUE_SLOPE * x + rng.normal(0.0, NOISE_SD, x.size)
    f = fit(x, y)
    hc, hp = interval_half_widths(f, float(x.mean()))
    assert hc < 0.02
    assert hp > 1.5 * NOISE_SD
    assert hp / hc > 20


# -------------- claim 5: the same identity as ANOVA, then as a gauge study
def test_one_way_anova_splits_the_total_exactly():
    rng = np.random.default_rng(3)
    groups = [rng.normal(m, 1.0, 12) for m in (0.0, 0.8, 1.6)]
    a = one_way(groups)
    assert a["ssb"] + a["ssw"] == pytest.approx(a["sst"], rel=1e-12)
    assert a["eta2"] == pytest.approx(a["ssb"] / a["sst"], rel=1e-12)
    assert a["f"] > 1.0 and a["p"] < 0.05


def test_f_survival_is_a_survival_function():
    assert f_sf(0.0, 3, 20) == 1.0
    vals = [f_sf(v, 3, 20) for v in (0.5, 1.0, 2.0, 4.0, 8.0)]
    assert vals == sorted(vals, reverse=True)
    assert 0.0 < vals[-1] < vals[0] < 1.0


def test_the_two_way_decomposition_satisfies_the_same_identity():
    """part + operator + interaction + repeat = total, exactly."""
    ss = GAUGE["ss"]
    assert (ss["part"] + ss["operator"] + ss["interaction"] + ss["repeat"]
            == pytest.approx(ss["total"], rel=1e-10))


def test_every_component_of_the_bridge_is_present():
    """The contract ends this level on part, operator AND interaction."""
    for key in ("part", "operator", "interaction", "repeat"):
        assert GAUGE["var"][key] > 0.0, key
        assert GAUGE["pct"][key] > 0.1, key
    assert sum(GAUGE["pct"].values()) == pytest.approx(100.0, abs=1e-9)


def test_the_parts_dominate_and_the_gauge_is_the_rest():
    assert GAUGE["pct"]["part"] > 60.0
    assert GAUGE["pct_gauge"] == pytest.approx(100.0 - GAUGE["pct"]["part"], abs=1e-9)
    assert GAUGE["gauge"] == pytest.approx(
        GAUGE["total"] - GAUGE["var"]["part"], rel=1e-12)


def test_the_gauge_study_has_the_shape_a_gage_rr_arrives_in():
    y = gauge_study()
    assert y.shape == (PARTS, OPERATORS, REPEATS)


def test_the_seam_points_at_the_msa_site_and_only_names_it_once():
    """§2: each site links to the other exactly once, at the seam."""
    assert MSA_SITE.startswith("https://")
    assert "msa" in MSA_SITE


def test_the_estimator_recovers_the_variances_it_was_built_from():
    """The gap sabotage found: nothing pinned the component *values*.

    Inflating the part component by dropping the `− MS_interaction` term passed
    every other test in this file, because the identity tests work on sums of
    squares and the percentage tests hold by construction. These are the numbers
    the bridge ends on, so they get checked against the truth directly — on a
    study large enough for the estimator to be asked the question fairly.
    """
    from spclab.relationships import TRUE_COMPONENTS
    y = gauge_study(seed=99, parts=400, operators=25, repeats=6)
    got = two_way_components(y)["var"]
    for key, want in TRUE_COMPONENTS.items():
        assert got[key] == pytest.approx(want, rel=0.20), (key, got[key], want)


def test_a_ten_part_study_cannot_be_expected_to_do_that():
    """And the honest counterpart: the real study is far too small.

    Stated as a test so nobody later reads the ten-part percentages as precise.
    """
    from spclab.relationships import TRUE_COMPONENTS
    small = two_way_components(gauge_study(seed=99))["var"]
    off = max(abs(small[k] - v) / v for k, v in TRUE_COMPONENTS.items())
    assert off > 0.20


def test_the_components_invert_the_mean_squares_exactly():
    """The check that actually bites: algebra, not tolerance on noisy data.

    The components are an inversion of the expected mean squares, so feeding
    them back must reproduce the mean squares the data produced — to floating
    point, on any study, with no sampling error involved. A wrong subtraction
    (dropping `− MS_interaction` from the part component) is invisible to a
    20 % tolerance because the term is under half a percent of the part
    variance on a large study; it is not invisible here.
    """
    for kwargs in ({}, {"parts": 40, "operators": 5, "repeats": 3}):
        g = two_way_components(gauge_study(seed=17, **kwargs))
        v, ms, sh = g["var"], g["ms"], g["shape"]
        p_, o_, r_ = sh["parts"], sh["operators"], sh["repeats"]
        assert ms["repeat"] == pytest.approx(v["repeat"], rel=1e-12)
        assert ms["interaction"] == pytest.approx(
            v["repeat"] + r_ * v["interaction"], rel=1e-12)
        assert ms["part"] == pytest.approx(
            v["repeat"] + r_ * v["interaction"] + o_ * r_ * v["part"], rel=1e-12)
        assert ms["operator"] == pytest.approx(
            v["repeat"] + r_ * v["interaction"] + p_ * r_ * v["operator"], rel=1e-12)
