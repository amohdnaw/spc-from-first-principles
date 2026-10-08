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
