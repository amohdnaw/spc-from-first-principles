"""LEVEL 7 — Evidence and decisions. Adding rules is arithmetic, not opinion.

Level 6 priced one decision rule: a point outside ±3σ. That bought a false-alarm
rate of 0.27 % and, as Level 2 showed, one alarm in 370 subgroups on average. What
Level 6 never mentioned is the other way to be wrong — missing a shift that is
really there — and that omission is where the Western Electric rules come from.

Four claims, none asserted:

1. **There are two ways to be wrong and both are computable.** α is the chance of
   crying wolf when nothing changed; β is the chance of staying silent when
   something did. Power is 1 − β, and it depends on how big the shift is.

2. **A single point is nearly blind to a small shift.** With limits at ±3σ and a
   shift of one σ of the plotted statistic, the power of the *next point* is about
   2 %. The chart is not broken; a one-sigma shift simply looks like ordinary
   noise to a test that only ever sees one point at a time. The reciprocal of that
   power is the average run length `detection` already publishes.

3. **The chart throws evidence away.** A point at 2.5σ carries a p-value of about
   1 %. The single-point rule calls it "in" and forgets it. The extra rules exist
   to spend the evidence in the pattern that one point cannot hold.

4. **So the trade is arithmetic.** Each rule added raises power *and* raises the
   false-alarm rate, and both sides can be computed. Turning on all four Western
   Electric rules roughly quarters the in-control run length while roughly
   tripling the sensitivity to a one-sigma shift. Whether that is a good trade
   depends on the process; the numbers do not.

The rules themselves are defined once, in `formulas.western_electric_violations`.
The vectorised `first_violation` here exists only because an average run length
needs millions of plotted points, and a test asserts the two agree exactly on
random series rather than trusting that they do.

    PYTHONPATH=src .venv/bin/python -m spclab.evidence
"""
from __future__ import annotations

import math

import numpy as np

from spclab.detection import ARL1_SHEW, SHEWHART_ARL0
from spclab.formulas import inside

# The four rules, in the order a practitioner switches them on.
RULES = (1, 2, 3, 4)
RULE_TEXT = {
    1: "one point beyond 3σ",
    2: "2 of 3 beyond 2σ, same side",
    3: "4 of 5 beyond 1σ, same side",
    4: "8 in a row on one side",
}

# The shift Level 9 also uses, in units of the plotted statistic's sigma.
SHIFT = 1.0

# Shift sizes for the power curve.
SHIFTS = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)

LIMIT = 3.0                       # ±3σ, from Level 6
# 4 000 series is enough for the two figures a page quotes (a standard error of
# about 1.5 subgroups on an ARL0 of 92) and keeps the import near fifteen
# seconds. The page generator pays this once per build, so precision past the
# quoted digits would be bought with everyone's time.
RUNS = 4_000                      # series simulated per rule set
MAX_LEN = 6_000                   # points per series
CHUNK = 2_000                     # series per batch, to bound memory


