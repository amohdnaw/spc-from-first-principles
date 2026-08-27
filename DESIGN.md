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
- **An uppercased label may not contain Greek.** `text-transform: uppercase` maps σ to Σ
  and λ to Λ — the summation sign and a different letter, not styling. Either keep the
  label ASCII ("what three sigma is worth") or opt the glyph out with `.nc`
  (`text-transform: none`), which keeps the label uppercase and the symbol correct.
  Four instances shipped before this was noticed, including the interactive's own
  "LIMIT AT ± 3.00 Σx̄".
- **Maths inside serif prose goes through KaTeX, not Unicode.** EB Garamond has no
  combining hat and no subscript digits, so `σ̂` renders as sigma plus a stray caret and
  `d₂` falls back mid-word to another face. Use `<span class="tex" data-tex="…">`, which
  `tools/typeset.mjs` renders. **Headings are the exception** — Computer Modern beside
  EB Garamond at 33px reads as a mistake, so reword the heading instead.

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

### Wide viewports (≥1440px) — added 2026-08-27, revised the same day

**Superseded in part.** The `--figure` band and the raised page widths below were the
first answer to a wide screen. The chapter grammar replaced them: the text block is now
the constraint, and **the page width is computed from the grid tokens** —

```
.wrap { max-width: calc(var(--measure) + var(--marg-gap) + var(--marg) + 2*var(--gutter)) }
```

The failure this fixes is worth naming, because it shipped twice. Raising the container
to 110rem while the text block stayed 1090px left-aligned inside it produced margins of
**149px left and 675px right** — the page looked broken on any wide monitor. A hardcoded
page width that is not derived from the grid *will* drift from it. Measured after:
253/253 at 1440, 412/412 at 1913, 735/735 at 2560, 1175/1175 at 3440.


The pages were built for a laptop and did nothing with a desktop. At 2560px the
content capped at 1216px, so **52% of the viewport was empty** and the 1920-native
video rendered at 704px — 37% of its own resolution. Direction picked from a
three-way mock (breakout / two tracks / margin apparatus).

**The measure never moves.** `--measure: 27em` (567px, measured at 64 characters) is
the same on a phone and on a 2560px monitor. Widening prose is still banned by §2.
What changes is that **figures spend the width the prose refuses**.

| Viewport | `--figure` band | Page `--max` |
|---|---|---|
| < 1440px | 44rem — 704px | 76rem — 1216px |
| ≥ 1440px | 64rem — 1024px | 84rem — 1344px |
| ≥ 1800px | 94rem — 1504px | 110rem — 1760px |

**No raster is ever displayed above its native width.** Each figure carries a cap
taken from its own source resolution, so the band is a ceiling, not a stretch. The
Manim renders are 1920 wide and reach the full 1504 band; the matplotlib sheets run
1153–2117, and the narrow ones stop at their own size rather than going soft. A
figure that looks blurry on a big screen is this rule being violated.

**Level pages pair their chart figures.** A run of consecutive image figures becomes
a two-up grid at wide widths — `repeat(auto-fit, minmax(560px, 1fr))` — because the
level pages are a short prose head followed by a stack of six charts, and two charts
side by side both fills the width and keeps each one under its native size. Video
figures never join a pair; they take the whole band.

Two things this deliberately does not do: no sticky media column (it is one step from
the fixed-chrome ban in §6), and no margin apparatus — the right margin stays empty
rather than filling with decoration that carries no information. Margin apparatus is
available later for a level that genuinely has units, definitions and spoken lines to
put there, and it would be contracted then.

### The level page is a chapter — added 2026-08-27

Diagnosed by measurement, not taste. `level-06.html` carried **104 words** across 5.3
screens, with 77% of its height spent on images and **zero headings**. It read as
scrolling past things because there was nothing to read. A level page is now a
textbook chapter, and the grammar is:

1. **Chapter opener** — `Level N · chapter n`, headline, dek, then a **contents block**:
   every numbered section with a one-line summary, plus a count of sections, acts and
   interactives. The reader knows what they are in for before scrolling once.
2. **Numbered sections** `n.1 … n.6`, one per movement of the argument, each with a
   heading. A section that cannot be named is not a section.
