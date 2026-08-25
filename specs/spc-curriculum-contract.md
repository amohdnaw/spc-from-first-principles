# Outcome contract — SPC curriculum, one dark design system

Agreed 2026-08-25. Governs the reskin of the SPC portfolio and the build-out of the
four curriculum level pages.

Design frozen in `/home/ammar/portfolio/DESIGN.md`.
Direction picked from a 14-variant gallery: **v13 skin + v14 skeleton + v03 readout tile**.

---

## 1. What you will see

Each line is literally checkable in a browser after the build.

### Level pages
1. Open `spc-from-first-principles.html` → the page ground is `#0d1114` and the
   Manim video sits on it with **no visible box or seam** — the render background
   and the page background are the same colour.
2. Every video on the site shows a **still frame before you press play**, never a
   grey rectangle.
3. Scroll the page → it scrolls **as one document**. No inner scroll pane, no
   content trapped below a `100vh` fold. `document.scrollHeight` exceeds the viewport.
4. Each level page ends with a working **"Level N — <title> →"** link to the next level,
   and the last one links back to the index.
5. Body prose is a **serif at 21px** across a **58–64 character** measure. Labels,
   units and readouts are **monospace and uppercase**. No paragraph is set in mono.
6. Every figure carries **`FIGURE n.n`** in mono above a serif caption, with a
   hairline rule above the image.
7. Every displayed equation carries a right-aligned **`(n.n)`** reference number.
8. The interactive block shows **three readout tiles** — in-control area,
   false-alarm rate, false alarm every — with tabular numerals, the pass value in
   teal `#65ccaf` and any alarm value in salmon `#de6a5d`.
9. **Five levels exist** as pages (0 Basics, I Variation, II Limits, III Capability,
   IV Detection) and the level rail highlights the current one in amber.
10. **All 9 Manim scenes appear somewhere.** Was 2 of 8 used. Now: Level0/1/2/3/4 on
    their own pages, and SPCGallery, ConstantsAct, EWMAMemory, WERules embedded in
    the level whose argument they support.

### Narration — added 2026-08-25
10a. **Every act is narrated.** Each video carries an audio stream, and playing one
     produces sound. Verified by decoded audio bytes, not by the container alone.
10b. **Every video has a caption track.** A `<track kind="captions">` pointing at a
     WebVTT file that parses to a non-zero cue count in the browser.
10c. **No act plays faster than its narration.** Pacing is not hand-tuned; the
     narration script drives it via `self.say` in `spclab/narration.py`. A silent
     render and a voiced render of the same scene stay within a second of each other.
10d. **`SPCLAB_VOICE=1 ./build-media.sh` reproduces every mp4, poster and caption**
     from source in one command.

### The other two pages
11. Open `index.html` → same dark ground, same two-voice type system. The
    scroll-linked process monitor strip still runs and now sits on a ground that
    matches it instead of fighting cream.
12. Open `line-of-sight.html` → same dark ground and type system; the four
    streaming line charts and the drift narrative still work.
13. Navigation between all pages works in both directions, and the nav fits at
    **320px** with no overflow and no collision.

### Proof
14. A `diagrams/spc-curriculum-flow.{mmd,excalidraw,svg,png}` set exists showing
    how content flows from `spclab` Python → figures/videos → level pages.
15. `cd spc-lab && PYTHONPATH=src .venv/bin/python -m pytest tests -q` still passes
    (7 tests). No library behaviour changes in this work.

---

## 2. The picked mock

Gallery of 14 directions, screenshot at `/tmp/gallery3.png`.

- **v13** — process control room HMI → supplies the skin: dark panels, panel headers
  with status badges, readout tiles, left level rail, amber wayfinding.
- **v14** — mathematical textbook → supplies the skeleton: natural document scroll,
  numbered equations and figures, serif reading column at a real measure, marginal notes.
- **v03** — terminal → supplies one component only: the readout-as-telemetry treatment
  and the `SYS_MSG` framing for the pull quote.

Explicitly rejected from all three: the `100vh` tiling shell (v03 hid 1066px of content,
v13 hid 1240px), and monospace body prose.

Mock files deleted after the pick, per the throwaway rule.

---

## 3. Not in scope

- **No new Manim renders in this pass.** See defaults below.
- No change to `spclab` Python behaviour, formulas, or test expectations.
- No GitHub repo creation, no Pages deploy, no DNS. Still an open TODO.
- No real case-study content for Line of Sight — the placeholder narratives stay
  until you supply real projects. Reskin only.
- No PyPI publish, no pandas-native chart classes, no Gage R&R module.
- `spc-lab/README.md` stays linked as a file; it becomes a repo link only once the
  GitHub repo exists.
- No mobile-specific redesign beyond "it must not overflow or collide at 320px".
- No print stylesheet.

## 4. Defaults taken

Approving this contract confirms these. Each is reversible; say so and I change it.

1. ~~**Level 0 is deferred, not dropped.**~~ **SUPERSEDED 2026-08-25** — you said
   "do all". Level 0 was built as new Manim (`level0_scene.py`, 102.5s) rather than
   reusing Level 1 footage, and every act was re-rendered. The cost reasoning behind
   the original default was wrong and is corrected here for the record: a full
   1080p60 render is **8 seconds per scene**, so all nine rebuild in under two
   minutes. Rendering was never the expensive part — authoring is.
2. **Dark everywhere**, including the landing page — your call, recorded here because
   it means `index.html` and `line-of-sight.html` get reskinned, which is the bulk of
   the work.
3. **Two font families only** — EB Garamond and IBM Plex Mono. Both self-hosted as
   woff2 to match the existing no-CDN pattern, not loaded from Google Fonts.
4. **One accent (amber `#ffae00`) for wayfinding**, plus a locked semantic pair
   (teal/salmon) used only for data. Sampled from the Manim renders, not chosen by eye.
5. **Figures and videos keep their current rendered look.** The page adapts to them,
   not the reverse. No re-rendering to change colours.
6. **`index.html` stays the entry point** and keeps its current section structure
   (about / selected work / visualize / toolbox / contact). Reskin, not rewrite.

---

## 5. Build order — each checkpoint is one reviewable screen

| # | Checkpoint | You review |
|---|---|---|
| 1 | Level II page, complete, to the frozen system | One finished level page — the hardest one, mocked already |
| 2 | Levels I, III, IV + the 6 unused scenes placed | The full four-level flow, clickable end to end |
| 3 | `index.html` reskinned dark | The landing page |
| 4 | `line-of-sight.html` reskinned dark | The interactive essay |
| 5 | Diagram set + full-site nav/mobile sweep | Proof artifacts |

No chrome-only or token-only phases. Every checkpoint yields a screen you can judge.

---

## 6. Verification

After each checkpoint, checks 1–15 above are re-run literally in a browser and read
back from this file, not from memory. A correction from you updates this contract
and `DESIGN.md`, not just the instance.
