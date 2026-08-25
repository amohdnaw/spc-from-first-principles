"""LEVEL 1 act — 'Variation is predictable.'

One part is unpredictable. The average of many parts obeys a law, and the law
has a number in it: σx̄ = σ/√n. The spreads annotated on screen are measured
from the simulation, not drawn by hand.

Pacing lives in the narration script: every beat is held for as long as its
line takes to speak, whether or not the audio is rendered. See narration.py.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level1_scene.py Level1
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level1_scene.py Level1
"""
import numpy as np
from manim import (
    Axes, Dot, Text, VGroup, Group, Rectangle, DashedLine,
    Create, Write, FadeIn, FadeTransform, ITALIC,
    UP, DOWN, RIGHT, config,
)

from spclab.narration import NarratedScene

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


def dice_bins(k, max_bars=55):
    """Bin edges aligned to the 1/k lattice the average of k dice can land on.

    Averages of k dice are discrete — multiples of 1/k. Bins that straddle that
    lattice unevenly put a comb of false notches through the bell, so each bin
    here spans a whole number of lattice steps.
    """
    if k == 1:
        return np.arange(0.5, 7.5, 1.0)
    step = 1.0 / k
    step *= max(1, int(np.ceil(5.0 / (max_bars * step))))
    return np.arange(1.0 - step / 2, 6.0 + step, step)


def hist_bars(axes, values, bins, color):
    """Density histogram of `values` as bars sitting on the x-axis of `axes`."""
    dens, edges = np.histogram(values, bins=bins, density=True)
    peak = dens.max()
    if peak > 0:
        dens = dens / peak
    bars = VGroup()
    for d, lo, hi in zip(dens, edges[:-1], edges[1:]):
        left, right = axes.c2p(lo, 0), axes.c2p(hi, 0)
        top = axes.c2p(lo, max(float(d), 0.004))
        bar = Rectangle(width=(right[0] - left[0]) * 0.94,
                        height=max(top[1] - left[1], 0.02),
                        stroke_width=0, fill_color=color, fill_opacity=0.85)
        bar.move_to((left + right) / 2, aligned_edge=DOWN)
        bars.add(bar)
    return bars


