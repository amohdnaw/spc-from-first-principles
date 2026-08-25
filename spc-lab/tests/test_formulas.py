import numpy as np
import pytest

from spclab import (
    control_limit_constants,
    xbar_r_limits,
    capability_indices,
    defects_per_million,
    ppm_from_cpk,
    ewma_limits,
    western_electric_violations,
)


def test_constants_match_aiag_table():
    """AIAG SPC Table B, n=5: A2=0.577, D3=0, D4=2.114, d2=2.326."""
    c = control_limit_constants(5)
    assert abs(c["A2"] - 0.577) < 0.005
    assert c["D3"] == 0.0
    assert abs(c["D4"] - 2.114) < 0.01
    assert abs(c["d2"] - 2.326) < 0.01


def test_constants_n2():
    """n=2: A2=1.880, D4=3.267."""
    c = control_limit_constants(2)
    assert abs(c["A2"] - 1.880) < 0.005
    assert abs(c["D4"] - 3.267) < 0.01


def test_xbar_r_limits_in_control_data():
    rng = np.random.default_rng(0)
    data = rng.normal(50, 0.1, size=(200, 5))
    lim = xbar_r_limits(data)
    assert lim["ucl_xbar"] > lim["xbarbar"] > lim["lcl_xbar"]
    assert lim["ucl_r"] > lim["rbar"] > 0


def test_capability_perfect_center():
    rng = np.random.default_rng(1)
    v = rng.normal(50, 0.05, size=1000)
    cap = capability_indices(v, lsl=49.7, usl=50.3)
    # tolerance width 0.6, 6σ = 0.30 → Cp ≈ 2.0
    assert cap["Cp"] == pytest.approx(2.0, abs=0.15)
    assert cap["Cpk"] == pytest.approx(cap["Cp"], rel=0.1)


def test_ppm_shift_convention():
    # Six Sigma: spec at ±6σ, mean drifts 1.5σ → worst tail at 4.5σ ≈ 3.4 DPMO
    ppm = defects_per_million(mu=50, sigma=1.0, lsl=44.0, usl=56.0, shift=1.5)
    assert 3 <= ppm <= 4
    # same specs, no assumed drift → ~2 per billion → rounds to 0
    ppm0 = defects_per_million(mu=50, sigma=1.0, lsl=44.0, usl=56.0, shift=0.0)
    assert ppm0 == 0


def test_ewma_asymptote():
    up, lo = ewma_limits(0.2, k=200)
    expected = 3 * np.sqrt(0.2 / 1.8)
    assert up[-1] == pytest.approx(expected, rel=1e-6)
    assert up[0] < up[10] < up[-1]  # limits start tight... wait, wide->tight


def test_we_rules_detect_shift():
    rng = np.random.default_rng(2)
    stable = list(rng.normal(0, 1, 40))
    shifted = stable + [x + 1.5 for x in rng.normal(0, 1, 15)]
    v = western_electric_violations(np.array(shifted), cl=0, sigma=1)
    assert any("Rule 4" in desc for _, desc in v)  # sustained shift → runs rule
    assert len(v) > len(western_electric_violations(np.array(stable), 0, 1))


def test_ppm_from_cpk_matches_normal_tail():
    """Cpk -> ppm is an integral, not a lookup. One tail by default."""
    # Cpk 1.00 -> z=3.00 -> 1350 ppm near tail; 1.33 -> z=3.99 -> 33 ppm
    assert ppm_from_cpk(1.00) == pytest.approx(1350, rel=0.01)
    assert ppm_from_cpk(1.33) == pytest.approx(33.0, rel=0.02)
    assert ppm_from_cpk(0.80) == pytest.approx(8198, rel=0.01)
    # two-sided is exactly double, never something in between
    assert ppm_from_cpk(0.80, two_sided=True) == pytest.approx(2 * ppm_from_cpk(0.80))
    # the Six Sigma drift convention: Cpk 2.0 with 1.5 sigma shift -> 3.4 ppm
    assert ppm_from_cpk(2.0, shift=1.5) == pytest.approx(3.4, rel=0.05)


def test_ppm_table_uses_one_convention():
    """Regression: the Level 3 promise table once mixed one- and two-sided rows.

    Every published row must sit on the same curve, so the ratio between a row
    and its own one-sided value is 1.0 for all of them or the table lies.
    """
    published = {0.80: 8198.0, 1.00: 1350.0, 1.33: 33.0, 1.67: 0.272}
    for cpk, claim in published.items():
        assert ppm_from_cpk(cpk) == pytest.approx(claim, rel=0.02), (
            f"Cpk {cpk} row is off the one-sided curve"
        )
