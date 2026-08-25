"""LEVEL 4 act — 'Detection theory: charts as evidence accumulators.'

    .venv/bin/manim -qh src/spclab/level4_scene.py Level4
"""
import numpy as np
from manim import (
    Scene, Axes, Dot, Line, Text, VGroup, Group, Rectangle, DashedLine,
    Create, Write, FadeIn, ITALIC,
    UP, DOWN, RIGHT, LEFT, config,
)

BG     = "#0e1116"
BLUE   = "#58C4DD"
TEAL   = "#5CD0B3"
YELLOW = "#FFD54F"
RED    = "#FC6255"
GREY   = MUTED = "#8a939f"

config.background_color = BG

LAM = 0.2


class Level4(Scene):
    def construct(self):
        self.blind_spot()
        self.memory_wins()

    # ------- part 1: why single points can't see slow drift -------------
    def blind_spot(self):
        rng = np.random.default_rng(55)
        n, shift_at = 60, 20
        raw = rng.normal(0, 1, n) + np.where(
            np.arange(n) >= shift_at, (np.arange(n) - shift_at) * 0.15, 0)

        t = Text("Level 4 · The blind spot: drift hides inside noise",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[0, n, 10], y_range=[-3.6, 3.6, 1],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        for v in (-3, 3):
            ln = Line(axes.c2p(0, v), axes.c2p(n, v),
                      stroke_color=BLUE, stroke_width=1.6)
            self.play(Create(ln), run_time=0.35)
        cl = Line(axes.c2p(0, 0), axes.c2p(n, 0), stroke_color=GREY, stroke_width=2)
        self.play(Create(cl))

        dots = VGroup(*[
            Dot(axes.c2p(i + 1, min(v, 3.5)), radius=0.05,
                color=RED if abs(v) > 3 else BLUE)
            for i, v in enumerate(raw)
        ])
        for i in range(0, n, 10):
            self.play(FadeIn(dots[i:i + 10]), run_time=0.22)

        note = Text("drift starts at subgroup 20 (+0.15σ per step) —\n"
                    "yet no point breaches ±3σ for a long time",
                    font_size=24, color=MUTED).to_edge(DOWN, buff=0.42)
        self.play(Write(note), run_time=1)
        self.wait(1.6)

        everything = Group(t, axes, cl, dots, note)
        self.play(everything.animate.scale(0.001).set_opacity(0), run_time=0.5)
        self.remove(everything)

    # ------- part 2: EWMA accumulates evidence and wins ------------------
    def memory_wins(self):
        rng = np.random.default_rng(55)
        n, shift_at = 60, 20
        raw = rng.normal(0, 1, n) + np.where(
            np.arange(n) >= shift_at, (np.arange(n) - shift_at) * 0.15, 0)
        z, zs = 0.0, []
        for x in raw:
            z = LAM * x + (1 - LAM) * z
            zs.append(z)
        zs = np.array(zs)
        lim = 3 * np.sqrt(LAM / (2 - LAM))
        det_e = next(i for i, v in enumerate(zs) if abs(v) > lim)

        t = Text("…but a chart with memory accumulates evidence",
                 font_size=30, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(t))

        axes = Axes(x_range=[0, n, 10], y_range=[-3.6, 3.6, 1],
                    x_length=10.5, y_length=4.3, tips=False,
                    axis_config={"stroke_color": GREY, "stroke_width": 1.5}
                    ).shift(DOWN * 0.35)
        for v in (lim, -lim):
            ln = Line(axes.c2p(0, v), axes.c2p(n, v),
                      stroke_color=YELLOW, stroke_width=1.8)
            lab = Text("EWMA limit", font_size=18, color=YELLOW)
            lab.next_to(ln, RIGHT, buff=0.12)
            self.play(Create(ln), FadeIn(lab), run_time=0.35)
        cl = Line(axes.c2p(0, 0), axes.c2p(n, 0), stroke_color=GREY, stroke_width=2)
        self.play(Create(cl))

        # faded raw points underneath
        ghost = VGroup(*[
            Dot(axes.c2p(i + 1, min(v, 3.5)), radius=0.03, color=BLUE,
                fill_opacity=0.3)
            for i, v in enumerate(raw)
        ])
        self.play(FadeIn(ghost), run_time=0.5)

        pts = VGroup()
        for i, v in enumerate(zs):
            col = RED if i <= det_e else TEAL
            col = YELLOW if i > det_e else col
            pts.add(Dot(axes.c2p(i + 1, max(-3.5, min(v, 3.5))),
                        radius=0.055, color=col))
        for i in range(0, n, 10):
            self.play(FadeIn(pts[i:i + 10]), run_time=0.22)

        ring = Dot(axes.c2p(det_e + 1, min(zs[det_e], 3.5)), radius=0.11,
                   color=YELLOW, fill_opacity=0)
        verdict = Text(f"evidence crosses the limit at subgroup {det_e+1} —\n"
                       f"while every raw point still sits inside ±3σ\n"
                       f"(ARL: ~4× faster detection of 1σ drift)",
                       font_size=24, color=YELLOW).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(ring), Write(verdict), run_time=1.2)
        self.wait(1.8)