3. **Prose is the act's own narration, adapted.** `narration.py` already renders one
   script two ways, silent and voiced; the page is the third render. Spoken register is
   edited for reading — never pasted. This is why the page and the video agree.
4. **Three figure positions, and only three** — taken from tufte-css, not invented:
   the main column by default, the margin for a *small* figure, and the full text
   block for anything larger. **Every element shares one left edge**: contents,
   prose, figures, the interactive and the headings all start at the same offset,
   verified at nine widths. A figure in the outer column at a vertical offset — which
   is what I built first — cuts an L-shaped hole and belongs to no book.
4a. **Margin notes are spans inside the paragraph they annotate**, injected after the
   first sentence, and they carry a negative right margin. Both halves matter: a
   float only rises to the line box where it appears, so a note that is a *sibling*
   of the paragraph lands at the paragraph's foot; and without the negative margin
   the float sits inside the 702px column and shortens every line beside it. With
   both, the longest rendered line measures 698px of 702.
4b. **Several data notes on one paragraph become one multi-row block.** Three stacked
   notes outrun the prose and stretch the section; one block with three rows reads as
   a small table, which is what a textbook margin actually looks like.
5. **Margin apparatus at 340px** — capped at a note width, never a column width. It
   carries the instrument voice only: a constant and its value, a symbol defined, the
   line the narrator speaks and its timestamp. Decoration here is the banned fake
   telemetry.
6. **A referenced act that is not this section's subject becomes a collapsed player** —
   `<details class="act">`: a poster strip closed (135px), the full text-block width
   open (1090px), no JavaScript. The first attempt made it a 340px margin card, which
   measured **323×182 on screen**: not a player but a thumbnail with controls, and
   unreadable for a 1920-wide render. **No video on this site renders under 400px at
   desktop widths** — that is now a checked invariant.
6a. **Collapsed by default, and the closed state must read as a video.** A level's own
   act is always open; an act borrowed from another scene is collapsed. Collapsing buys
   no bandwidth — `preload="none"` fetches only the poster either way — so the only
   thing it buys is ~590px of vertical space each, and the only thing it costs is
   discoverability. That cost is paid off in the closed state, not by opening
   everything: a **280px poster with a play glyph over it**, the figure number, the
   caption and a `PLAY` cue. At 180px with a word it read as a footnote.

Measured on Level 6: 104 → **555 words**, 20 → **79 words per screen**, 0 → 6 headings.
The page is 34% taller, which is the correct trade — the fix for "scrolling away" is
substance per screen, not fewer pixels.

**Body steps to 26px at ≥1500px.** A documented substitution, the mirror of the ≤560px
one in §2: 26px is already a step on the scale, and at `27em` it holds **59 characters**,
inside the frozen 58–64. The measure token does not change — `em` does the work.

### Identity — three sites, one grammar (2026-08-27)

`portfolio.amohdnaw.xyz` is white, Manrope sans, lowercase and personal.
`amohdnaw.github.io/case-studies` is white, Palatino serif, formal. They already differ
from each other more than either differs from this site, so there is no single house
skin to adopt.

**The dark ground stays, and it is functional.** Tested directly: the chapter rendered on
the case-studies palette turns every Manim video into a black rectangle punched into a
white page — the exact failure §6 names. Going light would mean re-rendering nine acts
and fourteen matplotlib sheets on a white ground and re-freezing every signal colour.

What converges is the furniture: the **mono wordmark string** (`Ammar Nawawi / SPC`, the
same primary name the siblings use), the **eyebrow device**, and **reciprocal navigation** —
every page links out to the portfolio and the case studies, not only the hub. Palette and
body font stay per site.

**Correction to an earlier version of this section:** it said links should converge on
teal. They should not. Teal is the in-control signal on this site, and amber is
wayfinding — which is exactly what a link is. Borrowing the signal colour for
navigation would break the palette's one job. The light sites use teal for links
because they have no signals to protect.

**And the light option is closed, on measurement rather than taste.** Every colour that
carries meaning here fails WCAG on white: amber 1.9:1, teal 1.9:1, body ink 1.6:1,
salmon 3.3:1 (large text only). Only the dark teal *fill* passes. Going light is not a
skin swap — it is a new palette plus re-rendering nine acts and fourteen sheets, and it
forfeits the sampled ground that makes video seamless.

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
