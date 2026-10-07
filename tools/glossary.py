#!/usr/bin/env python3
"""Link the first use of each glossary term on every level page, and build glossary.html.

    python3 tools/glossary.py            # rewrite the level pages and glossary.html
    python3 tools/glossary.py --check    # exit 1 if any page is out of date

Run it after chapterise.py and before typeset.mjs: the notes carry their formulas as
`data-tex`, and typeset renders them like every other equation on the page.

The term list is tools/glossary.json, shared with the MSA site (specs/glossary-contract.md).
This file is identical in both repos; it works out which site it is in from the wordmark.

Idempotent by construction: every run strips what the last run added, then adds it again,
so a rebuilt page and a re-linked page come out byte for byte the same.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = {"spc": "https://amohdnaw.github.io/spc-from-first-principles/",
        "msa": "https://amohdnaw.github.io/msa-from-first-principles/"}
NAME = {"spc": "SPC", "msa": "MSA"}

# Main prose only (the contract's "not in scope": headings, captions, figures, equations,
# nav, interactive labels and the margin notes stay unlinked).
BLOCKS = {"p", "li", "blockquote", "dd"}
VOID = {"br", "img", "meta", "link", "input", "hr", "source", "track", "wbr", "col", "area",
        "embed", "param"}
SKIP_TAGS = {"nav", "figure", "figcaption", "video", "script", "style", "math", "svg", "button",
             "h1", "h2", "h3", "h4", "h5", "h6", "aside", "canvas", "table", "select", "label",
             "a", "code", "template", "header", "footer"}
SKIP_CLASSES = {"note", "katex", "tex", "eq", "eq-body", "next", "lab", "lab-note", "speak", "toc",
                "toc-head", "tile", "rail", "sys", "widget", "controls"}

LINK_RE = re.compile(r'<a class="gl" href="glossary\.html#[^"]*" data-gl="[^"]*">(.*?)</a>', re.S)
BLOCK_RE = re.compile(r"\n?<!--glossary-->.*?<!--/glossary-->\n?", re.S)


def site_of(page: str) -> str:
    return "msa" if "<span>/ MSA" in page else "spc"


class Prose(HTMLParser):
    """Collect (start, end) source offsets of text that sits in main prose."""

    def __init__(self, src: str):
        super().__init__(convert_charrefs=False)
        self.lines = [0]
        for m in re.finditer("\n", src):
            self.lines.append(m.end())
        self.stack: list[tuple[str, bool, bool]] = []
        self.in_main = False
        self.spans: list[tuple[int, int]] = []

    def at(self) -> int:
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = set((dict(attrs).get("class") or "").split())
        if tag == "main":
            self.in_main = True
        self.stack.append((tag, tag in SKIP_TAGS or bool(cls & SKIP_CLASSES), tag in BLOCKS))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            if self.stack.pop()[0] == tag:
                break
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        if (self.in_main and any(b for _, _, b in self.stack)
                and not any(s for _, s, _ in self.stack)):
            start = self.at()
            self.spans.append((start, start + len(data)))


def pattern(entry: dict) -> re.Pattern:
    words = sorted(entry["match"], key=len, reverse=True)
    alt = "|".join(re.escape(w) for w in words)
    skip = ""
    if entry.get("skip_before"):
        skip = r"(?!\s+(?:" + "|".join(map(re.escape, entry["skip_before"])) + r")\b)"
    return re.compile(r"(?<![\w%-])(?:" + alt + r")(?![\w-])" + skip, re.I)


def built_line(entry: dict) -> str:
    parts = [f"{NAME[s]} {', '.join(map(str, entry['built'][s]))}"
             for s in ("spc", "msa") if entry["built"].get(s)]
    return " · ".join(parts)


def tex_attr(tex: str) -> str:
    return html.escape(tex, quote=True)


def note(entry: dict) -> str:
    sym = f' <span class="gl-sym">{html.escape(entry["symbol"])}</span>' if entry["symbol"] and entry["symbol"] != entry["term"] else ""
    eq = f'<div class="eq-body" data-tex="{tex_attr(entry["tex"])}"></div>' if entry["tex"] else ""
    return (f'<template id="gl-{entry["id"]}"><div class="gl-note" role="note">'
            f'<div class="micro">{html.escape(entry["term"])}{sym}</div>'
            f'<p>{html.escape(entry["def"])}</p>{eq}'
            f'<div class="gl-foot"><span class="micro">Built in {built_line(entry)}</span>'
            f'<a href="glossary.html#{entry["id"]}">full entry →</a></div></div></template>')


STYLE = """<style>
  a.gl{color:inherit;text-decoration:underline dotted var(--ink-dim);text-underline-offset:.22em;
    text-decoration-thickness:1px;cursor:pointer}
  a.gl:hover,a.gl[aria-expanded="true"]{text-decoration-color:var(--accent)}
  a.gl[aria-expanded="true"]{background:var(--accent-wash)}
  a.gl:focus-visible{outline:1px solid var(--accent);outline-offset:2px}
  .gl-note{border-left:2px solid var(--accent);padding:4px 0 4px 18px;margin:18px 0 22px;
    max-width:var(--measure);font-size:calc(var(--body) * .86);line-height:1.45;color:var(--ink);
    font-style:normal;font-weight:400;text-indent:0;letter-spacing:normal;text-transform:none}
  .gl-note .micro{color:var(--ink-dim);margin:0 0 4px;display:block}
  .gl-note .gl-sym{text-transform:none;letter-spacing:.04em}
  .gl-note p{margin:0}
  .gl-note .eq-body{font-size:22px;margin:10px 0;text-align:left;overflow-x:auto;overflow-y:hidden;
    scrollbar-width:thin;scrollbar-color:var(--rule-strong) transparent}
  .gl-note .eq-body::-webkit-scrollbar{height:6px}
  .gl-note .eq-body::-webkit-scrollbar-thumb{background:var(--rule-strong)}
  @media (max-width:560px){ .gl-note .eq-body{font-size:18px} }
  .gl-note .eq-body .katex-display{margin:0;text-align:left}
  .gl-note .eq-body .katex-display>.katex{text-align:left}
  .gl-foot{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:baseline;margin-top:8px}
  .gl-foot .micro{margin:0;display:inline}
  .gl-foot a{font-family:var(--mono);font-size:12px;color:var(--accent);text-decoration:none}
  .gl-foot a:hover{text-decoration:underline}
