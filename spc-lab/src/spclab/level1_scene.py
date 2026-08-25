"""LEVEL 1 act — 'Variation is predictable.'

    .venv/bin/manim -qh src/spclab/level1_scene.py Level1
"""
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Text, VGroup, Group, Rectangle, DashedLine,
    Create, Write, FadeIn, Unwrite, GrowFromEdge, LaggedStart, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = "#8a939f"

config.background_color = BG


class Level1(Scene):
    def construct(self):
        self.part1_dice()
        self.part2_sqrtn()

    # ------------------------------------------------ part 1: dice -> bell
    def part1_dice(self):
        rng = np.random.default_rng(4)
        t = Text("Level 1 · One part is noise. Many parts are information.",
                 font_size=28, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[0.5, 6.5, 1], y_range=[0, 0.45, 0.2],
                    x_length=10, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.4)
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

        batches = [(1, 0.05), (9, 0.25), (90, 0.5), (900, 0.8), (9000, 1.2)]
        for n_batch, rt in batches:
            new = rng.integers(1, 7, size=n_batch)
            for v in new:
                counts[v - 1] += 1
            for i in range(6):
                place(i)
            counter.set_text(f"rolls so far: {int(sum(counts)):,}")
            self.wait(rt)

        bell_lab = Text("the pile stops being random", font_size=24,
                        slant=ITALIC, color=TEAL).next_to(counter, UP, buff=0.25)
        self.play(Write(bell_lab), run_time=0.9)
        self.wait(1.2)

        everything = Group(t, axes, bars, counter, bell_lab)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # -------------------------------------------- part 2: sigma/sqrt(n)
    def part2_sqrtn(self):
        sig = 1.0
        t = Text("…and averaging shrinks uncertainty by √n",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[1, 25, 4], y_range=[0, 1.05, 0.25],
                    x_length=9.5, y_length=4.4, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        xl = axes.get_axis_labels(Text("subgroup size n", font_size=22),
                                  Text("σ of the mean", font_size=22))
        curve = axes.plot(lambda x: sig / np.sqrt(x), x_range=[1, 25],
                          color=BLUE, stroke_width=3)
        self.play(Create(axes), FadeIn(xl), run_time=0.8)
        self.play(Create(curve), run_time=1.2)

        formula = Text("σx̄ = σ / √n", font_size=40, color=YELLOW)
        formula.to_edge(RIGHT, buff=0.9).shift(UP * 1.2)
        self.play(Write(formula), run_time=1)

        # drop markers at n = 1, 4, 9 showing halving pattern
        for n in (1, 4, 9, 16):
            d = Dot(axes.c2p(n, sig / np.sqrt(n)), radius=0.06, color=YELLOW)
            lab = Text(f"n={n} → σ/√{n if n>1 else 1} = {sig/np.sqrt(n):.2f}",
                       font_size=18, color=YELLOW)
            lab.next_to(d, DOWN, buff=0.15)
            self.play(FadeIn(d, scale=0.4), FadeIn(lab), run_time=0.45)
        self.wait(0.8)

        payoff = Text("this one line is why control charts watch means",
                      font_size=26, slant=ITALIC, color=TEAL
                      ).to_edge(DOWN, buff=0.4)
        self.play(Write(payoff), run_time=1)
        self.wait(1.6)
