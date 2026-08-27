"""LEVEL 0 act — 'What a measurement is.'

The prerequisite the curriculum was missing. Level 4 opens with "variation is
predictable", which already assumes the viewer owns a mean, a standard
deviation and a distribution. This act supplies exactly those and stops: no
control limits, no subgroups, no charts. It ends by handing the one open
question — how far a sample estimate can sit from the truth — to Level 4.

Rebuilt 2026-08-26 under specs/spc-manim-craft-contract.md, checkpoint 4:

- **The mean is derived, not drawn.** A candidate centre sweeps along the value
  line; the twelve deviations follow it, a see-saw under the line tilts by the
  running imbalance, and three live readouts count the sums above, below and
  total. The candidate becomes x̄ at the position where the total reads zero —
  which is what "balance point" means, and it is now something you watch.
- **σ is derived by running mean.** The twelve squares enter one at a time and
  the average square's side follows the root of the running mean of squares, so
  the figure lands as the limit of a process rather than as a caption.
- **The bell is grown by a tracker** over the parts measured, on a log scale,
  instead of five static Transform batches.
- One camera push, on the two readings 0.001 mm apart, where the gauge stops.
- Every play carries a deliberate rate_func; every string is in one of the
  site's two voices; maths is Computer Modern.

Pacing still lives in the narration script — see narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level03_scene.py Level03
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level03_scene.py Level03
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, DashedLine, Dot, Group, Line, MathTex, Polygon, Rectangle, Square,
    ValueTracker, VGroup,
    Create, FadeIn, FadeOut, LaggedStart, ReplacementTransform, Restore,
    TransformMatchingTex, Write,
    always_redraw,
    DEGREES, DOWN, LEFT, RIGHT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    BLUE, GREY, INK, PANEL, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose,
)
from spclab.narration import NarratedCameraScene

# ---------------------------------------------------------------------------
# The data. Seeded once at import, so every number on screen is a real
# computed value and the same render twice gives the same frames.
# A shaft turned to 12.000 mm nominal, gauge resolution 0.001 mm.
# ---------------------------------------------------------------------------
NOMINAL    = 12.000
TRUE_SIGMA = 0.020
GAUGE      = 0.001

_rng   = np.random.default_rng(7)
PARTS  = np.round(_rng.normal(NOMINAL, TRUE_SIGMA, 12), 3)
# four more handfuls of twelve off the same process, for the last beat
HANDFULS = [np.round(_rng.normal(NOMINAL, TRUE_SIGMA, 12), 3) for _ in range(4)]

MEAN  = float(PARTS.mean())
DEV   = PARTS - MEAN
POS   = float(DEV[DEV > 0].sum())
NEG   = float(DEV[DEV < 0].sum())
VAR   = float((DEV ** 2).mean())         # mean of the squares
SIGMA = float(np.sqrt(VAR))              # root of that mean
S_SAMPLE = float(PARTS.std(ddof=1))      # the n-1 estimate, used in beat 5

X_LO, X_HI = 11.93, 12.07
TICKS = [11.94, 11.96, 11.98, 12.00, 12.02, 12.04, 12.06]

# where the candidate centre starts its walk: far enough off to be visibly
# unbalanced (the twelve deviations then sum to +0.17 mm)
C_START = 11.984


class ValueLine(VGroup):
    """A bare horizontal value axis — line, ticks, mono labels, no LaTeX."""

    def __init__(self, x_lo, x_hi, ticks, length=10.6, fmt="{:.2f}"):
        super().__init__()
        self.x_lo, self.x_hi, self.length = x_lo, x_hi, length
        self.line = Line(LEFT * length / 2, RIGHT * length / 2,
                         stroke_color=GREY, stroke_width=2)
        self.add(self.line)
        for v in ticks:
            p = self.n2p(v)
            tick = Line(p + DOWN * 0.12, p + UP * 0.12,
                        stroke_color=GREY, stroke_width=2)
            lab = micro(fmt.format(v), 18)
            lab.next_to(tick, DOWN, buff=0.50)   # room for the fulcrum
            self.add(tick, lab)

    def n2p(self, v):
        frac = (v - self.x_lo) / (self.x_hi - self.x_lo)
        return self.line.get_left() + RIGHT * (frac * self.length)


def strip_levels(values, window=0.0025):
    """Stack index per value so near-identical readings do not overlap."""
    levels, placed = [], []
    for v in values:
        levels.append(sum(1 for p in placed if abs(p - v) < window))
        placed.append(v)
    return levels


def closest_pair(values):
    """Indices of the two nearest readings — where the gauge runs out."""
    order = np.argsort(values)
    gaps = np.diff(values[order])
    k = int(np.argmin(gaps))
    return int(order[k]), int(order[k + 1])


class Level03(NarratedCameraScene):
    def construct(self):
        self.part1_parts_vary()
        self.part2_balance_point()
        self.part3_squaring()
        self.part4_the_shape()
        self.part5_sample_is_not_population()

    # ------------------------------------------- 1: nominally identical parts
    def part1_parts_vary(self):
        self.title = prose("Level 3 · twelve identical parts, twelve numbers",
                           30, GREY).to_edge(UP, buff=0.38)
        vline = ValueLine(X_LO, X_HI, TICKS).shift(DOWN * 1.35)
        xlab = micro("SHAFT DIAMETER (mm) · NOMINAL 12.000").next_to(
            vline, DOWN, buff=0.30)
        levels = strip_levels(PARTS)
        dots = VGroup(*[
            Dot(vline.n2p(v) + UP * (0.30 + 0.24 * k), radius=0.075, color=BLUE)
            for v, k in zip(PARTS, levels)
        ])

        with self.say("Take twelve parts off one machine. Same tool, same "
                      "operator, same gauge, one after another.") as tr:
            self.play(FadeIn(self.title, shift=DOWN * 0.12),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(Create(vline.line), FadeIn(xlab),
                      run_time=0.7, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(VGroup(*vline[1:])),
                      run_time=0.6, rate_func=rf.ease_out_sine)
            self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d in dots],
                                  lag_ratio=0.5),
                      run_time=max(1.8, tr.duration * 0.5), rate_func=rf.linear)

        top = dots.get_top()[1] + 0.35
        span = Line(np.array([vline.n2p(PARTS.min())[0], top, 0.0]),
                    np.array([vline.n2p(PARTS.max())[0], top, 0.0]),
                    stroke_color=YELLOW, stroke_width=2.5)
        span_lab = gauge(f"{PARTS.min():.3f} … {PARTS.max():.3f}   "
                         f"spread {PARTS.max() - PARTS.min():.3f} mm",
                         22, YELLOW).next_to(span, UP, buff=0.14)
        with self.say("Every reading is different, and nothing is broken. The "
                      "twelve of them cover forty seven microns."):
            self.play(Create(span), FadeIn(span_lab),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)

        # one camera push: the two readings a single gauge count apart
        i, j = closest_pair(PARTS)
        mid = (vline.n2p(PARTS[i]) + vline.n2p(PARTS[j])) / 2
        zoom = 0.30
        # the tick labels are type sized for the wide frame, so they leave too:
        # at 0.30 zoom a 18pt label renders as 60pt
        chrome = Group(self.title, xlab, span, span_lab, VGroup(*vline[1:]))
        self.camera.frame.save_state()
        pair_tags = VGroup(
            gauge(f"{PARTS[i]:.3f}", 24, INK),
            gauge(f"{PARTS[j]:.3f}", 24, INK),
        )
        # above and below, not beside: the cluster's other readings sit to the
        # right of these two and a side label lands on one of them
        for tag, idx, side in zip(pair_tags, (i, j), (UP, DOWN)):
            tag.scale(zoom).next_to(dots[idx], side, buff=0.12 * zoom)
        note = gauge(f"one gauge count apart: {GAUGE:.3f} mm", 22, YELLOW)
        note.scale(zoom).next_to(mid + DOWN * 0.55 * zoom, DOWN, buff=0.0)

        with self.say("Two of them differ by a single micron, which is exactly "
                      "where this gauge stops. Below that it has nothing to "
                      "say.") as tr:
            self.play(FadeOut(chrome), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(self.camera.frame.animate.scale(zoom).move_to(
                      mid + UP * 0.25 * zoom),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(pair_tags), FadeIn(note),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        note2 = prose("spread is not a defect — it is what every process does",
                      26, TEAL).move_to(UP * 2.45)
        with self.say("Spread is not a defect. It is what every real process "
                      "does, and the job is to describe it."):
            self.play(Restore(self.camera.frame), FadeOut(pair_tags),
                      FadeOut(note), run_time=1.3, rate_func=rf.ease_in_out_sine)
            # the ticks left with the chrome, so they come back with it
            self.play(FadeIn(Group(self.title, xlab, VGroup(*vline[1:]))),
                      FadeIn(note2), run_time=0.8, rate_func=rf.ease_out_sine)

        self.vline, self.xlab, self.dots = vline, xlab, dots
        self.p1_extra = Group(span, span_lab, note2)

    # ------------------------------------------------- 2: the balance point
    def part2_balance_point(self):
        vline, dots = self.vline, self.dots
        t2 = prose("Level 3 · the mean is the balance point", 30, GREY)
        t2.to_edge(UP, buff=0.38)
        with self.say("Twelve numbers are not an answer. You need one number "
                      "for the centre — so guess one, and check it."):
            self.play(FadeOut(self.p1_extra), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(self.title, t2),
                      run_time=0.7, rate_func=rf.ease_in_out_sine)
        self.title = t2

        c = ValueTracker(C_START)

        def above(cv: float) -> float:
            d = PARTS - cv
            return float(d[d > 0].sum())

        def below(cv: float) -> float:
            d = PARTS - cv
            return float(d[d < 0].sum())

        cand = always_redraw(lambda: DashedLine(
            vline.n2p(c.get_value()) + DOWN * 0.06,
            vline.n2p(c.get_value()) + UP * 1.75,
            dash_length=0.12, stroke_color=YELLOW, stroke_width=3))
        devs = always_redraw(lambda: VGroup(*[
            Line(d.get_center(),
                 np.array([vline.n2p(c.get_value())[0], d.get_center()[1], 0.0]),
                 stroke_color=TEAL if v > c.get_value() else RED,
                 stroke_width=3.5)
            for d, v in zip(dots, PARTS)
        ]))

        # a see-saw that carries a real quantity: it tilts by the imbalance
        # low enough that a tilted beam clears the axis label: at -2.55 it
        # struck straight through 'SHAFT DIAMETER (mm)' in every take
        BEAM_Y, BEAM_HALF, MAX_TILT = -3.15, 1.7, 20.0

        def beam() -> Line:
            cx = vline.n2p(c.get_value())[0]
            pivot = np.array([cx, BEAM_Y, 0.0])
            ln = Line(pivot + LEFT * BEAM_HALF, pivot + RIGHT * BEAM_HALF,
                      stroke_color=YELLOW, stroke_width=5)
            tilt = float(np.clip((above(c.get_value()) + below(c.get_value())) / 0.17,
                                 -1.0, 1.0)) * MAX_TILT
            return ln.rotate(-tilt * DEGREES, about_point=pivot)

        def fulcrum() -> Polygon:
            cx = vline.n2p(c.get_value())[0]
            return Polygon(np.array([cx, BEAM_Y - 0.06, 0.0]),
                           np.array([cx - 0.24, BEAM_Y - 0.50, 0.0]),
                           np.array([cx + 0.24, BEAM_Y - 0.50, 0.0]),
                           fill_color=GREY, fill_opacity=0.9, stroke_width=0)

        live_beam, live_fulcrum = always_redraw(beam), always_redraw(fulcrum)

        lab_above = at_panel(micro("SUM ABOVE THE LINE"), 0, value=False)
        val_above = always_redraw(lambda: at_panel(
            gauge(f"{above(c.get_value()):+.4f}", 26, TEAL), 0))
        lab_below = at_panel(micro("SUM BELOW"), 1, value=False)
        val_below = always_redraw(lambda: at_panel(
            gauge(f"{below(c.get_value()):+.4f}", 26, RED), 1))
        lab_net = at_panel(micro("THE TWO TOGETHER"), 2, value=False)
        val_net = always_redraw(lambda: at_panel(
            gauge(f"{above(c.get_value()) + below(c.get_value()):+.4f}", 26, YELLOW), 2))

        with self.say("Here is a guess, with every part's distance to it drawn "
                      "in. Add the distances on each side and the guess is out: "
                      "the two sides do not cancel, and the beam tips."):
            self.play(FadeIn(cand), FadeIn(devs),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(FadeIn(live_beam), FadeIn(live_fulcrum),
                      FadeIn(lab_above), FadeIn(val_above),
                      FadeIn(lab_below), FadeIn(val_below),
                      FadeIn(lab_net), FadeIn(val_net),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        with self.say("So walk the guess along until they do. One position "
                      "makes the two sides equal and opposite, and the beam "
                      "comes level.") as tr:
            self.play(c.animate.set_value(MEAN),
                      run_time=max(3.0, tr.duration * 0.72),
                      rate_func=rf.ease_in_out_sine)

        settled = gauge(f"x̄ = {MEAN:.4f} mm", 30, YELLOW)
        settled.next_to(vline.n2p(MEAN) + UP * 1.75, UP, buff=0.16)
        with self.say("That position is the mean. Not a formula you were handed "
                      "— the one place where the deviations cancel."):
            travelling = val_net.copy().clear_updaters()
            self.remove(val_net)
            self.play(ReplacementTransform(travelling, settled),
                      FadeOut(lab_net, shift=RIGHT * 0.2),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        self.beat(0.5)
        for m in self.mobjects:
            m.clear_updaters()
        self.p2_all = Group(*[m for m in self.mobjects if m is not self.title])

    # ------------------------------------------------- 3: why spread squares
    def part3_squaring(self):
        t3 = prose("Level 3 · spread has to be squared first", 30, GREY)
        t3.to_edge(UP, buff=0.38)
        dead_end = prose("the average deviation is 0.0000 mm — for every data "
                         "set that ever existed", 26, RED).move_to(UP * 0.6)
        with self.say("Now the spread. Averaging those deviations is useless: "
                      "we just proved they cancel, by construction."):
            self.play(FadeOut(self.p2_all), run_time=0.6, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(self.title, t3),
                      run_time=0.7, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(dead_end, shift=UP * 0.15),
                      run_time=1.0, rate_func=rf.ease_out_sine)
        self.title = t3

        K = 48.0  # mm of deviation → scene units; biggest square ≈ 1.4 units
        order = np.argsort(-np.abs(DEV))
        squares = VGroup(*[
            Square(side_length=max(abs(DEV[i]) * K, 0.07),
                   fill_color=BLUE, fill_opacity=0.35,
                   stroke_color=BLUE, stroke_width=2)
            for i in order
        ])
        squares.arrange(RIGHT, buff=0.10, aligned_edge=DOWN)
        squares.move_to(np.array([-2.4, -1.85, 0.0]), aligned_edge=DOWN)
        base = Line(squares.get_left() + LEFT * 0.3,
                    squares.get_right() + RIGHT * 0.3,
                    stroke_color=GREY, stroke_width=2)
        base.next_to(squares, DOWN, buff=0.0)
        side_note = micro("EACH SQUARE: SIDE = |x − x̄|,  AREA = (x − x̄)²", 20)
        side_note.next_to(base, DOWN, buff=0.24)

        # the running mean of squares: m squares in, and the average square's
        # side is the root of their mean area. σ is where that walk ends up.
        m = ValueTracker(0.0)
        sq_areas = np.array([DEV[i] ** 2 for i in order])

        def count() -> int:
            return int(np.clip(np.floor(m.get_value() + 1e-9), 0, 12))

        def mean_sq() -> float:
            k = max(count(), 1)
            return float(sq_areas[:k].mean())

        live_squares = always_redraw(lambda: VGroup(*[
            squares[i].copy() for i in range(count())
        ]))
        avg_sq = always_redraw(lambda: Square(
            side_length=max(np.sqrt(mean_sq()) * K, 0.05),
            fill_color=YELLOW, fill_opacity=0.35,
            stroke_color=YELLOW, stroke_width=2.5
        ).next_to(squares, RIGHT, buff=0.9, aligned_edge=DOWN))
        # anchored on the average square, and kept left of the readout column
        avg_tag = micro("THE AVERAGE SQUARE\nITS SIDE IS σ", 20, YELLOW)
        avg_tag.move_to([squares.get_right()[0] + 1.25, -0.35, 0])

        lab_n = at_panel(micro("SQUARES SO FAR"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{count():>2} of 12", 26, BLUE), 0))
        lab_ms = at_panel(micro("MEAN SQUARE (mm²)"), 1, value=False)
        val_ms = always_redraw(lambda: at_panel(
            gauge(f"{mean_sq():.6f}", 26, BLUE), 1))
        lab_rt = at_panel(micro("ITS ROOT (mm)"), 2, value=False)
        val_rt = always_redraw(lambda: at_panel(
            gauge(f"{np.sqrt(mean_sq()):.4f}", 26, YELLOW), 2))

        with self.say("Square each deviation instead. Negatives turn positive, "
                      "the cancelling stops, and every square is an area you "
                      "can put on a shelf.") as tr:
            self.play(FadeOut(dead_end), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(Create(base), FadeIn(side_note),
                      run_time=0.7, rate_func=rf.ease_in_out_sine)
            self.add(live_squares, avg_sq)
            self.play(FadeIn(avg_tag), FadeIn(lab_n), FadeIn(val_n),
                      FadeIn(lab_ms), FadeIn(val_ms),
                      FadeIn(lab_rt), FadeIn(val_rt),
                      run_time=0.7, rate_func=rf.ease_out_sine)
            self.play(m.animate.set_value(12.0),
                      run_time=max(3.2, tr.duration * 0.6), rate_func=rf.linear)

        eq_a = MathTex(r"\sigma", "=",
                       r"\sqrt{\overline{(x-\bar{x})^{2}}}",
                       font_size=40, color=INK).move_to(UP * 2.55)
        eq_b = MathTex(r"\sigma", "=", f"{SIGMA:.4f}\\ \\mathrm{{mm}}",
                       font_size=40, color=INK).move_to(UP * 2.55)
        with self.say("Twelve squares averaged, then rooted, which puts the "
                      "answer back in millimetres. That is sigma, and it is the "
                      "side of the average square."):
            self.play(Write(eq_a), run_time=1.3, rate_func=rf.linear)
        with self.say(f"For these twelve parts, {SIGMA * 1000:.1f} microns."):
            self.play(TransformMatchingTex(eq_a, eq_b),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        self.beat(0.5)
        for mob in self.mobjects:
            mob.clear_updaters()
        self.p3_all = Group(*[mob for mob in self.mobjects if mob is not self.title])

    # ------------------------------------------------ 4: the shape emerges
    def part4_the_shape(self):
        t4 = prose("Level 3 · many parts make a shape nobody chose", 30, GREY)
        t4.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[X_LO, X_HI, 0.02], y_range=[0, 1.08, 0.25],
                    x_length=10.0, y_length=3.8, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.85 + LEFT * 0.4)
        xlab = micro("SHAFT DIAMETER (mm)")
        ticks = VGroup(*[
            micro(f"{v:.2f}", 18).next_to(axes.c2p(v, 0), DOWN, buff=0.16)
            for v in (11.94, 11.98, 12.02, 12.06)
        ])
        xlab.next_to(ticks, DOWN, buff=0.20)

        # one big sample, drawn once; the tracker only decides how much of it
        # has been "measured" so far, so the bars grow monotonically
        TOTAL = 20_000
        edges = np.linspace(X_LO, X_HI, 29)
        centres = (edges[:-1] + edges[1:]) / 2
        pop = np.round(np.random.default_rng(11).normal(NOMINAL, TRUE_SIGMA, TOTAL), 3)
        which = np.clip(np.digitize(pop, edges) - 1, 0, 27)
        onehot = np.zeros((TOTAL, 28))
        onehot[np.arange(TOTAL), which] = 1.0
        cum = np.cumsum(onehot, axis=0)

        px_w = (axes.c2p(X_LO + (edges[1] - edges[0]), 0) - axes.c2p(X_LO, 0))[0]
        full = (axes.c2p(X_LO, 1.0) - axes.c2p(X_LO, 0.0))[1]

        lg = ValueTracker(np.log10(12.0))

        def measured() -> int:
            return int(np.clip(round(10 ** lg.get_value()), 1, TOTAL))

        def bars() -> VGroup:
            counts = cum[measured() - 1]
            peak = max(counts.max(), 1.0)
            grp = VGroup()
            for i, ct in enumerate(counts):
                h = max(ct / peak, 0.0015) * full
                grp.add(Rectangle(width=px_w * 0.9, height=h,
                                  fill_color=BLUE, fill_opacity=0.75,
                                  stroke_width=0)
                        .move_to(axes.c2p(centres[i], 0), aligned_edge=DOWN))
            return grp

        live_bars = always_redraw(bars)
        lab_n = at_panel(micro("PARTS MEASURED"), 0, value=False)
        val_n = always_redraw(lambda: at_panel(
            gauge(f"{measured():>6,}", 26, BLUE), 0))

        with self.say("Twelve parts say nothing about shape. Keep measuring, and "
                      "keep the same bins."):
            self.play(FadeOut(self.p3_all), run_time=0.6, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(self.title, t4),
                      run_time=0.6, rate_func=rf.ease_in_out_sine)
            self.play(Create(axes), FadeIn(xlab), FadeIn(ticks),
                      run_time=0.9, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(live_bars), FadeIn(lab_n), FadeIn(val_n),
                      run_time=0.6, rate_func=rf.ease_out_sine)
        self.title = t4

        with self.say("A hundred parts. A thousand. Twenty thousand, off the "
                      "same machine, measured with the same gauge.") as tr:
            self.play(lg.animate.set_value(np.log10(TOTAL)),
                      run_time=max(4.0, tr.duration * 0.8), rate_func=rf.ease_in_out_sine)

        xs = np.linspace(X_LO, X_HI, 240)
        pdf = np.exp(-((xs - NOMINAL) ** 2) / (2 * TRUE_SIGMA ** 2))
        curve = axes.plot_line_graph(xs, pdf, add_vertex_dots=False,
                                     line_color=TEAL, stroke_width=3)["line_graph"]
        with self.say("And a shape appears that nobody chose or asked for."):
            self.play(Create(curve), run_time=1.4, rate_func=rf.ease_in_out_sine)

        cause = prose("tool wear + temperature + material + clamping + gauge", 24, TEAL)
        cause.move_to(UP * 2.75)
        cause2 = prose("the bell is a consequence, not an assumption", 26, TEAL)
        cause2.next_to(cause, DOWN, buff=0.22)
        with self.say("Many small independent effects, added together, land on "
                      "this curve. The bell is a consequence of the process, "
                      "not an assumption about it."):
            self.play(FadeIn(cause, shift=DOWN * 0.1), FadeIn(cause2, shift=UP * 0.1),
                      run_time=1.3, rate_func=rf.ease_out_sine)

        self.beat(0.5)
        for mob in self.mobjects:
            mob.clear_updaters()
        self.p4_all = Group(*[mob for mob in self.mobjects if mob is not self.title])

    # -------------------------------------- 5: a sample is not the population
    def part5_sample_is_not_population(self):
        t5 = prose("Level 3 · you never measure everything", 30, GREY)
        t5.to_edge(UP, buff=0.38)
        axes = Axes(x_range=[11.94, 12.06, 0.02], y_range=[0, 1.15, 0.5],
                    x_length=6.6, y_length=3.1, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.75 + LEFT * 3.1)
        ticks = VGroup(*[
            micro(f"{v:.2f}", 18).next_to(axes.c2p(v, 0), DOWN, buff=0.16)
            for v in (11.96, 12.00, 12.04)
        ])
        curve = axes.plot(
            lambda x: np.exp(-((x - NOMINAL) ** 2) / (2 * TRUE_SIGMA ** 2)),
            x_range=[11.94, 12.06], color=TEAL, stroke_width=3)
        truth = gauge(f"μ = {NOMINAL:.3f} mm    σ = {TRUE_SIGMA:.3f} mm", 24, TEAL)
        truth.next_to(axes, UP, buff=0.34)
        never = prose("the process owns these two numbers, and never shows them",
                      22, GREY).next_to(truth, UP, buff=0.16)

        with self.say("One more thing, and then Level 4. You never measure "
                      "everything. The true centre and spread belong to the "
                      "process itself."):
            self.play(FadeOut(self.p4_all), run_time=0.6, rate_func=rf.ease_in_sine)
            self.play(ReplacementTransform(self.title, t5),
                      run_time=0.6, rate_func=rf.ease_in_out_sine)
            self.play(Create(axes), FadeIn(ticks), Create(curve),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(truth), FadeIn(never),
                      run_time=0.8, rate_func=rf.ease_out_sine)
        self.title = t5

        samples = [PARTS] + HANDFULS
        means = np.array([float(s.mean()) for s in samples])
        rows, marks = VGroup(), VGroup()
        for k, s in enumerate(samples):
            col = YELLOW if k == 0 else BLUE
            tag = "your 12 parts" if k == 0 else f"handful {k + 1}"
            # mono at 19pt runs ~0.15 scene units per character, so a 40-column
            # row is 6 units wide: any longer and it leaves the frame
            rows.add(gauge(f"{tag:<11} x̄ {s.mean():.3f}   s {s.std(ddof=1):.4f}",
                           19, col))
            marks.add(Dot(axes.c2p(float(s.mean()), 0.07), radius=0.07, color=col))
        rows.arrange(DOWN, buff=0.20, aligned_edge=LEFT)
        rows.move_to([0.35, 1.85, 0], aligned_edge=LEFT)

        with self.say("Your twelve parts only estimate them, and the estimate "
                      "is not the thing."):
            self.play(FadeIn(marks[0], scale=0.4), FadeIn(rows[0]),
                      run_time=0.9, rate_func=rf.ease_out_sine)

        spread_lab = gauge(f"five estimates, spread "
                           f"{(means.max() - means.min()) * 1000:.1f} µm",
                           21, YELLOW)
        spread_lab.next_to(rows, DOWN, buff=0.40, aligned_edge=LEFT)
        with self.say("Four more handfuls of twelve, off the same untouched "
                      "machine, land somewhere else every time.") as tr:
            self.play(LaggedStart(*[
                FadeIn(Group(marks[i], rows[i]), scale=0.6) for i in range(1, 5)],
                lag_ratio=0.7),
                run_time=max(2.0, tr.duration * 0.6), rate_func=rf.linear)
            self.play(FadeIn(spread_lab, shift=UP * 0.1),
                      run_time=0.8, rate_func=rf.ease_out_sine)

        bias = VGroup(
            micro("SAMPLE SPREAD, TWO DIVISORS", 18),
            gauge(f"n  {SIGMA:.4f}     n−1  {S_SAMPLE:.4f} mm", 21, INK),
        ).arrange(DOWN, buff=0.14)
        bias.next_to(axes, DOWN, buff=0.55)
        with self.say("It is also why a sample's spread divides by n minus one. "
                      "Twelve parts spread around their own mean sit a little "
                      "tighter than they do around the truth, so the smaller "
                      "divisor corrects for it."):
            self.play(FadeIn(bias, shift=UP * 0.1),
                      run_time=1.1, rate_func=rf.ease_out_sine)

        handoff = prose("every estimate carries uncertainty", 26, TEAL)
        handoff2 = MathTex(r"\text{Level 4 measures it: }",
                           r"\sigma_{\bar{x}} = \frac{\sigma}{\sqrt{n}}",
                           font_size=34, color=TEAL)
        VGroup(handoff, handoff2).arrange(DOWN, buff=0.28).move_to([2.4, -2.35, 0])
        with self.say("Every estimate carries uncertainty. Level 4 puts a "
                      "number on exactly how much."):
            self.play(FadeIn(handoff, shift=UP * 0.1), Write(handoff2),
                      run_time=1.4, rate_func=rf.ease_out_sine)

        self.beat(1.0)
