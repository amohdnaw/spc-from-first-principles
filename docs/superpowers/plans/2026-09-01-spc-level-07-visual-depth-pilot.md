# SPC Level 7 Visual-Depth Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn SPC Level 7 into a causal two-act lesson with an optional unseen-data decision, exact feedback, local mastery state, field-reference paths, and a contextual SPC platform seam.

**Architecture:** Python remains the numerical source of truth. `spclab` computes the rule-set trade, deterministic challenge cases, answers, and feedback values; `chapterise.py` embeds that data into the static chapter; small page-local JavaScript handles interaction and storage without reimplementing statistics. Manim Act A builds the error model; a new Act B applies one masked plant case. The frozen page grammar and tokens remain unchanged.

**Tech Stack:** Python 3.12, NumPy, pytest, Manim, manim-voiceover/Kokoro/RecorderService, static HTML/CSS/vanilla JavaScript, WebVTT, ffmpeg/ffprobe.

**Outcome contract:** `specs/spc-visual-depth-pilot-contract.md`

**Workflow artifacts:** `diagrams/spc-msa-visual-depth-flow.{mmd,excalidraw,svg,png}` and `diagrams/spc-msa-visual-depth-implementation.html`

---

## File map

| Responsibility | Path |
|---|---|
| Rule simulation and existing Level 7 claims | `spc-lab/src/spclab/evidence.py` |
| Deterministic transfer cases and expected-cost decision | `spc-lab/src/spclab/level07_mastery.py` (new) |
| Act A: persistent alpha/beta/power model | `spc-lab/src/spclab/level07_scene.py` |
| Act B: masked rule-set purchase | `spc-lab/src/spclab/level07_case_scene.py` (new) |
| Computation tests | `spc-lab/tests/test_level07_mastery.py` (new) |
| Static page and progress contract tests | `spc-lab/tests/test_level07_page.py` (new) |
| Media container and voice gates | `spc-lab/tests/test_level07_media.py` (new), `spc-lab/src/spclab/voice_check.py` (new), `spc-lab/tests/test_level07_voice.py` (new), `spc-lab/build-media.sh` |
| Generated chapter structure and embedded case JSON | `tools/chapterise.py` |
| Persistent CSS, JavaScript, figures, and captions | `tools/page-sources/level-07.html` |
| Served artifact | `level-07.html` |
| Synthetic/final media | `spc-lab/media/videos/level07*_scene/1080p60/`, `posters/level07*.jpg`, `captions/level07*.vtt` |
| Shot approval | `storyboards/spc-level-07-act-a.html`, `storyboards/spc-level-07-act-b.html` (new) |
| Human-use evidence | `docs/evidence/spc-level-07-pilot.html` (new) |

## Invariants

1. Never edit `level-07.html` as the source. Edit `tools/page-sources/level-07.html` and `tools/chapterise.py`, then regenerate.
2. JavaScript never computes ARLs, expected costs, p-values, or answer keys. It reads Python-generated JSON.
3. Act A and Act B import the same `spclab` values used by the page and tests.
4. Reading, transcripts, and derivations remain available without video, JavaScript, storage, or challenge completion.
5. No new design tokens, radii, gradients, generic product banner, account state, or cross-device sync.

---

### Task 1: Create the isolated implementation branch and prove the baseline

This task changes no product files.

- [ ] **Step 1: Create a worktree**

Invoke `@using-git-worktrees` in `/home/ammar/portfolio` and create branch `feat/spc-level-07-visual-depth`.

- [ ] **Step 2: Run the narrow baseline**

Run:

```bash
cd spc-lab
PYTHONPATH=src .venv/bin/pytest tests/test_evidence.py tests/test_page_claims.py -q
```

Expected: PASS. Record the exact count in `implementation-notes.html`.

- [ ] **Step 3: Regenerate Level 7 without changing it**

Run from the repo root:

```bash
PYTHONPATH=spc-lab/src spc-lab/.venv/bin/python tools/chapterise.py level-07.html
node tools/typeset.mjs level-07.html
```

