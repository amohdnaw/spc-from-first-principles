# Outcome contract — step 6, the newcomer test

Step 6 of the six-step plan. Picked 2026-10-07: "Model first, then a human",
"All 12 levels in order", "Claim test + stall log". Approved 2026-10-07.

## What you will see

1. One report page (HTML, screenshotted into the chat) with a row per level, 1 to
   12: the reader's own restatement of the level's claim, its answers to the two
   set questions marked right or wrong, and its stalls with a quote and a section
   number.
2. A ranked fix list on the same page: claim-test failures first, then stalls
   grouped by type (undefined term, jump in the argument, figure it couldn't read),
   split into do-now and later.
3. The 3 worst spots flagged "for a human", each with a short paste-ready message.
4. Before the reader starts, the 24 questions (2 per level) and their answers are
   committed to `specs/newcomer-test-questions.md`, so the scoring cannot bend.

## Not in scope

Fixing anything the test finds; the MSA site; the videos.

## Defaults taken

One fresh-context Opus agent, told it has no SPC background, reads Levels 1 to 12
in order: the rendered page text plus the figure images. Videos are skipped (it
cannot watch them; the prose carries the same argument). The glossary is used only
where the page links it. About an hour of run time.
