# Outcome contract — narrated acts for Levels 10–12

Approved by Ammar 2026-10-07. Step 4 of the six-step plan. Craft rules come from
`spc-manim-craft-contract.md`; voice from `narration-voice.md`.

## What you will see — Level 10 pilot

1. Level 10, section "The spread is not a free parameter", opens with a video as
   Figure 10.1: poster, controls, English captions, on the page with no box or
   seam, like Level 9.
2. It runs 2–3 minutes, narrated in the same voice as Levels 1–9.
3. A slider moves p from 0.02 to 0.5. The binomial bars, the ±3σ limits and a live
   σ = √(p(1−p)/n) readout follow it continuously. No σ value appears on screen
   before the movement produces it.
4. With p held still, n moves 50 → 200 → 50 and the limits narrow and widen live.
   The σ formula for a count changes term by term into the one for a proportion;
   nothing is retyped.
5. At small p the lower limit runs into 0 and stops there visibly.
6. The page's existing figures become 10.2 onwards; the contents line for that
   section shows "ACT".
7. The text-overlap checker (`tools/text_collisions.py`) reports 0 collisions.
   Every animation has its own easing; the act has at least one camera move.

## After "go"

- L11: a line slides across the scatter while the squares of the residuals
  shrink; the live sum bottoms out at the least-squares line.
- L12: the one-factor-at-a-time path walks the shaded response map and stops at
  8; the four-corner design then finds 6.

## Not in scope

MSA videos; re-rendering Levels 1–9; recording Ammar's own voice; a separate
phone cut; step 5's interactives.

## Defaults taken

1080p60; Kokoro `am_michael` at 0.92; captions built from the narration as in the
existing acts; each video sits in the section whose idea it derives.
