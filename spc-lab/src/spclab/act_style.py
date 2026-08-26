"""One place for how an act looks, so three acts cannot drift apart.

Everything here was settled in DESIGN.md and in the Manim craft contract
(`specs/spc-manim-craft-contract.md`); it is written down once because Level I,
II and III all have to obey it and a copied constant is a constant that rots.

Two voices, and every string in a render belongs to exactly one:

    prose()  EB Garamond   claims, hypotheses, verdicts — anything you read
    gauge()  IBM Plex Mono readouts, units, quantities — anything you measure
    micro()  IBM Plex Mono the label above a readout, written in caps at the
                           callsite (never .upper()'d — that turns σ into Σ)

Maths stays in Computer Modern via MathTex: mixing CM with Garamond prose is
the convention this curriculum follows, not a breach of the two-voice rule.

The fonts come from the repo's own woff2 via tools/install-fonts.py, so a
render's outlines are the outlines the website serves.
"""
from __future__ import annotations

import math

import numpy as np
from manim import LEFT, Text, config

# Sampled from the renders; the page's --ground matches it so video and page
# bleed into each other with no seam. Never re-pick these by eye.
BG     = "#0e1116"
BLUE   = "#58C4DD"   # raw material: single parts, single dice
TEAL   = "#5CD0B3"   # in control, the law, the region that behaves
YELLOW = "#FFD54F"   # limits and reference lines — wayfinding, never data
RED    = "#FC6255"   # the alarm, the tail, the leak
GREY   = "#8a939f"   # chrome: axes, titles, labels
INK    = "#e8e8e8"   # equations and neutral prose

SERIF = "EB Garamond"
MONO  = "IBM Plex Mono"

# Left edge of the readout column. Corners collide at 1920px, so the right one
# is reserved: nothing but the panel may be placed right of this.
PANEL = 4.15

# Panel rows, top to bottom: (label y, value y).
ROWS = ((2.95, 2.52), (1.92, 1.49), (0.89, 0.46))

config.background_color = BG


def prose(txt: str, size: float = 28, color: str = INK) -> Text:
    return Text(txt, font=SERIF, weight="MEDIUM", font_size=size, color=color)


def gauge(txt: str, size: float = 26, color: str = INK) -> Text:
    return Text(txt, font=MONO, font_size=size, color=color)


def micro(txt: str, size: float = 16, color: str = GREY) -> Text:
    return Text(txt, font=MONO, font_size=size, color=color)


def at_panel(mob: Text, row: int, value: bool = True) -> Text:
    """Left-align `mob` in the readout column, on `row` (0-2)."""
    return mob.move_to([PANEL, ROWS[row][1 if value else 0], 0], aligned_edge=LEFT)


def phi(x: float) -> float:
    """Standard normal density at x."""
    return math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi)


def norm_pdf(xs, mu=0.0, sg=1.0):
    return np.exp(-((xs - mu) ** 2) / (2 * sg ** 2)) / (sg * np.sqrt(2 * np.pi))


def inside(k: float) -> float:
    """Exact area within ±k σ: Φ(k) − Φ(−k) = erf(k/√2). Not a table lookup."""
    return math.erf(k / math.sqrt(2.0))