Expected: `level-07.html` rebuilds from `tools/page-sources/level-07.html`; the existing narrow tests still pass.

- [ ] **Step 4: Commit only if regeneration exposed tracked drift**

Do not commit a byte-identical baseline.

---

### Task 2: Lock shot-level storyboards before Manim code

**Files:**
- Create: `storyboards/spc-level-07-act-a.html`
- Create: `storyboards/spc-level-07-act-b.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Write Act A's visual claim**

Use one sentence: \"Every added signal rule buys earlier detection by spending a fixed stream of false alarms.\"

- [ ] **Step 2: Build Act A's shot table**

The HTML must name, per shot: persistent object, learner prediction, transformation, surprise, counterexample, formula reveal, camera move, narration line, and exit state. Required sequence:

1. One in-control curve, one shifted curve, one decision boundary.
2. False-alarm and missed-shift areas exist before `α` and `β`.
3. The shift tracker moves continuously; power appears as changing area, not a table.
4. A 2.5σ point separates \"inside limits\" from \"weak evidence.\"
5. Rules 1, 1+2, and all four change both ARL0 and detection delay on one persistent cost board.

- [ ] **Step 3: Build Act B's shot table**

Use one masked line, no company/product/part/person identifiers. Required sequence:

1. Reveal expected shift size, false-alarm cost, missed-shift cost, and sampling cadence.
2. Ask for a rule-set choice before totals appear.
3. Price `Rule 1 only`, `Rules 1 + 2`, and `All four` from the same case.
4. Change one premise and show the winner change.
5. End on a plant action, not a formula recap.

- [ ] **Step 4: Review visually**

Open both with `review-open`; render with `shot`; read the PNGs. Reject any shot where narration carries the causal link or motion merely decorates a label.

- [ ] **Step 5: Commit**

```bash
git add storyboards/spc-level-07-act-a.html storyboards/spc-level-07-act-b.html implementation-notes.html
git commit -m "design: lock SPC Level 7 storyboards"
```

---

### Task 3: Add the deterministic expected-cost model

**Files:**
- Create: `spc-lab/src/spclab/level07_mastery.py`
- Create: `spc-lab/tests/test_level07_mastery.py`
- Modify: `spc-lab/src/spclab/__init__.py`

- [ ] **Step 1: Write the failing choice tests**

The tests must cover all three rule-set winners, both allowed shift sizes, deterministic seeds, no ties at printed precision, and a retry bank whose surface stories contain no project identifiers.

```python
from spclab.level07_mastery import CASE_SEEDS, challenge_case, expected_cost


def test_seed_bank_exercises_every_rule_set():
    assert {challenge_case(seed)["answer"] for seed in CASE_SEEDS} == {
        "rule-1", "rules-1-2", "all-four"
    }


def test_expected_cost_prices_delay_and_false_alarms():
    case = challenge_case(CASE_SEEDS[0])
    for option in case["options"]:
        assert option["expected_cost"] == expected_cost(
            option["rules"],
            expected_shift_size=case["expected_shift_size"],
            false_alarm_cost=case["false_alarm_cost"],
            missed_shift_cost=case["missed_shift_cost"],
            sampling_cadence=case["sampling_cadence"],
        )
```

- [ ] **Step 2: Run the new tests and watch them fail**

```bash
cd spc-lab
PYTHONPATH=src .venv/bin/pytest tests/test_level07_mastery.py -q
```

Expected: FAIL because `spclab.level07_mastery` does not exist.

- [ ] **Step 3: Implement the minimal decision API**

Use these public names and units:

```python
RULE_OPTIONS = {
    "rule-1": (1,),
    "rules-1-2": (1, 2),
    "all-four": (1, 2, 3, 4),
}
SHIFT_GRID = (1.0, 3.0)
CASE_SEEDS = tuple(range(701, 713))


def _rule_key(rules: Sequence[int]) -> tuple[int, ...]:
    key = tuple(rules)
    if key not in RULE_OPTIONS.values():
        raise ValueError(f"unknown rule set: {key}")
    return key


