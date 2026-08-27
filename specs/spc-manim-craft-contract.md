# Outcome contract — Manim animation craft

Agreed 2026-08-26. Governs the rebuild of the nine Manim acts in `spc-lab/`.
Design stays frozen in `DESIGN.md`; the render palette and ground are unchanged.

---

## 0. Why — the measured diagnosis

Across the nine existing acts there are **271 animation calls**:

| Verb | Count | |
|---|---|---|
| `FadeIn` | 114 | appear |
| `Create` | 66 | appear |
| `Write` | 56 | appear |
| **subtotal** | **236 — 87%** | **things appearing** |
| `Transform` | 9 | actual morphing |
| `LaggedStart` | 8 | staggered appear |
| `Circumscribe` / `Indicate` | 6 | emphasis |

And the absences: **zero** `rate_func` anywhere (every animation uses Manim's
default easing), **zero** camera movement, **zero** `ValueTracker` /
`add_updater` / `always_redraw`, **zero** `ReplacementTransform` or
`TransformMatchingTex`.

It is slideware rendered in Manim. Things appear, then other things appear.
Nothing morphs, nothing is followed, nothing moves continuously. The 3b1b feel
comes almost entirely from the verbs that are absent.

Concrete instance, `level06_scene.py`: the ±3σ region and both tails `FadeIn` as
static polygons, then the punchline is typed —
`Write(Text("outside: 0.27% → false alarm ≈ once per 370 subgroups"))`. The
number is **asserted**. For a curriculum whose claim is *"derived, not
asserted"*, that is the wrong verb.

---

## 1. What you will see

Checkable after the first act is rebuilt.

### The rebuilt Level II
1. Open the rebuilt `Level06.mp4` → the 99.73% figure **arrives as the result of
   a movement**: the ±σ limits sweep outward from the centre while the filled
   area and a live readout follow them continuously. No frame of the video
   contains that number before the sweep produces it.
2. The readout counts through real values on the way (`± 2.97 σ / 99.70 %` …
   `± 3.00 σ / 99.73 %`), computed from `erf`, not from a lookup table.
3. The tail is **revealed by exaggeration**: the vertical axis stretches ~×70
   and 0.135% grows from an invisible sliver into a visible wing, with a live
   `vertical axis × N` readout. The bell's peak leaves the top of frame — it is
   **not** clamped into a flat-topped box.
4. The odds are **restated by morph**, not retyped: two tail labels converge
   into `0.27 %`, which becomes `1 alarm in 370 subgroups`. No new sentence is
   written on screen to state a number already derived.
5. At least one equation **morphs term-into-term** via `TransformMatchingTex`
   (e.g. the tail integral becoming the 0.0027 figure).
6. Every animation in the act carries a **deliberate `rate_func`**. The act
   contains at least one camera move and at least one continuously-driven
   (`ValueTracker`) passage.
7. All in-frame text is set in the site's **own two voices** — EB Garamond for
   prose, IBM Plex Mono for readouts, units and status. No Pango default sans.
8. Watched end to end at 1080p60, the act has **no overlapping text**, no label
   sitting on the mark it labels, and no mobject left behind by a `Transform`.

### Doesn't break
9. `narration.py` still drives all pacing — no hand-tuned `run_time` stands in
   for a spoken line, and the act renders correctly **silent** (the default).
10. `cd spc-lab && PYTHONPATH=src .venv/bin/python -m pytest tests -q` still
    passes (9 tests). No `spclab` formula or constant changes.
11. `./build-media.sh` still reproduces every mp4, poster and caption in one
    command.
12. The level pages still embed their videos with a poster and a caption track,
    and `index.html`'s gallery figure still plays.

### Then, only after you approve that act
13. The same patterns applied to the remaining eight acts, act by act, each one
    watchable on its own before the next starts.

---

## 2. The style test (Phase 2 evidence)

Rendered, watched, and thrown away. `/tmp/spclab_style/` — one beat of Level II,
before and after, plus a verdict table.

**Proven and adopted:**
- *Derive by motion* — `ValueTracker` + `always_redraw`. The strongest single
  change available.
- *Reveal by exaggeration* — stretching the axis beats pushing the camera,
  because the frame never moves and type therefore stays at native size.
- *Site fonts in video* — EB Garamond and IBM Plex Mono, converted from the
  repo's own woff2 with `fontTools` into `~/.local/share/fonts/spclab/`. No
  root, no network, byte-identical to what the site serves.

**Proven and rejected:**
- *Camera push into a tail.* Text authored at `font_size 6` and magnified by the
  camera destroys Pango's glyph metrics — it rendered `0135%lves out here`.
  If a camera move is used, type is built at native size and `.scale()`d.
- *Digit-level `TransformMatchingShapes`.* On unequal digit counts it renders as
  mud (`0 12375 %`). Numbers change by value-tracker or whole-label transform.

**Bugs the test found, carried forward as build rules:**
- Clamping a stretched curve makes a flat-topped box; let the peak leave frame.
- `Transform(a, b)` leaves **a** as the survivor. Never position or add `b`
  afterwards.
- Corner labels collide at 1920px. Reserve corners explicitly.
- Never place a label on top of the mark it labels.

