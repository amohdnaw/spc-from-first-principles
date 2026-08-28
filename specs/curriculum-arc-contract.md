# Outcome contract — the twelve-level arc

Agreed 2026-08-27. Governs the expansion of the SPC curriculum from five levels to
twelve, and the split of measurement-systems analysis into a sibling site.

Design stays frozen in `DESIGN.md`. The craft rules for acts stay frozen in
`spc-manim-craft-contract.md`. This contract governs **what is taught, in what
order, and in which medium** — nothing else.

---

## 0. Who this is for

Two readers, and every level must serve both:

- **Someone with no statistics.** They should finish a level intrigued rather than
  filtered out. No level may assume a term the arc has not already earned.
- **Someone who has to do the job.** SPC, MSA, and manufacturing statistics at
  practitioner depth — AIAG-shaped where AIAG has a view, derived rather than quoted.

The existing rule holds and is what makes both possible: **no number is asserted.**
Every constant on screen is computed at render time by `spclab`, and the tests check
the same functions the videos read from.

---

## 1. The arc

Three parts, twelve levels. Each level answers a question the previous one raised,
and ends by raising the next. That chain is the contract — a level that does not
hand something to its successor is in the wrong place.

### Part I — Foundations · medium: video

| # | Level | The one idea | Hands on | Status |
|---|---|---|---|---|
| 1 | Variation | Nothing repeats. Two "identical" parts differ, and many parts make a shape nobody chose. Population vs sample. | histogram builds itself from parts | **new act** |
| 2 | Chance | Probability as long-run frequency. Independence, expectation. What a statement like "0.27 %" is a claim *about*. | — | **new act** |
| 3 | Centre and spread | The mean is a balance point; spread has to be squared first; why the divisor is n−1. | — | exists (`level-0`) |
| 4 | The average is predictable | One part is noise, many parts are information. Sampling distribution, CLT, σ/√n. | — | exists (`level-1`) |
| 5 | Estimation and uncertainty | Every estimate carries error. Standard error becomes a confidence interval — including for the constants used later in the arc. | interval narrows as n grows | **new act** |

### Part II — The control chart · medium: video

| # | Level | The one idea | Status |
|---|---|---|---|
| 6 | Limits are a hypothesis test | ±3σ is not taste, it is a bet: 99.73 % in, one false alarm per 370 subgroups. | exists (`level-2`) |
| 7 | Evidence and decisions | α and β, p-values, power, and the Western Electric rules as *evidence* rules. Adding rules buys sensitivity with false alarms — the trade is arithmetic, not opinion. | **new act**, absorbs the `WERules` scene |
| 8 | Capability | Cp, Cpk, ppm. Voice of the process against voice of the customer. | exists (`level-3`) |
| 9 | Detection | ARL. Shewhart forgets every point; EWMA remembers. Memory beats sensitivity on drift. | exists (`level-4`) |

### Part III — Manufacturing statistics · medium: interactive lab

| # | Level | The one idea | Status |
|---|---|---|---|
| 10 | Counting, not measuring | Attribute data: binomial and Poisson, p/np/c/u charts, chart selection, rational subgrouping. Annex: capability when the distribution is not normal. | **new lab** |
| 11 | Relationships | Least squares, residuals, R², prediction intervals — then ANOVA as variance decomposition, which is the same arithmetic a Gage R&R runs on. | **new lab** |
| 12 | Experiments | Factorial DOE. Interactions are why one-factor-at-a-time fails. Screening, then response surface. | **new lab** |

Level 11 is deliberately the bridge: it ends by decomposing a variance into part,
operator, and interaction — and hands the reader to the MSA site mid-thought.

---

## 2. The MSA sibling

MSA gets its **own site**, not a level. It repeats the arc's method on a different
subject: the measurement system is itself a process, and it has variation.

Its own spine, to be contracted separately before it is built:
measurement as a process → repeatability against reproducibility → GR&R by ANOVA
(not average-and-range) → %GRR, ndc, and %tolerance against %study → bias,
linearity, stability → attribute agreement and kappa → the handshake back: a Cpk is
only as trustworthy as the gage that fed it.

Boundary rule: **the SPC site never teaches GR&R, and the MSA site never teaches
control limits.** Each links to the other exactly once, at the seam — Level 11 out,
and the MSA closing back to Level 8.

---

## 3. Renumbering — done once, now

The five published pages move into the single sequence. New paths are **zero-padded**,
and that is load-bearing rather than cosmetic: with plain numbers, `level-3.html` would
be both an old path (Capability) and a new path (Centre and spread), so a bookmark to
Capability would silently open the wrong topic. Silently wrong content is worse than a
404. Padding means no string is ever both an old path and a new one.

| Old URL | New URL | Old title | New title |
|---|---|---|---|
| `level-0.html` | `level-03.html` | Level 0 | Level 3 |
| `level-1.html` | `level-04.html` | Level 1 | Level 4 |
| `level-2.html` | `level-06.html` | Level 2 | Level 6 |
| `level-3.html` | `level-08.html` | Level 3 | Level 8 |
| `level-4.html` | `level-09.html` | Level 4 | Level 9 |

