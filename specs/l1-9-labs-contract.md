# Outcome contract — interactive labs for Levels 1–4, 7 and 9

Step 5 of the six-step plan. Picked 2026-10-07: "Core claims", "Pilot L1, then go".
The lab shell is the existing one (Levels 5, 6, 8, 10–12): canvas, sliders, three
readout tiles, a note, a SYS_MSG aside. No new chrome.

## What you will see — Level 1 pilot

1. Level 1, section 1.5 "Reacting to noise makes it worse", has a lab headed
   "Interactive — Deming's funnel" below the existing figure.
2. One slider: "Share of each miss you correct", 0 % to 100 %, starting at 100 %.
3. The canvas draws the same 400 parts twice from one fixed set of noise: grey
   left alone, blue adjusted. Drag the slider and the blue run widens or narrows
   live; at 0 % the two runs lie on top of each other.
4. Three tiles: σ left alone (≈ 1.00), σ adjusted (computed from the drawn run),
   and the exact variance ratio 2 / (2 − g). At 100 % the ratio reads 2.00 and σ
   adjusted is about 1.41 × σ left alone.
5. Works with keyboard arrows on the slider and at phone width with no sideways
   scroll. (The site is dark-only, so there is no light theme to check; corrected
   after approval, 2026-10-07.)
6. The contents line for 1.5 shows "INTERACTIVE"; the head estimate counts 1
   interactive.

## After "go"

- L2: flip count slider; the gap from half grows while the rate settles.
- L3: sample size slider; average s² over many samples, ÷n low, ÷(n−1) on σ².
- L4: subgroup size 1→10 on a die; the averages become a bell; σ/√n tile.
- L7: shift size δ; power of one point, β, average run length.
- L9: EWMA λ on a slow drift; alarm subgroup, EWMA against Shewhart.

## Not in scope

New lab chrome or styles; MSA labs; changes to the videos; any lab for Levels
5, 6, 8, 10–12 (they have one); the newcomer test (step 6).

## Defaults taken

Vanilla JS inline in the page like the other labs; fixed seed so every reader
sees the same run; each lab sits in the section whose claim it tests; numbers
cross-checked against the `spclab` module the section cites.