**Render cost, measured:** a 17s act at 1080p60 costs **23s** with ordinary
animations and **107s** with heavy per-frame updaters — roughly 5×. Budget
accordingly; do not put `always_redraw` on an `axes.plot` of 587 points unless
the motion needs it.

---

## 3. Not in scope

- **No voice recording.** Silent-first: every act is built and judged silent,
  which `narration.py` already paces correctly. gTTS stays the fallback and
  your own voice remains a later decision.
- No change to `spclab` formulas, constants, or test expectations.
- No new acts and no change to the curriculum's argument — same nine acts,
  same claims, better told.
- No re-rendering to change the palette or the ground colour.
- No deploy. Still no GitHub repo, still nothing live.
- No website changes; the pages already embed whatever the build produces.
- No ManimGL migration (see defaults).

## 4. Defaults taken

Approving this confirms them. Each is reversible.

1. **Anchor: 3b1b mathematical.** Equations morph, the camera narrates,
   quantities move continuously. Not the "instrument cinema" alternative.
2. **Narration is rewritable and silent beats are allowed.** Runtime may grow
   from 11 min toward 14–18 min where a visual needs room to land.
3. **LaTeX installed, maths in Computer Modern.** `texlive-latex-*` +
   `dvipng`. Mixing CM maths with EB Garamond prose is what 3b1b does; it is
   the convention, not a breach of the two-voice rule. Prose stays Garamond.
4. **Level II is the first act**, because it is the most mathematical and its
   central beat is the one already style-tested.
5. **Stay on ManimCE 0.21.** The gap was never the engine — it was the verbs.
   ManimGL would break `manim_voiceover`, which is what makes pacing
   reproducible.
6. **The GL experiment is `--renderer=opengl`, not 3b1b's manimgl.** CE 0.21
   ships an OpenGL renderer (`moderngl` and `pyglet` are already installed), so
   the experiment is a flag on an existing act — same API, same voiceover, no
   second toolchain. One act rendered both ways and compared.
7. **Fonts are installed per-user**, not system-wide, and are generated from
   the repo's woff2 rather than fetched.

---

## 5. Build order — each checkpoint is one watchable act

| # | Checkpoint | You review |
|---|---|---|
| 1 | LaTeX proven + `NarratedScene` gains a camera-capable variant | a rendered MathTex morph, ~5s |
| 2 | **Level II rebuilt end to end** | one finished act, silent, 1080p60 |
| 3 | Levels I and III | the derivation spine, three acts consistent |
| 4 | Level 0 and IV | all five levels |
| 5 | The four embedded scenes (SPCGallery, ConstantsAct, EWMAMemory, WERules) | all nine acts |
| 6 | `--renderer=opengl` comparison on one act | a quality/speed verdict, then a keep-or-drop call |

No layer-only or chrome-only phases. Checkpoint 2 is the real gate: if the
finished act is wrong, only one act is wasted.

---

## 6. Known blocker to solve at checkpoint 1

`narration.py` builds `NarratedScene` on `Scene` or `VoiceoverScene`. Camera
moves need `MovingCameraScene`. The base class has to gain a camera-capable
variant without duplicating the `say()` pacing logic — otherwise every act that
wants a camera move has to abandon narration-driven pacing, which is the one
thing in this repo that must not regress.

## 7. Verification

After each checkpoint, checks 1–12 are re-run against the rendered mp4 — read
back from this file, not from memory — and the act is watched end to end at
1080p60 before it is called done. A correction from you updates this contract,
not just the instance.

---

## 8. Closed — 2026-08-27

All six checkpoints are done and reviewed. What the build order produced, and
the decisions taken at the end of it:

| # | Checkpoint | Landed |
|---|---|---|
| 1 | LaTeX + camera-capable narration base | `9d879f1` |
| 2 | Level II rebuilt | `8fd8783` |
| 3 | Levels I and III | `f28d14a` |
| 4 | Level 0 and IV | `798632b` |
| 5 | The four embedded scenes | `b573b82` |
| 6 | `--renderer=opengl` comparison | `e26a5ab` |

**Runtime: accepted at 18:59 for all nine acts** (five levels 13:30). Default 2
said 14–18 min; the extra minute is where the derivations landed, and it stands
as approved rather than trimmed. `index.html` quotes the five levels, which is
what its own sentence measures.

**OpenGL: dropped, and not to be revisited** unless a ManimCE release both
restores `MovingCameraScene`'s frame API and beats cairo on this content. On
this machine GL was 23.7 % slower with no visual gain — measured, with evidence
in `spc-lab/docs/opengl-verdict.html`.

**Four asserted numbers were found and killed** in acts that predate this
contract: Level III's spoken 0.89 against its own computed 0.80, Level IV's
typed "~4× faster", EWMAMemory's "~2× sooner" contradicting it, and WERules
flagging a Rule 3 that `western_electric_violations` never detects. Every
figure on screen is now computed at render time by the library the tests check.

**The gate that made the difference**: `act_style.at_panel` raises when a
readout runs off the frame. It caught a clipped label that three rounds of
frame review had missed. Any new readout inherits the check for free.

Narration remains gTTS by decision, not by default — the voice choice is a
separate open question with samples, not a build task.
