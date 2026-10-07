# Glossary contract (SPC + MSA)

Approved 2026-10-07. Step 3 of the six-step curriculum plan. Picked mock: **Direction B**,
the SYS note in flow (amber left border, opens under the paragraph, pushes the text down).

## What you will see
1. On any SPC or MSA level, the first use of each glossary term in the main text has a dotted
   underline. Later uses in that level are plain text.
2. Tap it and a note opens under the paragraph in style B: amber left border, the term and its
   symbol in small mono capitals, one plain sentence, the formula typeset like the rest of the
   page, then "BUILT IN SPC 3 · MSA 1" and "full entry →". The text below moves down; nothing
   covers it.
3. Tap the term again, or press Esc, and the note closes. Opening a second note closes the first.
   Tab and Enter work the same as a tap.
4. On a 390px phone the note fits the column with no sideways scroll.
5. "full entry →" opens `glossary.html` on the same site at that term. The page lists every term
   A–Z, tagged SPC and/or MSA, with links to the levels that build it. Both sites show identical
   entries.
6. Before anything links, Ammar gets one review page with every drafted entry and a keep/cut
   choice per term.
7. With JavaScript off, each marked term is a plain link to its glossary entry.

## Not in scope
- Terms inside videos, captions, interactive labels, headings, equations or the nav.
- A search box on the glossary page.
- Hover previews on desktop.
- Any change to the landing pages.

## Defaults taken
- The list lives in `~/portfolio/tools/glossary.json`. The MSA repo keeps a copy, and a test
  fails if the two differ.
- Terms match case-insensitively, using the spellings and plurals listed in each entry.
- One note is open at a time.
- About 40–60 terms expected; the real number comes out of the review.
- Every definition goes through an unslop pass and reads at grade 6–8.
