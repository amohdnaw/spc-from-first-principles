# DESIGN.md — SPC portfolio

Frozen 2026-08-25. Governs `index.html`, `line-of-sight.html` and every curriculum
level page. (`spc-from-first-principles.html` was absorbed into `index.html` and
deleted — see `specs/spc-landing-contract.md`.)

Picked from a 14-variant gallery. Winner is a synthesis:
**v13 (process control room HMI) skin on v14 (mathematical textbook) skeleton**,
with the readout-tile component from v03 (terminal).

## The one idea

The site is a **curriculum** (a document) about **process monitoring** (an instrument).
Two voices, and every element belongs to exactly one of them:

| Voice | Font | Owns |
|---|---|---|
| **Document** | EB Garamond | prose, headlines, deks, equations, figure captions, pull quotes |
| **Instrument** | IBM Plex Mono | labels, readouts, status, nav, panel headers, figure numbers, units |

If an element is neither reading nor measuring, it should not exist.

---

## 1. Palette — one accent

Ground and ink are sampled from the actual Manim renders, so figures and video
sit on the page with no visible seam. **Do not re-pick these by eye.**

```
--ground        #0d1114   exact Manim frame background — the page IS the render
--panel         #14181c   raised surface
--panel-high    #1b2026   input wells, table stripes
--rule          #2a3138   hairline borders
--rule-strong   #3d4650   emphasised borders
--ink-dim       #7d8b98   captions, secondary labels
--ink           #d7dee4   body text on ground
--ink-bright    #eef3f7   headlines, key numbers

--accent        #ffae00   THE one accent. Amber.
--accent-wash   rgba(255,174,0,0.14)
```

**Accent rule.** Amber is for *wayfinding only*: current nav item, interactive
controls, links, level numbers, focus rings. Amber NEVER encodes data.

**Semantic pair — data only.** Inherited from the Manim renders. These are not
accents, they are the encoding the videos already use; the UI must agree with its
own figures or the page contradicts itself.

```
--signal-ok     #65ccaf   in control, pass, the 99.73% region
--signal-alarm  #de6a5d   violation, false-alarm tails, out of spec
--fill-ok       #2a534b   filled distribution regions (matches render fill)
```

Semantic colours NEVER appear outside a data context — no ok-green buttons,
no alarm-red headings.

## 2. Type scale

Body is the anchor: **21px / 1.55**. Everything else is a step from it.

| px | rem | Voice | Use |
|---|---|---|---|
| 11 | 0.688 | mono | micro labels, panel headers, units — uppercase, tracking .14em |
| 13 | 0.813 | mono | figure numbers, status text, captions |
| 16 | 1.000 | mono | readout values, nav |
| 17 | 1.063 | serif | secondary prose — lab notes, list items, chart captions, callouts |
| 21 | 1.313 | serif | body prose |
| 26 | 1.625 | serif italic | dek / standfirst |
| 33 | 2.063 | serif | h3, section heads |
| 42 | 2.625 | serif | page headline |
| 56 | 3.500 | serif | level opener display |

- Body serif on dark runs **weight 500**, not 400 — 400 goes thin and grey on `--ground`.
- Reading measure **58–64ch**. Never full width.
- Readouts and any figure use **tabular lining numerals** (`font-variant-numeric: tabular-nums`).
- Mono labels: uppercase, `letter-spacing: .14em`. Serif: normal tracking, never letter-spaced.

**Added 2026-08-25.** The 17px serif step was missing and got improvised as 15px and 17px
in shipped code (`line-of-sight` `.verdict p`, `index` `.lab-note` / `.tools li` /
`.two-cap`). It is a real need — secondary prose that must not compete with the 21px
reading column — so it is now a documented step rather than an ad-hoc value. Nothing
between 17 and 21, and nothing below 17 in serif; smaller than that is mono's job.

### Narrow viewports (≤560px)

21px serif cannot hold a 58–64ch measure on a 320px screen (that is roughly 25ch), so the
scale is allowed exactly three substitutions below 560px, and no others:

| Element | Normal | ≤560px |
|---|---|---|
| body prose | 21 | **19** |
| mono micro-label, where a row would otherwise wrap | 11 | **10** |
| wordmark | 21 | **18** |

These were already in `index.html` and `line-of-sight.html` as undocumented values before
being written down here. Anything else stays on the scale at every width — a 10px panel
header at desktop width is a bug, not a substitution.