def expected_cost(rules: Sequence[int], *, expected_shift_size, false_alarm_cost,
                  missed_shift_cost, sampling_cadence):
    key = _rule_key(rules)
    delay = detection_delay(key, expected_shift_size)
    expected_false_alarms = delay / false_alarm_run_length(key)
    delay_minutes = delay * sampling_cadence
    return expected_false_alarms * false_alarm_cost + delay_minutes * missed_shift_cost
```

`false_alarm_run_length()` must read `TRADE[key]["arl0"]`. `detection_delay()` must read `TRADE[key]["arl1"]` at 1σ and a deterministic cached `average_run_length()` result at 3σ. Do not copy numeric results into the module. Add a boundary test proving `expected_cost([1, 2], ...) == expected_cost((1, 2), ...)`.

`challenge_case(seed)` returns JSON-safe data with these keys:

```python
{
    "seed": 701,
    "surface_story": "Masked line ...",
    "expected_shift_size": 1.0,
    "false_alarm_cost": 120.0,
    "missed_shift_cost": 8.0,
    "sampling_cadence": 15.0,
    "deciding_field": "missed-shift cost",
    "options": [
        {"id": "rule-1", "rules": [1], "expected_cost": 0.0},
        {"id": "rules-1-2", "rules": [1, 2], "expected_cost": 0.0},
        {"id": "all-four", "rules": [1, 2, 3, 4], "expected_cost": 0.0},
    ],
    "answer": "all-four",
}
```

Blueprints may type input assumptions and masked stories; all costs, ARLs, winners, and feedback values must be computed. Each blueprint's `deciding_field` must be validated by a counterfactual test that restoring that field to its neutral value removes or flips the winner.

- [ ] **Step 4: Run the focused tests**

Expected: PASS, including a test that every gate first failed on a sabotaged formula.

- [ ] **Step 5: Commit**

```bash
git add spc-lab/src/spclab/level07_mastery.py spc-lab/src/spclab/__init__.py spc-lab/tests/test_level07_mastery.py
git commit -m "feat: compute Level 7 transfer decisions"
```

---

### Task 4: Rebuild Act A from the approved storyboard

**Files:**
- Modify: `spc-lab/src/spclab/level07_scene.py`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Keep one persistent model**

Retain `NarratedCameraScene`, `act_style`, and `spclab.evidence`. Remove any shot that redraws a concept already visible. The curves, boundary, error areas, and cost board must transform in place.

- [ ] **Step 2: Delay symbols until geometry exists**

Create the false-alarm and missed-shift areas first. Only then transform their plain-language labels into `α` and `β`.

- [ ] **Step 3: Make the inside-limit point a separate evidence object**

The point's chart verdict and p-value must occupy different screen objects and survive long enough to compare.

- [ ] **Step 4: Make rule purchases continuous**

Use one cost board with three stops: rule 1, rules 1+2, all four. Read every number from `TRADE` or `level07_mastery`; no strings containing copied ARLs.

- [ ] **Step 5: Render a silent draft**

```bash
cd spc-lab
PYTHONPATH=src .venv/bin/manim -qh --disable_caching src/spclab/level07_scene.py Level07
```

Expected: render succeeds. Watch muted. Reject if the alpha/beta trade or rule purchase cannot be stated from motion alone.

- [ ] **Step 6: Commit**

```bash
git add spc-lab/src/spclab/level07_scene.py implementation-notes.html
git commit -m "feat: rebuild SPC Level 7 causal act"
```

---

### Task 5: Build the masked Act B

**Files:**
- Create: `spc-lab/src/spclab/level07_case_scene.py`
- Modify: `spc-lab/build-media.sh`

- [ ] **Step 1: Create `Level07Case`**

Import one fixed `challenge_case()` seed. Show the four named case fields before the rule-set totals. Use the same option IDs as the transfer challenge.

- [ ] **Step 2: Price all three options**

The expected-cost bars and printed totals must read the case's generated `options`. A transformed counterexample changes one premise and recomputes the winner.

- [ ] **Step 3: Register the second act**

Add:

```bash
"level07_case_scene:Level07Case:level07-case"
```

to `SCENES` in `spc-lab/build-media.sh`.

- [ ] **Step 4: Render a silent draft**

```bash
cd spc-lab
ONLY=Level07Case ./build-media.sh
```

Expected: `Level07Case.mp4`, `posters/level07-case.jpg`, and no copied calculation paths.

- [ ] **Step 5: Commit**

```bash
git add spc-lab/src/spclab/level07_case_scene.py spc-lab/build-media.sh
git commit -m "feat: add SPC Level 7 plant case act"
```

---

### Task 6: Add the optional mastery loop and secondary paths

**Files:**
- Modify: `tools/chapterise.py`
- Modify: `tools/page-sources/level-07.html`
- Modify: `level-07.html` (generated)
- Create: `spc-lab/tests/test_level07_page.py`

- [ ] **Step 1: Write failing DOM-contract tests**

Test the served DOM, not implementation strings. Assert:

1. The chapter's prose precedes and remains outside the optional mastery form.
2. Prediction appears before Act A.
3. Both videos have posters and caption tracks.
4. Transfer case JSON contains the full seed bank and Python-computed answers.
5. Retry and saved-progress status have `aria-live` output.
6. `Use this when…`, `Evidence`, and `https://spc.amohdnaw.xyz/app#g-weco` appear after the decision.
7. Figure 7.2 describes the two-error/power image; Figure 7.3 describes the Western Electric trade.