class Level1(NarratedScene):
    def construct(self):
        self.part1_dice()
        self.part2_averaging()
        self.part3_sqrtn()

    # ------------------------------------------------ part 1: dice -> bell
    def part1_dice(self):
        rng = np.random.default_rng(4)
        t = Text("Level 1 · One part is noise. Many parts are information.",
                 font_size=28, color=GREY).to_edge(UP, buff=0.4)
        axes = Axes(x_range=[0.5, 6.5, 1], y_range=[0, 0.45, 0.2],
                    x_length=10, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.4)
        with self.say("One part is noise. Many parts are information. Six faces, "
                      "all equally likely."):
            self.play(FadeIn(t))
            self.play(Create(axes), run_time=0.7)

        # histogram bars grow as rolls accumulate (6 faces)
        counts = np.zeros(6)
        bars = VGroup(*[
            Rectangle(stroke_width=0, fill_color=BLUE, fill_opacity=0.8)
            for _ in range(6)
        ])
        width = axes.x_length / 6

        def place(i):
            h = counts[i] / counts.max() * 3.9 if counts.max() else 0.001
            bars[i].stretch_to_fit_width(width * 0.92)
            bars[i].stretch_to_fit_height(max(h, 0.01))
            bars[i].move_to(axes.c2p(i + 1, 0), aligned_edge=UP)

        for i in range(6):
            place(i); self.add(bars[i])

        counter = Text("", font_size=26, color=YELLOW).to_edge(DOWN, buff=0.4)
        self.add(counter)

        batches = [
            (1, "One roll. It tells you nothing."),
            (9, "Ten rolls. Still lumpy."),
            (90, "A hundred. Evening out."),
            (900, "A thousand. Nearly level."),
            (9000, "Ten thousand: flat, one sixth each."),
        ]
        for n_batch, line in batches:
            new = rng.integers(1, 7, size=n_batch)
            for v in new:
                counts[v - 1] += 1
            for i in range(6):
                place(i)
            counter.set_text(f"rolls so far: {int(sum(counts)):,}")
            with self.say(line):
                pass

        bell_lab = Text("the pile stops being random", font_size=24,
                        slant=ITALIC, color=TEAL).next_to(counter, UP, buff=0.25)
        with self.say("Predictable in bulk. Still flat, still one die at a time."):
            self.play(Write(bell_lab), run_time=0.9)

        everything = Group(t, axes, bars, counter, bell_lab)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # ------------------------------- part 2: averaging k dice -> the bell
    def part2_averaging(self):
        rng = np.random.default_rng(0)
        rolls = rng.integers(1, 7, size=(60_000, 30))
        sd1 = float(rolls[:, 0].std())

        t = Text("…now average the dice instead of counting them",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        axes = Axes(x_range=[0.5, 6.5, 1], y_range=[0, 1.05, 0.25],
                    x_length=10, y_length=4.0, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.5)
        centre = DashedLine(axes.c2p(3.5, 0), axes.c2p(3.5, 1.05),
                            stroke_color=GREY, stroke_width=1.5,
                            dash_length=0.12)

        panels = [
            (1, BLUE, "one roll — uniform chaos",
             "Now average the dice instead of counting them. One die is the "
             "baseline."),
            (2, TEAL, "average of 2 — edges melting",
             "Average two, and the flat top is gone."),
            (5, TEAL, "average of 5 — a shape appears",
             "Average five: a shape where there was none."),
            (30, TEAL, "average of 30 — a law, not a guess",
             "Thirty dice, and it is a bell."),
        ]

        bars = lab = cap = None
        for k, colour, title, line in panels:
            values = rolls[:, 0] if k == 1 else rolls[:, :k].mean(axis=1)
            new_bars = hist_bars(axes, values, dice_bins(k), colour)
            new_lab = Text(title, font_size=24, slant=ITALIC, color=colour
                           ).next_to(axes, UP, buff=0.18)
            meas = float(values.std())
            cap_txt = (f"measured σ = {meas:.3f}" if k == 1 else
                       f"measured σ = {meas:.3f}   ·   σ/√{k} = {sd1/np.sqrt(k):.3f}")
            new_cap = Text(cap_txt, font_size=24, color=YELLOW
                           ).to_edge(DOWN, buff=0.35)

            with self.say(line):
                if bars is None:
                    self.play(FadeIn(t), Create(axes), FadeIn(centre), run_time=0.8)
                    self.play(FadeIn(new_bars, shift=UP * 0.2), FadeIn(new_lab),
                              FadeIn(new_cap), run_time=0.9)
                else:
                    self.play(FadeTransform(bars, new_bars),
                              FadeTransform(lab, new_lab),
                              FadeTransform(cap, new_cap), run_time=1.1)
            bars, lab, cap = new_bars, new_lab, new_cap

        with self.say("Those spreads are measured, not drawn: one die's spread "
                      "over the square root of the count."):
            self.play(cap.animate.scale(1.18).set_color(YELLOW), run_time=0.8)

        self.beat(0.6)

        everything = Group(t, axes, centre, bars, lab, cap)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # -------------------------------------------- part 3: sigma/sqrt(n)
    def part3_sqrtn(self):
        sig = 1.0
        t = Text("…and averaging shrinks uncertainty by √n",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        axes = Axes(x_range=[1, 25, 4], y_range=[0, 1.05, 0.25],
                    x_length=9.5, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        xl = axes.get_axis_labels(Text("subgroup size n", font_size=22),
                                  Text("σ of the mean", font_size=22))
        with self.say("Subgroup size across the bottom, spread of the mean going "
                      "up."):
            self.play(FadeIn(t))
            self.play(Create(axes), FadeIn(xl), run_time=0.8)

        curve = axes.plot(lambda x: sig / np.sqrt(x), x_range=[1, 25],
                          color=BLUE, stroke_width=3)
        formula = Text("σx̄ = σ / √n", font_size=40, color=YELLOW)
        formula.to_edge(RIGHT, buff=0.9).shift(UP * 1.2)
        with self.say("Sigma of x bar equals sigma over root n."):
            self.play(Create(curve), run_time=1.2)
            self.play(Write(formula), run_time=1)

        # drop markers at n = 1, 4, 9 showing halving pattern
        with self.say("Four parts halve it. Nine, a third. Sixteen, a quarter."):
            for n in (1, 4, 9, 16):
                d = Dot(axes.c2p(n, sig / np.sqrt(n)), radius=0.06, color=YELLOW)
                lab = Text(f"n={n} → σ/√{n if n>1 else 1} = {sig/np.sqrt(n):.2f}",
                           font_size=18, color=YELLOW)
                lab.next_to(d, DOWN, buff=0.15)
                self.play(FadeIn(d, scale=0.4), FadeIn(lab), run_time=0.45)

        payoff = Text("this one line is why control charts watch means",
                      font_size=26, slant=ITALIC, color=TEAL
                      ).to_edge(DOWN, buff=0.4)
        with self.say("This is why charts watch subgroup means: a shift moves a "
                      "mean visibly, and drowns in single parts."):
            self.play(Write(payoff), run_time=1)

        self.beat(1.0)
