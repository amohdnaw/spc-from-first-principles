# Spec: phone versions of multi-panel figures

Status: specced, not scheduled. Written 2026-10-07 after two deferrals (graveyard rule).
Covers both sites: SPC (~/portfolio) and MSA (~/msa-from-first-principles).

## Problem

Side-by-side panel figures shrink to the phone column (~358 px) whole. A figure
rendered 1600–2100 px wide shows at 17–23 % scale, so axis labels and annotations
land at roughly 3–4 px tall and cannot be read. Pinch-zoom is the only way in.

Inventory (served PNGs wider than 2:1, measured 2026-10-07):

| site | figures | scale on phone |
|------|---------|----------------|
| SPC  | l04_1_dice_to_bell (1×4), l04_2_sqrt_n (1×2), 02_A2_D3_D4 (1×2) | 17–20 % |
| MSA  | all 14 level figures (L1–L7, two each, side by side) | 19–23 % |

The 22 other SPC figures are single panel or already stacked (L8, L9 use 2×1)
and stay as they are.

## What you will see

1. On a phone (390 px wide), each of the 17 figures above shows its panels stacked
   top to bottom, one panel per screen width, with axis text at least 10 px tall.
2. On desktop nothing changes: same PNG, same pixels (md5 of the desktop file
   unchanged).
3. The caption, figure number and glossary links are the same at both widths.
4. No sideways scroll at 390 px on any level page of either site.
5. Rotating a phone to landscape (wider than 560 px) shows the desktop figure.

## How (reference, not the contract)

- Each generator that builds a 1×N figure takes a `stacked=True` flag that draws
  the same panels as N×1 at phone width (~6 in wide), saved as `<name>_phone.png`.
  Same data, same seed, same annotations; only the layout changes.
- The page serves both with `<picture><source media="(max-width: 560px)"
  srcset="…_phone.png"><img src="….png"></picture>`. Done in chapterise's
  `K["fig"]`, so the 17 figures switch with no hand edits to page sources.
- A test per site asserts every `_phone.png` exists for each listed figure and is
  taller than it is wide.

## Not in scope

- Single-panel figures, videos, labs (labs already pass at phone width).
- Restyling fonts or colours (done in bc802ec / 0ea703d).
- A tap-to-zoom lightbox.

## Defaults taken

- Stacked panels in one image, not one image per panel: one file per figure,
  caption stays whole, simpler markup.
- Breakpoint 560 px, the pages' existing narrow-layout switch (`@media(max-width:560px)`).
- Phone PNGs are committed next to the desktop ones (same pipeline, same cache
  busting).

## Cost

About a day: ~2 h for SPC (3 generators: level04.py ×2, formula_sheets.py), ~3 h
for MSA (14 separate `add_gridspec(1, 2)` calls across level01–07.py, no shared
helper), 1 h for `K["fig"]` and the tests in both repos, 2 h for the phone sweep
with `shot --mobile` on all 17.

## Verify

`shot --mobile` on each affected level, read the PNG, and confirm check 1 by
eye; `shot` at 1440 px and compare the desktop PNG md5 (check 2); scrollWidth
equals clientWidth at 390 px (check 4).
