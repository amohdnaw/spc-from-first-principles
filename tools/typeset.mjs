#!/usr/bin/env node
/**
 * Typeset the page maths with KaTeX, at build time.
 *
 * The formulas used to be unicode text — `±Lσ√(λ/(2−λ)·(1−(1−λ)2i))` was on the
 * Level IV page, and it is not readable. They are now written as TeX in a
 * `data-tex` attribute and rendered into the element by this script, so:
 *
 *   - no JavaScript runs on the page, and there is no flash of raw TeX
 *   - the TeX is the version-controlled source, and re-running is idempotent
 *   - maths is Computer Modern, which is what the Manim acts already use
 *     (spc-manim-craft-contract.md, default 3), so a formula reads the same on
 *     the page as it does in the video
 *
 *   node tools/typeset.mjs           # rewrite the pages
 *   node tools/typeset.mjs --check   # exit 1 if any page is out of date
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import katex from "katex";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PAGES = ["index.html", "level-01.html", "level-03.html", "level-04.html", "level-06.html",
               "level-08.html", "level-09.html", "line-of-sight.html"];

// `<div class="eq-body" data-tex="…">` renders in display mode,
// `<span class="tex" data-tex="…">` renders inline.
const TARGETS = [
  { open: /<div class="eq-body" data-tex="([^"]+)">/g, close: "</div>", tag: "div", display: true },
  { open: /<span class="tex" data-tex="([^"]+)">/g, close: "</span>", tag: "span", display: false },
];

const unescapeAttr = (s) =>
  s.replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");

/**
 * Find the closer that matches an opening tag, counting nesting depth.
 *
 * The naive `indexOf("</span>")` is wrong the moment the element already holds
 * rendered KaTeX, because that output is full of nested spans: the second run
 * would find an inner closer, truncate the body and re-wrap it. `--check`
 * caught exactly that, which is the whole reason `--check` exists.
 */
function matchingClose(html, bodyStart, tag) {
  const open = new RegExp(`<${tag}\\b`, "g");
  const close = new RegExp(`</${tag}>`, "g");
  let depth = 0;
  let i = bodyStart;
  for (;;) {
    open.lastIndex = i;
    close.lastIndex = i;
    const o = open.exec(html);
    const c = close.exec(html);
    if (!c) return -1;
    if (o && o.index < c.index) { depth += 1; i = o.index + 1; continue; }
    if (depth === 0) return c.index;
    depth -= 1;
    i = c.index + 1;
  }
}

function typeset(html, file) {
  let out = html;
  let count = 0;

  for (const { open, close, display, tag } of TARGETS) {
    open.lastIndex = 0;
    let m;
    const edits = [];
    while ((m = open.exec(out)) !== null) {
      const bodyStart = m.index + m[0].length;
      const bodyEnd = matchingClose(out, bodyStart, tag);
      if (bodyEnd === -1) throw new Error(`${file}: unclosed ${close} after ${m[0]}`);
      const tex = unescapeAttr(m[1]);
      let rendered;
      try {
        rendered = katex.renderToString(tex, {
          displayMode: display,
          throwOnError: true,
          strict: "warn",
          output: "htmlAndMathml",   // MathML for screen readers, HTML for looks
        });
      } catch (e) {
        throw new Error(`${file}: KaTeX refused ${JSON.stringify(tex)}\n  ${e.message}`);
      }
      edits.push({ bodyStart, bodyEnd, rendered });
      count += 1;
    }
    // apply back to front so earlier offsets stay valid
    for (const { bodyStart, bodyEnd, rendered } of edits.reverse()) {
      out = out.slice(0, bodyStart) + rendered + out.slice(bodyEnd);
    }
  }
  return { out, count };
}

const check = process.argv.includes("--check");
let total = 0;
let stale = [];

for (const page of PAGES) {
  const path = join(ROOT, page);
  const before = readFileSync(path, "utf8");
  const { out, count } = typeset(before, page);
  total += count;
  if (out !== before) {
    if (check) stale.push(page);
    else writeFileSync(path, out);
  }
  console.log(`  ${count > 0 ? "typeset" : "   none"}  ${page}  ${count} formula${count === 1 ? "" : "s"}`);
}

console.log(`\n${total} formulas across ${PAGES.length} pages`);
if (check && stale.length) {
  console.error(`\nout of date: ${stale.join(", ")}\nrun: node tools/typeset.mjs`);
  process.exit(1);
}
