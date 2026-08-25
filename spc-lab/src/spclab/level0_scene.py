"""LEVEL 0 act — 'What a measurement is.'

The prerequisite the curriculum was missing. Level 1 opens with "variation is
predictable", which already assumes the viewer owns a mean, a standard
deviation and a distribution. This act supplies exactly those and stops: no
control limits, no subgroups, no charts. It ends by handing the one open
question — how far a sample estimate can sit from the truth — to Level 1.

Pacing lives in the narration script: every beat is held for as long as its
line takes to speak, whether or not the audio is rendered. See narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level0_scene.py Level0
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level0_scene.py Level0
"""
import numpy as np
from manim import (
    Axes, Dot, Line, DashedLine, Polygon, Rectangle, Square,
    Text, VGroup, Group,
    Create, Write, FadeIn, FadeOut, Transform, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

from spclab.narration import NarratedScene

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG

# ---------------------------------------------------------------------------
# The data. Seeded once at import, so every number on screen is a real
# computed value and the same render twice gives the same frames.
# A shaft turned to 12.000 mm nominal, gauge resolution 0.001 mm.
# ---------------------------------------------------------------------------
NOMINAL    = 12.000
TRUE_SIGMA = 0.020

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


class ValueLine(VGroup):
    """A bare horizontal value axis — line, ticks, Text labels, no LaTeX."""

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
            lab = Text(fmt.format(v), font_size=20, color=GREY)
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


class Level0(NarratedScene):
    def construct(self):
        self.part1_parts_vary()
        self.part2_balance_point()
        self.part3_squaring()
        self.part4_the_shape()
        self.part5_sample_is_not_population()

    # ------------------------------------------- 1: nominally identical parts
    def part1_parts_vary(self):
        self.title = Text("Level 0 · Twelve identical parts, twelve numbers",
                          font_size=30, color=GREY).to_edge(UP, buff=0.4)

        vline = ValueLine(X_LO, X_HI, TICKS).shift(DOWN * 1.35)
        xlab = Text("shaft diameter (mm) · nominal 12.000", font_size=22,
                    color=GREY).next_to(vline, DOWN, buff=0.30)
        with self.say("Take twelve parts off one machine. Same tool, same gauge."):
            self.play(FadeIn(self.title))
            self.play(Create(vline.line), FadeIn(xlab), run_time=0.7)
            self.play(FadeIn(VGroup(*vline[1:])), run_time=0.6)

        self.dots = VGroup(*[
            Dot(vline.n2p(v) + UP * (0.30 + 0.24 * k), radius=0.075, color=BLUE)
            for v, k in zip(PARTS, strip_levels(PARTS))
        ])
        with self.say("Every reading is different. Nothing is broken."):
            for d in self.dots:
                self.play(FadeIn(d, scale=0.4), run_time=0.16)

        top = self.dots.get_top()[1] + 0.35
        span = Line(np.array([vline.n2p(PARTS.min())[0], top, 0.0]),
                    np.array([vline.n2p(PARTS.max())[0], top, 0.0]),
                    stroke_color=YELLOW, stroke_width=2.5)
        span_lab = Text(f"{PARTS.min():.3f} … {PARTS.max():.3f}   "
                        f"(spread {PARTS.max() - PARTS.min():.3f} mm)",
                        font_size=22, color=YELLOW).next_to(span, UP, buff=0.14)
        note = Text("not a defect — this is what every process does",
                    font_size=24, slant=ITALIC, color=TEAL).to_edge(UP, buff=1.15)
        with self.say("Spread is not a defect. It is what every real process does."):
            self.play(Create(span), FadeIn(span_lab), run_time=0.8)
            self.play(Write(note), run_time=1.0)

        self.vline, self.xlab = vline, xlab
        self.p1_extra = Group(span, span_lab, note)

    # ------------------------------------------------- 2: the balance point
    def part2_balance_point(self):
        vline, dots = self.vline, self.dots
        t2 = Text("Level 0 · The mean is the balance point",
                  font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Twelve numbers is not an answer. You need one number "
                      "for the centre."):
            self.play(FadeOut(self.p1_extra), run_time=0.5)
            self.play(Transform(self.title, t2), run_time=0.7)

        mp = vline.n2p(MEAN)
        mean_line = DashedLine(mp + DOWN * 0.06, mp + UP * 1.75,
                               stroke_color=YELLOW, stroke_width=3,
                               dash_length=0.12)
        mean_lab = Text(f"x̄ = {MEAN:.3f} mm", font_size=30,
                        color=YELLOW).next_to(mean_line, UP, buff=0.14)
        fulcrum = Polygon(mp + DOWN * 0.04,
                          mp + DOWN * 0.44 + LEFT * 0.26,
                          mp + DOWN * 0.44 + RIGHT * 0.26,
                          fill_color=YELLOW, fill_opacity=0.9, stroke_width=0)
        with self.say("The mean is the balance point of the measurements."):
            self.play(Create(mean_line), FadeIn(fulcrum), run_time=0.8)
            self.play(Write(mean_lab), run_time=0.9)

        # every deviation drawn as a horizontal reach back to the mean
        devs = VGroup()
        for d, v in zip(dots, PARTS):
            end = np.array([mp[0], d.get_center()[1], 0.0])
            devs.add(Line(d.get_center(), end,
                          stroke_color=TEAL if v > MEAN else RED,
                          stroke_width=3.5))

        pos_lab = Text(f"above x̄:  {POS:+.4f} mm", font_size=25, color=TEAL)
        neg_lab = Text(f"below x̄:  {NEG:+.4f} mm", font_size=25, color=RED)
        sum_lab = Text("sum of deviations = 0.0000 mm", font_size=28, color=YELLOW)
        stats = VGroup(pos_lab, neg_lab, sum_lab).arrange(DOWN, buff=0.18,
                                                         aligned_edge=LEFT)
        stats.to_edge(LEFT, buff=0.7).shift(UP * 1.75)

        with self.say("The deviations above the mean add to plus zero point "
                      "zero six two five."):
            self.play(FadeIn(devs), run_time=0.9)
            self.play(Write(pos_lab), run_time=0.8)

        with self.say("Below it, the same amount with the opposite sign. "
                      "The sum is exactly zero."):
            self.play(Write(neg_lab), run_time=0.8)
            self.play(Write(sum_lab), run_time=1.0)

        self.beat(0.7)
        self.p2_all = Group(vline, self.xlab, dots, devs, mean_line, mean_lab,
                            fulcrum, stats)

    # ------------------------------------------------- 3: why spread squares
    def part3_squaring(self):
        t3 = Text("Level 0 · Spread has to be squared first",
                  font_size=30, color=GREY).to_edge(UP, buff=0.4)
        with self.say("Now spread. Averaging the deviations is useless, "
                      "they cancel by construction."):
            self.play(self.p2_all.animate.scale(0.001).set_opacity(0),
                      run_time=0.6)
            self.remove(self.p2_all)
            self.play(Transform(self.title, t3), run_time=0.7)
            dead_end = Text("average of the deviations = 0.0000 mm\n"
                            "→ zero, every time, for every data set",
                            font_size=28, color=RED, line_spacing=0.9)
            self.play(Write(dead_end), run_time=1.5)

        K = 48.0  # mm of deviation → scene units; biggest square ≈ 1.4 units
        squares = VGroup()
        for i in np.argsort(-np.abs(DEV)):
            col = TEAL if DEV[i] > 0 else RED
            squares.add(Square(side_length=max(abs(DEV[i]) * K, 0.07),
                               fill_color=col, fill_opacity=0.35,
                               stroke_color=col, stroke_width=2))
        squares.arrange(RIGHT, buff=0.10, aligned_edge=DOWN)
        squares.move_to(np.array([-2.6, -1.75, 0.0]), aligned_edge=DOWN)
        base = Line(squares.get_left() + LEFT * 0.3,
                    squares.get_right() + RIGHT * 0.3,
                    stroke_color=GREY, stroke_width=2)
        base.next_to(squares, DOWN, buff=0.0)
        side_note = Text("each square: side = |x - x̄|,  area = (x - x̄)²",
                         font_size=22, color=GREY).next_to(base, DOWN, buff=0.22)

        with self.say("Square each one. Negatives turn positive and the "
                      "cancelling stops."):
            self.play(FadeOut(dead_end), run_time=0.4)
            self.play(Create(base), FadeIn(side_note), run_time=0.6)
            self.play(FadeIn(squares, shift=UP * 0.25), run_time=1.1)
            self.play(*[s.animate.set_fill(BLUE).set_stroke(BLUE)
                        for s in squares], run_time=0.9)

        var_lab = Text(f"mean of the squares = {VAR:.6f} mm²",
                       font_size=28, color=BLUE)
        sig_lab = Text(f"σ = √{VAR:.6f} = {SIGMA:.4f} mm",
                       font_size=32, color=YELLOW)
        VGroup(var_lab, sig_lab).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        VGroup(var_lab, sig_lab).to_edge(UP, buff=1.15)

        with self.say("Average the squares. That is the variance, "
                      "in millimetres squared."):
            self.play(Write(var_lab), run_time=1.1)

        avg_sq = Square(side_length=SIGMA * K, fill_color=YELLOW,
                        fill_opacity=0.35, stroke_color=YELLOW, stroke_width=2.5)
        avg_sq.next_to(squares, RIGHT, buff=0.9, aligned_edge=DOWN)
        avg_lab = Text("the average square\nits side is σ", font_size=22,
                       color=YELLOW, line_spacing=0.8)
        avg_lab.next_to(avg_sq, UP, buff=0.25)
        with self.say("Take the root and you are back in millimetres. "
                      "That is sigma."):
            self.play(FadeIn(avg_sq, shift=UP * 0.2), FadeIn(avg_lab),
                      run_time=0.9)
            self.play(Write(sig_lab), run_time=1.0)

        self.beat(0.7)
        self.p3_all = Group(squares, base, side_note, var_lab, sig_lab,
                            avg_sq, avg_lab)

    # ------------------------------------------------ 4: the shape emerges
    def part4_the_shape(self):
        t4 = Text("Level 0 · Many parts make a shape nobody chose",
                  font_size=30, color=GREY).to_edge(UP, buff=0.4)

        axes = Axes(x_range=[X_LO, X_HI, 0.02], y_range=[0, 1.08, 0.25],
                    x_length=10.4, y_length=3.9, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.75)
        xl = axes.get_axis_labels(Text("shaft diameter (mm)", font_size=20),
                                  Text("count", font_size=20))
        ticks = VGroup(*[
            Text(f"{v:.2f}", font_size=18, color=GREY)
            .next_to(axes.c2p(v, 0), DOWN, buff=0.16)
            for v in (11.94, 11.98, 12.02, 12.06)
        ])

        edges = np.linspace(X_LO, X_HI, 29)
        centres = (edges[:-1] + edges[1:]) / 2
        px_w = (axes.c2p(X_LO + (edges[1] - edges[0]), 0) - axes.c2p(X_LO, 0))[0]
        full = (axes.c2p(X_LO, 1.0) - axes.c2p(X_LO, 0.0))[1]

        bars = VGroup(*[
            Rectangle(width=px_w * 0.9, height=0.006, fill_color=BLUE,
                      fill_opacity=0.75, stroke_width=0)
            .move_to(axes.c2p(c, 0), aligned_edge=DOWN)
            for c in centres
        ])
        counter = Text("", font_size=28, color=YELLOW).to_edge(DOWN, buff=0.3)

        hist_rng = np.random.default_rng(11)
        counts = np.zeros(28)
        total = 0

        def grow(n_new, rt):
            nonlocal total, counts
            batch = np.round(hist_rng.normal(NOMINAL, TRUE_SIGMA, n_new), 3)
            counts = counts + np.histogram(batch, edges)[0]
            total += n_new
            mx = max(counts.max(), 1)
            anims = []
            for i, c in enumerate(counts):
                tgt = bars[i].copy()
                tgt.stretch_to_fit_height(max(c / mx, 0.0015) * full)
                tgt.move_to(axes.c2p(centres[i], 0), aligned_edge=DOWN)
                anims.append(Transform(bars[i], tgt))
            anims.append(Transform(counter,
                                   Text(f"{total:,} parts measured", font_size=28,
                                        color=YELLOW).to_edge(DOWN, buff=0.3)))
            self.play(*anims, run_time=rt)

        with self.say("Twelve parts say nothing about shape. Keep measuring."):
            self.play(self.p3_all.animate.scale(0.001).set_opacity(0),
                      run_time=0.6)
            self.remove(self.p3_all)
            self.play(Transform(self.title, t4), run_time=0.6)
            self.play(Create(axes), FadeIn(xl), FadeIn(ticks), run_time=0.8)
            self.add(bars, counter)
            grow(12, 0.5)

        with self.say("Sixty. Three hundred. Three thousand."):
            grow(48, 0.45)
            grow(240, 0.5)
            grow(2700, 0.7)

        with self.say("Twenty thousand parts, and a shape appears that "
                      "nobody chose."):
            grow(17000, 1.1)
            xs = np.linspace(X_LO, X_HI, 240)
            pdf = np.exp(-((xs - NOMINAL) ** 2) / (2 * TRUE_SIGMA ** 2))
            curve = axes.plot_line_graph(
                xs, pdf, add_vertex_dots=False,
                line_color=TEAL, stroke_width=3)["line_graph"]
            self.play(Create(curve), run_time=1.2)

        cause = Text("tool wear + temperature + material + clamping + gauge\n"
                     "→ the bell is a consequence, not an assumption",
                     font_size=24, color=TEAL, line_spacing=0.8)
        cause.to_edge(UP, buff=1.05)
        with self.say("Many small independent effects add up. The bell is a "
                      "consequence, not an assumption."):
            self.play(Write(cause), run_time=1.6)

        self.beat(0.7)
        self.p4_all = Group(axes, xl, ticks, bars, counter, curve, cause)

    # -------------------------------------- 5: a sample is not the population
    def part5_sample_is_not_population(self):
        t5 = Text("Level 0 · You never measure everything",
                  font_size=30, color=GREY).to_edge(UP, buff=0.4)
        axes = Axes(x_range=[11.94, 12.06, 0.02], y_range=[0, 1.15, 0.5],
                    x_length=6.8, y_length=3.2, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.55 + LEFT * 2.9)
        ticks = VGroup(*[
            Text(f"{v:.2f}", font_size=18, color=GREY)
            .next_to(axes.c2p(v, 0), DOWN, buff=0.16)
            for v in (11.96, 12.00, 12.04)
        ])
        curve = axes.plot(
            lambda x: np.exp(-((x - NOMINAL) ** 2) / (2 * TRUE_SIGMA ** 2)),
            x_range=[11.94, 12.06], color=TEAL, stroke_width=3)
        truth = Text(f"the process:  μ = {NOMINAL:.3f} mm    "
                     f"σ = {TRUE_SIGMA:.3f} mm", font_size=24, color=TEAL)
        truth.next_to(axes, UP, buff=0.30)
        never = Text("you never observe these two numbers", font_size=22,
                     slant=ITALIC, color=GREY).next_to(truth, UP, buff=0.14)

        with self.say("You never measure everything. The true mean and spread "
                      "belong to the process."):
            self.play(self.p4_all.animate.scale(0.001).set_opacity(0),
                      run_time=0.6)
            self.remove(self.p4_all)
            self.play(Transform(self.title, t5), run_time=0.6)
            self.play(Create(axes), FadeIn(ticks), Create(curve), run_time=1.0)
            self.play(FadeIn(truth), FadeIn(never), run_time=0.8)

        rows, marks = VGroup(), VGroup()
        for k, (sample, col) in enumerate([(PARTS, YELLOW)]
                                          + [(h, BLUE) for h in HANDFULS]):
            xb, sd = float(sample.mean()), float(sample.std(ddof=1))
            tag = "your 12 parts" if k == 0 else f"handful {k + 1}"
            rows.add(Text(f"{tag}:   x̄ = {xb:.3f}    s = {sd:.4f}",
                          font_size=22, color=col))
            marks.add(Dot(axes.c2p(xb, 0.07), radius=0.07, color=col))
        rows.arrange(DOWN, buff=0.20, aligned_edge=LEFT)
        rows.to_edge(RIGHT, buff=0.45).shift(UP * 1.25)

        with self.say("Your twelve parts only estimate them."):
            self.play(FadeIn(marks[0], scale=0.4), Write(rows[0]), run_time=0.8)

        with self.say("Four more handfuls of twelve land somewhere else "
                      "every time."):
            for i in range(1, 5):
                self.play(FadeIn(marks[i], scale=0.4), FadeIn(rows[i]),
                          run_time=0.45)

        bias = Text(f"s divides by n - 1, not n\n"
                    f"n:  {SIGMA:.4f} mm      n - 1:  {S_SAMPLE:.4f} mm",
                    font_size=22, color=YELLOW, line_spacing=0.8)
        bias.next_to(axes, DOWN, buff=0.55)
        with self.say("That is also why the sample spread divides by n minus one."):
            self.play(Write(bias), run_time=1.3)

        handoff = Text("every estimate carries uncertainty\n"
                       "Level 1 measures it:  σx̄ = σ / √n",
                       font_size=26, color=TEAL, line_spacing=0.9)
        handoff.next_to(rows, DOWN, buff=1.1).to_edge(RIGHT, buff=0.45)
        with self.say("Every estimate carries uncertainty. Level one puts "
                      "a number on it."):
            self.play(Write(handoff), run_time=1.4)

        self.beat(1.0)