</style>"""

# One note open at a time; it opens under the block that holds the term, so nothing
# is covered (contract: style B). Without JS the term is a plain link to the entry.
SCRIPT = """<script>
(function(){
  var open=null;
  function close(){ if(!open) return; open.note.remove(); open.a.setAttribute('aria-expanded','false'); open=null; }
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a.gl'); if(!a) return;
    e.preventDefault();
    var same=open&&open.a===a; close(); if(same) return;
    var t=document.getElementById('gl-'+a.dataset.gl); if(!t) return;
    var n=t.content.firstElementChild.cloneNode(true);
    n.id='gl-open'; a.setAttribute('aria-controls','gl-open'); a.setAttribute('aria-expanded','true');
    // a block may carry margin notes and more prose after the term: open above the first of those
    var block=a.closest('p,li,blockquote,dd')||a;
    var side=[].find.call(block.querySelectorAll('.note'),function(x){ return a.compareDocumentPosition(x)&4; });
    if(side) side.before(n); else block.after(n); open={a:a,note:n};
  });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&open){ var a=open.a; close(); a.focus(); } });
  document.querySelectorAll('a.gl').forEach(function(a){ a.setAttribute('role','button'); a.setAttribute('aria-expanded','false'); });
})();
</script>"""


def link_page(src: str, terms: list[dict]) -> str:
    src = BLOCK_RE.sub("\n", LINK_RE.sub(r"\1", src)) if "glossary" in src else src
    p = Prose(src)
    p.feed(src)
    taken: list[tuple[int, int]] = []
    hits: list[tuple[int, int, dict]] = []
    # longest phrases first, so "tolerance ratio" is claimed before "tolerance"
    for entry in sorted(terms, key=lambda e: -max(map(len, e["match"]))):
        rx = pattern(entry)
        for a, b in p.spans:
            found = None
            for m in rx.finditer(src, a, b):
                s, e = m.span()
                if not any(s < te and ts < e for ts, te in taken):
                    found = (s, e)
                    break
            if found:
                taken.append(found)
                hits.append((*found, entry))
                break
    if not hits:
        return src
    out = src
    for s, e, entry in sorted(hits, key=lambda h: -h[0]):
        out = (out[:s] + f'<a class="gl" href="glossary.html#{entry["id"]}" data-gl="{entry["id"]}">'
               + out[s:e] + "</a>" + out[e:])
    used = sorted({h[2]["id"] for h in hits})
    by_id = {t["id"]: t for t in terms}
    block = ("\n<!--glossary-->\n" + STYLE + "\n" + "\n".join(note(by_id[i]) for i in used)
             + "\n" + SCRIPT + "\n<!--/glossary-->\n")
    i = out.rindex("</body>")
    return out[:i].rstrip("\n") + "\n" + block + out[i:]


def level_links(entry: dict, site: str, field: str) -> str:
    out = []
    for s in ("spc", "msa"):
        for n in entry[field].get(s, []):
            href = f"level-{n:02d}.html" if s == site else f"{BASE[s]}level-{n:02d}.html"
            out.append(f'<a href="{href}">{NAME[s]} {n}</a>')
    return ", ".join(out)


def glossary_page(template: str, terms: list[dict], site: str) -> str:
    head_end = template.index("<main")
    head = template[:head_end]
    head = re.sub(r"<title>.*?</title>", f"<title>Glossary · {NAME[site]} from First Principles</title>", head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  '<meta name="description" content="Every term the SPC and MSA levels use, in one '
                  'plain sentence each, with the level that builds it.">', head)
    head = head.replace(' aria-current="page"', "")
    foot = template[template.index("</main>"):]
    foot = BLOCK_RE.sub("\n", foot)
    rows, first = [], {}
    for e in sorted(terms, key=lambda e: e["term"].lstrip("%").lower()):
        first.setdefault(e["term"].lstrip("%")[0].upper(), e["id"])
        tags = " ".join(NAME[s] for s in ("spc", "msa") if e["used"].get(s))
        sym = f' <span class="gl-sym">{html.escape(e["symbol"])}</span>' if e["symbol"] and e["symbol"] != e["term"] else ""
        eq = f'<div class="eq-body" data-tex="{tex_attr(e["tex"])}"></div>' if e["tex"] else ""
        rows.append(
            f'<section class="gl-entry" id="{e["id"]}"><h2>{html.escape(e["term"])}{sym}'
            f'<span class="micro gl-tags">{tags}</span></h2>'
            f'<p>{html.escape(e["def"])}</p>{eq}'
            f'<p class="gl-meta"><span class="micro">Built in</span> {level_links(e, site, "built")}<br>'
            f'<span class="micro">Used in</span> {level_links(e, site, "used")}</p></section>')
    style = """<style>
  /* the level pages' .leaf box, so the column starts on the same left edge */
  .gl-page{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg));margin:0 auto;padding:64px 0 96px}
  .gl-page > *{max-width:var(--measure)}
  .gl-az{display:flex;flex-wrap:wrap;margin:0 0 40px;max-width:none!important;font-family:var(--mono);font-size:14px}
  .gl-az a,.gl-az span{min-width:22px;min-height:40px;display:inline-flex;align-items:center;justify-content:center}
  .gl-az a{color:var(--accent);text-decoration:none}
  .gl-az a:hover{text-decoration:underline}
  .gl-az span{color:var(--rule-strong)}
  .gl-page h1{margin:0 0 8px}
  .gl-page .dek{color:var(--ink-dim);margin:0 0 24px}
  .gl-entry{border-left:2px solid var(--rule-strong);padding:2px 0 2px 18px;margin:0 0 32px;scroll-margin-top:96px}
  .gl-entry:target{border-left-color:var(--accent)}
  .gl-entry h2{font-size:1.15em;margin:0 0 4px;font-weight:400;color:var(--ink-bright)}
  .gl-entry .gl-sym{color:var(--ink-dim);font-style:italic;margin-left:6px}
  .gl-entry p{margin:0}
  .gl-entry h2 .gl-tags{display:inline;margin-left:12px;vertical-align:.2em}
  .gl-entry .eq-body,.gl-note .eq-body{font-size:22px;margin:10px 0;text-align:left;overflow-x:auto;overflow-y:hidden;
    scrollbar-width:thin;scrollbar-color:var(--rule-strong) transparent}
  .gl-entry .eq-body::-webkit-scrollbar{height:6px}
  .gl-entry .eq-body::-webkit-scrollbar-thumb{background:var(--rule-strong)}
  @media (max-width:560px){ .gl-entry .eq-body,.gl-note .eq-body{font-size:18px} }
  .gl-entry .eq-body .katex-display{margin:0;text-align:left}
  .gl-entry .eq-body .katex-display>.katex,.gl-note .eq-body .katex-display>.katex{text-align:left}
  .gl-meta{margin-top:8px!important;font-size:15px;line-height:1.8;color:var(--ink-dim)}
  .gl-meta .micro{display:inline-block;width:6.5em;margin:0}
  .gl-entry .gl-meta a{color:var(--accent);text-decoration:none}
  .gl-entry .gl-meta a:hover{text-decoration:underline}
