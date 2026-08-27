# SPC from First Principles

An interactive statistical process control curriculum, where every number is derived
rather than asserted. Five levels, nine Manim acts, and a Python library whose tests
check the same functions the videos read from.

**Live: <https://spc-lab.amohdnaw.xyz>** · a teaching project from
**<https://portfolio.amohdnaw.xyz>**, which is the front door, and
**<https://amohdnaw.github.io/case-studies>**, which holds the applied work.
This repository is the curriculum only: it teaches the statistics, it does not
make claims about anybody's career.

## Why it exists

Most SPC training hands you constants. A₂ is 0.577 because the table says so; ±3σ
catches 99.73 % because the slide says so. This site refuses that. Every figure on
screen is computed at render time by `spclab`, and you watch it arrive:

- the **mean** is found by sweeping a candidate centre until the deviations cancel
- **σ** is the limit of a running mean of squares, square by square
- **99.73 %** is `erf(k/√2)` evaluated live while the ±kσ limits sweep outward
- **d₂ = 2.33** is where the mean range of 20,000 simulated subgroups settles, and
  **A₂ = 0.577** falls out of it
- an **EWMA chart is 4.4× faster** than Shewhart at a 1σ shift — from 4,000 simulated
  shifts at a calibrated, matched false-alarm rate, not from a textbook

If a formula changes, the video changes with it. That is the whole design.

## The pages

| Page | What it covers |
|---|---|
| `index.html` | front door and curriculum hub, with the chart as the syllabus |
| `level-0.html` | what a measurement is: mean, σ, the shape, sample vs population |
| `level-1.html` | variation is predictable: the central limit theorem and σ/√n |
| `level-2.html` | control limits are a hypothesis test: ±3σ, 0.27 %, ARL 370 |
| `level-3.html` | capability: two voices, Cp, Cpk, and ppm as a promise |
| `level-4.html` | detection theory: charts as evidence accumulators |
| `line-of-sight.html` | a long-form essay on the same discipline applied to a browser |

## The library

`spc-lab/src/spclab/` — SPC formulas with nothing hidden. Control chart constants by
numerical integration instead of a lookup table, capability indices, ppm from Cpk,
EWMA limits, Western Electric rules. `pytest` covers the formulas the acts quote.

```bash
cd spc-lab
python -m venv .venv && .venv/bin/pip install -e .
PYTHONPATH=src .venv/bin/python -m pytest tests -q
```

## Rebuilding the videos

```bash
cd spc-lab
python tools/install-fonts.py          # the site's own woff2 → ttf, for Pango
./build-media.sh                       # silent, correctly paced, no network
SPCLAB_VOICE=1 ./build-media.sh        # narrated + WebVTT captions
```

One command produces every mp4, poster and caption track. Pacing lives in the
narration script, so the silent and narrated cuts are timed identically —
see `spc-lab/src/spclab/narration.py`.

## Decisions and their evidence

The design system and every scope decision are frozen in files, not in memory:

- `DESIGN.md` — the palette, the two voices, the type scale, the ban list
- `specs/spc-landing-contract.md` — the front door, 19 checks
- `specs/spc-curriculum-contract.md` — what each level owes the next
- `specs/spc-manim-craft-contract.md` — the animation craft rebuild, six checkpoints, closed
- `spc-lab/docs/opengl-verdict.html` — why the OpenGL renderer was measured and dropped

## Licence

Code under `spc-lab/` is MIT. The written curriculum, the videos and the design are
© Ammar Nawawi, all rights reserved — read them, learn from them, don't republish them.