Run and watch the new tests fail.

- [ ] **Step 2: Generate the page data**

In `chapter_07()`, import `challenge_case` and `CASE_SEEDS`, JSON-encode the cases, and emit them in:

```html
<script type="application/json" id="level07-cases">...</script>
```

Never calculate a winner in JavaScript.

- [ ] **Step 3: Add the four-stage mastery markup**

Use existing tokens and square edges:

1. `Predict` radio question before Act A.
2. Act A player and transcript.
3. Act B player and transcript.
4. Transfer form with rule-set choice and deciding-field choice.

The form is optional and never disables navigation or prose.

- [ ] **Step 4: Add page-local interaction**

Use `textContent`, `createElement`, and `appendChild`; never use `innerHTML` for generated case content. Store under `spc-fp:mastery:v1`:

```js
{
  "level-07": {
    "prediction": "more-signals",
    "watched": {"act-a": true, "act-b": true},
    "passed": true,
    "seed": 706
  }
}
```

Wrap every storage read/write in `try/catch`. On failure, keep the current case active and say `Progress was not saved.` Set watched state only on the video's `ended` event; never on `play`, `loadedmetadata`, or `error`.

Wrong-answer feedback must name one of the four contract labels, show all three Python-generated costs at printed precision, preserve the learner's submitted choices, then load a different seed only when `Retry with new data` is pressed.

- [ ] **Step 5: Add the secondary paths**

After the transfer decision:

- `Use this when…`: concise field answer about small shifts, false-alarm cost, and sampling cadence.
- `Evidence`: `spclab.level07_mastery`, seed, `test_level07_mastery.py`, and the three option totals.
- `Open the WECO task`: `https://spc.amohdnaw.xyz/app#g-weco`, `target="_blank"`, `rel="noopener"`.

- [ ] **Step 6: Correct the two Level 7 captions in the source**

Do not touch Level 11 under this pilot.

- [ ] **Step 7: Regenerate and typeset**

```bash
PYTHONPATH=spc-lab/src spc-lab/.venv/bin/python tools/chapterise.py level-07.html
node tools/typeset.mjs level-07.html
```

