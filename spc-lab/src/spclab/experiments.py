"""LEVEL 12 — Experiments. Why one factor at a time finds the wrong answer.

The last level. Everything before it watched a process or described a
relationship in data that arrived on its own. This one changes the settings on
purpose, and the whole subject turns on a single fact: if two factors interact,
studying them one at a time can lead you confidently to the wrong setting.

Not inefficiently. Wrongly. That distinction is the level.

Five claims, none asserted:

1. **One factor at a time lands on a setting that is not the best one.** With a
   real interaction present, the classic procedure — hold everything, tune A,
   fix A, tune B — terminates at a corner the factorial identifies as worse. The
   gap is computed, not alleged.

2. **The interaction is not merely mis-estimated by OFAT; it is invisible.**
   OFAT never visits the fourth corner, so the interaction term is not
   identifiable from its runs at all. A factorial gets it from the same number
   of runs.

3. **A factorial is more precise on the same budget.** Every run contributes to
   every effect — the hidden replication — so the standard error of an effect
   estimate is smaller than the one-at-a-time comparison it replaces, by a
   factor this module measures.

4. **Screening buys width with aliasing, and the trade is a table.** A
   sixteenth-fraction studies seven factors in eight runs, and the price is
   exact: each main effect is confounded with a set of two-factor interactions,
   which can be written down before the experiment is run.

5. **A two-level design cannot see curvature at all.** Adding centre points
   makes curvature testable, because the difference between the factorial mean
   and the centre mean is a pure quadratic signal with a known standard error.

    PYTHONPATH=src .venv/bin/python -m spclab.experiments
"""
from __future__ import annotations

import itertools
import math

import numpy as np

from spclab.relationships import f_sf

# ---------------------------------------------------------------------------
# The worked example: injection moulding, shrinkage in thousandths of an inch.
# Hold pressure (A) and melt temperature (B), coded −1 / +1. Lower is better.
#
# The coefficients are chosen so the interaction is larger than one of the main
# effects, which is the case where one-at-a-time does not merely take longer.
# ---------------------------------------------------------------------------
B0, BA, BB, BAB = 10.0, -2.0, -1.0, 3.0
NOISE_SD = 0.45

FACTORS = ("pressure", "temperature")
CORNERS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
BASELINE = (-1, -1)          # where an engineer starts: everything low


def response(a: float, b: float) -> float:
    """The true mean response at coded settings (a, b). Never observed directly."""
    return B0 + BA * a + BB * b + BAB * a * b


def observe(a: float, b: float, rng: np.random.Generator) -> float:
    return response(a, b) + rng.normal(0.0, NOISE_SD)


def truth_table() -> dict[tuple[int, int], float]:
    return {c: response(*c) for c in CORNERS}


def best_corner() -> tuple[tuple[int, int], float]:
    t = truth_table()
    c = min(t, key=t.get)
    return c, t[c]


# ---------------------------------------------------------------------------
# 1 & 2. One factor at a time, and what it cannot see
# ---------------------------------------------------------------------------
def ofat(baseline: tuple[int, int] = BASELINE) -> dict:
    """Tune B at fixed A, then tune A at the chosen B. Noise-free, on purpose.

    Run without noise so the failure cannot be blamed on sampling: even with
    perfect measurements the procedure stops at the wrong corner.
    """
    a0, _ = baseline
    # phase 1: vary the second factor at the baseline level of the first
    b_best = min((-1, 1), key=lambda b: response(a0, b))
    # phase 2: vary the first factor at the level just chosen
    a_best = min((-1, 1), key=lambda a: response(a, b_best))
    chosen = (a_best, b_best)
    opt, opt_y = best_corner()
    return {"visited": [(a0, -1), (a0, 1), (-1, b_best), (1, b_best)],
            "chosen": chosen, "chosen_y": response(*chosen),
            "optimum": opt, "optimum_y": opt_y,
            "shortfall": response(*chosen) - opt_y,
            # success is landing on a best-VALUED corner. Comparing coordinates
            # reports failure when two corners tie for best and the procedure
            # picks the other one, which is not a failure of the procedure.
            "found_optimum": abs(response(*chosen) - opt_y) < 1e-12}


def ofat_can_estimate_interaction(baseline: tuple[int, int] = BASELINE) -> bool:
    """Does the one-at-a-time run set contain all four corners?

    An interaction is the difference of two differences, so it needs all four.
    OFAT visits three, which is why the term is unidentifiable rather than
    imprecise — a distinction worth being pedantic about.
    """
    return set(ofat(baseline)["visited"]) == set(CORNERS)


