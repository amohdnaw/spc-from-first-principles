"""Level 1's two claims, which sound like opinions and are not."""
import numpy as np

from spclab.variation import (
    TWELVE_CLOSEST_UM,
    TWELVE_SHAFTS_MM,
    TWELVE_SPAN_UM,
    ADJUST_EVERY,
    LEAVE_IT,
    PAIR_BINS_IDENTICAL,
    PAIR_MEAN_GAP,
    PAIR_RUN_DRIFTING,
    PAIR_RUN_STABLE,
    PAIR_SD_GAP,
    TAMPER_SIGMA_RATIO,
    TAMPER_SIGMA_RATIO_EXACT,
    TAMPER_VAR_RATIO,
    TAMPER_VAR_RATIO_EXACT,
    funnel,
    histograms_identical,
    run_of_same_side,
    same_histogram_pair,
)


def test_tampering_doubles_the_variance():
    """Deming's funnel rule 2: adjusting after every part gives Var = 2σ².

    The algebra says exactly 2. If the simulation ever disagrees by more than
    sampling noise, one of the two is wrong and the page is asserting a number
    it cannot back.
    """
    assert abs(TAMPER_VAR_RATIO - TAMPER_VAR_RATIO_EXACT) < 0.02
    assert abs(TAMPER_SIGMA_RATIO - TAMPER_SIGMA_RATIO_EXACT) < 0.01
    assert abs(TAMPER_SIGMA_RATIO_EXACT - 2 ** 0.5) < 1e-12


def test_tampering_is_the_rule_not_the_luck():
    """Both rules see the same draws, so the penalty cannot be a lucky seed."""
    for seed in (1, 7, 23, 99):
        left = funnel(LEAVE_IT, n=40_000, seed=seed)
        adjusted = funnel(ADJUST_EVERY, n=40_000, seed=seed)
        ratio = adjusted.var(ddof=1) / left.var(ddof=1)
        assert 1.9 < ratio < 2.1, f"seed {seed}: ratio {ratio:.3f}"


def test_adjusted_series_is_a_difference_of_consecutive_draws():
    """The closed form behind the factor of two: outcome_i = e_i − e_{i−1}."""
    e = np.random.default_rng(4).normal(0.0, 1.0, size=50)
    got = funnel(ADJUST_EVERY, n=50, seed=4)
    expected = np.concatenate([[e[0]], e[1:] - e[:-1]])
    assert np.allclose(got, expected, atol=1e-12)


def test_histogram_throws_away_time_order():
    """The same measurements in two orders: identical summary, different process.

    Equal to machine precision rather than approximately equal, because they
    are the same multiset. This is the claim the level is built on.
    """
    assert PAIR_MEAN_GAP < 1e-12
    assert PAIR_SD_GAP < 1e-12
    assert PAIR_BINS_IDENTICAL is True


def test_only_the_order_separates_them():
    """A run statistic sees what the histogram cannot."""
    assert PAIR_RUN_STABLE < 15
    assert PAIR_RUN_DRIFTING > 100
    assert PAIR_RUN_DRIFTING > 8 * PAIR_RUN_STABLE


def test_pair_is_the_same_multiset_at_any_size():
    for n in (60, 240, 1000):
        stable, drifting = same_histogram_pair(n=n, seed=5)
        assert np.allclose(np.sort(stable), np.sort(drifting), atol=1e-12)
        assert histograms_identical(stable, drifting)
        assert run_of_same_side(drifting) > run_of_same_side(stable)


def test_the_twelve_parts_are_one_dataset():
    """Level 1 introduces the twelve parts; Level 3 puts a mean and sigma on them.

    An earlier draft had Level 1 inventing its own twelve and claiming a 26 µm
    span while Level 3 claimed 47 µm about the same "twelve parts off one
    machine". Level 3 asserts against these at import; this pins the numbers the
    pages and the narration quote.
    """
    from spclab.level03_scene import PARTS      # its own assert runs on import

    assert np.allclose(PARTS, TWELVE_SHAFTS_MM)
    assert TWELVE_SPAN_UM == 47.0
    assert TWELVE_CLOSEST_UM == 1.0