- [ ] **Step 8: Run the page tests**

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add tools/chapterise.py tools/page-sources/level-07.html level-07.html spc-lab/tests/test_level07_page.py
git commit -m "feat: add SPC Level 7 mastery loop"
```

---

### Task 7: Add media, caption, container, and voice gates

**Files:**
- Modify: `spc-lab/build-media.sh`
- Create: `spc-lab/tests/test_level07_media.py`
- Create: `spc-lab/src/spclab/voice_check.py`
- Create: `spc-lab/tests/test_level07_voice.py`
- Modify: `spc-lab/tests/test_page_claims.py`

- [ ] **Step 1: Write failing media tests**

For both `Level07.mp4` and `Level07Case.mp4`, assert: 1920×1080, 60 fps, a decoded non-empty audio stream, `moov` before `mdat`, non-empty WebVTT cues, non-empty scored poster, and a build manifest naming scene, service, duration, poster time, and cue count.

- [ ] **Step 2: Add the decoded-audio instrument**

Port the calibrated PCM/F0/voiced-frame estimator pattern from the sibling MSA repo into `spclab.voice_check`. Scope `test_level07_voice.py` to `level07_scene` and `level07_case_scene` only. Assert decoded audio bytes, voiced fraction above 0.25, duration above 30 seconds, a recognized manifest service, and the Kokoro explainer band while the service is `kokoro`.

- [ ] **Step 3: Make `build-media.sh` emit the manifest**

Write one JSON file beside each final MP4. Values come from `ffprobe`, the selected poster scorer result, cue count, and `${SPCLAB_VOICE_SERVICE:-kokoro}`.

- [ ] **Step 4: Prove the gates are not vacuous**

Run each sabotage separately and observe failure: remove the audio stream, replace decoded audio with silence, remove one cue, move `moov` behind `mdat`, set frame rate to 30, zero the poster, and set manifest service to an unrecognised value. Restore after each.

- [ ] **Step 5: Update the index runtime gate**

Confirm `test_runtime_claim_matches_the_rendered_acts` counts `level07_case_scene`. Regenerate the index claim if the total minute floor changes.

- [ ] **Step 6: Commit**

```bash
git add spc-lab/build-media.sh spc-lab/src/spclab/voice_check.py spc-lab/tests/test_level07_media.py spc-lab/tests/test_level07_voice.py spc-lab/tests/test_page_claims.py index.html
git commit -m "test: gate SPC pilot media"
```

---

### Task 8: Render the synthetic lock candidate

**Files:** Generated media, captions, posters, manifests, and the page references.

- [ ] **Step 1: Render Act A with Kokoro**

```bash
cd spc-lab
SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=kokoro ONLY=Level07 ./build-media.sh
```

- [ ] **Step 2: Render Act B with Kokoro**

```bash
SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=kokoro ONLY=Level07Case ./build-media.sh
```

- [ ] **Step 3: Run focused numerical and media gates**

```bash
PYTHONPATH=src .venv/bin/pytest tests/test_evidence.py tests/test_level07_mastery.py tests/test_level07_page.py tests/test_level07_media.py tests/test_level07_voice.py tests/test_page_claims.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit the synthetic candidate**

Commit only after the videos, captions, posters, and manifests are all present and the page points at them.

---

### Task 9: Verify the real browser experience and failure states

**Files:**
- Create: `docs/evidence/spc-level-07-browser.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Serve the repo and open the real page**

From the SPC worktree root, start the server with:

```text
hub(op="start", name="spc-pilot-http", application="python3",
    args=["-m", "http.server", "8765"], cwd=".",
    ready={"port": 8765, "timeout": 15})
```

Open the live human view with:

```bash
review-open http://127.0.0.1:8765/level-07.html
```
Open the interactive automation tab through `xd://browser`, which is a mounted OMP device in this harness:

```text
write(path="xd://browser",
      content="{\"action\":\"open\",\"name\":\"spc-level-07\",\"url\":\"http://127.0.0.1:8765/level-07.html\"}")
```

- [ ] **Step 2: Exercise the full loop**

Predict → play both acts → submit a wrong rule set → verify exact field feedback and preserved answer → retry → verify new seed → pass → reload → verify progress survives.

- [ ] **Step 3: Exercise storage failure**