# ---------------------------------------------------------------------------
# 3. Effects from a factorial, and the precision of the same budget
# ---------------------------------------------------------------------------
def factorial_effects(y: dict[tuple[int, int], float]) -> dict:
    """Main effects and the interaction, as differences of averages.

    Effect of A = mean(y at A=+1) − mean(y at A=−1), and the interaction is the
    same contrast applied to the product column. Every run appears in every
    estimate, which is the hidden replication.
    """
    def contrast(col) -> float:
        hi = [v for c, v in y.items() if col(c) > 0]
        lo = [v for c, v in y.items() if col(c) < 0]
        return sum(hi) / len(hi) - sum(lo) / len(lo)

    return {"A": contrast(lambda c: c[0]),
            "B": contrast(lambda c: c[1]),
            "AB": contrast(lambda c: c[0] * c[1])}


def precision_comparison(runs: int = 16, trials: int = 20_000,
                          seed: int = 3) -> dict:
    """Spread of the estimated A effect: factorial against one-at-a-time.

    Same total runs both ways. The factorial spends them on four corners and
    uses all of them for every effect; OFAT spends half on its first phase and
    half on its second, so each comparison rests on half the data.
    """
    rng = np.random.default_rng(seed)
    per_corner = runs // 4
    per_ofat = runs // 4          # two levels x two phases
    fac, ofa = [], []
    for _ in range(trials):
        y = {c: float(np.mean([observe(*c, rng) for _ in range(per_corner)]))
             for c in CORNERS}
        fac.append(factorial_effects(y)["A"])
        # OFAT's estimate of the A effect: one comparison, at whatever B it fixed
        b_fixed = ofat()["chosen"][1]
        hi = float(np.mean([observe(1, b_fixed, rng) for _ in range(per_ofat)]))
        lo = float(np.mean([observe(-1, b_fixed, rng) for _ in range(per_ofat)]))
        ofa.append(hi - lo)
    f_sd = float(np.std(fac, ddof=1))
    o_sd = float(np.std(ofa, ddof=1))
    return {"runs": runs, "factorial_sd": f_sd, "ofat_sd": o_sd,
            "ratio": o_sd / f_sd, "true_A_effect": 2 * BA,
            "factorial_bias": float(np.mean(fac)) - 2 * BA}


# ---------------------------------------------------------------------------
# 4. Screening, and the price written down
# ---------------------------------------------------------------------------
SCREEN_FACTORS = "ABCDEFG"
# The standard 2^(7-4) III design: D=AB, E=AC, F=BC, G=ABC.
GENERATORS = {"D": "AB", "E": "AC", "F": "BC", "G": "ABC"}


def _sign(word: str, run: dict[str, int]) -> int:
    s = 1
    for ch in word:
        s *= run[ch]
    return s


def screening_design() -> list[dict[str, int]]:
    """Eight runs covering seven factors — a sixteenth of the full factorial."""
    runs = []
    for a, b, c in itertools.product((-1, 1), repeat=3):
        run = {"A": a, "B": b, "C": c}
        for letter, word in GENERATORS.items():
            run[letter] = _sign(word, run)
        runs.append(run)
    return runs


def alias_pairs() -> dict[str, list[str]]:
    """Which two-factor interactions each main effect is confounded with.

    Two columns are aliased when they are identical across all eight runs. This
    is computed from the design rather than quoted from a table, which is the
    point: the price of a fraction is knowable before any run is made.
    """
    runs = screening_design()
    cols = {L: [r[L] for r in runs] for L in SCREEN_FACTORS}
    for x, y in itertools.combinations(SCREEN_FACTORS, 2):
        cols[x + y] = [a * b for a, b in zip(cols[x], cols[y])]
    out: dict[str, list[str]] = {}
    for L in SCREEN_FACTORS:
        out[L] = sorted(k for k, v in cols.items()
                        if len(k) == 2 and v == cols[L])
    return out


def full_factorial_runs(k: int = 7) -> int:
    return 2 ** k


# ---------------------------------------------------------------------------
# 5. Curvature needs centre points
# ---------------------------------------------------------------------------
CURVATURE = -1.6          # a genuine bend the corners cannot report


def response_curved(a: float, b: float) -> float:
    """The same surface plus a quadratic bend.

    With coded ±1 factors a² = 1 at every corner and 0 at the centre, so this
    term adds the *same* amount at all four corners and nothing at the middle.
    That is the real reason a two-level design cannot see curvature: not that
    the bend is absent at the corners, but that it is identical at every one of
    them, so no contrast among corners can separate it from the intercept. Only
    a centre point can.

    An earlier version subtracted 1.0 here to try to make the term vanish at
    the corners, which broke the very thing the section is about.
    """
    return response(a, b) + CURVATURE * (a * a + b * b)


