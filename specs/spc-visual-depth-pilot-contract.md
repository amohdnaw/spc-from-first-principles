# Outcome contract — SPC visual-depth pilot

Agreed 2026-09-01. This contract governs the visual-depth pilot on SPC Level 7,
`Evidence and decisions`. The sibling contract is
`~/msa-from-first-principles/specs/msa-visual-depth-pilot-contract.md`.

The pilot tests one production pattern before it is considered for the other
seventeen levels across both curricula. The frozen system in `DESIGN.md` still
governs the page.

For this visual-depth pilot only, this contract supersedes prior no-human-voice
clauses after both pilot levels are locked. Synthetic narration is the iteration
voice. Ammar's recording is the final locked cut.

## What you will see

1. Open `level-07.html`. The chapter remains readable from start to finish without
   completing a challenge, signing in, or watching a video.
2. Before Act A explains the trade, the page asks the learner to predict what happens
   when a chart gains more signal rules. The prediction does not affect access or a
   score.
3. Act A builds one persistent visual model. A process distribution, a shifted
   distribution, and one decision boundary remain on screen while false alarms and
   missed shifts appear as areas. The motion establishes the trade before the symbols
   α and β appear.
4. Act A shows why a point can be inside the limits and still carry evidence. The
   p-value and the chart verdict appear as different objects, not two labels on one
   number.
5. Act B uses a masked manufacturing case. The case states the expected shift size,
   false-alarm cost, missed-shift cost, and sampling cadence. It contains no customer,
   product, part, or employee identifier.
6. Act B asks which signal rule set earns its false alarms for that case. The act
   prices the learner's choice. It does not claim that one rule set always wins.
7. The old Level 7 act is replaced by Act A. The page does not retain a redundant cut
   that teaches the same argument twice.
8. The two acts normally total 12–18 minutes. Runtime is not a gate. A shot stays only
   when it creates, transforms, tests, or applies the visual model.
9. After Act B, one optional challenge presents unseen data and a different surface
   story. The learner chooses `Rule 1 only`, `Rules 1 + 2`, or `All four Western
   Electric rules`, then selects which of the same four case fields justifies the
   choice: expected shift size, false-alarm cost, missed-shift cost, or sampling
   cadence. Repeating the video's arithmetic cannot pass.
10. The pass condition chooses the lowest computed expected cost from those same four
    fields. A wrong answer names the mismatched field using the same label, shows the
    competing computed costs at printed precision, and retries with new data. The page
    never responds with only a red verdict.
11. Passing saves Level 7 progress in the browser. If storage is unavailable, the
    challenge still works for the current visit and says that progress was not saved.
12. The level exposes three secondary paths without replacing the chapter:
    `Use this when…` gives the field answer, `Evidence` shows the functions, seed, and
    tests, and a contextual link opens the matching SPC platform task.
13. The platform link appears only after the decision it serves. The page does not add
    a generic product banner.
14. If either video is unavailable, the prose and transcript still carry the full
    derivation. The page does not mark the act watched.
15. Captions, transcript, and static keyframes preserve the argument when the learner
    reduces motion.
16. The finished acts have 1080p60 video, decoded audio bytes, non-empty WebVTT cues, a
    scored poster, and faststart playback.
17. With audio muted, a reviewer can state the qualitative causal claim from the
    motion. If narration owns the causal link, the storyboard fails.
18. No symbol appears before its quantity exists as an area, distance, repetition, or
    physical action.
19. Video, prose, challenge, and tests read the same `spclab` functions or compare
    against them at printed precision. No result is typed into more than one layer.
20. One novice explains the error trade and one practitioner chooses the plant action
    without coaching. Both must succeed before this pattern is proposed for another
    level.
21. The incorrect Level 7 figure captions are repaired before pilot review. Figure 7.2
    must describe the two-error or power view shown in its image. Figure 7.3 must
    describe the Western Electric rule trade shown in its image.