Override `Storage.prototype.setItem` to throw. Verify the challenge still works and reports `Progress was not saved.` No false saved state.

- [ ] **Step 4: Exercise media failure**

Abort each MP4 request in turn. Verify prose, transcript, and challenge remain usable and the failed act is not marked watched.

- [ ] **Step 5: Verify reduced motion and layouts**

Use `shot` and read all PNGs: light and dark if the site supports both; desktop and mobile; reduced-motion emulation; no overflow; no new radius or token drift.

- [ ] **Step 6: Record evidence and commit**

The evidence HTML must list exact URLs, viewport sizes, storage/media sabotage, observed states, and screenshots. No generic \"works\" row.

---

### Task 10: Run the two-person human gate and lock the pilot

**Files:**
- Create: `docs/evidence/spc-level-07-pilot.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Run the novice session**

Without coaching, ask one novice to predict, watch muted where possible, and explain the false-alarm versus missed-shift trade. Pass only if they can state why more rules are not automatically better.

- [ ] **Step 2: Run the practitioner session**

Give one practitioner the transfer case. Pass only if they choose the computed plant action and can name the field that changes the choice.

- [ ] **Step 3: Record facts, not identities**

Store role, task, observed decision, failure point, retry, and pass/fail. Do not store employer, product, part, employee ID, or customer information.

- [ ] **Step 4: Fix and rerun any failed gate**

A narrated explanation that compensates for unclear motion is a storyboard failure, not a script fix.

- [ ] **Step 5: Commit the locked synthetic pilot**

```bash
git add docs/evidence/spc-level-07-pilot.html implementation-notes.html
git commit -m "test: pass SPC Level 7 human gate"
```

---

### Task 11: Record Ammar's final voice after both pilots lock

**Dependency:** The MSA Level 4 plan must also have passed its browser and human gates.

**Files:** Pilot media, captions, manifests, `spc-lab/tests/test_level07_media.py`, `spc-lab/tests/test_level07_voice.py`.

- [ ] **Step 1: Tighten the final voice gate**

Change the Level 7-scoped voice test so both manifests must say `recorder`; retain decoded-audio and voiced-fraction checks. Do not assert a Kokoro pitch band for human recordings.

- [ ] **Step 2: Watch the tightened gate fail on the synthetic manifests**

Expected: FAIL with `kokoro != recorder` for both acts.

- [ ] **Step 3: Record Act A**

```bash
cd spc-lab
SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=recorder ONLY=Level07 ./build-media.sh
```

- [ ] **Step 4: Record Act B**

```bash
SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=recorder ONLY=Level07Case ./build-media.sh
```

- [ ] **Step 5: Run the focused suite and browser smoke again**

Expected: all numerical, page, media, storage, and failure-state checks pass; browser playback has decoded audio and matching cues.

- [ ] **Step 6: Commit**

```bash
git add spc-lab/media/videos/level07_scene spc-lab/media/videos/level07_case_scene posters/level07.jpg posters/level07-case.jpg captions/level07.vtt captions/level07-case.vtt spc-lab/tests/test_level07_media.py spc-lab/tests/test_level07_voice.py
git commit -m "feat: lock SPC Level 7 human narration"
```

---

### Task 12: Final SPC checkpoint

- [ ] **Step 1: Run the complete SPC lab suite**

```bash
cd spc-lab
PYTHONPATH=src .venv/bin/pytest -q
```

Expected: PASS with a non-zero test count; compare against the baseline count plus new tests.

- [ ] **Step 2: Re-run the real page**

Use the served `level-07.html`, not a fixture. Complete one fresh challenge, inspect saved state, and play both final videos.

- [ ] **Step 3: Update audit trails**

Update `implementation-notes.html`, `~/agent-ledger/NOW.md`, and `~/agent-ledger/changes.md`; run `brain index` after memory updates.

- [ ] **Step 4: Stop before rollout**

Do not touch another SPC level. Scaling requires both pilot repos to pass the shared gate and a new approved contract.
