"""The site's type on the static figures.

The pages set prose in Libron and labels in IBM Plex Mono; the figures were
DejaVu Serif with a suptitle that repeated the figcaption beneath it. apply()
loads the same faces (TTF copies in ~/.local/share/fonts/spclab, beside the ones
the Manim scenes use) and finish() runs at save time: it drops the suptitle and
sets each panel title as a mono micro-label, the way the pages label a panel.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.text import Text

FONTS = Path.home() / ".local/share/fonts/spclab"
MONO = ["IBM Plex Mono", "DejaVu Sans Mono"]
MUTED = "#8a939f"


def apply():
    for f in FONTS.glob("*.ttf"):
        font_manager.fontManager.addfont(str(f))
    mpl.rcParams.update({
        # a list, not "serif": only a list falls back per glyph (Libron has no σ or ⇒)
        "font.family": ["Libron", "EB Garamond", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "axes.titlepad": 16,  # data labels at the top of a plot ran into the title
        "axes.labelsize": 12, "xtick.labelsize": 10, "ytick.labelsize": 10,
    })
    for k in ("xtick", "ytick"):
        mpl.rcParams[f"{k}.labelcolor"] = MUTED


def label_case(s: str) -> str:
    """Upper-case the prose of a title, never its math ($...$ is TeX) and never
    Greek (upper() turns σ into Σ)."""
    parts = s.split("$")
    return "$".join(p if i % 2 or any("\u0370" <= c <= "\u03ff" for c in p) else p.upper()
                    for i, p in enumerate(parts))


def finish(fig):
    if fig._suptitle is not None:
        print("dropped suptitle:", " ".join(fig._suptitle.get_text().split()))
        fig._suptitle.remove()
        fig._suptitle = None
    for ax in fig.axes:
        for t in (ax.title, ax._left_title, ax._right_title):
            if t.get_text():
                t.set_text(label_case(t.get_text()))
                t.set_fontfamily(MONO)
                t.set_fontsize(10.5)
                t.set_color(MUTED)
                t.set_fontweight(600)
        ax.tick_params(labelfontfamily=MONO)
    for a, b in collisions(fig):
        print(f"COLLISION: {a!r} x {b!r}")


def collisions(fig, pad=1.0) -> list[tuple[str, str]]:
    """Pairs of visible texts whose drawn boxes overlap (pixels, after layout).
    A sheet restyle changes every metric at once; this is the check that it fits."""
    r = fig.canvas.get_renderer()
    fig.draw(r)
    # findobj also returns tick labels outside the view limits, never drawn
    ticks, drawn = set(), set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                ticks |= {id(tk.label1), id(tk.label2)}
            if not (ax.axison and axis.get_visible()):
                continue
            for tk in axis._update_ticks():
                drawn |= {id(tk.label1), id(tk.label2)}
    boxes = []
    for t in fig.findobj(Text):
        if id(t) in ticks and id(t) not in drawn:
            continue
        if t.get_visible() and t.get_text().strip() and t.get_alpha() != 0:
            b = Text.get_window_extent(t, r)  # an Annotation's own extent includes its arrow
            if b.width > 0 and b.height > 0:
                boxes.append((" ".join(t.get_text().split())[:40], b.expanded(1, 1).padded(-pad)))
    return [(a, b) for (a, ba), (b, bb) in itertools.combinations(boxes, 2) if ba.overlaps(bb)]