## Approved visual direction

Direction B, `What error are you buying?`, was selected from three pilot directions.
The three approved outcome views are:

- `diagrams/spc-msa-visual-depth-learning-loop.png`
- `diagrams/spc-msa-visual-depth-four-layers.png`
- `diagrams/spc-msa-visual-depth-production.png`

The production flow is stored as editable and rendered artifacts:

- `diagrams/spc-msa-visual-depth-flow.mmd`
- `diagrams/spc-msa-visual-depth-flow.excalidraw`
- `diagrams/spc-msa-visual-depth-flow.svg`
- `diagrams/spc-msa-visual-depth-flow.png`

These images are schematic approval artifacts. They define the teaching sequence,
information hierarchy, and production gates. They are not Manim storyboards or the
animation quality target.

**Amendment 1, 2026-09-02 — Act A gets a physical opening.** Ammar watched the synthetic
candidate and returned: *"Still too technical where simple process are not properly
visualised, we have visualised the actual graphs and maths, but not a proper physical
things."* Act A's first object today is an `Axes`, so the level asks the viewer to accept a
density curve before anything physical has been shown. The sibling MSA repository already
carries an opening grammar for exactly this correction, in
`specs/act-opening-contract.md`; this repository had none.

Shot `A0`, specified in `storyboards/spc-level-07-act-a.html`, is added in front of `A1`.
It shows parts arriving on a belt at their own measured heights, the later ones visibly
taller, and then collapses the belt: the parts slide out of their time slots and stack by
height into the curve `A1` opens on.

Two checks come with it, and they are the reason the shot is worth its runtime:

1. **The opening contains an act, not only objects.** Something arrives, drifts, or
   stacks. A frame full of physical shapes in which nothing happens fails this check.
2. **The handover morphs and never cuts.** There must exist a single frame in which the
   belt and the forming curve are both on screen. A fade from a factory shot to an axis is
   a cut dressed as a fade, and it would leave the axis as unexplained as it is today while
   costing a minute of runtime.

The part heights and the drift point are read from `spclab.evidence`, the same source `A1`
plots, so the belt and the board cannot disagree about how far the mean moved.

## Production sequence

1. Write one visual claim for the act.
2. Approve a shot-level storyboard that names the persistent object, surprise,
   transformation, counterexample, and decision.
3. Compute geometry and readouts from tested `spclab` functions.
4. Build the Manim cut with synthetic narration driving timing.
5. Build the unseen-data challenge and its exact feedback.
6. Watch every numerical, media, progress, and failure-state gate fail on a sabotaged
   copy before trusting it.
7. Record Ammar's voice only after the storyboard, visuals, script, and browser
   experience are locked.

## Failure behaviour

- A calculation failure preserves the learner's answer, names the failure, and never
  guesses a verdict or marks completion.
- A storage failure keeps the challenge usable for the current visit and never shows a
  false saved state.
- A video failure leaves the written derivation and transcript usable and never shows a
  false watched state.
- A wrong answer explains the faulty premise and retries with new data.

## Not in scope

- Rebuilding any SPC level other than Level 7.
- Adding video to SPC Levels 10–12.
- Accounts, certificates, public rankings, or cross-device progress.
- Sitewide search or a full reference-mode redesign.
- New design tokens or a change to `DESIGN.md`.
- Publishing human narration before both pilot levels are locked.
- Real company data or identifiers.

## Defaults taken

- Reading stays open. Mastery is optional.
- Progress stays in the browser. There is no login or platform sync.
- Synthetic voice remains the iteration tool. Ammar's voice is the final locked cut.
- The masked case uses realistic semiconductor or manufacturing decisions.
- The pilot scales only after the SPC and MSA levels pass the same visual, numerical,
  browser, and human-use gates.
- After the pilot, each remaining level receives one verdict: keep its current act,
  rewrite one act, or earn a selective Act B. Two acts are never automatic.