**Fluid type is allowed, its endpoints are not negotiable.** `clamp(min, vw, max)` may
interpolate between two steps — at 760px a `clamp(42px, 7vw, 86px)` headline renders 53px
and that is fine. What must be on the scale (or a documented exception) is the **min and
the max**. Auditing every rendered width against the table will flag fluid type forever;
audit the endpoints.

### What the scale does NOT govern

**Text drawn inside a figure** — `<text>` in a chart SVG, anything painted into a canvas —
is part of the figure, not the page, and sets its own sizes. The Manim renders already do
this (font_size 18–40 in scene units), and the in-page charts match them: 9–11px for axis
and limit labels, 13px for annotations, larger for a value the chart exists to show. §5's
figure rule already says the page adapts to the figures, not the reverse.

This is an exemption, not a loophole. The moment that text is a page element — a caption,
a readout tile, a panel header — it is back on the scale.

### Documented exceptions — `line-of-sight.html`

Both approved 2026-08-25 rather than "fixed", because this page is a single long
four-act essay and not a document in the curriculum sequence:

1. **Display type runs off-scale**: `h1` to 86px and `h2` to 46px, against the 42/33
   steps. The oversized opener is the essay's signature. Its *body* prose was brought
   onto the 21px anchor and the 58–64ch measure; only the display sizes are excepted.
2. **The nav is `position: sticky`**, where every other page lets it scroll away. Four
   acts need act-to-act jumping. It already reverts to `position: static` at ≤900px so
   it never squeezes the reading column on a laptop or phone, which is the case the
   §6 fixed-chrome ban exists to prevent.

## 3. Spacing

Base unit **8px**. Vertical rhythm **32px** (equals body line-height — blocks land on it).

```
4  8  16  24  32  48  64  96  128
```

Section gap 96. Block gap 48. Inside a panel 24. Label-to-value 8.
Page gutter `clamp(24px, 5vw, 72px)`.

## 4. Radius

**0 everywhere.** Hard edges where edges meet.
The only exception is an element that genuinely floats free of the layout
(a toast, a dropdown, a tooltip): max **2px**. Nothing else rounds. Ever.

## 5. Component grammar

Eight components. Anything not on this list needs a reason.

1. **Panel** — 1px `--rule` border, no radius, no shadow. Optional header bar:
   mono micro-label left, status right (`SYSTEM-OK`, `REC 1080P/60`).
2. **Readout tile** — mono micro-label above, large tabular value below,
   value takes a semantic colour. Never a card, never shadowed.
3. **Status strip** — a row of readout tiles. Belongs to the interactive block.
   It does NOT persist as fixed chrome (see the 100vh ban).
4. **Figure block** — dark image sits directly on `--ground`, no border, no box.
   Above it a hairline rule; below it `FIGURE n.n` in mono 13 + serif caption.
5. **Equation block** — display serif, centred, with a right-aligned `(n.n)`
   reference number. Caption in mono 13 beneath.
6. **Level rail** — the four-level nav. Current item amber with a filled square
   marker; the rest `--ink-dim`.
7. **SYS note** — the aside/pull-quote as an instrument message:
   mono micro-label (`SYS_MSG`) above a serif line. Left border in amber.
8. **Video block** — `<video>` with a **required `poster`** frame. No visible
   box; it bleeds into the ground.

## 6. Ban list

House bans:
- purple-blue gradients; any gradient used as decoration
- emoji as icons
- glassmorphism / blur panels
- uniform border-radius
- drop shadows as default decoration
- Inter or a system stack chosen as the "safe" font
- centred hero with three feature cards

Project-specific bans, each earned from evidence in the gallery:
- **`100vh` shells with inner scrollers.** v03 hid 1066px and v13 hid 1240px of
  content in internal panes and both silently dropped the next-level link.
  The page scrolls. The document is the scroll container. No exceptions.
- **Dark figures on a light ground.** Every Manim render and matplotlib figure is
  dark-framed; on cream they read as punched-out rectangles.
- **Monospace body prose.** Mono is for labels, data and units. Never paragraphs.
- **Fixed chrome that squeezes the reading column** on laptop heights.
- Decorative "technical" ornament — fake telemetry, fake serial numbers, scanlines,
  CRT glow. The instrument language must carry real information or be removed.

## Tuning

Per the knob-tool rule: if any single visual parameter survives **two** counted
correction rounds, stop prompt-iterating — build a throwaway slider panel wired to
the live element, tune in the browser, read the values back, hardcode, delete the panel.

Most likely candidates: body serif weight/size on dark, and `--ink` contrast against
`--ground`.
