"""LEVEL 12 act — 'One factor at a time is not slow. It is wrong.'

Built 2026-10-07 against specs/l10-12-acts-contract.md ("after go": L12) and
the craft rules in specs/spc-manim-craft-contract.md.

- The level's worked example (spclab.experiments): shrinkage against hold
  pressure and melt temperature, coded −1/+1, lower is better, no noise.
- The response is a shaded map nobody gets to see. The setting is a pair of
  ValueTrackers; the dot and the live shrinkage readout are computed from them,
  so every number on screen is read off the map as the walk reaches it.
- The walk is spclab.experiments.ofat(): it stops at 8. The four corners are
  CORNERS; one of them, never visited, holds 6.
- The one camera move is the push onto that unvisited corner.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/spclab/level12_scene.py Level12
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level12_scene.py Level12
"""
from __future__ import annotations

import numpy as np
from manim import (
    Arrow, Dot, Group, MathTex, Square, ValueTracker, VGroup, VMobject,
    Circumscribe, Create, FadeIn, FadeOut, GrowArrow, Restore,
    always_redraw, interpolate_color, ManimColor,
    DOWN, LEFT, UP,
)
from manim.utils import rate_functions as rf

from spclab.act_style import (
    GREY, INK, RED, TEAL, YELLOW,
    at_panel, gauge, micro, prose, within_frame,
)
from spclab.experiments import B0, BA, BB, BAB, BASELINE, CORNERS, OPTIMUM, OPTIMUM_Y, PRECISION, ofat, response
from spclab.narration import NarratedCameraScene

OF = ofat()
CX, CY, HALF = -2.9, -0.4, 2.8      # the map: coded [-1.25, 1.25] on both axes
EXT = 1.25
CELLS = 56
LO, HI = ManimColor("#10161e"), ManimColor("#6f84a3")   # lighter = more shrinkage


def at(a: float, b: float) -> list[float]:
    return [CX + a / EXT * HALF, CY + b / EXT * HALF, 0]


def sign(v: int) -> str:
    return "+" if v > 0 else "−"


