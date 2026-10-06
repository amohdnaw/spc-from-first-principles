"""Find text that overlaps other text in a rendered act.

    PYTHONPATH=src .venv/bin/python tools/text_collisions.py level09_scene:Level09 [...]

A 12-frame contact sheet found "64" printed over "UCL" in Level 9 and axis
titles sitting on their own tick numbers in Levels 2 and 5. A sample only sees
the frames it lands on, so this runs the scene without writing video and, at
every wait() and after every play(), compares the bounding box of each visible
piece of text with every other. Exit status is the number of collisions.

It also samples every visible stroke (curves, lines, bars) and reports one
passing through a label's box: the see-saw over "SHAFT DIAMETER" in Level 3
and the zoomed curve through the Level 8 title were caught by eye, not by this.
A line meant to cross text (a strike-through) sets `crosses_text = True` on
each of its family members and is skipped.
"""
from __future__ import annotations

import importlib
import itertools
import sys
import tempfile

import numpy as np

from manim import (DecimalNumber, Integer, MathTex, Scene, SingleStringMathTex, VMobject,
                   VectorizedPoint,
                   Text, tempconfig)

TEXTY = (Text, MathTex, SingleStringMathTex, DecimalNumber, Integer)
MIN_AREA = 0.004   # square units; below this the boxes only kiss
# Levels 2 and 5 printed axis titles 0.06 units under their tick numbers: no
# overlap, yet on a phone they read as one smudge. Each box grows by PAD first.
PAD = 0.05


def visible(m) -> bool:
    fam = m.family_members_with_points()
    return bool(fam) and any(f.get_fill_opacity() > 0.05 or f.get_stroke_opacity() > 0.05
                             for f in fam)


def leaves(scene) -> list:
    """Outermost text mobjects on screen: a MathTex's own sub-tex is not separate text."""
    out, seen = [], set()

    def walk(m):
        if id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, TEXTY):
            if visible(m):
                out.append(m)
            return
        for s in m.submobjects:
            walk(s)
    for m in scene.mobjects:
        walk(m)
    return out


def spread(m) -> bool:
    """A curve filled by always_redraw + become() keeps the VectorizedPoint class:
    skipping the class left those curves unchecked, so keep any that has extent."""
    return len(m.points) > 1 and float(np.ptp(m.points[:, :2], axis=0).max()) > 0.01


def strokes(scene, texts) -> list:
    """Visible non-text leaf shapes, i.e. whatever is drawn that is not a label."""
    inside = {id(f) for t in texts for f in t.get_family()}
    return [f for m in scene.mobjects for f in m.family_members_with_points()
            if isinstance(f, VMobject) and (not isinstance(f, VectorizedPoint) or spread(f))
            and id(f) not in inside and not f.submobjects
            and not getattr(f, "crosses_text", False)
            and f.get_stroke_opacity() > 0.05 and f.get_stroke_width() > 0]


T = np.linspace(0, 1, 9)
BEZ = np.stack([(1 - T) ** 3, 3 * (1 - T) ** 2 * T, 3 * (1 - T) * T ** 2, T ** 3], 1)


def samples(m) -> np.ndarray:
    pts = m.points[: len(m.points) // 4 * 4].reshape(-1, 4, 3)
    return np.einsum("tk,ckd->ctd", BEZ, pts).reshape(-1, 3)


def box(m):
    (x0, y0, _), (x1, y1, _) = m.get_corner([-1, -1, 0]), m.get_corner([1, 1, 0])
    return x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD


def name(m) -> str:
    s = getattr(m, "text", None) or getattr(m, "tex_string", None)
    if s is None and hasattr(m, "get_value"):
        s = f"{m.get_value():g}"
    return " ".join(str(s or type(m).__name__).split())[:40]


def check(scene, found: dict):
    for a, b in itertools.combinations(leaves(scene), 2):
        ax0, ay0, ax1, ay1 = box(a)
        bx0, by0, bx1, by1 = box(b)
        w, h = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
        if w > 0 and h > 0 and w * h > MIN_AREA:
            key = tuple(sorted((name(a), name(b))))
            found.setdefault(key, round(scene.renderer.time, 1))
    texts = leaves(scene)
    for st in strokes(scene, texts):
        p = samples(st)
        if not len(p):
            continue
        for t in texts:
            x0, y0, x1, y1 = box(t)
            if np.any((p[:, 0] > x0) & (p[:, 0] < x1) & (p[:, 1] > y0) & (p[:, 1] < y1)):
                found.setdefault((f"<{type(st).__name__}>", name(t)), round(scene.renderer.time, 1))


def run(spec: str) -> dict:
    mod, klass = spec.split(":")
    cls = getattr(importlib.import_module(f"spclab.{mod}" if "." not in mod else mod), klass)
    found: dict = {}
    wait, play = Scene.wait, Scene.play

    def w(self, *a, **k):
        check(self, found)
        return wait(self, *a, **k)

    def p(self, *a, **k):
        r = play(self, *a, **k)
        check(self, found)
        return r
    Scene.wait, Scene.play = w, p
    try:
        # own media dir: sharing media/texts with a running render raced on its svgs
        with tempconfig({"media_dir": tempfile.mkdtemp(prefix="collisions-"), "dry_run": True, "quality": "low_quality", "disable_caching": True,
                         "verbosity": "ERROR", "progress_bar": "none"}):
            cls().render()
    finally:
        Scene.wait, Scene.play = wait, play
    return found


if __name__ == "__main__":
    total = 0
    for spec in sys.argv[1:]:
        hits = run(spec)
        total += len(hits)
        print(f"{spec}: {len(hits)} collision(s)")
        for (a, b), t in sorted(hits.items(), key=lambda kv: kv[1]):
            print(f"   t={t:6.1f}s  {a!r}  x  {b!r}")
    sys.exit(min(total, 99))