def phi(z: float) -> float:
    """Standard normal CDF, from erf. `inside` is the two-sided version."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def alpha_one_point(limit: float = LIMIT) -> float:
    """The false-alarm rate of the single-point rule: 1 − erf(k/√2)."""
    return 1.0 - inside(limit)


def power_one_point(shift: float, limit: float = LIMIT) -> float:
    """Chance the next point falls outside ±limit when the mean has moved.

    Both tails, because a chart does not know which way the process went:
        P = Φ(−limit − δ) + Φ(−limit + δ)   for a shift of δ.
    """
    return phi(-limit - shift) + phi(-limit + shift)


def beta_one_point(shift: float, limit: float = LIMIT) -> float:
    """The chance of staying silent when the mean really moved."""
    return 1.0 - power_one_point(shift, limit)


def p_value(z: float) -> float:
    """Two-sided p-value of a plotted point at `z` sigma.

    The number the in-or-out decision discards. A chart reports a verdict; this
    reports how surprised to be.
    """
    return 2.0 * (1.0 - phi(abs(z)))


# ---------------------------------------------------------------------------
# Run lengths under a set of rules
# ---------------------------------------------------------------------------
def _win(a: np.ndarray, k: int) -> np.ndarray:
    """Sliding windows of width k along the last axis."""
    return np.lib.stride_tricks.sliding_window_view(a, k, axis=-1)


def first_violation(z: np.ndarray, rules: tuple[int, ...]) -> np.ndarray:
    """Index of the first point flagged by `rules`, per row. −1 if none.

    Vectorised twin of `formulas.western_electric_violations`, kept honest by
    `test_evidence.py::test_first_violation_matches_the_canonical_rules`.
    """
    z = np.atleast_2d(z)
    n = z.shape[-1]
    hit = np.zeros(z.shape, dtype=bool)
    up, dn = z > 0, z < 0

    if 1 in rules:
        hit |= np.abs(z) > LIMIT

    if 2 in rules and n >= 3:
        for beyond, same in ((z > 2.0, up), (z < -2.0, dn)):
            cnt = _win(beyond & same, 3).sum(axis=-1)
            # the newest point must itself be one of the two
            ok = cnt >= 2
            hit[..., 2:] |= ok & beyond[..., 2:]

    if 3 in rules and n >= 5:
        for beyond, same in ((z > 1.0, up), (z < -1.0, dn)):
            cnt = _win(beyond & same, 5).sum(axis=-1)
            # the side is set by the newest point, which need not be beyond 1σ
            hit[..., 4:] |= (cnt >= 4) & same[..., 4:]

    if 4 in rules and n >= 8:
        for same in (up, dn):
            hit[..., 7:] |= _win(same, 8).all(axis=-1)

    idx = np.where(hit.any(axis=-1), hit.argmax(axis=-1), -1)
    return idx


def average_run_length(rules: tuple[int, ...], shift: float = 0.0,
                       runs: int = RUNS, max_len: int = MAX_LEN,
                       seed: int = 7) -> tuple[float, float]:
    """Mean points until the first alarm, and the fraction that never alarmed.

    Series that reach `max_len` without an alarm are censored; the second return
    value reports how many, so a run length quoted here can be trusted or not on
    the evidence rather than on faith.
    """
    rng = np.random.default_rng(seed)
    total, censored, done = 0.0, 0, 0
    while done < runs:
        m = min(CHUNK, runs - done)
        z = rng.normal(shift, 1.0, size=(m, max_len))
        idx = first_violation(z, rules)
        found = idx >= 0
        # A censored series contributes the length it survived, not nothing.
        # Averaging only over the series that alarmed drops the longest ones and
        # biases the run length downward: the one-rule chart came out at 363
        # against the 370.4 this site quotes everywhere else.
        total += float((idx[found] + 1).sum()) + float((~found).sum() * max_len)
        censored += int((~found).sum())
        done += m
    return total / runs, censored / runs


def cumulative_sets() -> list[tuple[int, ...]]:
    """(1,), (1,2), (1,2,3), (1,2,3,4) — the order rules get switched on."""
    return [tuple(RULES[:k]) for k in range(1, len(RULES) + 1)]


# ---------------------------------------------------------------------------
# Computed once; read by the act, the sheets, the page and the tests.
# ---------------------------------------------------------------------------
ALPHA_1 = alpha_one_point()
POWER_AT = {s: power_one_point(s) for s in SHIFTS}
BETA_AT = {s: beta_one_point(s) for s in SHIFTS}

# Level 9 publishes the single-point run length at a 1σ shift; this must agree.
ARL1_FROM_POWER = 1.0 / POWER_AT[SHIFT]

P_AT_2_5 = p_value(2.5)
P_AT_3 = p_value(3.0)

TRADE: dict[tuple[int, ...], dict[str, float]] = {}
for _rs in cumulative_sets():
    _arl0, _c0 = average_run_length(_rs, shift=0.0)
    _arl1, _c1 = average_run_length(_rs, shift=SHIFT)
    TRADE[_rs] = {"arl0": _arl0, "arl1": _arl1,
                  "censored0": _c0, "censored1": _c1}

# The trade is not one number: the sensitivity it buys depends on the shift you
# are trying to catch, while the false alarms it costs do not. At a shift the
# one-point rule already sees, the extra rules buy almost nothing and still cost
# the same. That comparison is the level's payload.
BIG_SHIFT = 3.0
ARL_BIG_ONE = average_run_length((1,), shift=BIG_SHIFT)[0]
ARL_BIG_ALL = average_run_length(RULES, shift=BIG_SHIFT)[0]

ALL_RULES = cumulative_sets()[-1]
ARL0_ONE_RULE = TRADE[(1,)]["arl0"]
ARL0_ALL = TRADE[ALL_RULES]["arl0"]
ARL1_ONE_RULE = TRADE[(1,)]["arl1"]
ARL1_ALL = TRADE[ALL_RULES]["arl1"]
FALSE_ALARM_COST = ARL0_ONE_RULE / ARL0_ALL       # how much noisier
SENSITIVITY_GAIN = ARL1_ONE_RULE / ARL1_ALL       # how much quicker

# Champ & Woodall (1987) published 91.75 for all four rules; the simulation
# landing there is external corroboration rather than self-agreement.
CHAMP_WOODALL_ARL0 = 91.75


if __name__ == "__main__":
    print(f"one-point rule at ±{LIMIT:.0f}σ: alpha {ALPHA_1:.6f}  "
          f"ARL0 {SHEWHART_ARL0:.1f} (published)\n")
    print("  two ways to be wrong")
    print(f"  {'shift':>7}  {'power':>8}  {'beta':>8}")
    for s in SHIFTS:
        print(f"  {s:>7.1f}  {POWER_AT[s]:>8.4f}  {BETA_AT[s]:>8.4f}")
    print(f"\n  at a {SHIFT:.0f} sigma shift the next point has power "
          f"{POWER_AT[SHIFT]:.4f}")
    print(f"  so one point alone takes {ARL1_FROM_POWER:.1f} subgroups on average; "
          f"detection.py publishes {ARL1_SHEW:.1f}")
    print(f"\n  a point at 2.5 sigma has p = {P_AT_2_5:.4f}, and the chart calls it in")
    print(f"  a point at 3.0 sigma has p = {P_AT_3:.4f}\n")
    print("  the trade, simulated")
    print(f"  {'rules':>12}  {'ARL0':>8}  {'ARL1 (1σ)':>10}  {'censored':>9}")
    for rs in cumulative_sets():
        d = TRADE[rs]
        print(f"  {'+'.join(map(str, rs)):>12}  {d['arl0']:>8.1f}  {d['arl1']:>10.2f}  "
              f"{d['censored0']:>8.2%}")
    print(f"\n  all four rules: false alarms {FALSE_ALARM_COST:.1f}x more often")
    print(f"  a {SHIFT:.0f} sigma shift caught {SENSITIVITY_GAIN:.1f}x sooner "
          f"({ARL1_ONE_RULE:.1f} -> {ARL1_ALL:.1f} subgroups)")
    print(f"  a {BIG_SHIFT:.0f} sigma shift caught {ARL_BIG_ONE / ARL_BIG_ALL:.1f}x sooner "
          f"({ARL_BIG_ONE:.2f} -> {ARL_BIG_ALL:.2f}) - the same cost buys almost nothing")
    print(f"  published ARL0 for all four (Champ & Woodall 1987): "
          f"{CHAMP_WOODALL_ARL0}")
