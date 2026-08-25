# Outcome contract — SPC landing page overhaul

Agreed 2026-08-25. Governs the rebuild of `index.html` as the curriculum front door,
and the absorption of `spc-from-first-principles.html` into it.

Design stays frozen in `DESIGN.md` — this contract changes **composition**, not tokens.
Supersedes two lines of `specs/spc-curriculum-contract.md` (see §5).

---

## 1. What you will see

Each line is literally checkable in a browser after the build.

### The opening act
1. Open `index.html` → the first screen is a **full-width control chart sitting in the
   page flow**, under one serif headline. Not a fixed strip, not a box.
2. Scroll to the bottom of the page → **nothing is pinned to the viewport**. The count of
   elements with computed `position: fixed` on the page is **zero**. The nav scrolls away
   with the document.
3. The chart's trace is **teal `#65ccaf` while in control and salmon `#de6a5d` for the
   out-of-control run**, with exactly **one amber marker** (`RULE 1 — POINT BEYOND 3σ`).
   No amber anywhere in the data itself.
4. Directly under the chart, **four phase doors** in a row: `PHASE I · BASELINE`,
   `PHASE II · THE LIMITS`, `PHASE III · VIOLATION`, `PHASE IV · CORRECTIVE ACTION`.
   Clicking each one lands on the level page that explains it (I → `level-1.html`,
   II → `level-2.html`, III → `level-3.html`, IV → `level-4.html`).

### The syllabus
5. Below the opening act, **five numbered rows** — `0`, `I`, `II`, `III`, `IV` — set as
   large display serif numerals, each with a title, a one-idea line, and its hook on the
   right (`start here`, `σ/√n`, `370:1`, `Cpk → ppm`, `ARL 10 vs 44`). Each row links to
   its level page.
6. A **provenance readout strip** in the flow: `400 000` subgroups, d₂ `2.326`,
   A₂ `0.577`, `AIAG Table B` — the two constants in teal, tabular numerals.
7. The **gallery video** appears with a still poster frame before you press play, a
   hairline rule above it, and `FIGURE 0.1` in mono over a serif caption.
8. The `SYS_MSG` note survives: *"If a number here disagrees with the table, the test
   fails. That is the point."*

### Applied — the credibility half
9. A section headed **"The curriculum, applied"** holding all three case studies with
   their numbers intact (`Cpk 1.1 → 1.6`, `%GRR 61% → 9%`, `< 3 hrs signal→containment`).
10. **Lab A is still interactive** — drag the tool-wear slider and the three readouts
    (X̄ detects / EWMA detects / final Cpk) change. It opens at wear **26**, the lowest
    setting where EWMA fires and X̄ does not, so the lab lands on its own thesis instead
    of on "neither detected".
10a. **AMENDED after build.** These readouts judge the *chart*, not the process, so
    `not detected` is the **salmon** state and a detection is **teal**. The inherited
    code had it inverted — painting the Shewhart chart's failure to see real drift as a
    teal pass, and EWMA's catch as an alarm, which contradicted the lab's own argument.
    Reversible: say so and I put it back.
11. **Lab B is still interactive** — drag the gage slider and %GRR, ndc and the AIAG
    verdict change, with the verdict flipping colour between teal and salmon.
12. The **"same data, two audiences"** demo still toggles between engineer view and
    management view, and the **Toolbox** list is still on the page.

### Body rules
13. Every paragraph is **serif at 21px** and **no wider than 64 characters**. No paragraph
    is set in monospace. Labels, hooks, readouts and status text are mono and uppercase.

### The absorption
14. `spc-from-first-principles.html` **no longer exists**, and every link that pointed at
    it now points at `index.html`: the nav item, the in-page deep link, `level-0.html`'s
    back-link, `WRAP.md`, `DESIGN.md`, and `specs/spc-curriculum-contract.md`.
15. **No dead links anywhere on the site.** Every `href` on every page resolves to a file
    that exists.

### Doesn't break anything
16. At **320px** the page has no horizontal overflow (`scrollWidth == clientWidth`) and
    the nav neither collides nor clips.
17. `level-0.html` … `level-4.html` and `line-of-sight.html` still open and still navigate.
18. `cd spc-lab && PYTHONPATH=src .venv/bin/python -m pytest tests -q` still passes
    (9 tests). No `spclab` behaviour changes in this work.
19. A `diagrams/spc-landing-flow.{mmd,excalidraw,svg,png}` set exists showing how the
    absorbed hub, the level pages and the applied section now link together.

---

## 2. The picked mock

`mock-landing.html`, three directions, screenshots captured at 1485px.
**Pick: "B hero + A spine"** — B's in-flow full-bleed chart and four phase doors as the
opening act, then A's five-row numbered spine as the syllabus, then A's applied rows.

Rejected: C (contents rail — the rail is the fixed-chrome pattern `DESIGN.md` is hostile
to, and at 216px every label wrapped to three lines). Rejected from B as drawn: demoting
the levels to a compact index. Rejected from A as drawn: an opening screen with no image.

Mock file deleted after the pick, per the throwaway rule.

---

## 3. Not in scope

- **No deploy.** No GitHub repo, no Pages, no DNS. Still the standing open item, and
  `spc-lab/README.md` stays a raw-markdown link.
- No new Manim renders, no re-render for colour.
- Narration stays **gTTS**, not your voice.
- No real Line of Sight case studies — the placeholder narratives stay.
- No changes to `level-0.html` … `level-4.html` beyond repointing `level-0`'s back-link.
- No changes to `spclab` Python, formulas, or test expectations.
- No print stylesheet.
- No mobile-specific redesign beyond check 16 (must not overflow or collide at 320px).

## 4. Defaults taken

Approving this contract confirms these. Each is reversible; say so and I change it.

1. **The nav stops being fixed.** It scrolls away with the document. Required by check 2
   and by the `DESIGN.md` ban on fixed chrome; it also removes the second of the two bars
   the old page had.
2. **The old fixed process-monitor strip is not kept in any form.** Its job is taken over
   by the in-flow hero chart, which carries the same four-phase narrative as navigation
   instead of as decoration.
3. **The hero chart is static on load, not scroll-linked.** The trace draws once with all
   four phases visible at the same time, because the phases are now doors that must all be
   clickable without scrolling. Reversible: say so and I re-link it to scroll.
4. **Headline is "Every number on this chart can be derived."** Copy was open to rewrite;
   the old hiring headline ("I find the drift before it finds the scrap bin") moves down
   to the applied section rather than being deleted.
5. **`index.html` becomes the curriculum entry point**, so `Writing` leaves the nav and is
   replaced by `Curriculum` / `Line of Sight` / `Applied` / `CV`.
6. **Toolbox compresses** to a single band near the footer rather than owning a numbered
   section of its own.
7. **All keepers stay interactive** — Lab A, Lab B and the two-audiences toggle keep their
   JS; none is downgraded to a static figure.

---

## 5. Supersedes

`specs/spc-curriculum-contract.md`:
- **Check 1** ("Open `spc-from-first-principles.html` → …") — that page is deleted; the
  same seamless-ground check now applies to `index.html`.
- **Default 6** ("`index.html` stays the entry point and keeps its current section
  structure … Reskin, not rewrite") — reversed. Composition and copy were both reopened
  because the reskin left the landing page as the only surface not actually built to the
  frozen system: a fixed 150px monitor strip, 15–17px body against a 21px scale, and a
  ~90ch measure against the 58–64ch rule.

---

## 6. Verification

After the build, checks 1–19 are re-run literally in a browser and read back **from this
file, not from memory**. A correction from you updates this contract and `DESIGN.md`, not
just the instance.