def centre_point_test(n_centre: int = 4, reps: int = 2, seed: int = 11,
                      curved: bool = True) -> dict:
    """Test for curvature from the factorial mean against the centre mean.

        SS_pure_quad = n_f·n_c (ȳ_f − ȳ_c)² / (n_f + n_c)

    A two-level design has no term for curvature; the centre points supply one,
    and their own scatter supplies the error to judge it against.
    """
    rng = np.random.default_rng(seed)
    f = response_curved if curved else response
    fact = [f(*c) + rng.normal(0, NOISE_SD) for c in CORNERS for _ in range(reps)]
    cent = [f(0.0, 0.0) + rng.normal(0, NOISE_SD) for _ in range(n_centre)]
    nf, nc = len(fact), len(cent)
    yf, yc = float(np.mean(fact)), float(np.mean(cent))
    ss_q = nf * nc * (yf - yc) ** 2 / (nf + nc)
    ms_e = float(np.var(cent, ddof=1))
    f_stat = ss_q / ms_e
    return {"factorial_mean": yf, "centre_mean": yc, "gap": yf - yc,
            "ss_quadratic": ss_q, "ms_error": ms_e, "f": f_stat,
            "p": f_sf(f_stat, 1, nc - 1), "n_centre": nc}


# ---------------------------------------------------------------------------
# Computed once; read by the sheets, the page, the lab and the tests.
# ---------------------------------------------------------------------------
TRUTH = truth_table()
OPTIMUM, OPTIMUM_Y = best_corner()
OFAT = ofat()
OFAT_SEES_INTERACTION = ofat_can_estimate_interaction()

_rng = np.random.default_rng(5)
OBSERVED = {c: observe(*c, _rng) for c in CORNERS}
EFFECTS = factorial_effects(TRUTH)
EFFECTS_OBSERVED = factorial_effects(OBSERVED)

PRECISION = precision_comparison()

ALIASES = alias_pairs()
SCREEN_RUNS = len(screening_design())
FULL_RUNS = full_factorial_runs(len(SCREEN_FACTORS))

CURVED = centre_point_test(curved=True)
FLAT = centre_point_test(curved=False)


if __name__ == "__main__":
    print("shrinkage at the four corners (lower is better)")
    for c in CORNERS:
        mark = "  <- best" if c == OPTIMUM else ""
        print(f"   pressure {c[0]:+d}  temperature {c[1]:+d}   {TRUTH[c]:5.1f}{mark}")
    print()
    print("  1. one factor at a time, with no noise at all")
    print(f"     starts at {BASELINE}, visits {len(set(OFAT['visited']))} of 4 corners")
    print(f"     stops at {OFAT['chosen']} -> {OFAT['chosen_y']:.1f}")
    print(f"     the optimum is {OFAT['optimum']} -> {OFAT['optimum_y']:.1f}")
    print(f"     shortfall {OFAT['shortfall']:.1f} thousandths "
          f"({100 * OFAT['shortfall'] / OFAT['optimum_y']:.0f} % worse), "
          f"found optimum: {OFAT['found_optimum']}")
    print()
    print("  2. the interaction it cannot see")
    print(f"     all four corners visited: {OFAT_SEES_INTERACTION}")
    print(f"     true effects  A {EFFECTS['A']:+.1f}   B {EFFECTS['B']:+.1f}   "
          f"AB {EFFECTS['AB']:+.1f}")
    print(f"     |AB| is larger than |B|: {abs(EFFECTS['AB']) > abs(EFFECTS['B'])}")
    print()
    print("  3. the same budget, spent two ways")
    print(f"     {PRECISION['runs']} runs: factorial s.d. {PRECISION['factorial_sd']:.4f}, "
          f"one-at-a-time {PRECISION['ofat_sd']:.4f}  (x{PRECISION['ratio']:.2f})")
    print()
    print(f"  4. screening seven factors in {SCREEN_RUNS} runs instead of {FULL_RUNS}")
    for L in SCREEN_FACTORS:
        print(f"     {L} is confounded with {', '.join(ALIASES[L])}")
    print()
    print("  5. curvature is invisible without centre points")
    print(f"     curved surface: gap {CURVED['gap']:+.2f}  F {CURVED['f']:.1f}  "
          f"p {CURVED['p']:.4f}")
    print(f"     flat surface:   gap {FLAT['gap']:+.2f}  F {FLAT['f']:.2f}  "
          f"p {FLAT['p']:.3f}")