The same padding applies inside `spc-lab`, for the same reason — `level3_scene.py`
would otherwise mean Capability today and Centre-and-spread tomorrow. Modules become
`level03_scene.py` … `level09_scene.py`, scene classes `Level03` … `Level09`, and the
media, poster and caption basenames follow. On-screen and spoken text stays unpadded:
a title card reads **Level 3**, never "Level 03".

Consequences, all of them accepted:

- **15 places inside the acts name a level number** — on-screen titles and spoken
  narration lines such as "Level one told us which distribution every subgroup mean is
  drawn from". All are edited and all nine acts are rebuilt. This costs machine time
  and nothing else, because the voice is local.
- **This is the last cheap moment.** Renumbering after any line is recorded in
  Ammar's own voice would throw away takes. It happens before that, or not at all.
- **Old URLs are published**, including in an open PR against `portfolio-site`. Each
  old path keeps a stub that redirects to its new number and carries
  `rel="canonical"`, so nothing already shared 404s.
- Numbers are **frozen by this contract**. A twelve-slot map with five things in it
  only works if the empty slots hold still.

---

## 4. What you will see

Checkable in a browser, in order of delivery.

### After the renumber
1. `level-03.html` exists and its rail reads **Level 3**; the video's own title card
   reads **Level 3**, and the narration says "Level three".
2. Opening the old `level-0.html` lands you on `level-03.html` without a 404, and no
   old path resolves to a page about a different topic than it used to name.
3. No page anywhere says "Level 0", and no act speaks a number that disagrees with
   the page it sits on. Checked by grep across sources and by playing each act.
4. The index rail shows **twelve slots**, five live and seven marked as not yet
   written — an explicit gap, never a silent one.

### After each new level
5. The page follows the frozen system: dark ground, two voices, `FIGURE n.n`,
   numbered equations in real LaTeX, no horizontal overflow at 320 px.
6. A Part I or II level carries a **narrated act** meeting the craft contract:
   derived by motion, every `self.play` carrying an explicit `rate_func`, captions
   present, faststart applied.
7. A Part III level carries an **interactive lab** you can drag, computing its
   numbers in the browser from the same formulas the Python library tests.
8. Every level ends with a working link to the next, and the last links to the MSA
   site at the seam described in §2.

   **Clarified 2026-08-28, while writing Level 12.** These two clauses pulled apart
   once Level 12 existed: §2 fixes the seam at "Level 11 out" and allows exactly one
   link each way, so the last level cannot also carry one without breaking the count.
   Resolved in favour of §2, on content grounds as well as arithmetic — Level 11 ends
   on variance components, which is what a gauge study decomposes, whereas Level 12
   ends on factorial designs and has nothing to hand over. So: **Level 11 owns the
   single outbound MSA link; Level 12, as the last level, closes the arc and links back
   to the curriculum.** The chain reads 01 → … → 12 → index.

   A second finding, recorded because it cost a fix: three `next` links pointed past
   levels written later the same day (01→03, 04→06, 06→08). None of them 404'd, so this
   check passed while readers were walked over a level. **"Working" is not sufficient —
   the chain has to be walked, not just resolved.**
9. `pytest` covers any new library function, and no new page asserts a number that
   is not computed.

### Not in scope
- No change to `DESIGN.md`. If a new level needs a component that does not exist, it
  gets contracted separately rather than invented in place.
- No new video for Part III. Labs there are the decision, not a shortfall.
- No MSA content on this site beyond the single link.
- No reliability, Weibull, or acceptance-sampling material. Sampling plans and AQL
  are **explicitly deferred** — if they come back a second time they become a spec of
  their own rather than a silent third deferral.
- No human-voice re-record as part of this work. It stays a separate open call.

---

## 5. Order of work

1. ~~**Renumber**~~ — **DONE 2026-08-27 (`4fad4ec`)**, verified on the live Pages site.
   Sources, pages, redirect stubs, and all nine acts rebuilt. Checks 1–4 pass: five old
   paths each land on the topic they used to name (old `level-3.html` → Level 8
   Capability, which is the case the padding fix exists for); title cards read
   Level 3/4/6/8/9 and the caption tracks — generated from the spoken script — say
   "Level four told us"; rails show twelve slots with seven inert; figures and equations
   renumbered per page; 7 pages at 320 and 1440 with zero overflow; every internal link
   200; all nine mp4s play with poster, faststart and cues.
   One defect in this contract was found and fixed while executing it: the §3 table
   originally mapped to unpadded paths, which would have made `level-3.html` mean two
   different topics.
2. **Level 1, 2, 5** — the three foundation acts, in that order, one at a time.
3. **Level 7** — the evidence act, absorbing `WERules`.
4. **Levels 10, 11, 12** — the three labs.
5. **MSA sibling** — its own contract first, then its own build.

One level at a time, verified before the next starts. If the shape is wrong, only one
level is wasted.

**Completed 2026-08-28.** All twelve levels are written and live. Order actually
executed: renumber, then 1, 2, 5, 7, 10, 11, 12 — the four pre-existing levels (3, 4,
6, 8, 9) rebuilt as chapters along the way. Part I and II carry narrated acts (nine acts,
28 minutes); Part III carries three interactive labs and no video, as §4 intended. The
MSA sibling remains uncontracted and unbuilt; its own contract comes before anything is
made.

## 6. Verification

After each level: the checks in §4 are re-read **from this file, not from memory**,
and run against the built page at 1080p60 and at 320 px. A correction updates this
contract, not just the instance.