</style>"""
    az = "".join(f'<a href="#{first[c]}">{c}</a>' if c in first else f'<span>{c}</span>'
                 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    body = (f'<main class="gl-page">\n{style}\n<h1>Glossary</h1>\n'
            f'<p class="dek">{len(terms)} terms from both sites, SPC and MSA, one plain sentence each.</p>\n'
            f'<div class="gl-az" role="navigation" aria-label="Jump to a letter">{az}</div>\n'
            + "\n".join(rows) + "\n")
    return head + body + foot


EQ_RE = re.compile(r'(<div class="eq-body" data-tex="[^"]*">).*?</div>', re.S)


def bare(page: str) -> str:
    """The page with typeset's KaTeX output emptied: typeset runs after this script."""
    return EQ_RE.sub(r"\1</div>", page)


def main() -> int:
    check = "--check" in sys.argv[1:]
    terms = json.loads((ROOT / "tools" / "glossary.json").read_text())
    pages = sorted(ROOT.glob("level-[0-9][0-9].html"))
    first = LINK_RE.sub(r"\1", pages[0].read_text())
    targets = [(p, lambda old: link_page(old, terms)) for p in pages]
    targets.append((ROOT / "glossary.html", lambda old: glossary_page(first, terms, site_of(first))))
    stale = []
    for page, build in targets:
        old = page.read_text() if page.exists() else ""
        new = build(old)
        if bare(new) != bare(old):
            stale.append(page.name)
            if not check:
                page.write_text(new)
    if check:
        for page in pages:
            ids = re.findall(r'<a class="gl" href="glossary\.html#[^"]*" data-gl="([^"]*)">', page.read_text())
            if len(ids) != len(set(ids)):
                stale.append(f"{page.name} links a term twice")
        for page in targets:
            if re.search(r'<div class="eq-body" data-tex="[^"]*"></div>', page[0].read_text()):
                stale.append(f"{page[0].name} has a formula typeset never rendered")
        # the two sites share one list and one linker (glossary-contract.md, defaults)
        for twin in ("portfolio", "msa-from-first-principles"):
            other = ROOT.parent / twin / "tools"
            if other.resolve() != (ROOT / "tools").resolve() and other.is_dir():
                for name in ("glossary.json", "glossary.py"):
                    if (other / name).read_bytes() != (ROOT / "tools" / name).read_bytes():
                        stale.append(f"{name} differs from {twin}")
    if check and stale:
        print("glossary out of date:", ", ".join(stale))
        return 1
    print(("ok" if check else "linked") + f": {len(pages)} levels, {len(terms)} terms, {len(stale)} rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