class Level12(NarratedCameraScene):
    def construct(self):
        self.a = ValueTracker(BASELINE[0])
        self.b = ValueTracker(BASELINE[1])
        self.runs = ValueTracker(0)
        self.part1_walk()
        self.part2_corners()

    # ---------------- the map ----------------------------------------------
    def build_map(self):
        side = 2 * HALF / CELLS
        g = np.linspace(-EXT, EXT, CELLS + 1)
        mids = (g[:-1] + g[1:]) / 2
        zs = [[response(a, b) for a in mids] for b in mids]
        z0, z1 = min(map(min, zs)), max(map(max, zs))
        cells = VGroup()
        for j, b in enumerate(mids):
            for i, a in enumerate(mids):
                t = (zs[j][i] - z0) / (z1 - z0)
                cells.add(Square(side * 1.02, stroke_width=0, fill_opacity=1,
                                 fill_color=interpolate_color(LO, HI, t)).move_to(at(a, b)))
        # iso-shrinkage lines: the surface is bilinear, so each level c is the
        # hyperbola b = (c − B0 − BA·a) / (BB + BAB·a); sampled, cut at the asymptote
        iso = VGroup()
        for c in (6, 8, 10, 12, 14, 16):
            run = []
            for a in np.linspace(-EXT, EXT, 400):
                den = BB + BAB * a
                b = (c - B0 - BA * a) / den if abs(den) > 1e-6 else 99
                if abs(b) <= EXT and (not run or np.sign(den) == run[-1][0]):
                    run.append((np.sign(den), at(a, b)))
                    continue
                if len(run) > 1:
                    iso.add(VMobject(stroke_color=GREY, stroke_width=1.2, stroke_opacity=0.55, fill_opacity=0)
                            .set_points_as_corners([q for _, q in run]))
                run = [(np.sign(den), at(a, b))] if abs(b) <= EXT else []
            if len(run) > 1:
                iso.add(VMobject(stroke_color=GREY, stroke_width=1.2, stroke_opacity=0.55, fill_opacity=0)
                        .set_points_as_corners([q for _, q in run]))
        ticks = VGroup()
        for v in (-1, 1):
            ticks.add(micro(f"{sign(v)}1", 14).move_to([at(v, 0)[0], CY - HALF - 0.28, 0]))
            ticks.add(micro(f"{sign(v)}1", 14).move_to([CX - HALF - 0.28, at(0, v)[1], 0]))
        xlab = micro("HOLD PRESSURE").move_to([CX, CY - HALF - 0.28, 0])
        ylab = micro("MELT TEMPERATURE").rotate(np.pi / 2).move_to([CX - HALF - 0.28, CY, 0])
        key = micro("LIGHTER = MORE SHRINKAGE", 13).move_to([CX, CY + HALF + 0.24, 0])
        for m in (xlab, ylab, key):
            within_frame(m, "map label")
        return dict(cells=cells, iso=iso, ticks=ticks, xlab=xlab, ylab=ylab, key=key)

    def here(self) -> float:
        return response(self.a.get_value(), self.b.get_value())

    def readouts(self):
        rows = [
            (micro("PRESSURE · TEMP"),
             lambda: gauge(f"{self.a.get_value():+.2f} · {self.b.get_value():+.2f}"
                           .replace("-", "−"), 24, INK)),
            (micro("SHRINKAGE"),
             lambda: gauge(f"{self.here():.1f}", 24, YELLOW)),
            (micro("RUNS"),
             lambda: gauge(f"{int(round(self.runs.get_value()))}", 24, INK)),
        ]
        out = []
        for i, (lab, val) in enumerate(rows):
            at_panel(lab, i, value=False)
            out += [lab, always_redraw(lambda val=val, i=i: at_panel(val(), i))]
        return out

    def reading(self, c, color=INK) -> VGroup:
        """The value at corner c, set just outside it, on a dark chip-free halo."""
        out = np.array(at(c[0] * 1.17, c[1] * 1.17))
        return gauge(f"{response(*c):.0f}", 30, color).move_to(out)

    def step(self, to, tr_duration, runs: int):
        self.play(self.a.animate.set_value(to[0]), self.b.animate.set_value(to[1]),
                  self.runs.animate.set_value(runs),
                  run_time=max(1.6, tr_duration * 0.5), rate_func=rf.ease_in_out_sine)

    # ---------------- part 1: the walk --------------------------------------
    def part1_walk(self):
        title = prose("Level 12 · Experiments", 30, GREY).to_edge(UP, buff=0.38)
        m = self.build_map()
        with self.say("A moulded part shrinks as it cools. Two settings decide how "
                      "much: hold pressure and melt temperature. Lower is better."):
            self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(m["xlab"]), FadeIn(m["ylab"]),
                      FadeIn(m["ticks"]), run_time=0.9, rate_func=rf.ease_out_sine)
            self.play(FadeIn(m["cells"], lag_ratio=0.0004), FadeIn(m["key"]), Create(m["iso"]),
                      run_time=2.0, rate_func=rf.ease_out_sine)

        with self.say("This map is the truth. Nobody gets to see it. All an engineer "
                      "can do is run the process at a setting and read one number."):
            self.play(m["cells"].animate.set_fill(opacity=0.45), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)

        dot = always_redraw(lambda: Dot(at(self.a.get_value(), self.b.get_value()),
                                        radius=0.11, color=INK))
        ro = self.readouts()
        start = self.reading(BASELINE)
        with self.say("Start where most people start: everything low. The part "
                      "shrinks sixteen."):
            self.play(FadeIn(dot, scale=1.6), *[FadeIn(x) for x in ro],
                      self.runs.animate.set_value(1), run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(FadeIn(start, shift=UP * 0.1), run_time=0.6, rate_func=rf.ease_out_sine)

        v = OF["visited"]  # (−1,−1), (−1,+1), (−1,+1), (+1,+1)
        arrows = []
        with self.say("One factor at a time. Hold the pressure, and try the "
                      "temperature high.") as tr:
            arr = Arrow(at(*v[0]), at(*v[1]), buff=0.2, color=RED, stroke_width=5)
            self.play(GrowArrow(arr), run_time=0.6, rate_func=rf.ease_out_sine)
            self.step(v[1], tr.duration, 2)
            arrows.append(arr)
        r2 = self.reading(v[1])
        with self.say("Eight. Better. Keep the high temperature."):
            self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.6, rate_func=rf.ease_out_sine)

        with self.say("Now hold that, and try the pressure high.") as tr:
            arr = Arrow(at(*v[2]), at(*v[3]), buff=0.2, color=RED, stroke_width=5)
            self.play(GrowArrow(arr), run_time=0.6, rate_func=rf.ease_out_sine)
            self.step(v[3], tr.duration, 3)
            arrows.append(arr)
        r3 = self.reading(v[3])
        with self.say("Ten. Worse. Go back.") as tr:
            self.play(FadeIn(r3, shift=UP * 0.1), run_time=0.6, rate_func=rf.ease_out_sine)
            self.step(OF["chosen"], tr.duration, 3)

        stop = prose(f"stops at {OF['chosen_y']:.0f}", 30, RED).move_to([1.9, 1.4, 0])
        with self.say("Three runs, every one of them measured perfectly, and the "
                      "procedure stops at eight. It looks finished."):
            self.play(FadeIn(stop, shift=UP * 0.12), Circumscribe(ro[3], color=RED, buff=0.08),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
        self.title, self.m, self.dot, self.ro = title, m, dot, ro
        self.readings, self.arrows, self.stop = [start, r2, r3], arrows, stop

    # ---------------- part 2: the corner it never visited --------------------
    def part2_corners(self):
        m = self.m
        missing = [c for c in CORNERS if c not in OF["visited"]][0]
        corner = Dot(at(*missing), radius=0.11, color=TEAL)
        self.camera.frame.save_state()
        with self.say("Look at the one corner it never ran: high pressure, low "
                      "temperature.") as tr:
            self.play(self.camera.frame.animate.scale(0.55).move_to([at(*missing)[0] - 0.4,
                                                                      at(*missing)[1] + 0.9, 0]),
                      run_time=max(1.6, tr.duration * 0.6), rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(corner, scale=1.6), run_time=0.6, rate_func=rf.ease_out_back)

        r4 = self.reading(missing, TEAL)
        with self.say("A design that runs all four corners finds it. Six."):
            self.play(Restore(self.camera.frame), run_time=1.2, rate_func=rf.ease_in_out_sine)
            self.play(self.a.animate.set_value(missing[0]), self.b.animate.set_value(missing[1]),
                      self.runs.animate.set_value(4),
                      run_time=1.6, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(r4, shift=UP * 0.1), m["cells"].animate.set_fill(opacity=1.0),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        found = prose(f"finds {OPTIMUM_Y:.0f}", 30, TEAL).next_to(self.stop, DOWN, buff=0.3)
        found.align_to(self.stop, LEFT)
        worse = round(100 * OF["shortfall"] / OPTIMUM_Y)
        with self.say(f"Four runs instead of three, and the answer one at a time "
                      f"gave is {worse} per cent worse. Noise had nothing to do with it."):
            self.play(FadeIn(found, shift=UP * 0.12), Circumscribe(r4, color=TEAL, buff=0.1),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)

        lo_p = response(-1, 1) - response(-1, -1)
        hi_p = response(1, 1) - response(1, -1)
        why = MathTex(rf"{lo_p:+.0f}".replace("-", "-"), r"\ne", rf"{hi_p:+.0f}",
                      font_size=48, color=INK).move_to([1.9, -0.9, 0])
        cap = VGroup(micro("WHAT TEMPERATURE DOES", 13),
                     micro("AT LOW · AT HIGH PRESSURE", 13)).arrange(DOWN, buff=0.1)
        cap.next_to(why, DOWN, buff=0.22)
        within_frame(cap, "interaction caption")
        with self.say("The reason is the interaction. Raising the temperature cuts "
                      "shrinkage by eight at low pressure, and adds four at high "
                      "pressure. What one factor does depends on the other, and a "
                      "walk that moves one at a time never sees that."):
            self.play(FadeIn(why, shift=UP * 0.12), FadeIn(cap),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        # hidden replication: every run sits in every estimate
        hi = [response(1, b) for b in (-1, 1)]
        lo = [response(-1, b) for b in (-1, 1)]
        eff = MathTex(r"A", "=", rf"\tfrac{{{hi[0]:.0f}+{hi[1]:.0f}}}{{2}}", "-",
                      rf"\tfrac{{{lo[0]:.0f}+{lo[1]:.0f}}}{{2}}", "=",
                      rf"{(sum(hi) - sum(lo)) / 2:+.0f}".replace("-", "-"),
                      font_size=36, color=INK).move_to([2.1, -0.9, 0])
        within_frame(eff, "effect")
        with self.say("The four corners buy something else as well. The effect of "
                      "pressure is the average of the high pressure runs, minus the "
                      "average of the low ones.") as tr:
            self.play(FadeOut(why, shift=UP * 0.12), FadeOut(cap), run_time=0.6,
                      rate_func=rf.ease_in_sine)
            self.play(FadeIn(eff, shift=UP * 0.12), run_time=1.0, rate_func=rf.ease_out_sine)
            self.play(Circumscribe(VGroup(r4, self.readings[2]), color=TEAL, buff=0.1),
                      Circumscribe(eff[2], color=TEAL, buff=0.06),
                      run_time=max(1.2, tr.duration * 0.25), rate_func=rf.ease_in_out_sine)
        with self.say("Every run is used in that estimate, and in the temperature "
                      "effect, and in the interaction. Nothing is spent on one "
                      "question alone.") as tr:
            self.play(Circumscribe(VGroup(*self.readings, r4), color=YELLOW, buff=0.12),
                      run_time=max(1.6, tr.duration * 0.5), rate_func=rf.ease_in_out_sine)
        prec = MathTex(rf"{PRECISION['factorial_sd']:.3f}", r"\;\text{vs}\;",
                       rf"{PRECISION['ofat_sd']:.3f}", font_size=40, color=INK)
        prec[0].set_color(TEAL)
        prec[2].set_color(RED)
        prec.next_to(eff, DOWN, buff=0.45)
        pcap = micro("SPREAD OF THE ESTIMATE · SAME RUNS", 13).next_to(prec, DOWN, buff=0.18)
        within_frame(pcap, "precision caption")
        with self.say(f"Add real measurement noise and spend {PRECISION['runs']} runs "
                      "either way. The factorial's estimate of the pressure effect "
                      f"is {PRECISION['ratio']:.1f} times steadier than the "
                      "one-at-a-time comparison it replaces."):
            self.play(FadeIn(prec, shift=UP * 0.12), FadeIn(pcap),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        verdict = prose("not slow: wrong", 34, YELLOW).move_to([1.9, 2.55, 0])
        within_frame(verdict, "verdict")
        with self.say("One factor at a time is not slow. It is wrong. Change the "
                      "factors together, and the design sees what they do together."):
            self.play(FadeOut(self.title, shift=UP * 0.12), run_time=0.5, rate_func=rf.ease_in_sine)
            self.play(FadeIn(verdict, shift=UP * 0.14), run_time=1.0, rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for mob in self.mobjects:
            mob.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7, rate_func=rf.ease_in_sine)
