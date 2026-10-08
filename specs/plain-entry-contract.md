# Outcome contract — plain entry: hooks and plain-words lines

Approved 2026-10-08. Trigger: the L5 human check failed (most readers "no idea"), and a
read from Level 1 found the site opens with jargon a newcomer stops at.
Readers to keep: shop-floor engineer, operator, manager, curious outsider (all four), so
every hook assumes no factory and no statistics background.
Picked mock: Direction A, the instrument panel (bordered try-it panel with dot strip and
two readout tiles; amber-ruled "In plain words" block).

## What you will see — pilot (home, Level 1, Level 2)

1. Home: the first screen is a plain-words story — at 2 a.m. every part was in spec; by
   6 a.m. the customer had rejected thousands; the machine drifted and nobody could see
   it. No symbol or jargon above the fold. The X̄ trace is the second screen, relabelled
   "the same drift, drawn as a chart". The d₂/A₂/Monte Carlo block moves down beside the
   curriculum list.
2. Level 1 opens, before the contents list, with a Direction A panel "Try it first ·
   20 parts": a part comes out 0.3 mm too big, adjust the machine? Clicking plays 20
   parts as dots; two tiles show "if you'd left it" vs "what you got" (about 41 % worse
   when adjusting); one plain sentence follows, ending "This level shows why."
3. Level 2 opens with a question panel in the same style: 8 heads in 10 flips, is the
   coin unfair? Yes / No / Can't tell; the reveal says a fair coin does it about 1 time
   in 18 (computed).
4. Every section in Levels 1 and 2 (10 sections) starts with an amber-ruled
   "In plain words" block: one or two everyday sentences, no symbols, no Greek. The
   existing text stays below unchanged.
5. Panels work by keyboard and at phone width with no sideways scroll; every number is
   computed by the build, none typed.

6. (Added 2026-10-08, Ammar pick "A + C graft".) Beside every hook panel, in the margin
   column (stacked below it under 1280 px), three notes: a first note that does not give
   the answer away (how to read it / before you pick), "You have done this" (an everyday
   version), and "The name for it" (the real term, linked to where the course covers it).
   Notes two and three appear only after the pick.

## After "go"

Levels 3–12: one hook each plus plain-words lines in about 50 more sections.
L3 two machines both average 50.00 mm — equally good? · L4 roll one die vs the average
of five · L5 five parts average 50.02 mm — how sure? · L6 the alarm everyone ignores ·
L7 the chart stays quiet — is the process fine? · L8 every part in spec — capable? ·
L9 the 2 a.m. drift, raced live · L10 4 bad out of 200 yesterday, 9 today ·
L11 faster cutting, rougher surface — how sure? · L12 tune two knobs one at a time.

## Not in scope

Rewriting the existing technical text; a plain/technical toggle; new videos; the MSA
site; glossary changes.

## Defaults taken

Pilot first (home + L1 + L2), then "go", as with the labs. Direction A styling within
DESIGN.md (radius 0, one accent, Panel + Readout tile grammar). Hook panels reuse the
existing lab code, no new libraries. Plain-words lines pass deslop-lint. About 3 h for
the pilot, about 5 h for Levels 3–12.

## Round 2 — a second hook at each level's hardest section (proposed 2026-10-08)

Ammar pick: "one at each hard section". Same question panel as the top hook, placed
right after that section's "In plain words" block. Every answer computed at build.

| Level | Section | Question | The surprise |
|---|---|---|---|
| 1 | 1.2 | Same parts, wider bars: same picture? | the story the chart tells changes |
| 2 | 2.5 | False alarm "once in 370": chance one comes before point 100? | about 24 % |
| 3 | 3.5 | Does a sample's spread come out too small, right or too big on average? | too small, by a known amount |
| 4 | 4.4 | Averaging 4 parts halves the wobble. How many to halve it again? | 16, not 8 |
| 5 | 5.3 | A "95 %" range from 5 parts using the usual 1.96: how often does it miss? | about 12 %, not 5 % |
| 6 | 6.2 | Move the limits from 3 steps out to 2: how many more false alarms? | about 17 times as many |
| 7 | 7.4 | Switch on all four extra rules: false alarms go up by how much? | computed from the rule set |
| 8 | 8.3 | Same scatter, average slides one step toward a limit: bad parts go up how much? | several times over |
| 9 | 9.3 | How much does a part from 10 hours ago still count in the running score? | about 2 % |
| 10 | 10.5 | 4 % bad, batches of 50: can the chart warn when things get better? | no; needs batches of about 216 |
| 11 | 11.3 | Add columns of pure random numbers to a fit: does its score go up? | yes, every time |
| 12 | 12.5 | Test only the high and low ends: can you see a best setting in the middle? | no; centre runs can |

### What you will see
7. Each level has a second question panel inside the section named above, after its
   plain-words block, before its prose. Pick → two computed tiles + a reply.
8. These mid-level panels carry no side notes (the section's own margin notes stay).
9. Keyboard and 390 px phone work as for the top hooks; no sideways scroll.

### Not in scope (round 2)
Guess-before-every-section; follow-up chains; a home-page question.
