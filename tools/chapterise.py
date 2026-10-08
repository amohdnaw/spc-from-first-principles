#!/usr/bin/env python3
"""Turn a level page into a textbook chapter (DESIGN.md §3, 'The level page is a chapter').

Rebuilds <main> from a chapter spec while preserving, byte for byte, the blocks that
already carry verified content: the KaTeX equation, the interactive lab, the SYS note,
every figure, and the next-level link. Nothing is re-typeset or re-rendered here.

Input  is tools/page-sources/<page>, tracked, pre-chapter.
Output is <page> at the repo root, overwritten.

    python3 tools/chapterise.py level-06.html      # one page
    for f in level-01 level-03 level-04 level-06 level-08 level-09; do \
        python3 tools/chapterise.py $f.html; done  # all of them

Then link the glossary terms and render the maths, in that order:

    python3 tools/glossary.py && (cd tools && node typeset.mjs)
"""
from __future__ import annotations
import math
import re
import sys
import pathlib

# ---------------------------------------------------------------- CSS injected once
CHAPTER_CSS = """
  /* ---------- chapter grammar (DESIGN.md §3) ----------
     Layout follows the book convention rather than an invented one. Tufte CSS:
     figures are constrained to the main column by default, a *small* figure may
     go in the margin, and anything larger takes the full text block. Margin notes
     sit "as close as possible to the text that references them" - which is done
     with a float at the note's position in the flow, never with grid rows. Grid
     rows put the note in a row of its own and cut an L-shaped hole in the page. */
  :root{ --marg:320px; --marg-gap:48px; }
  .lab-link{margin-top:var(--rhythm)}
  /* the lab is another site in a new tab: say so before the click */
  .lab-link a[target="_blank"]::after{content:"external";font-family:var(--mono);font-size:11px;font-weight:600;
    letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-left:8px;padding:1px 6px;vertical-align:.15em;
    border:1px solid color-mix(in srgb,var(--accent) 40%,transparent);display:inline-block;text-decoration:none}
  /* Links in the prose. The browser's own blue measured 2.0:1 on this ground. */
  main section a[href^="http"]{color:var(--ink-bright);text-decoration:underline;
    text-decoration-color:var(--accent);text-underline-offset:3px}
  main section a[href^="http"]:hover{color:var(--accent)}
  /* a figure opens at full size on tap; the link must not change how it looks */
  a.zoom{display:block;cursor:zoom-in}

  /* The page IS the grid. Before this the container was 110rem while the text
     block was 1090px and left-aligned inside it, so the margins came out 149px
     left and 675px right - the dead right column. The page width is now computed
     from the same tokens the grid uses, so it can never drift from it again. */
  .wrap{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg) + 2 * var(--gutter))}
  /* the text block: measure + gutter + margin. Everything aligns to its left edge. */
  .leaf{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  .leaf > div > p,.leaf > div > .eq,.leaf > div > .sys{max-width:var(--measure)}

  .ch-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.16em;
    text-transform:uppercase;color:var(--accent);margin:0 0 18px}

  .toc{border-top:1px solid var(--rule-strong);border-bottom:1px solid var(--rule);
    padding:22px 0 24px;margin:8px 0 0;
    max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  .toc-head{display:flex;gap:18px;align-items:baseline;margin:0 0 14px;flex-wrap:wrap}
  .toc-head .est{margin-left:auto}
  .toc ol{list-style:none;margin:0;padding:0;display:grid;
    grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:2px 48px}
  .toc li{display:grid;grid-template-columns:44px 1fr;gap:10px;padding:7px 0;
    border-bottom:1px solid rgba(42,49,56,.55)}
  .toc .n{font-family:var(--mono);font-size:13px;color:var(--accent);padding-top:.35em}
  .toc a{color:var(--ink);text-decoration:none;font-size:19px}
  .toc a:hover{color:var(--accent)}
  .toc .tag{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.12em;
    text-transform:uppercase;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 40%,transparent);
    padding:1px 6px;margin-left:10px;vertical-align:.15em;white-space:nowrap}
  .toc-chain{font-family:var(--serif);font-size:17px;color:var(--ink-dim);margin:14px 0 0;
    display:flex;flex-wrap:wrap;gap:0 8px;align-items:baseline}
  .toc-chain .sep{color:var(--rule-strong);padding:0 4px}
  .toc .sub{display:block;font-size:17px;color:var(--ink-dim);line-height:1.4}

  /* a heading must clear the sticky nav when jumped to from the contents */
  main section{scroll-margin-top:96px}
  .sec-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.14em;
    color:var(--accent);display:block;margin-bottom:10px}
  /* headings balance across lines; body prose gets pretty so no line is left
     carrying a single word (better-typography principle 9) */
  main h2{font-family:var(--serif);font-size:33px;font-weight:600;line-height:1.12;
    color:var(--ink-bright);margin:0 0 14px;max-width:26em;text-wrap:balance}
  .leaf > div > p{text-wrap:pretty}
  .toc .sub,.note em,figcaption .figtext{text-wrap:pretty}
  /* captions run to three lines: mono 13px read as a footnote */
  .eq-cap{font-family:var(--serif);font-size:17px;line-height:1.45;text-align:left;text-wrap:pretty;font-variant-numeric:oldstyle-nums;max-width:var(--measure)}
  /* one drop cap per chapter: on every section it hung into the block below a
     one-line opener. */
  #s1 .lead::first-letter{initial-letter:2;font-weight:600;color:var(--ink-bright);margin-right:.08em}

  /* margin notes: instrument voice, level with the paragraph they annotate.
     Below the margin breakpoint they simply follow the prose at measure width. */
  .note{display:block;font-family:var(--mono);font-size:12.5px;line-height:1.6;
    color:var(--ink-dim);border-left:1px solid var(--rule);padding-left:14px;
    margin:0 0 26px;max-width:var(--measure);text-indent:0}
  .note .k{display:block;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;
    font-size:11px;margin-bottom:5px}
  .note .v{color:var(--ink-bright);font-size:21px;font-variant-numeric:tabular-nums}
  /* a note that argues is document voice: serif at the 17px step. Mono stays for
     the label, numbers and data rows (DESIGN.md 6 bans mono body prose). */
  .note:not(.data):not(.watch){font-family:var(--serif);font-size:17px;line-height:1.45;
    color:var(--ink-dim);font-variant-numeric:oldstyle-nums}
  .note .k,.note .v{font-family:var(--mono)}
  .note em{font-style:italic;color:var(--ink)}
  /* only the spoken quote is a block; inline italics inside a sentence stay inline */
  .note.speak em{font-family:var(--serif);font-size:17px;line-height:1.45;display:block;
    font-variant-numeric:oldstyle-nums}
  .note.speak{border-left-color:var(--accent)}
  .note.data .row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;
    align-items:baseline;padding:3px 0;border-bottom:1px solid rgba(42,49,56,.6);min-width:0}
  .note.data .row:last-child{border-bottom:0}
  /* .data is also the bordered panel component on some levels; without this the
     note inherited its box and the right-aligned values ran into its edge */
  .note.data{border:0;border-left:1px solid var(--rule);background:none}
  /* NB: these labels are uppercased, which maps σ to Σ - the summation sign.
     Keep label text ASCII and put Greek in the value. */
  .note.data .rk{color:var(--ink-dim);letter-spacing:.06em;text-transform:uppercase;font-size:11px}
  .note.data .rv{color:var(--ink-bright);font-variant-numeric:tabular-nums;min-width:0;
    overflow-wrap:anywhere}
  .note.data .row.num .rv{font-size:16px;text-align:right;white-space:nowrap}
  /* a sentence is not data: own line, left aligned, in the reading voice */
  .note.data .row.txt{display:block}
  .note.data .row.txt .rv{display:block;font-family:var(--serif);font-size:17px;
    line-height:1.45;margin-top:3px;font-variant-numeric:oldstyle-nums}
  .note.data .rn{flex:1 1 100%;min-width:0;color:var(--ink-dim);font-size:11.5px;
    line-height:1.5;overflow-wrap:anywhere}

  /* A referenced act, collapsed. Closed it is a poster strip; open it is a player
     at the full text-block width. The previous version was a 340px margin card,
     which measured 323x182 on screen - not a player, a thumbnail with controls. */
  .act{border-top:1px solid var(--rule);margin:40px 0 0}
  .act > summary{display:flex;gap:18px;align-items:center;cursor:pointer;
    padding:16px 0;list-style:none}
  .act > summary::-webkit-details-marker{display:none}
  .act > summary::marker{content:""}
  .act > summary:hover .k{color:var(--ink-bright)}
  /* the closed strip has to look like a video, or it reads as a footnote. A poster
     at 280px with a play glyph over it does that; 180px and a word did not. */
  .act .thumb-wrap{position:relative;flex:none;display:block;line-height:0}
  .act .thumb{width:280px;height:auto;display:block;border:1px solid var(--rule)}
  .act .thumb-wrap::after{content:"";position:absolute;left:50%;top:50%;
    transform:translate(-50%,-50%);width:0;height:0;
    border-left:18px solid var(--ink-bright);border-top:11px solid transparent;
    border-bottom:11px solid transparent;filter:drop-shadow(0 0 6px rgba(0,0,0,.6))}
  .act > summary:hover .thumb-wrap::after{border-left-color:var(--accent)}
  .act[open] > summary .thumb-wrap{display:none}
  .act .meta{min-width:0}
  .act .k{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);display:block;margin-bottom:5px}
  .act .cap{font-size:17px;line-height:1.45;color:var(--ink-dim);display:block;
    max-width:52ch;text-wrap:pretty}
  .act .cue{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-dim);margin-left:auto;flex:none;white-space:nowrap}
  .act[open] > summary .cue{color:var(--accent)}
  .act video{display:block;width:100%;height:auto;background:var(--ground);
    margin:0 0 8px;max-width:min(100%,calc(68vh * 16 / 9))}
  @media(max-width:640px){ .act > summary{flex-wrap:wrap} .act .thumb{width:160px} }
  /* a margin figure - Tufte's one case for a figure outside the main flow */
  .note.watch video{display:block;width:100%;height:auto;margin:8px 0;border:1px solid var(--rule)}
  .note.watch:hover .k{color:var(--ink-bright)}

  /* figures take the whole text block and share its left edge */
  figure,.figpair{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  figure video{max-width:min(100%,calc(68vh * 16 / 9))}

  @media (min-width:1500px){ :root{ --body:26px; --marg:340px; } }
  /* 1280, not 1500: below 1500 the 21px measure plus the 320px margin still
     fits, and the margin otherwise sat empty beside a stacked note */
  @media (min-width:1280px){
    /* the note floats into the margin at its position in the flow. This is the
       whole trick: no row of its own, so no hole beside it. */
    /* tufte-css's mechanism: a negative right margin pulls the float out of the
       text column so it consumes no horizontal space there. Without it the float
       lives inside the 702px paragraph and shortens every line beside it, which
       destroys the measure the whole design is built on. */
    .note{float:right;clear:right;width:var(--marg);max-width:var(--marg);
      margin:0 calc(-1 * (var(--marg) + var(--marg-gap))) 26px 0;
      position:relative;z-index:1}
    /* a note that must not float (it holds something wide) */
    .note.nofloat{float:none;width:auto;max-width:var(--measure);margin-top:34px}
    .leaf > div::after{content:"";display:block;clear:both}
  }
  /* after the base .note rules, or they win on source order */
  /* a note right after a drop cap must start at the left edge, not beside the
     cap. Only below the margin breakpoint: above it the note floats right. */
  /* clear does not move a note past initial-letter (it is not a float), so push
     it a body line down; a note further into the paragraph just gains air. */
  @media (max-width:1279px){ #s1 .lead .note{margin-top:calc(var(--body) * 1.5)} }
  @media (max-width:1499px){
    /* the number's own column left the formula 504px; six equations scrolled */
    .eq{grid-template-columns:1fr;gap:10px}
    .eq-num{justify-self:end}
  }
  @media (max-width:640px){
    /* 12.5px mono read as a footnote on a phone */
    .note{font-size:14px}
    .note .k,.note.data .rk{font-size:12px}
    .note.data .rn{font-size:13px}
    /* tap targets: the rail links measured 30x23 */
    .rail a,.rail span.soon{min-height:44px;padding:0 4px}
    /* the wrapped rail took ~320px before the title: a fixed grid of equal cells
       (6 to a row) stacks it into tight rows instead */
    .rail{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:0 6px}
    .rail a,.rail span.soon{min-height:40px;letter-spacing:.06em;gap:5px}
  }
  /* Plain entry (specs/plain-entry-contract.md): a hook panel before the
     contents, and one everyday-words line under every section title. Panel and
     readout-tile grammar from DESIGN.md §5; radius 0, one accent. */
  .hook-row{margin:32px 0 8px}
  .hook{border:1px solid var(--rule);max-width:var(--measure)}
  .hk-side{max-width:var(--measure);margin-top:28px}
  .hk-note{font-family:var(--mono);font-size:12.5px;line-height:1.6;color:var(--ink);
    border-left:1px solid var(--rule);padding:2px 0 2px 16px;margin-bottom:24px}
  .hk-note .k{display:block;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;font-size:11px;margin-bottom:6px}
  .hk-note a{color:var(--accent);border-bottom:1px solid var(--accent-wash)}
  .hk-note[hidden]{display:none}
  .hk-key{display:block;margin-top:6px}.hk-key i{font-style:normal;margin-right:6px}
  @media (min-width:1280px){
    .hook-row{display:grid;grid-template-columns:var(--measure) var(--marg);gap:var(--marg-gap);align-items:start}
    .hk-side{margin-top:0}
  }
  .hk-bar{display:flex;justify-content:space-between;gap:12px;padding:10px 16px;
    border-bottom:1px solid var(--rule)}
  .hk-body{padding:20px}
  .hk-q{font-size:calc(var(--body) * 1.22);line-height:1.3;color:var(--ink-bright);margin:0 0 18px}
  .hook button{font-family:var(--mono);font-size:14px;letter-spacing:.06em;background:transparent;
    color:var(--ink-bright);border:1px solid var(--rule-strong);padding:12px 18px;cursor:pointer;
    margin:0 8px 8px 0;border-radius:0;min-height:44px}
  .hook button[aria-pressed="true"]{background:var(--accent-wash)}
  .hook button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .hk-dots{display:block;width:100%;height:auto;margin-top:12px}
  .hk-tiles{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--rule)}
  .hk-tiles[hidden],.hk-after[hidden]{display:none}
  .hk-tiles > div{padding:14px 20px}
  .hk-tiles > div + div{border-left:1px solid var(--rule)}
  .hk-tiles b{display:block;font-family:var(--mono);font-weight:500;font-size:28px;
    font-variant-numeric:tabular-nums;margin-top:4px}
  @media (max-width:560px){.hk-tiles > div{padding:12px 14px}.hk-tiles b{font-size:22px}}
  .hk-after{padding:0 20px 20px;margin:16px 0 0}
  .ok{color:var(--signal-ok)} .alarm{color:var(--signal-alarm)}
  .plain{border-left:2px solid var(--accent);padding:4px 0 4px 16px;margin:0 0 24px;
    max-width:var(--measure)}
  .plain p{margin:4px 0 0;color:var(--ink-bright)}
  .plain .micro,.hook .micro{display:block}
  .hk-bar .micro{display:inline}
"""

def tex(latex: str) -> str:
    """Inline maths, rendered by tools/typeset.mjs.

    EB Garamond has no combining hat and no subscript digits, so a literal
    "sigma-hat" arrives on screen as sigma followed by a stray caret, and a
    subscript falls back mid-word to another font. Anything mathematical inside
    serif prose goes through KaTeX instead of hoping for the glyph.
    """
    return '<span class="tex" data-tex="' + latex + '"></span>'


def take_div(s: str, start: int) -> str:
    """Return the complete <div> beginning at `start`, matching nesting.

    Regex cannot do this: the equation block contains rendered KaTeX, which is
    hundreds of nested divs and spans, so a non-greedy `</div>\\s*</div>` match
    stops in the middle of the formula and leaves the document unbalanced. The
    symptom is later blocks nesting inside the equation - a 2032px "lab".
    """
    depth = 0
    i = start
    while i < len(s):
        if s.startswith("<div", i) and (i + 4 >= len(s) or s[i + 4] in " >\t\n"):
            depth += 1
            i += 4
        elif s.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return s[start:i]
        else:
            i += 1
    raise ValueError("unbalanced div")


def extract(html: str) -> dict:
    """Pull the blocks that must survive untouched."""
    body = html[html.index("<main"):html.index("</main>")]
    out = {}

    def block(pattern, name, flags=re.S):
        m = re.search(pattern, body, flags)
        if not m:
            sys.exit(f"chapterise: could not find {name}")
        return m.group(0)

    out["eq"] = take_div(body, body.index('<div class="eq">'))
    # not every level has an interactive
    out["lab"] = (take_div(body, body.index('<div class="lab">'))
                  if '<div class="lab">' in body else "")
    out["sys"] = block(r'<aside class="sys">.*?</aside>', "sys note")
    out["next"] = block(r'<a class="next".*?</a>', "next link")

    figs = {}
    for m in re.finditer(r'<figure[^>]*>.*?</figure>', body, re.S):
        f = m.group(0)
        # a figure may hold <img src>, <source src> or a bare <video src>
        src = re.search(r'<(?:img|source|video)[^>]*\bsrc="([^"]+\.(?:png|jpg|mp4|webm))"', f)
        if src:
            figs[src.group(1).split("/")[-1]] = f
    out["figs"] = figs
    return out


def nc(sym: str) -> str:
    """A symbol that must keep its case inside an uppercased label.

    Margin labels are `text-transform: uppercase`, which does not merely restyle
    a variable — it renames it. In SPC `n` is the subgroup size and `N` is the
    lot size, so "at n = 100" rendered "AT N = 100", which is a different
    quantity. Greek is worse: sigma becomes the summation sign.
    """
    return f'<span class="nc">{sym}</span>'


def note(k, v=None, text=None, speak=False, serif=False):
    """A margin note.

    Emitted as a span so it can live *inside* a paragraph: a float only rises to
    the line box where it appears, so a note that is a sibling of the paragraph
    lands at the paragraph's foot instead of level with its reference.
    """
    cls = "note speak" if speak else "note"
    inner = f'<span class="k">{k}</span>'
    if v:
        inner += f'<span class="v">{v}</span>'
    if text:
        inner += f"<em>{text}</em>" if serif else text
    return f'<span class="{cls}">{inner}</span>'


def datanote(*rows, k=None):
    """One margin block carrying several label/value rows.

    Three separate notes on one paragraph stack to 246px of float and stretch the
    section; one block with three rows is shorter and reads as a table.
    """
    out = []
    if k:
        out.append(f'<span class="k">{k}</span>')
    for label, value, *rest in rows:
        tail = f'<span class="rn">{rest[0]}</span>' if rest else ""
        # under ~14 characters it is data and aligns right against its label;
        # longer than that it is a sentence, and right-aligning a sentence is
        # exactly what made the chapter opener unreadable
        kind = "num" if len(str(value)) <= 14 else "txt"
        out.append(f'<span class="row {kind}"><span class="rk">{label}</span>'
                   f'<span class="rv">{value}</span>{tail}</span>')
    return '<span class="note data">' + "".join(out) + "</span>"



# Level 1's prose quotes computed constants. Importing them here means the page,
# the act, the figure sheets and the test suite all read one source; a literal
# typed into the prose would be exactly the "asserted number" this repo rejects.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "spc-lab" / "src"))
from spclab.variation import (  # noqa: E402
    PAIR_N, PAIR_RUN_DRIFTING, PAIR_RUN_STABLE,
    TAMPER_SIGMA_RATIO_EXACT, TAMPER_VAR_RATIO_EXACT,
    TWELVE_CLOSEST_UM, TWELVE_SPAN_UM,
)
from spclab.chance import (  # noqa: E402
    ARL0, DIE_E, GAP_AT, MEDIAN_WAIT, MEMORY, MEMORY_WORST, MILESTONES,
    P_IN_ARL0, P_IN_SHIFT, RATE_ERR_AT, SHIFT_SUBGROUPS,
)
from spclab.evidence import phi  # noqa: E402

# Level 4.5 reads areas off the bell. Every share is computed from erf here,
# never typed, so the table and the later levels that quote it cannot drift.
Z95 = 1.959963984540054  # the two-sided 95 % point; asserted against phi below
assert abs((2 * phi(Z95) - 1) - 0.95) < 1e-12
INSIDE_K = {k: 2 * phi(k) - 1 for k in (1, 2, 3)}
TAIL_K = {k: 1 - phi(k) for k in (1, 2, 3)}
TAIL3_PPM = f"{TAIL_K[3]*1e6:,.0f}".replace(",", " ")  # the site writes 1 350

from spclab.level06 import XR_SIGMA, xbar_r_example  # noqa: E402
from spclab.level04 import SQRTN_SIGMA  # noqa: E402
from spclab.formulas import ppm_from_cpk  # noqa: E402
from spclab.level08 import CPK_DRIFT  # noqa: E402
from spclab import detection as DT  # noqa: E402

# Levels 8 and 9 quote these; the prose, the figures and the tests share them.
PPM_DRIFT = ppm_from_cpk(CPK_DRIFT)
PPM_DRIFT_S = f"{PPM_DRIFT:,.0f}".replace(",", "\u00a0")
ONE_IN_DRIFT = round(1e6 / PPM_DRIFT)
CPK_PPM = {c: ppm_from_cpk(c) for c in (1.00, 1.33, 1.67)}
# detection indexes subgroups from 0; the page counts from 1
D9_SHEW, D9_EWMA = DT.DET_SHEW + 1, DT.DET_EWMA + 1
assert DT.LAM == 0.2  # the prose says "a fifth" and "one part new and four parts memory"

# Level 6.7 builds one X̄–R chart. The page quotes the same arrays the figure
# draws, so the arithmetic in the prose and the lines on the chart cannot part.
XR = xbar_r_example()
XR_OUT = int(((XR["means"] > XR["ucl_xbar"]) | (XR["means"] < XR["lcl_xbar"])).sum()
             + (XR["ranges"] > XR["ucl_r"]).sum())

from spclab.estimation import (  # noqa: E402
    CONF, COVER_T, COVER_Z, D2_MEAN, D2_PUBLISHED, D2_SE, D2_SUBGROUPS_FOR_3DP,
    HALVE_FROM, HALVE_N_T, HALVE_N_Z, SE_EXACT, SE_OBSERVED, SIZES, SUBGROUP_N,
    TRUE_SIGMA, T_AT, WIDTH_AT_Z,
)

# ---------------------------------------------------------------- chapters
# Each chapter is data: the opener facts, the contents, and a builder that lays
# out its sections. Prose is adapted from that act's own narration — the page is
# the third render of the one script (see DESIGN.md §3).

P = "          "


def para(text, *notes, lead=False):
    """A paragraph, with its margin notes injected after the first sentence.

    The injection point matters: a float only rises to the line box where it
    appears, so a note placed after the paragraph lands at the paragraph's foot.
    """
    cls = ' class="lead"' if lead else ""
    if notes:
        m = re.search(r"(?<=[.?!])\s", text)
        cut = m.end() if m else len(text)
        text = text[:cut] + "".join(notes) + text[cut:]
    return f"{P}<p{cls}>{text}</p>"


def chapter_06(K):
    return [
        ("s1", "6.1", "A curve that is a claim", [
                    para("Level 4 told us which distribution every subgroup mean is drawn from, so long"
                         " as nothing about the process has changed. Draw that distribution and you have"
                         " not drawn a picture of your parts. You have drawn a claim.",
                         note("H₀ — the null", text="The process is unchanged: every subgroup mean is "
                              "drawn from one distribution."), lead=True),
                    para("The claim is that the process is unchanged — one stable stream, every subgroup"
                         " mean pulled from the same curve. That is the null hypothesis, and it is worth"
                         " being pedantic about what it is a hypothesis <em>about</em>. Not this part."
                         " Not this batch. The process.",
                         note("not H₀", text="A statement about any individual part. A part is never in "
                              "or out of control.")),
                    para("Everything that follows in this chapter is a consequence of taking that claim"
                         " seriously enough to test it.",
                         note("spoken · 0:11", text="“That curve is the null hypothesis. Not an "
                              "assumption about the parts, but a claim about the process.”",
                              speak=True, serif=True)),
                    "      " + K["fig"]("l06_1_null_distribution.png"),
        ]),
        ("s2", "6.2", "Pricing ±3σ", [
                    para("Put a pair of limits on that curve and sweep them outward from the centre. At"
                         " every position the question has an exact answer: how much of the distribution"
                         " is inside? Not looked up in a table — it is the integral of the curve between"
                         " the limits, evaluated as they move.",
                         datanote(("in-control", "99.73 %"), ("outside", "0.27 %"),
                                  k="what three sigma is worth")),
                    para("Stop at three sigma and the answer is 99.73%. Nobody chose that number. It is"
                         " simply what ±3σ is worth, and everything the process should ever do lives"
                         " inside it. The σ is the spread of whatever the chart plots: one part's"
                         " σ on a chart of single parts, σ/√<em>n</em> on a chart of subgroup"
                         " means, which is why an average chart's limits sit tighter than the"
                         " parts do.",
                         note("Φ", text="The standard normal CDF, computed from erf — not a table."),
                         note("spoken · 0:38", text="“Ninety-nine point seven three percent. Nobody "
                              "chose that number.”", speak=True, serif=True)),
                    "      " + K["eq"],
                    "  " + K["lab"],
                    "      " + K["fig"]("Level06.mp4"),
        ]),
        ("s3", "6.3", "Where the price hides", [
                    para("The whole of the rest — the part that makes the chart worth running — is out in"
                         " the tails, and at the scale of the last figure you cannot see it at all. So"
                         " stretch the vertical axis and let the tails grow. The peak goes straight out"
                         " of frame, which is the point: the tails are about seventy times smaller than"
                         " anything else on the chart.",
                         note("axis stretch", v="×70", text="needed before the tails are visible at all.")),
                    para("Each wing is one tenth of one percent of everything, and there are two of them."
                         " Together they are the tail integral, and it has a closed form: 0.0027. Invert"
                         " it and the bet is priced — one false alarm in 370 subgroups.",
                         datanote(("each wing", "0.135 %"), ("both wings", "0.0027"),
                                  ("false alarm", "1 in 370"), k="the tail, priced")),
        ]),
        ("s4", "6.4", "The chart is that test, repeated", [
                    para("A control chart is not a new idea on top of this one. It is the same test, run"
                         " again on every subgroup, forever. The limits are the boundary we just drew,"
                         " turned on its side. Every point inside is the process agreeing with the null"
                         " hypothesis, and that is what boring looks like. Boring is the goal. The"
                         " usual form of it, the Shewhart chart, gets built from real numbers in 6.7.",
                         note("allowed by H₀", v="1 in 370")),
                    para("Then one point steps outside — say 4.1σ above the centre line, where the null"
                         " allows one point in 370. That point is not a bad part, and scrapping it changes"
                         " nothing. It is evidence against the hypothesis that nothing changed. The"
                         " correct response is to go and find what did.",
                         note("the violation", v="4.1 σ"),
                         note("spoken · 2:09", text="“This is not a bad part, and scrapping it changes "
                              "nothing. It is evidence against the hypothesis that nothing changed.”",
                              speak=True, serif=True)),
                    "      " + K["sys"],
        ]),
        ("s5", "6.5", "How good is the σ estimate?", [
                    para("Everything so far assumed we know σ. On a real line we do not — we estimate it,"
                         " usually from the average range of the subgroups divided by a constant. That"
                         " estimate is unbiased on average, but a chart built from twenty-five subgroups"
                         " carries real fuzz in its own limits, which is why Phase I needs enough data"
                         " before the limits mean anything.",
                         datanote(("sigma-hat from ranges", "R̄ / d₂"),
                                  ("at 25 subgroups", "±0.075 σ", "spread in the estimate itself"),
                                  k="estimating sigma")),
                    "      " + K["fig"]("l06_2_rbar_plumbing.png"),
        ]),
        ("s6", "6.6", "Where the constants come from", [
                    para(tex(r"d_2") + " is the expected range of n standard normals. "
                         + tex(r"A_2") + ", " + tex(r"D_3") + " and " + tex(r"D_4") + " are the numbers"
                         " printed on every shop-floor chart form. None of them is looked up here: each"
                         " one is simulated, and then checked against the published table in a test suite."
                         " If the simulation and the table ever disagreed, the test would fail rather than"
                         " the page quietly lying.",
                         datanote((f"{nc('d₂')} at {nc(chr(110))} = 5", "2.326"), (f"A₂ at {nc(chr(110))} = 5", "0.577"),
                                  ("simulated", "400 000", "subgroups, checked against AIAG Table B"),
                                  k="the constants")),
                    K["watch"]("ConstantsAct.mp4", "constants", "figure 6.4",
                               "Where the constants come from: d₂ simulated from 400 000 subgroups,"
                               " landing on the published value."),
                    '      <div class="figpair">',
                    "      " + K["fig"]("01_d2.png"),
                    "      " + K["fig"]("02_A2_D3_D4.png"),
                    "      </div>",
        ]),
        ("s7", "6.7", "Building the chart", [
            para("Here is the whole procedure on one stable process: twenty-five subgroups of"
                 " five parts, measured in millimetres. Each subgroup gives two numbers, its mean"
                 " and its range. Plot the means on one chart and the ranges on a second chart"
                 " under it. That pair is the " + tex(r"\bar{X}") + "–R chart. Walter Shewhart"
                 " drew the first control chart in 1924, so it also goes by his name.",
                 datanote(("subgroups", f"{len(XR['means'])} × 5"),
                          ("grand mean", f"{XR['xbarbar']:.4f}"),
                          ("mean range R̄", f"{XR['rbar']:.4f}"),
                          k="the data, mm"), lead=True),
            para("The top chart's centre line is the grand mean, " + tex(r"\bar{\bar{x}}") + ","
                 " the mean of the means. Its limits sit " + tex(r"A_2\bar{R}") + " either side."
                 f" For subgroups of five A₂ is {XR['A2']:.3f}, so the distance is"
                 f" {XR['A2']:.3f} × {XR['rbar']:.4f} = {XR['A2']*XR['rbar']:.4f} mm and the"
                 f" limits land at {XR['lcl_xbar']:.4f} and {XR['ucl_xbar']:.4f}.",
                 note("why A₂ works", text=tex(r"\bar{R}/d_2") + " estimates one part's σ (6.5). Divide by"
                      " √n for the σ of a mean (4.3), then take three of those: "
                      + tex(r"3\bar{R}/(d_2\sqrt{n}) = A_2\bar{R}") + ".")),
            para("The ranges get a chart of their own because a process can go wrong without its"
                 " mean moving. A loose fixture lets parts scatter while the average stays put."
                 " The R chart's centre line is " + tex(r"\bar{R}") + " and its upper limit is "
                 + tex(r"D_4\bar{R}") + f" = {XR['D4']:.3f} × {XR['rbar']:.4f} ="
                 f" {XR['ucl_r']:.4f} mm. Its lower limit, " + tex(r"D_3\bar{R}") + ", is"
                 " zero, because D₃ is zero for any subgroup of six parts or fewer.",
                 datanote(("A₂", f"{XR['A2']:.3f}"), ("D₃", f"{XR['D3']:.0f}"),
                          ("D₄", f"{XR['D4']:.3f}"), k="at n = 5")),
            para("Read the range chart first. If the ranges are out of control, " + tex(r"\bar{R}") + " is wrong,"
                 " and so is every limit built from it on the top chart. Here "
                 + ("nothing crosses a line on either chart" if XR_OUT == 0 else
                    f"{XR_OUT} points cross a line")
                 + ": twenty-five subgroups of a process doing nothing but varying.",
                 datanote((nc("σ") + " from R̄ / d₂", f"{XR['sigma_hat']:.4f}"),
                          (nc("σ") + " that made the data", f"{XR_SIGMA:.4f}"),
                          k="the estimate, checked")),
            "      " + K["fig"]("l06_3_xbar_r.png"),
        ]),
    ]


def chapter_12(K):
    from spclab.experiments import (
        ALIASES, BASELINE, CORNERS, CURVED, EFFECTS, FLAT, FULL_RUNS, GENERATORS,
        OFAT, OPTIMUM, OPTIMUM_Y, PRECISION, SCREEN_FACTORS, SCREEN_RUNS, TRUTH,
    )
    worse = 100.0 * OFAT["shortfall"] / OPTIMUM_Y
    # defining relation: every product of the generator words (I = ABD, ...)
    import functools, itertools as _it, operator
    words = [set(w + L) for L, w in GENERATORS.items()]
    relation = [functools.reduce(operator.xor, c) for r in range(1, len(words) + 1)
                for c in _it.combinations(words, r)]
    resolution = min(len(w) for w in relation)
    roman = {3: "III", 4: "IV", 5: "V"}[resolution]
    gens = ", ".join(f"{L}&nbsp;=&nbsp;{w}" for L, w in GENERATORS.items())
    base = "".join(L for L in SCREEN_FACTORS if L not in GENERATORS)
    return [
        ("s1", "12.1", "Changing things on purpose", [
            para("Every level so far watched a process, or described data that arrived"
                 " on its own. This one changes the settings deliberately, and the whole"
                 " subject turns on a single fact that is easy to state and easy to"
                 " ignore.",
                 note("the last level", text="Eleven levels of listening. This one "
                      "asks."), lead=True),
            "      " + K["eq"],
            para("Here <em>y</em> is the response and each <em>x</em> is a factor coded"
                 " −1 at its low setting and +1 at its high one. " + tex(r"\beta_0") +
                 " is the average over the four corners; " + tex(r"\beta_A") + " and "
                 + tex(r"\beta_B") + " are how far <em>y</em> moves per unit of each factor;"
                 " " + tex(r"\beta_{AB}") + " is the twist, how much the first factor's"
                 " slope changes as the second moves; " + tex(r"\varepsilon") + " is the"
                 " measurement noise."),
            para("Low to high is two units, so an <em>effect</em>, the change from one"
                 " setting to the other, is twice its β. The interaction effect of"
                 f" {EFFECTS['AB']:+.0f} in 12.3 is a " + tex(r"\beta_{AB}") +
                 f" of {EFFECTS['AB']/2:+.1f}, the value the lab in 12.3 starts at."),
            para("If two factors interact — if what the second one does depends on where"
                 " the first one is set — then studying them one at a time can lead you"
                 " confidently to the wrong setting. Not slowly. Wrongly.",
                 note("the condition", text="An interaction larger than a main effect. "
                      "Below that, one-at-a-time is merely slow.")),
        ]),
        ("s2", "12.2", "One factor at a time, with perfect measurements", [
            "      " + K["fig"]("Level12.mp4"),
            para("Hold pressure and melt temperature, two levels each, shrinkage as the"
                 " response and lower is better. The classic procedure: start with"
                 " everything low, tune the second factor, fix it, tune the first.",
                 datanote(*[(f"pressure {c[0]:+d}, temp {c[1]:+d}", f"{TRUTH[c]:.0f}")
                            for c in CORNERS],
                          k="true shrinkage at the four corners"), lead=True),
            para(f"Run it with no measurement noise whatsoever — every reading exactly"
                 f" the true value — and it stops at {OFAT['chosen_y']:.0f} when"
                 f" {OPTIMUM_Y:.0f} was available. That is {worse:.0f} % worse, and it"
                 " cannot be blamed on sampling error because there is none.",
                 datanote(("stops at", f"{OFAT['chosen_y']:.0f}"),
                          ("optimum", f"{OPTIMUM_Y:.0f}"),
                          ("shortfall", f"{OFAT['shortfall']:.0f}"),
                          ("corners visited", f"{len(set(OFAT['visited']))} of 4"),
                          k="one at a time, noise-free")),
            para("The reason is visible once it is drawn: the procedure never visits the"
                 " corner with high pressure and low temperature, so the setting that"
                 " wins is one it never tries.",
                 note("spoken plainly", text="It is not a search that stopped early. It "
                      "is a search that cannot reach the answer.")),
            "      " + K["fig"]("l12_1_why_ofat_fails.png"),
        ]),
        ("s3", "12.3", "The interaction it cannot estimate", [
            para("An interaction is a difference of differences: what the temperature"
                 " does at high pressure, minus what it does at low pressure, halved. That"
                 " needs all four corners, and one at a time visits three.",
                 datanote(("effect A", f"{EFFECTS['A']:+.0f}"),
                          ("effect B", f"{EFFECTS['B']:+.0f}"),
                          ("interaction AB", f"{EFFECTS['AB']:+.0f}"),
                          k="from the full factorial"), lead=True),
            para(f"So the interaction here — {EFFECTS['AB']:+.0f}, larger than either"
                 " main effect — is not estimated badly by the one-at-a-time runs. It is"
                 " not estimable from them at all. The factorial gets it from the same"
                 " number of runs, because a factorial spends its runs on corners rather"
                 " than on paths.",
                 note("not a precision problem", text="Unidentifiable, which is a "
                      "stronger statement than imprecise.")),
            para("And the same design is more precise about the main effects too. Every"
                 " run contributes to every effect — the hidden replication — so on"
                 f" {PRECISION['runs']} runs the factorial's estimate of the pressure"
                 f" effect has a standard deviation of {PRECISION['factorial_sd']:.3f}"
                 f" against {PRECISION['ofat_sd']:.3f} for the comparison it replaces.",
                 datanote(("factorial", f"{PRECISION['factorial_sd']:.3f}"),
                          ("one at a time", f"{PRECISION['ofat_sd']:.3f}"),
                          ("ratio", f"×{PRECISION['ratio']:.2f}"),
                          k=f"s.d. of the effect, {PRECISION['runs']} runs")),
            "  " + K["lab"],
            para("Drag the interaction to zero and the procedure never fails — which is"
                 " the honest version of the claim. One at a time is not wrong in"
                 " general; it is wrong exactly when factors interact, and you cannot"
                 " know whether they do without a design that could have told you.",
                 note("why that matters", text="The condition for the method to work is "
                      "the thing the method cannot check.")),
        ]),
        ("s4", "12.4", "Screening: width, bought with aliasing", [
            para(f"With seven factors a full factorial is {FULL_RUNS} runs. A"
                 f" fraction does it in {SCREEN_RUNS}, one sixteenth of that, and the price"
                 " is not vague — it is a table you can write down before the first run.",
                 datanote(*[(f"main effect {L}", ", ".join(ALIASES[L]))
                            for L in SCREEN_FACTORS[:4]],
                          k="confounded with"), lead=True),
            para(f"The {SCREEN_RUNS} runs are a full factorial in {', '.join(base)}. The"
                 f" other {len(GENERATORS)} factors get no runs of their own: each is set by"
                 " a generator, a rule that copies a product of existing columns —"
                 f" {gens}. That is how {SCREEN_RUNS} runs hold {len(SCREEN_FACTORS)}"
                 " factors, and it is also the bill."),
            para("Each main effect is confounded with a set of two-factor interactions:"
                 " the columns are literally identical across the eight runs, so no"
                 " arithmetic can separate them. Resolution grades that damage: it is the"
                 " length of the shortest word you get by multiplying generators together"
                 f" (D&nbsp;=&nbsp;AB gives ABD), {resolution} here, written {roman}. Resolution {roman}"
                 " keeps main effects clear of each other but tangles each with two-factor"
                 " interactions.",
                 note("the deal", text="Screening finds which factors matter. It cannot "
                      "also tell you how they interact — that is the next experiment.")),
            para("Which is the right trade at the start of an investigation and the wrong"
                 " one at the end. Screen wide and cheap, then spend the second"
                 " experiment on the two or three factors that survived."),
        ]),
        ("s5", "12.5", "Curvature, and why the corners cannot see it", [
            para("A two-level design fits a plane with a twist in it. If the true surface"
                 " bends, the corners cannot report it — and the reason is sharper than"
                 " it first looks.",
                 datanote(("corners", f"{CURVED['factorial_mean']:.2f}"),
                          ("centre", f"{CURVED['centre_mean']:.2f}"),
                          ("gap", f"{CURVED['gap']:+.2f}"),
                          ("p", f"{CURVED['p']:.4f}"),
                          k="a surface that really bends"), lead=True),
            para("With coded ±1 factors the quadratic term contributes the <em>same</em>"
                 " amount at every corner and nothing at the centre. So it is not absent"
                 " from the corner readings — it is constant across them, which makes it"
                 " inseparable from the intercept. Every effect estimate comes out"
                 " unchanged.",
                 note("the test", text="A few runs at the middle, and the gap between "
                      "the corner mean and the centre mean is a pure quadratic signal.")),
            para(f"Add centre points and it becomes a test. On the bent surface the gap"
                 f" is {CURVED['gap']:+.2f} with p = {CURVED['p']:.4f}; on a genuinely"
                 f" flat one it is {FLAT['gap']:+.2f} with p = {FLAT['p']:.2f}. The"
                 " design does not merely estimate better — it can now be wrong out"
                 " loud, which is the property Level 7 spent its whole length arguing"
                 " for.",
                 datanote(("flat surface gap", f"{FLAT['gap']:+.2f}"),
                          ("its p", f"{FLAT['p']:.2f}"),
                          k="and it does not cry curvature")),
            "      " + K["fig"]("l12_2_screening_and_curvature.png"),
        ]),
        ("s6", "12.6", "Twelve levels", [
            para("That closes the arc. Twelve levels, and the thread through all of them"
                 " is that every number on a chart is the result of an argument that can"
                 " be reconstructed — so none of them has to be taken on faith.",
                 note("the rule", text="No number on this site is asserted. Every "
                      "constant is computed at render time and the tests check the same "
                      "functions."), lead=True),
            para("Variation, chance, centre and spread, the predictable average,"
                 " estimation. Then limits as a bet, evidence as a trade, capability,"
                 " detection. Then counting rather than measuring, relationships, and"
                 " experiments. Each level ends by raising the question the next one"
                 " answers, which is the only structure the whole thing has.",
                 note("where it goes next", text="Level 11 hands measurement systems to "
                      "their own site. Nothing here needed a citation to be believed.")),
        ]),
    ]


def chapter_11(K):
    from spclab.relationships import (
        ADJ_WITH_NOISE, CURVED_FIT, CURVED_RUN, FIT, GAUGE, HALF_CI, HALF_PI,
        MSA_CURRICULUM, OPERATORS, PARTS, R2_PLAIN, R2_WITH_NOISE, REPEATS,
        STRAIGHT_RUN, X0, COVERAGE,
    )
    ks = sorted(R2_WITH_NOISE)
    return [
        ("s1", "11.1", "One identity, three names", [
            para("Every level so far watched one number over time. This one asks what a"
                 " number has to do with another number — and the machinery turns out to"
                 " be something already familiar, relabelled twice.",
                 note("why it is the bridge", text="Regression, ANOVA and a gauge study "
                      "are one identity. Seeing that is what makes the last of them "
                      "ordinary."), lead=True),
            para("Draw a straight line through a cloud of points. For each point,"
                 " " + tex(r"y_i") + " is what was measured, " + tex(r"\hat{y}_i") +
                 " is what the line predicts at that point, and " + tex(r"\bar{y}") +
                 " is the average of all the readings. Each reading's distance from the"
                 " average then breaks into two pieces: the line's prediction minus the"
                 " average, and the reading minus the prediction. Square each piece and sum"
                 " over the points, and for a least-squares line the three sums obey the"
                 " identity below exactly."),
            "      " + K["eq"],
            para("Split the total variation in two and you have regression, where the"
                 " explained part over the total is R². Relabel those two terms"
                 " between-groups and within-groups and you have ANOVA. Split the total"
                 " four ways instead of two and you have a Gage R&amp;R. Nothing new is"
                 " introduced at any step.",
                 note("what changes", text="Only the labels on the terms. The subtraction "
                      "is the same subtraction.")),
        ]),
        ("s2", "11.2", "Least squares is a claim", [
            "      " + K["fig"]("Level11.mp4"),
            para("The line is not drawn by eye and it is not fitted by iteration: it is"
                 " the slope that minimises the sum of squared residuals, and the closed"
                 " form lands exactly at that minimum rather than near it: "
                 + tex(r"b = \sum (x_i-\bar{x})(y_i-\bar{y}) \,/\, \sum (x_i-\bar{x})^2") +
                 ", and the intercept puts the line through the point of averages, "
                 + tex(r"a = \bar{y} - b\bar{x}") + ".",
                 datanote(("slope", f"{FIT['slope']:.5f}"),
                          ("intercept", f"{FIT['intercept']:.4f}"),
                          ("residual SS", f"{FIT['sse']:.4f}"),
                          ("R²", f"{FIT['r2']:.4f}"),
                          k=f"{FIT['n']} speeds, one line"), lead=True),
            para("Sweeping the slope traces a parabola in the residual sum of squares."
                 " That parabola is why the phrase means something: any other slope is"
                 " worse, and it is worse by a computable amount.",
                 note("orthogonal residuals", text="Least squares leaves the residuals "
                      "summing to zero and uncorrelated with the predictor — exactly, "
                      "not approximately.")),
            "      " + K["fig"]("l11_1_least_squares.png"),
        ]),
        ("s3", "11.3", "R² is a ratio, not a grade", [
            para("R² is the fraction of the total variation the line accounts for. It is a"
                 " summary, and it has two properties worth knowing before quoting it.",
                 datanote((f"the line alone", f"{R2_PLAIN:.4f}"),
                          *[(f"plus {k} noise columns", f"{R2_WITH_NOISE[k]:.4f}")
                            for k in ks[1:]],
                          k="R² after adding nothing"), lead=True),
            para("The first is that it cannot fall when a predictor is added, so adding"
                 " columns of pure noise raises it. Ten such columns take it from"
                 f" {R2_PLAIN:.4f} to {R2_WITH_NOISE[ks[-1]]:.4f} while explaining nothing"
                 " whatsoever. Adjusted R² exists precisely because of this, and it turns"
                 f" down — {ADJ_WITH_NOISE[ks[0]]:.4f} to {ADJ_WITH_NOISE[ks[-1]]:.4f}.",
                 note("adjusted R²", text="The same ratio, penalised for the number of "
                      "columns spent buying it.")),
            para("The second is worse: a high R² can sit beside residuals that are"
                 " visibly wrong. Fitting a straight line to a curved relationship here"
                 f" scores {CURVED_FIT['r2']:.3f} — respectable by any rule of thumb —"
                 f" while the residuals stay on the same side of zero for {CURVED_RUN}"
                 f" points in a row against {STRAIGHT_RUN} for the honest fit.",
                 datanote(("straight, R²", f"{FIT['r2']:.3f}"),
                          ("its longest run", f"{STRAIGHT_RUN}"),
                          ("curved, R²", f"{CURVED_FIT['r2']:.3f}"),
                          ("its longest run", f"{CURVED_RUN}"),
                          k="the number R² cannot see")),
            "  " + K["lab"],
            para("Drag the curvature up and watch R² barely move while the run climbs and"
                 " the status flips. The residuals are the diagnostic; R² is only the"
                 " summary.",
                 note("Level 1 again", text="The longest same-sign run is the same "
                      "statistic that showed a histogram throws away time order.")),
        ]),
        ("s4", "11.4", "Two intervals that are not the same interval", [
            para("Asked to predict at a speed, there are two honest answers and they are"
                 " different sizes. One is an interval for the <em>mean</em> response"
                 " there; the other is an interval for a <em>single new reading</em>.",
                 datanote(("the mean response", f"±{HALF_CI:.3f}"),
                          ("one new reading", f"±{HALF_PI:.3f}"),
                          ("ratio", f"×{HALF_PI/HALF_CI:.2f}"),
                          k=f"95 % half-widths at {X0:.0f} m/min"), lead=True),
            para("With <em>s</em> the residual standard deviation, " + tex(r"S_{xx} = \sum (x_i-\bar{x})^2") +
                 " and <em>t</em> the Level 5 quantile at <em>n</em> − 2 degrees of freedom,"
                 " the mean response gets " + tex(r"\pm\, t s \sqrt{1/n + (x_0-\bar{x})^2/S_{xx}}") +
                 " and one new reading gets " + tex(r"\pm\, t s \sqrt{1 + 1/n + (x_0-\bar{x})^2/S_{xx}}") + "."),
            para("The difference is a single 1 inside a square root, and that 1 is the"
                 " variance of the new reading itself. It is why more data shrinks the"
                 " first interval toward nothing and never shrinks the second below the"
                 " noise of the process.",
                 note("counted, not claimed", text=f"Coverage over 4 000 refits: "
                      f"{COVERAGE['ci']*100:.1f} % for the mean, "
                      f"{COVERAGE['pi']*100:.1f} % for a reading.")),
            para("Quoting the narrow one when someone asked about the next part is the"
                 " most common way a regression gets misused on a shop floor, and it is"
                 " an arithmetic error rather than a judgement call."),
        ]),
        ("s5", "11.5", "The same total, split four ways", [
            para("Now take the identity two-way. Ten parts, three operators, each part"
                 " measured twice by each: the total variation splits into part,"
                 " operator, their interaction, and repeat-to-repeat error — using the"
                 " subtraction from §11.1 and nothing else.",
                 datanote(("part", f"{GAUGE['pct']['part']:.2f} %"),
                          ("repeat", f"{GAUGE['pct']['repeat']:.2f} %"),
                          ("operator", f"{GAUGE['pct']['operator']:.2f} %"),
                          ("interaction", f"{GAUGE['pct']['interaction']:.2f} %"),
                          k="share of total variance"), lead=True),
            para("That is a Gage R&amp;R. Repeatability is the repeat term, reproducibility"
                 " is the operator term, and the gauge is everything that is not the"
                 f" parts — {GAUGE['pct_gauge']:.1f} % here. No new technique was"
                 " introduced to get there.",
                 note("a caution", text="Ten parts is far too few to pin these "
                      "percentages. The estimator can even return a negative component, "
                      "which is reported as zero.")),
            "      " + K["fig"]("l11_2_intervals_and_bridge.png"),
            para("What those percentages mean — whether this gauge may be used, on what"
                 " tolerance, and what to do when reproducibility dominates — is a"
                 " different subject with its own arc, and this curriculum stops at the"
                 " boundary rather than summarising it badly. It continues at"
                 f' <a href="{MSA_CURRICULUM}" target="_blank" rel="noopener">MSA from'
                 " first principles</a>, a sibling site that repeats this method on the"
                 " measurement system itself: a gauge is a process, so it has a"
                 " distribution, so the same arithmetic applies to it.",
                 note("the seam", text="This site never teaches gauge acceptance, and "
                      "the MSA side never teaches control limits. One link each way.")),
        ]),
    ]


def chapter_10(K):
    from spclab.counting import (
        C_AT, C_BAR, DISPERSION_BATCHED, DISPERSION_CLEAN, MISCLASS, NP_THRESHOLD,
        N_CONST, N_FOR_LCL, NP_AT_CONST, P_AT_CONST, P_BAR, TAIL, UNIT_DEFECT, UNIT_ITEM,
        CHART_TABLE,
    )
    folklore = int(round(5.0 / P_BAR))
    return [
        ("s1", "10.1", "The spread is not a free parameter", [
            "      " + K["fig"]("Level10.mp4"),
            para("Levels 3 to 5 spent their time estimating a spread, because for a"
                 " measurement the spread is a separate fact about the process — it has"
                 " to be measured, and it carries its own error. Stop measuring and"
                 " start counting, and that stops being true.",
                 note("what changes", text="A measurement needs a range chart beside "
                      "it. A count does not, and this is why."), lead=True),
            para("Count defective items and the result is binomial, so its standard"
                 " deviation is fixed by its mean. Count defects and the result is"
                 " Poisson, where the variance <em>is</em> the mean. Either way nothing"
                 " is estimated separately.",
                 datanote((f"{nc('p̄')} assumed", f"{P_BAR:.2f}"),
                          (f"{nc('n')}", f"{N_CONST}"),
                          (f"{nc('σ')} of the proportion", f"{P_AT_CONST['sigma']:.5f}"),
                          (f"{nc('c̄')} = {C_BAR}", f"{nc('σ')} = {C_AT['sigma']:.3f}"),
                          k="the mean fixes the spread")),
            "      " + K["eq"],
            para("Which makes a disagreement informative. If the observed scatter is"
                 " wider than the binomial says it must be, the binomial assumption is"
                 " wrong — and the usual reason is that the rate moved between"
                 " subgroups.",
                 note("free diagnostic", text="Observed variance over theoretical. One "
                      "for a genuine binomial; above one and the subgroups were not "
                      "rational.")),
        ]),
        ("s2", "10.2", "Same mean, different scatter", [
            para("Two processes, both averaging four per cent defective. One has a"
                 " single rate behind every subgroup; in the other the rate drifts —"
                 " a shift change, a supplier lot, an operator. The means are"
                 " indistinguishable and the charts are not.",
                 datanote(("one rate throughout", f"{DISPERSION_CLEAN:.2f}"),
                          ("rate drifting", f"{DISPERSION_BATCHED:.2f}"),
                          k="observed ÷ binomial variance"), lead=True),
            para("The second process is not wider. It is a process whose rate moved, and"
                 " every limit computed from the binomial is too tight for it — so it"
                 " will trip its own chart for a reason that has nothing to do with the"
                 " thing being counted. This is what rational subgrouping means for"
                 " attribute data."),
            "      " + K["fig"]("l10_1_spread_is_not_free.png"),
        ]),
        ("s3", "10.3", "Four charts, two questions", [
            para("The four attribute charts are usually presented as four names to learn."
                 " They are two binary questions, and once they are asked the name is"
                 " determined.",
                 note("question one", text="Defective <em>items</em>, or "
                      "<em>defects</em>? One is binomial, the other Poisson."),
                 lead=True),
            para("Are you counting defective items — each thing inspected is either good"
                 " or bad — or counting defects, where one thing can carry several? And"
                 " is the subgroup size constant?",
                 datanote(*[(f"{u}, {nc('n')} {'constant' if c else 'varies'}",
                             f"{name}-chart")
                            for (u, c), name in CHART_TABLE.items()],
                          k="the whole selection rule"),
                 note("question two", text="Constant subgroup size, or not? That is the "
                      "only other thing the choice depends on.")),
            para("Each chart plots a single number per subgroup. The np-chart plots the count"
                 " of defective items and the p-chart the fraction defective; the c-chart"
                 " plots the count of defects and the u-chart defects per unit inspected."
                 " The fraction and the per-unit rate exist so that subgroups of different"
                 " sizes land on one scale."),
            para("That is the entire decision. There is no fifth chart hiding behind a"
                 " third question."),
        ]),
        ("s4", "10.4", "When the limits have to breathe", [
            para("If the subgroup size varies, the limits vary with it — a bigger"
                 " subgroup gives a tighter proportion, so the band narrows. The"
                 " tempting shortcut is one set of limits computed at the average size.",
                 datanote(("subgroup sizes", f"{MISCLASS['spread'][0]}–{MISCLASS['spread'][1]}"),
                          ("false signals", f"{MISCLASS['false_signal']*100:.2f} %"),
                          ("signals missed", f"{MISCLASS['missed']*100:.2f} %"),
                          ("disagreement", f"{MISCLASS['disagree']*100:.2f} %"),
                          k="average-n limits against honest ones"), lead=True),
            para(f"Over sizes from {MISCLASS['spread'][0]} to {MISCLASS['spread'][1]} that"
                 f" shortcut disagrees with the honest limits on"
                 f" {MISCLASS['disagree']*100:.2f} % of subgroups, and most of the"
                 f" disagreement is false alarms rather than misses — it spends more than"
                 " the whole false-alarm budget Level 6 designed for.",
                 note("Level 7's language", text="A fixed cost for nothing bought. The "
                      "shortcut is not a trade, it is a leak.")),
            "      " + K["fig"]("l10_2_breathing_limits.png"),
        ]),
        ("s5", "10.5", "Where the lower limit goes", [
            para("At low counts the lower limit goes negative, and a chart cannot draw a"
                 " negative fraction. It gets clamped to zero, and a limit at zero is"
                 " not a limit: the chart can only ever signal upward.",
                 datanote(("lower limit, raw", f"{P_AT_CONST['lcl_raw']*100:.2f} %"),
                          ("as drawn", "0"),
                          (f"{nc('n')} needed", f"{N_FOR_LCL}"),
                          k=f"at {nc('n')} = {N_CONST}"), lead=True),
            para("Like every limit in this course, it is the centre minus three of its own"
                 " sigmas: " + tex(r"\mathrm{LCL} = \bar{p} - 3\sqrt{\bar{p}(1-\bar{p})/n}") + "."
                 f" At <em>n</em> = {N_CONST} that is {P_BAR:.2f}&nbsp;− 3&nbsp;×&nbsp;{P_AT_CONST['sigma']:.4f}"
                 f" = {P_AT_CONST['lcl_raw']:.4f}".replace("-", "−") + ", below zero."),
            para("There is a threshold and it is exact. Ask when that difference stays above"
                 " zero, square both sides, and the lower limit clears zero only"
                 " while " + tex(r"n\bar{p} > k^{2}(1-\bar{p})") + f", which at three"
                 f" sigma is {NP_THRESHOLD:.2f}. At four per cent defective that means"
                 f" subgroups of {N_FOR_LCL} — not the {folklore} the familiar"
                 " “" + tex(r"n\bar{p} \ge 5") + "” rule of thumb allows.",
                 note("the rule of thumb", text="A weaker version of the same "
                      "arithmetic. At " + tex(r"n\bar{p} = 5") + " the limit is still "
                      "negative.")),
            "  " + K["lab"],
            para("Drag the two controls. The status reads ONE-SIDED whenever the lower"
                 " limit has been clamped, and the third tile tells you the subgroup size"
                 " that would fix it.",
                 note("computed here", text="The lab runs the same formulas "
                      "<code>spclab.counting</code> is tested against, in the browser.")),
        ]),
        ("s6", "10.6", "Annex — capability when the shape is wrong", [
            para("Level 8 turned a spread into a ppm by walking out the tail of a normal"
                 " curve. Counts are not normal, and the approximation fails in the"
                 " direction that flatters the process.",
                 datanote(("exact tail", f"{TAIL['exact']:.5f}"),
                          ("normal approximation", f"{TAIL['approx']:.5f}"),
                          ("ratio", f"×{TAIL['ratio']:.2f}"),
                          k="P(16 or more defective)"), lead=True),
            para(f"Take the process from 10.1: subgroups of {N_CONST} at {P_BAR*100:.0f} %"
                 f" defective, so {NP_AT_CONST['cl']:.0f} defective on average and an np-chart"
                 f" upper limit at {NP_AT_CONST['ucl']:.1f}. Sixteen defective is a subgroup"
                 " sitting just under that limit. How often does one land there or beyond?"),
            para(f"The true probability is {TAIL['ratio']:.1f} times what the normal"
                 " approximation reports. Quoting a normal-based ppm on count data is"
                 " therefore not a rounding error — it understates the risk by a factor"
                 " you would notice. The approximation improves as the counts grow; it"
                 " is wrong where attribute data usually lives.",
                 note("so what to do", text="Use the exact tail: add up the binomial "
                      "probabilities from 16 to 200. For large subgroups the same sum comes "
                      "from the incomplete beta function, which Level 5 already uses for "
                      "<em>t</em>.")),
        ]),
    ]


def chapter_07(K):
    # imported here rather than at module scope: the trade table is simulated at
    # import, and regenerating the other seven chapters should not pay for it
    from spclab.evidence import (
        ALPHA_1, ARL0_ALL, ARL0_ONE_RULE, ARL1_ALL, ARL1_ONE_RULE, ARL_BIG_ALL,
        ARL_BIG_ONE, BIG_SHIFT, CHAMP_WOODALL_ARL0, FALSE_ALARM_COST, LIMIT,
        POWER_AT, RULE_TEXT, RULES, SHIFT, TRADE, cumulative_sets, p_value,
    )
    gain_small = ARL1_ONE_RULE / ARL1_ALL
    gain_big = ARL_BIG_ONE / ARL_BIG_ALL
    return [
        ("s1", "7.1", "The other way to be wrong", [
            para("Level 6 priced one decision: a point outside three sigma. It costs"
                 f" {ALPHA_1*100:.2f} % of subgroups a false alarm, and Level 2 turned that"
                 " rate into one alarm in 370. What neither level mentioned is the other"
                 " way a chart can be wrong — staying silent when the process really"
                 " has moved.",
                 note(nc("α"), text="Crying wolf. Priced in Level 6, and the only error a "
                      "three-sigma limit is chosen against."), lead=True),
            para("Draw the shifted process against the same limits and the problem is"
                 " visible before it is named. A mean that has moved by a full sigma"
                 " sits almost entirely inside them. Sigma here, as on every chart, is the"
                 " spread of the plotted point: one part's σ for single parts, σ/√<em>n</em>"
                 " for subgroup means.",
                 datanote((f"{nc(chr(945))}, crying wolf", f"{ALPHA_1*100:.2f} %"),
                          (f"{nc(chr(946))} at {SHIFT:.0f}{nc(chr(963))}", f"{1-POWER_AT[SHIFT]:.3f}"),
                          ("so it is caught", f"{POWER_AT[SHIFT]*100:.1f} %"),
                          k="two ways to be wrong")),
            para(f"So the chance of catching that shift on the next point is"
                 f" {POWER_AT[SHIFT]*100:.1f} %. The chart is not broken. A one-sigma"
                 " shift simply looks like ordinary noise to a test that only ever sees"
                 " one point at a time — and this is the bigger of the two errors,"
                 " because nobody is counting it.",
                 note("spoken · 0:48", text="“That is the error Level 6 never "
                      "mentioned, and it is the bigger one.”", speak=True, serif=True)),
            "      " + K["fig"]("l07_1_two_errors.png"),
        ]),
        ("s2", "7.2", "Power", [
            para("Put a number on it at every shift size and you have the power curve:"
                 " the chance that one point sees a shift of a given size. It is worth"
                 " reading slowly, because it is unflattering.",
                 datanote(*[(f"{s:.1f}{nc('σ')}", f"{POWER_AT[s]*100:.1f} %")
                            for s in (0.5, 1.0, 2.0, 3.0)],
                          k="chance the next point signals"), lead=True),
            "      " + K["eq"],
            para(f"At two sigma it is {POWER_AT[2.0]*100:.1f} %. It takes a shift of"
                 f" three full sigma — the mean landing exactly on the limit — before"
                 " the next point is even a coin toss, and that is not a coincidence:"
                 " when the mean sits on the limit, half the distribution is on each"
                 " side of it.",
                 note("why exactly a half", text="At " + tex(r"\delta = k")
                      + " one tail contributes almost nothing and the other contributes "
                      + tex(r"\Phi(0)") + ".")),
            para("One point, one chance. Everything the extra rules do is an attempt to"
                 " get around that single sentence.",
                 note("spoken · 1:36", text="“One point, one chance. That is the whole "
                      "limitation.”", speak=True, serif=True)),
            "      " + K["fig"]("Level07.mp4"),
            "  " + K["lab"],
        ]),
        ("s3", "7.3", "The chart throws evidence away", [
            para("Consider a point at two and a half sigma. It is inside the limits, so"
                 " the chart calls it in control and moves on. Ask instead how"
                 " surprising it is, and the answer is a p-value of"
                 f" {p_value(2.5):.4f} — about one in eighty.",
                 datanote(("point at 2.5" + nc("σ"), f"{p_value(2.5):.4f}"),
                          ("point at 3.0" + nc("σ"), f"{p_value(LIMIT):.4f}"),
                          ("the chart's verdict", "in control"),
                          k="p-value, two-sided"), lead=True),
            para("Anywhere else in statistics that is a finding. Here it is filed as a"
                 " pass and forgotten, because the in-or-out rule keeps the verdict and"
                 " discards the evidence.",
                 note("the same number twice", text="A point exactly on the limit has "
                      "a p-value equal to α. The chart <em>is</em> a test with its "
                      "threshold already chosen.")),
            para("A verdict is not the same as the evidence. The extra rules exist to"
                 " spend what a single point cannot hold — a pattern across several"
                 " points, none of which is damning on its own."),
        ]),
        ("s4", "7.4", "Four rules, one at a time", [
            para("The Western Electric rules are usually taught as a list to memorise."
                 " They are not a list. They are four purchases, and each one has a"
                 " price that can be computed.",
                 datanote(*[(f"rule {r}", RULE_TEXT[r]) for r in RULES],
                          k="what each rule reads"), lead=True),
            para("Switch them on one at a time and watch two run lengths move in the"
                 " same direction — the subgroups between false alarms, which you want"
                 f" long, and the subgroups to catch a real {SHIFT:.0f}σ shift, which"
                 " you want short. Every rule shortens both.",
                 datanote(*[("rule " + "+".join(str(r) for r in rs),
                             f"{TRADE[rs]['arl0']:.0f} / {TRADE[rs]['arl1']:.1f}")
                            for rs in cumulative_sets()],
                          k="false alarm every / catches in")),
            para(f"All four together give a false alarm every {ARL0_ALL:.0f} subgroups"
                 f" instead of {ARL0_ONE_RULE:.0f} (simulated; the exact value for rule 1"
                 " alone is 370.4, the 370 of Levels 2 and 6). That figure was published in 1987 as"
                 f" {CHAMP_WOODALL_ARL0}, and the simulation here was not told about it"
                 " — it reproduces it from the rules themselves.",
                 note("corroboration", text="Champ &amp; Woodall, 1987. Agreement with "
                      "a number derived elsewhere is worth more than internal "
                      "consistency.")),
            "          " + '<p class="lab-link">To watch rules fire as the points land, step 6 of <a href="https://portfolio.amohdnaw.xyz/lab.html#ch3" target="_blank" rel="noopener">CH 3 of the control lab</a> bumps a table partway through a run and names each rule as it trips. It numbers them Nelson\'s way, with eight rules, so this page\'s rule 2 shows up there as rule 5.</p>',
            "      " + K["fig"]("07_western_electric.png"),
        ]),
        ("s5", "7.5", "So is it worth it", [
            para("Line up what the rules cost against what they buy, and the answer"
                 " stops being a matter of taste.",
                 datanote(("cost, always", f"×{FALSE_ALARM_COST:.1f} false alarms"),
                          (f"bought at {SHIFT:.0f}{nc('σ')}", f"×{gain_small:.1f} sooner"),
                          (f"bought at {BIG_SHIFT:.0f}{nc('σ')}", f"×{gain_big:.1f} sooner"),
                          k="all four rules"), lead=True),
            para(f"Against a slow one-sigma drift the rules catch it ×{gain_small:.1f}"
                 f" sooner — more than the ×{FALSE_ALARM_COST:.1f} in false alarms they"
                 " cost, so the trade is good. Against a three-sigma jump they catch it"
                 f" only ×{gain_big:.1f} sooner, because rule one already sees it on the"
                 " next point. Same cost, almost nothing bought.",
                 note("read it twice", text="The cost is one number. The benefit is a "
                      "function of the shift, and the shift is a fact about your "
                      "process.")),
            para("So the rules are not good or bad, and the argument about whether to"
                 " use them is not really about statistics. The cost is fixed; the"
                 " benefit is whatever shift you are actually afraid of. Level 9 asks"
                 " the same question of a chart with memory, and gets a better answer.",
                 note("spoken · 3:44", text="“The cost is fixed. The benefit is the "
                      "shift you fear.”", speak=True, serif=True)),
            "      " + K["fig"]("l07_2_the_trade.png"),
        ]),
    ]


def chapter_05(K):
    n = SUBGROUP_N
    # Share of samples whose s falls below SHORT_AT of the true σ: (n−1)s²/σ² is
    # chi-square with n−1 df, whose CDF at 4 df is 1 − e^(−x/2)(1 + x/2).
    assert n - 1 == 4
    SHORT_AT = 0.7
    x = (n - 1) * SHORT_AT ** 2
    SHORT_S = 1 - math.exp(-x / 2) * (1 + x / 2)
    import numpy as _np
    _r = _np.random.default_rng(2).normal(size=(400_000, n))
    _s = _r.std(axis=1, ddof=1)
    _miss = _np.abs(_r.mean(axis=1)) > Z95 * _s / math.sqrt(n)
    _low = _s < SHORT_AT
    assert abs(_low.mean() - SHORT_S) < 0.005  # simulation agrees with the formula
    MISS_LOW, MISS_REST = _miss[_low].mean(), _miss[~_low].mean()
    MISS_SHARE = (_miss & _low).sum() / _miss.sum()
    return [
        ("s1", "5.1", "Every number here is an estimate", [
            para("Somewhere behind a process there is a real mean and a real spread."
                 " Nobody on a shop floor has ever seen either of them. Every number on"
                 " every chart in this curriculum is a guess made from a handful of"
                 " parts.",
                 note("what Level 4 gave", text="The sampling distribution, and the "
                      "width " + tex(r"\sigma/\sqrt{n}") + ". This level puts an error "
                      "bar on it."), lead=True),
            para("Take five parts and average them: that average is an estimate, and it"
                 " is wrong by a little. Take another five and it is wrong by a"
                 " different amount. Do it enough times and the estimates make a shape"
                 " of their own — narrower than the parts, and with a width you can"
                 " predict before measuring anything.",
                 datanote((f"{nc('σ')} of the parts", f"{TRUE_SIGMA:.2f} mm"),
                          (f"{nc('σ')}/√{n} predicted", f"{SE_EXACT[n]:.4f} mm"),
                          ("spread observed", f"{SE_OBSERVED[n]:.4f} mm"),
                          k=f"samples of {n}")),
            para("That width is the standard error, and it is the size of being wrong."
                 " Everything in this chapter is built out of it.",
                 note("spoken · 0:52", text="“Sigma over root n. Here it is the size of "
                      "being wrong.”", speak=True, serif=True)),
        ]),
        ("s2", "5.2", "What “ninety-five percent” has to earn", [
            para("An interval is the estimate plus and minus a margin, and the margin is"
                 f" {Z95:.2f} standard errors. That number comes from the bell: 95 % of it"
                 f" lies within {Z95:.2f} sigmas of the centre, which 4.5 worked out. Build"
                 " one interval from every sample and it is the <em>interval</em> that"
                 " moves; the truth stays where it is. So the way to check a confidence"
                 " level is not to argue about it — it is to count.",
                 note("not the parameter", text="The interval varies from sample to "
                      "sample. The mean it is chasing does not."), lead=True),
            para("Draw an interval per sample and mark the ones that missed. On a shop"
                 " floor you would never know which kind you were holding, and that is"
                 " precisely the point: the confidence level is a property of the"
                 " procedure, not of the interval in your hand.",
                 datanote(("intervals drawn", "40"),
                          ("nominal", f"{CONF*100:.0f} %"),
                          ("counted", f"{COVER_T[n]*100:.1f} %"),
                          k=f"samples of {n}, {nc(chr(116))} multiplier")),
            "      " + K["fig"]("l05_1_coverage.png"),
            "      " + K["fig"]("Level05.mp4"),
        ]),
        ("s3", "5.3", "Why t exists", [
            para("The standard error is σ/√<em>n</em>, and nobody knows σ, the true"
                 " spread. All you have is <em>s</em>, the spread of the same five parts,"
                 f" so <em>s</em> goes where σ should be. Keep {Z95:.2f} anyway and count"
                 " what you actually get.",
                 datanote(*[(f"{nc(chr(110))} = {k}", f"{COVER_Z[k]*100:.1f} %") for k in SIZES],
                          k=f"a “95 %” interval built with {Z95:.2f}"), lead=True),
            para(f"At {n} parts the interval that advertises ninety-five delivers"
                 f" {COVER_Z[n]*100:.1f}. The reason is luck in the spread. Five parts"
                 " often happen to sit close together: in"
                 f" {SHORT_S*100:.0f} % of samples <em>s</em> comes out below"
                 f" {SHORT_AT*100:.0f} % of the true σ. Those samples build intervals that"
                 f" are too narrow: they miss {MISS_LOW*100:.0f} % of the time against"
                 f" {MISS_REST*100:.0f} % for the rest, and supply"
                 f" {MISS_SHARE*100:.0f} % of all the misses. {Z95:.2f} was worked out for"
                 " a spread known exactly, and this one was guessed.",
                 note("the substitution", text="Not a correction bolted on. It is what "
                      "the arithmetic gives when the spread is guessed too.")),
            para("The fix is to reach further out: far enough that, lucky-narrow samples"
                 " included, 95 % of intervals still catch the mean. How far depends only"
                 " on how many parts the spread came from."),
            "      " + K["eq"],
            para("In 1908 William Gosset, a chemist at the Guinness brewery who published"
                 " as “Student”, worked that distance out. His table is the <em>t</em>"
                 f" distribution. With {n} parts the multiplier is {T_AT[n]:.3f}; with 100"
                 f" it is {T_AT[100]:.3f}, almost {Z95:.2f} again, because 100 parts pin"
                 " the spread down. The table is indexed by <em>n</em> − 1, called the"
                 " degrees of freedom: the same <em>n</em> − 1 Level 3 divided by. Five"
                 " parts leave four.",
                 datanote(*[(f"{nc(chr(110))} = {k}", f"{T_AT[k]:.3f}") for k in SIZES],
                          ("spread known", f"{Z95:.3f}"),
                          k=f"the 95 % {nc(chr(116))} multiplier"),
                 note("in a spreadsheet", text="T.INV.2T(0.05, n − 1) returns the"
                      " multiplier.")),
            para(f"So {Z95:.2f} is the multiplier when the spread is known, and"
                 f" {T_AT[n]:.3f} is the multiplier when the spread was guessed from {n}"
                 " parts. Build the interval with it and the count lands where it"
                 " belongs — at every sample size, not just the comfortable ones.",
                 datanote(*[(f"{nc(chr(110))} = {k}", f"{COVER_T[k]*100:.1f} %") for k in SIZES],
                          k=f"the same interval built with {nc(chr(116))}"),
                 note("spoken · 2:10", text="“t is not a correction. It is the honest "
                      "quantile.”", speak=True, serif=True)),
        ]),
        ("s4", "5.4", "Precision has a price", [
            para("So how many parts does it take to be sure? Hold σ known for a moment,"
                 " so the quantile stops moving and only the " + tex(r"\sqrt{n}") +
                 " is left. The width falls fast at first, and then it stops paying.",
                 datanote(*[(f"{nc(chr(110))} = {k}", f"{WIDTH_AT_Z[k]:.3f} mm") for k in SIZES],
                          k="width of the interval"), lead=True),
            para(f"Halve the width and the bill is four times the parts:"
                 f" {HALVE_FROM} becomes {HALVE_N_Z}. Not double — the error falls as"
                 f" the root, so precision is bought by the square. That is the sentence"
                 f" for anyone who asks for a tighter number without more parts.",
                 note(f"with {nc(chr(116))} it is cheaper", text=f"{HALVE_N_T} parts, not "
                      f"{HALVE_N_Z} — because the quantile is shrinking with the sample "
                      "too. The square law is the σ-known case.")),
            "  " + K["lab"],
        ]),
        ("s5", "5.5", "Including ours", [
            para("One last place to point this instrument. Every control chart ahead"
                 " multiplies a range by a constant called " + tex("d_2") + ", and this"
                 " site does not look it up — it simulates it. Anything simulated is an"
                 " estimate.",
                 datanote(("published", f"{D2_PUBLISHED:.4f}"),
                          ("60 replicates", f"{D2_MEAN:.4f}"),
                          ("its standard error", f"{D2_SE:.4f}"),
                          k=tex("d_2") + f" at {nc(chr(110))} = 5"), lead=True),
            para("Run that simulation sixty times over and the answers scatter. The"
                 " scatter is the standard error of our own constant, and it sets a"
                 " limit on honesty: earning the third decimal from simulation alone"
                 f" would take {D2_SUBGROUPS_FOR_3DP/1e6:.1f} million subgroups. The"
                 " fourth figure in the published table is not simulated at all — it"
                 " comes from the exact integral.",
                 note("why it still says 2.326", text="Theory earns that digit. "
                      "Simulation earns three, and only just.")),
            "      " + K["fig"]("l05_2_price.png"),
            para("So when Level 6 builds limits out of a range and Level 8 divides by a"
                 " spread, remember what they are made of. Estimates — with a size you"
                 " now know how to work out.",
                 note("spoken · 3:38", text="“Every constant ahead is an estimate. Now "
                      "you can price one.”", speak=True, serif=True)),
        ]),
    ]


def chapter_02(K):
    lo, mid, hi = MILESTONES
    return [
        ("s1", "2.1", "A long-run frequency", [
            para("Level 1 ended on a funnel: reacting to noise makes it worse. Telling"
                 " noise from a real change means saying something like “99.73 % inside”, and before this curriculum"
                 " is allowed to say it, it has to be honest about what such a number is a"
                 " statement <em>about</em>.",
                 note("the claim ahead", text="Level 6 prices a pair of limits at 99.73 %. "
                      "This level earns the right to say it."), lead=True),
            para("Flip a fair coin once and the proportion of heads is nought or one. No"
                 " single flip is ever half a head. Flip it again and again and the"
                 " proportion goes wherever the flips send it — and then it stops wandering,"
                 " and settles.",
                 note("not a property", text="A probability describes a repeated process, "
                      "never the next trial.")),
            para("That settling <em>is</em> the definition. A probability is a long-run"
                 " frequency: a statement about what a repeated process does, and never a"
                 " statement about the next part off the machine.",
                 note("spoken · 0:31", text="“A probability is a long-run frequency — a "
                      "statement about what a repeated process does.”",
                      speak=True, serif=True)),
        ]),
        ("s2", "2.2", "The gap grows, the rate settles", [
            para("The belief worth killing lives here. If heads are behind, are they owed?"
                 " Read one sequence of flips two ways at once and the answer is exact"
                 " rather than rhetorical.",
                 datanote((f"at {nc('n')} = {lo:,}", f"gap {GAP_AT[lo]:.0f}"),
                          (f"at {nc('n')} = {mid:,}", f"gap {GAP_AT[mid]:.0f}"),
                          (f"at {nc('n')} = {hi:,}", f"gap {GAP_AT[hi]:.0f}"),
                          k="the surplus, expected"), lead=True),
            para("Above, the surplus of heads over tails. It climbs, and it has an exact"
                 " expected size — " + tex(r"\mathbb{E}|S_n| = 2^{1-n} n \binom{n-1}"
                                          r"{\lfloor (n-1)/2 \rfloor}") + ", which for any"
                 " n worth plotting is " + tex(r"\sqrt{2n/\pi}") + ". A hundredfold in n"
                 " multiplies it by ten.",
                 note("no repayment", text="The expected surplus never returns toward "
                      "zero. There is nothing to repay it.")),
            para("Below, the proportion, from the same flips. Its error is that same"
                 " quantity divided by twice the number of flips, so the same hundredfold"
                 " <em>divides</em> it by ten. Root n in the numerator, n in the"
                 " denominator.",
                 datanote((f"at {nc('n')} = {lo:,}", f"{RATE_ERR_AT[lo]:.5f}"),
                          (f"at {nc('n')} = {mid:,}", f"{RATE_ERR_AT[mid]:.5f}"),
                          (f"at {nc('n')} = {hi:,}", f"{RATE_ERR_AT[hi]:.5f}"),
                          k="error in the rate")),
            para("There is no law of averages. Nothing is owed and nothing is repaid; the"
                 " proportion converges because the denominator outruns the gap. Both"
                 " statements are about one sequence, which is what makes them impossible"
                 " to argue with."),
            "      " + K["fig"]("l02_1_long_run.png"),
            "      " + K["fig"]("Level02.mp4"),
            "  " + K["lab"],
        ]),
        ("s3", "2.3", "The coin has no memory", [
            para("Two million flips, sorted by the run that came immediately before each"
                 " one. After a single head, after two, after six — how often is the next"
                 " flip a head?",
                 datanote(("after 1 head", f"{MEMORY[1]:.4f}"),
                          ("after 3 heads", f"{MEMORY[3]:.4f}"),
                          ("after 6 heads", f"{MEMORY[6]:.4f}"),
                          ("worst departure", f"{MEMORY_WORST:.4f}"),
                          k="next flip is a head"), lead=True),
            para("Every answer is one half. Nothing happens, and the fact that nothing"
                 " happens is the result: the sequence carries no debt. That is"
                 " independence, and it is also the assumption every control limit in"
                 " Part II quietly rests on.",
                 note("why it is here", text="Limits computed from independent subgroups "
                      "are wrong the moment the points inform each other.")),
        ]),
        ("s4", "2.4", "Expectation", [
            para("One more idea before the chart. Slide a fulcrum under six equal weights,"
                 " one per face of a fair die, until they balance. It settles between three"
                 " and four.",
                 datanote(("balance point", f"{DIE_E:.1f}"),
                          ("a face of the die", "no"), k="a fair die"), lead=True),
            para("Three point five is not a face. The die can never show it, and it is"
                 " still the value to expect. An expected value is a balance point, not a"
                 " prediction — and it need not be attainable at all.",
                 note("forward", text="Level 3 puts this same balance point on real "
                      "measurements and calls it the mean.")),
        ]),
        ("s5", "2.5", "What a percentage claims", [
            para("Now the number this level was written to protect. Nought point two seven"
                 " percent — the other side of 99.73 % — has three readings, and only one"
                 " of them is true.",
                 note("not the part", text="A part is never a probability. It is one part."),
                 lead=True),
            para("It is not the chance this part is bad. It is not the fraction of parts out"
                 " of tolerance — that is capability, and it waits until Level 8. It is the"
                 " rate at which a chart on an unchanged process trips its own limits.",
                 note("not capability", text="Parts against tolerance is Level 8. This is "
                      "the chart against itself.")),
            para("Which has a consequence worth doing the arithmetic for. Run a shift of"
                 f" {SHIFT_SUBGROUPS} subgroups with nothing wrong and the chance of having"
                 f" been alarmed at least once is already {P_IN_SHIFT*100:.1f} %. Run the"
                 f" {ARL0:.0f} that the phrase “one alarm in {ARL0:.0f}” actually names, and"
                 f" it is {P_IN_ARL0*100:.1f} % — not certainty.",
                 datanote((f"over {SHIFT_SUBGROUPS} subgroups", f"{P_IN_SHIFT*100:.1f} %"),
                          (f"over {ARL0:.0f} subgroups", f"{P_IN_ARL0*100:.1f} %"),
                          ("the limit", "1 − 1/e"),
                          k="at least one false alarm")),
            "      " + K["eq"],
            para("And because the waiting time is geometric, the typical wait is shorter"
                 f" than the average one: half of all first false alarms arrive by subgroup"
                 f" {MEDIAN_WAIT:.0f}, not {ARL0:.0f}. An average is not a deadline.",
                 datanote(("mean wait", f"{ARL0:.1f}"),
                          ("median wait", f"{MEDIAN_WAIT:.0f}"),
                          k="subgroups to the first alarm")),
            para("A percentage on a control chart is a claim about a repeated process, never"
                 " about a part. Level 6 can price the limits now.",
                 note("spoken · 3:52", text="“A rate is a claim about the process, not "
                      "about a part.”", speak=True, serif=True)),
            "      " + K["fig"]("l02_2_what_a_rate_claims.png"),
        ]),
    ]


def chapter_01(K):
    run_ratio = PAIR_RUN_DRIFTING / PAIR_RUN_STABLE
    return [
        ("s1", "1.1", "Nothing repeats", [
            para("Take twelve parts off one machine — same tool, same operator, same gauge,"
                 " one after another. Every reading is different, and nothing is broken.",
                 datanote(("span of twelve", f"{TWELVE_SPAN_UM:.0f} µm"),
                          ("closest pair", f"{TWELVE_CLOSEST_UM:.0f} µm"),
                          ("gauge resolution", f"{TWELVE_CLOSEST_UM:.0f} µm"),
                          k="one machine, one shift"),
                 lead=True),
            para("The closest two parts differ by a single micron, which is exactly where"
                 " this gauge stops: below that it has nothing to say. Spread is not a"
                 " defect, it is what every real process does, and the job of the next"
                 " eleven chapters is to describe it well enough to act on.",
                 note("spoken · 0:31", text="“Spread is not a defect. It is what every real"
                      " process does, and the job is to describe it.”", speak=True, serif=True)),
            "      " + K["fig"]("Level01.mp4"),
        ]),
        ("s2", "1.2", "A histogram is an instrument", [
            para("Pile 240 measurements into bins and a shape appears. The shape looks like"
                 " a fact about the process, and it is not: bin width is a setting on the"
                 " instrument, and the setting changes the answer.",
                 datanote(("at 4 bins", "one lump"), ("at 52 bins", "a comb"),
                          k="same data, two settings")),
            para("Four bins says the process is a single lump. Fifty-two says it is a row of"
                 " spikes. Neither is the process. Somewhere in between is a picture you can"
                 " read, and knowing that the knob exists is the difference between reading a"
                 " histogram and believing one."),
        ]),
        ("s3", "1.3", "The histogram throws away the order", [
            para(f"Here is the claim this chapter is built on. Take {PAIR_N} measurements and"
                 " write them down twice: once in the order they were made, and once sorted,"
                 " which is what a slow drift looks like written down as it happened.",
                 datanote(("mean", "identical"), ("spread", "identical"),
                          ("histogram", "identical, bin for bin"), k="what does not change"),
                 lead=True),
            para("These are not two similar samples. They are the same numbers, so the mean"
                 " is identical, the spread is identical, and the histogram is identical bin"
                 " for bin — not approximately, exactly. The only thing that differs is the"
                 " order, and one of those two processes needs an engineer today.",
                 datanote(("longest run, stable", f"{PAIR_RUN_STABLE}"),
                          ("longest run, drifting", f"{PAIR_RUN_DRIFTING}"),
                          ("ratio", f"{run_ratio:.0f}×"), k="what does change")),
            para("A run statistic sees what the histogram cannot. That is the whole reason"
                 " every chart in this curriculum is drawn in time order rather than as a"
                 " pile of measurements — and why Level 7 prices the run rules that formalise"
                 " it.",
                 note("spoken · 1:58", text="“Same histogram, and one of those two processes"
                      " needs an engineer today.”", speak=True, serif=True)),
            "      " + K["fig"]("l01_1_time_order.png"),
        ]),
        ("s4", "1.4", "Two kinds of variation", [
            para("Shewhart's distinction, and the one the rest of the subject rests on. Some"
                 " variation is the process being itself — many small causes, none of them"
                 " findable, none of them worth chasing. Some variation is something"
                 " identifiable that happened: a tool changed, a batch differed, an operator"
                 " was new.",
                 datanote(("common cause", "the process being itself"),
                          ("special cause", "something identifiable happened"),
                          k="the distinction")),
            para("The first kind is called common cause and the second special cause. They"
                 " demand opposite responses, which is why telling them apart is worth"
                 " eleven chapters: you improve a common-cause process by changing the"
                 " process, and a special-cause process by finding the thing that happened."),
            "      " + K["sys"],
        ]),
        ("s5", "1.5", "Reacting to noise makes it worse", [
            para("Suppose you cannot tell them apart, and you treat every wobble as a signal:"
                 " after each part, you correct the machine by exactly what that part was out"
                 " by. It is the most reasonable-looking policy on a shop floor, and it is"
                 " Deming's funnel.",
                 datanote(("variance", f"×{TAMPER_VAR_RATIO_EXACT:.0f} exactly"),
                          ("spread", f"×{TAMPER_SIGMA_RATIO_EXACT:.3f}"),
                          k="the cost of answering noise"), lead=True),
            para("Each correction subtracts the previous part's noise from this part's, so"
                 " every outcome after the first is a difference of two independent draws."
                 " Two numbers measure that scatter, and Level 3 builds both from real"
                 " parts: the variance is the average squared distance of each part from"
                 " the average, and its square root, σ (sigma), is the spread in the parts'"
                 " own units. Here the variance doubles exactly and stays doubled, so the"
                 " spread the customer receives is √2 times wider, bought with a full shift of"
                 " conscientious work."),
            "      " + K["eq"],
            para("Noise is not a signal, and answering it is how you add variation rather"
                 " than remove it. Everything from here — the limits, the capability"
                 " arithmetic, the detection theory — is machinery for knowing which kind you"
                 " are looking at before you touch anything.",
                 note("spoken · 2:41", text="“Answering it is how you add variation rather"
                      " than remove it.”", speak=True, serif=True)),
            "      " + K["fig"]("l01_2_tampering.png"),
            "  " + K["lab"],
            "          " + '<p class="lab-link">You can run it yourself: <a href="https://portfolio.amohdnaw.xyz/lab.html#ch3" target="_blank" rel="noopener">CH 3 of the control lab</a> drops the marbles in 3D, lets you try correcting by hand against the same draws, and runs Deming\'s other two rules, which are worse.</p>',
        ]),
    ]


def chapter_03(K):
    return [
        ("s1", "3.1", "Twelve parts, twelve numbers", [
            para("Take twelve parts off one machine — same tool, same operator, same gauge, one"
                 " after another. Every reading is different, and nothing is broken. The twelve of"
                 " them cover forty-seven microns, and two differ by a single micron, which is"
                 " exactly where this gauge stops. Below that it has nothing to say.",
                 datanote(("span of twelve", "47 µm"), ("gauge resolution", "1 µm"),
                          k="what one machine did"), lead=True),
            para("Spread is not a defect. It is what every real process does, and the job of this"
                 " chapter is to describe it with three numbers instead of twelve.",
                 note("spoken · 0:21", text="“Spread is not a defect. It is what every real"
                      " process does, and the job is to describe it.”", speak=True, serif=True)),
        ]),
        ("s2", "3.2", "The mean is a balance point", [
            para("Twelve numbers are not an answer; you need one number for the centre. So guess"
                 " one and check it. Draw every part's distance to the guess, then add the"
                 " distances on each side and see whether they cancel.",
                 note("the test", text="A candidate centre is right when the deviations either"
                      " side of it cancel exactly.")),
            para("They do not, and the beam tips. So walk the guess along until they do. One"
                 " position makes the two sides equal and opposite and the beam comes level."
                 " That position is the mean — not a formula you were handed, but the one place"
                 " where the deviations cancel.",
                 note("spoken · 0:58", text="“Not a formula you were handed — the one place where"
                      " the deviations cancel.”", speak=True, serif=True)),
        ]),
        ("s3", "3.3", "Spread has to be squared first", [
            para("Now the spread. Averaging those deviations is useless: we have just proved they"
                 " cancel, by construction. Square each one instead. Negatives turn positive, the"
                 " cancelling stops, and every square is an area you can put on a shelf.",
                 datanote(("sigma, twelve parts", "12.7 µm"), k="the spread")),
            "      " + K["eq"],
            para("Twelve squares averaged, then rooted, which puts the answer back into"
                 " millimetres. That is " + tex(r"\sigma") + ", and it is the side of the average"
                 " square. For these twelve parts, 12.7 microns."),
        ]),
        ("s4", "3.4", "A shape nobody chose", [
            para("Twelve parts say nothing about shape. Keep measuring, and keep the same bins: a"
                 " hundred parts, a thousand, twenty thousand off the same machine with the same"
                 " gauge. A shape appears that nobody chose or asked for.",
                 datanote(("parts measured", "20 000"), ("bins", "unchanged"),
                          k="keep going")),
            para("Many small independent effects, added together, land on this curve. The bell is"
                 " a consequence of the process, not an assumption about it."),
            "      " + K["fig"]("Level03.mp4"),
        ]),
        ("s5", "3.5", "You never measure everything", [
            para("The true centre and spread belong to the process itself. Your twelve parts only"
                 " estimate them, and the estimate is not the thing: four more handfuls of twelve,"
                 " off the same untouched machine, land somewhere else every time.",
                 note("sample, not process", text="Twelve parts estimate the centre and spread."
                      " They are not the centre and spread.")),
            para("It is also why a sample's spread divides by n − 1. Twelve parts spread around"
                 " their own mean sit a little tighter than they do around the truth, so the"
                 " smaller divisor corrects for it. Every estimate carries uncertainty, and Level"
                 " 4 puts a number on exactly how much.",
                 datanote(("divisor", "n − 1"), k=f"why not {nc(chr(110))}")),
            "  " + K["lab"],
            "      " + K["sys"],
        ]),
    ]


def chapter_04(K):
    return [
        ("s1", "4.1", "One part tells you nothing", [
            para("One part tells you almost nothing; many parts obey a law. Start with the"
                 " simplest part there is — one die, six faces, all equally likely. Ten rolls tell"
                 " you nothing: the worst face is out by two hundred percent.",
                 datanote(("10 rolls", "200 % off"), ("10 000 rolls", "a few % off"),
                          k="predictable in bulk"), lead=True),
            para("Keep rolling and watch that distance close. At ten thousand rolls the worst face"
                 " is within a few percent of one sixth. Nobody arranged that; it is what"
                 " randomness does in bulk.",
                 note("spoken · 0:28", text="“Nobody arranged that. It is what randomness does in"
                      " bulk.”", speak=True, serif=True)),
            "      " + K["fig"]("Level04.mp4"),
        ]),
        ("s2", "4.2", "Averaging makes a shape", [
            para("One die is the baseline: every face equally likely, no shape at all. Average two"
                 " of them and the flat top is already gone. Average five, and there is a shape"
                 " where there was none. Thirty, and it is a bell.",
                 note("the point", text="Nothing about a die is bell shaped. The averaging did"
                      " this.")),
            para("That matters because nothing about a die is bell shaped. The shape did not come"
                 " from the parts; it came from averaging them."),
            "      " + K["fig"]("l04_1_dice_to_bell.png"),
            "  " + K["lab"],
        ]),
        ("s3", "4.3", "The law", [
            para("Two numbers, measured separately, agree to three decimals: the spread of the"
                 " averages, and one die's spread divided by the root of the count. That agreement"
                 " is the law, and it is the reason a control chart can exist at all.",
                 datanote(("agreement", "3 decimals"), k="measured, not assumed")),
            "      " + K["eq"],
        ]),
        ("s4", "4.4", "What averaging buys", [
            para("Put subgroup size along the bottom and the spread of the mean up the side,"
                 f" for a machined part with σ = {SQRTN_SIGMA:.3f} mm, then walk the subgroup"
                 " size from one to twenty-five. At twenty-five parts the spread of the mean is"
                 f" {SQRTN_SIGMA/5:.3f} mm, a fifth of one part's spread — the root is doing all"
                 " the work.",
                 datanote(("2nd part buys", "0.29 σ"), ("25th part buys", "0.004 σ"),
                          k="the shape of the deal")),
            para("But look at the shape of what you are buying. The second part cuts your"
                 " uncertainty by 29 % (it halves the variance); the twenty-fifth buys four thousandths of a sigma. Averaging is"
                 " cheap at the start and almost free of value at the end, which is why subgroups"
                 " of four and five are everywhere and subgroups of fifty are not."),
            para("It is also why a control chart plots subgroup means rather than parts: a shift"
                 " that hides inside single measurements moves a mean far enough to see.",
                 note("spoken · 2:04", text="“A shift that hides inside single parts moves a mean"
                      " far enough to see.”", speak=True, serif=True)),
            "      " + K["sys"],
            "      " + K["fig"]("l04_2_sqrt_n.png"),
        ]),
        ("s5", "4.5", "Reading the bell", [
            para("A bell is only useful if you can read areas off it. Measure the distance"
                 " from the centre in sigmas and the share of the bell inside any distance"
                 f" is fixed, the same for every bell: {INSIDE_K[1]*100:.0f} % within one"
                 f" sigma, {INSIDE_K[2]*100:.0f} % within two, {INSIDE_K[3]*100:.2f} % within"
                 " three.",
                 datanote(("±1 " + nc("σ"), f"{INSIDE_K[1]*100:.2f} %"),
                          (f"±{Z95:.2f} " + nc("σ"), "95.00 %"),
                          ("±2 " + nc("σ"), f"{INSIDE_K[2]*100:.2f} %"),
                          ("±3 " + nc("σ"), f"{INSIDE_K[3]*100:.2f} %"),
                          k="share inside"), lead=True),
            para("Every one of those shares comes from a single function, written "
                 + tex(r"\Phi(z)") + ": the share of the bell below " + nc("z") + " sigmas."
                 " It has no tidy formula. Calculators and spreadsheets compute it from"
                 " the error function, erf. Two sigmas hold"
                 f" {INSIDE_K[2]*100:.2f} %, so the round 95 % sits a little closer in, at"
                 f" {Z95:.2f} sigmas. That is the {Z95:.2f} Level 5 builds its intervals with.",
                 note("Φ", text=tex(r"\Phi(z)=\tfrac12\bigl(1+\operatorname{erf}(z/\sqrt2)\bigr)")
                      + ". In a spreadsheet, NORM.S.DIST(z, TRUE).")),
            para("Often only one side matters: a part too thick, a mean that has drifted"
                 " up. Then read one tail, which holds half of what lies outside. Beyond one"
                 f" sigma on one side lies {TAIL_K[1]*100:.1f} % of the bell, beyond two"
                 f" {TAIL_K[2]*100:.1f} %, beyond three {TAIL_K[3]*100:.3f} %, or"
                 f" {TAIL3_PPM} parts per million.",
                 datanote(("beyond +1 " + nc("σ"), f"{TAIL_K[1]*100:.1f} %"),
                          ("beyond +2 " + nc("σ"), f"{TAIL_K[2]*100:.1f} %"),
                          ("beyond +3 " + nc("σ"), f"{TAIL3_PPM} ppm"),
                          k="one tail")),
            para("Count every distance in sigmas, never in millimetres. That is why Level 6"
                 " sets its limits at three sigmas and Level 8 turns a gap to the spec limit"
                 " into sigmas before it reads anything off the bell. And the far"
                 f" tails are small but never empty: the {(1-INSIDE_K[3])*100:.2f} % outside"
                 f" three sigmas is the false alarm Level 6 prices at one subgroup in"
                 f" {1/(1-INSIDE_K[3]):.0f}.",
                 note("which bell", text="These areas belong to the normal curve. Averages"
                      " of a few parts come close to it, as 4.2 showed. Single parts often"
                      " do too, but nothing guarantees it.")),
        ]),
    ]


def chapter_08(K):
    return [
        ("s1", "8.1", "Two distributions on one axis", [
            para("Capability compares two distributions. One belongs to the customer and one"
                 " belongs to the process, and the whole trick is that they are drawn on the same"
                 " axis, in millimetres. The customer speaks in limits: anything between these two"
                 " lines is accepted, and nothing outside them is.",
                 note("the customer's voice", text="Two lines on a drawing. They know nothing"
                      " about your machine."), lead=True),
            para("The process answers with a spread. It never read the drawing, and at this width"
                 " it does not fit."),
            "      " + K["fig"]("l08_1_two_voices.png"),
        ]),
        ("s2", "8.2", "Cp is pure geometry", [
            para("Improve the process and watch the only number that matters here: the tolerance"
                 " divided by six sigma. That ratio is Cp, and it is pure geometry — no"
                 " probability in it at all.",
                 datanote(("Cp", "TOL / 6σ"), ("at Cp 1.33", "spread = 75 % of TOL"),
                          k="geometry only")),
            "      " + K["eq"],
            para("At 1.33 the natural spread is three quarters of the tolerance, and there is room"
                 " on both sides. Drag the slider and the ratio moves with the spread."),
            "  " + K["lab"],
            "      " + K["fig"]("Level08.mp4"),
        ]),
        ("s3", "8.3", "The near side is the one you fail", [
            para("Now let the mean drift and change nothing else. The spread stays exactly where"
                 " it was, but the number collapses, because Cpk keeps the smaller of the two"
                 " one-sided ratios: the near limit is the one you fail first.",
                 datanote(("Cpk", f"{CPK_DRIFT:.2f}"), ("leak", f"{PPM_DRIFT_S} ppm"), ("in plain counting", f"1 in {ONE_IN_DRIFT}"),
                          k="what the drift costs")),
            para(f"That leak is {PPM_DRIFT_S} parts per million, and at this scale you cannot see it. So"
                 " stretch the vertical axis until it is visible: the peak leaves the frame, and"
                 " the tail is what we came for. The index itself is only the near gap, measured"
                 " in three sigmas.",
                 note("spoken · 1:36", text=f"“{PPM_DRIFT_S} parts per million is the same sentence as 1 in"
                      f" {ONE_IN_DRIFT} parts.”", speak=True, serif=True)),
        ]),
        ("s4", "8.4", "Every Cpk is a promise about defect rate", [
            para("Parts per million up the side, on a logarithmic scale, because it spans five"
                 " decades. Walk Cpk upward from 0.6 and read the promise off the curve. Every"
                 " figure here is computed at render time by the same function the test suite"
                 " checks — nothing is read off a table.",
                 datanote(("Cpk 1.00", f"{CPK_PPM[1.00]:,.0f} ppm".replace(",", "\u00a0")), ("Cpk 1.33", f"{CPK_PPM[1.33]:.2f} ppm"),
                          ("Cpk 1.67", f"{CPK_PPM[1.67]:.2f} ppm"), k="the promise")),
            para("Which is why the difference between 1.33 and 1.67 is not a rounding argument. It"
                 " is two orders of magnitude of scrap. A capability index is a defect rate"
                 " wearing a friendlier number. The σ inside it is the spread of single"
                 " parts, never of subgroup means: the customer receives parts, not averages,"
                 " and the narrower σ/√<em>n</em> would promise a defect rate nobody ships."),
            K["watch"]("SPCGallery.mp4", "gallery", "figure 8.4",
                       "The overview act: a chart and its limits drawing themselves from the data,"
                       " and where capability geometry sits among them."),
            "      " + K["sys"],
            "      " + K["fig"]("l08_2_cpk_to_ppm.png"),
        ]),
    ]


def chapter_09(K):
    return [
        ("s1", "9.1", "The most expensive failure mode", [
            para("Slow drift is the most expensive failure mode in manufacturing, because every"
                 " single measurement of it looks acceptable. Here is a Shewhart chart with limits"
                 f" at ±3σ, which buys one false alarm in {DT.SHEWHART_ARL0:.0f} subgroups.",
                 datanote(("false alarm budget", f"1 in {DT.SHEWHART_ARL0:.0f}"), ("drift rate", f"{DT.DRIFT} σ / subgroup"),
                          k="the setup"), lead=True),
            para(f"The first {DT.SHIFT_AT} subgroups are noise around the target. Then the mean starts"
                 f" walking at {DT.DRIFT} sigma per subgroup — slow enough that no single measurement"
                 " looks wrong, and the chart carries on saying nothing."),
            "      " + K["fig"]("Level09.mp4"),
        ]),
        ("s2", "9.2", "A chart with no memory", [
            para(f"The first violation lands at subgroup {D9_SHEW}. That is {D9_SHEW - DT.SHIFT_AT} subgroups after the drift"
                 f" began, by which time the mean has moved {DT.OFF_SHEW:.1f} sigma and every part in between was"
                 " made by a process nobody knew had changed.",
                 datanote(("drift starts", f"after subgroup {DT.SHIFT_AT}"), ("first alarm", f"subgroup {D9_SHEW}"),
                          ("mean moved by then", f"{DT.OFF_SHEW:.1f} σ"), k="what it cost")),
            para("Each point was judged on its own and then forgotten. That is the whole weakness,"
                 " and it is not a tuning problem: the chart has no memory.",
                 note("spoken · 1:12", text="“Each point was judged on its own and then forgotten."
                      " That is the whole weakness.”", speak=True, serif=True)),
        ]),
        ("s3", "9.3", "A statistic that remembers", [
            para("Same process, same data, same false-alarm budget — and a statistic that"
                 " remembers. Each new subgroup gets a fifth of the weight and the running"
                 " statistic keeps the rest: with lambda at 0.2 that is one part new and four"
                 " parts memory. Written out, with " + tex(r"x_i") + " the newest subgroup"
                 " mean and " + tex(r"z_i") + " the running statistic, " + tex(r"z_i = \lambda x_i + (1-\lambda)\,z_{i-1}") + ","
                 " started at the target.",
                 datanote(("lambda", f"{DT.LAM:.2f}"), ("weighting", "1 new : 4 memory"),
                          k="how much it keeps")),
            para("Its limits are not ±3. They are calibrated by simulation until this chart cries"
                 f" wolf exactly as rarely as the last one — one alarm in {DT.ARL0_EWMA:.0f} quiet subgroups"
                 f" against {DT.SHEWHART_ARL0:.0f}, so the comparison that follows is fair."),
            "      " + K["eq"],
            "      " + K["fig"]("EWMAMemory.mp4"),
        ]),
        ("s4", "9.4", "The same eighty subgroups again", [
            para("While the process is quiet the statistic wanders near zero, because new noise"
                 " keeps cancelling old noise. Once the drift starts the noise still cancels but"
                 " the drift does not: it is the same direction every time, so it adds up.",
                 datanote(("crosses at", f"subgroup {D9_EWMA}"), ("mean off by", f"{DT.OFF_EWMA:.1f} σ"),
                          ("raw point there", f"{DT.RAW[DT.DET_EWMA]:+.2f} σ"), k="caught early")),
            para(f"It crosses the limit at subgroup {D9_EWMA}, with the mean only {DT.OFF_EWMA:.1f} sigma off and the raw"
                 f" measurement sitting at {DT.RAW[DT.DET_EWMA]:+.2f} sigma — a number no Shewhart chart would look at"
                 f" twice. The other chart waited until subgroup {D9_SHEW}, {D9_SHEW - D9_EWMA} subgroups later."),
            "      " + K["fig"]("l09_2_race.png"),
            "  " + K["lab"],
        ]),
        ("s5", "9.5", "One drift is an anecdote", [
            para("That is one drift. The standard yardstick swaps the slow walk for a sudden"
                 " step: the mean jumps by one sigma and stays there. Run thousands of those and"
                 f" the average wait comes out at {DT.ARL1_SHEW:.0f} subgroups for the Shewhart rule and {DT.ARL1_EWMA:.0f} for"
                 f" this one. Divide them: {DT.SPEEDUP:.1f} times sooner, bought with no extra false alarms at"
                 f" all. The {DT.ARL1_SHEW:.0f} matching the drift above is a coincidence; that run gave {D9_SHEW - DT.SHIFT_AT}"
                 f" against {D9_EWMA - DT.SHIFT_AT}.",
                 datanote(("Shewhart ARL", f"{DT.ARL1_SHEW:.0f}"), ("EWMA ARL", f"{DT.ARL1_EWMA:.0f}"), ("speed-up", f"{DT.SPEEDUP:.1f}×"),
                          k="thousands of 1" + nc("σ") + " steps")),
            para("That trade — sensitivity bought without paying in false alarms — is the whole of"
                 " detection theory.",
                 note("spoken · 3:41", text=f"“{DT.SPEEDUP:.1f} times sooner, bought with no extra false alarms"
                      " at all.”", speak=True, serif=True)),
            "      " + K["sys"],
            "      " + K["fig"]("l09_1_arl.png"),
        ]),
    ]


# ---------------------------------------------------------------- hooks
# specs/plain-entry-contract.md. Each hook is a question a newcomer can answer
# before meeting a single term. Its numbers are computed here and handed to a
# few lines of JS that only draw them, so the page cannot disagree with the build.
def hook_row(panel, notes):
    """The try-it panel plus its margin notes: how to read it, an everyday
    version, and the real name with a link to where the level covers it.
    The first note shows before the pick, so it must not give the answer away."""
    # notes after the first are spoilers, so they appear with the result
    side = "".join(f'<div class="hk-note"{" hidden" if i else ""}><span class="k">{k}</span>{v}</div>'
                   for i, (k, v) in enumerate(notes))
    return f'          <div class="hook-row">\n{panel}\n            <aside class="hk-side">{side}</aside>\n          </div>'


def hook_01():
    import numpy as _np
    sig, first = 0.2, 0.3
    # the first fixed-seed run whose 20 parts show what the long run promises:
    # left alone near sigma, adjusted near the exact sqrt(2) ratio
    for seed in range(1000):
        e = _np.random.default_rng(seed).normal(0, sig, 21)
        e[0] = first
        left, adj = e[1:], e[1:] - e[:-1]
        rl, ra = _np.sqrt((left ** 2).mean()), _np.sqrt((adj ** 2).mean())
        if abs(ra / rl - TAMPER_SIGMA_RATIO_EXACT) < 0.02 and abs(rl - sig) < 0.02:
            break
    else:
        raise SystemExit("hook_01: no representative run in 1000 seeds")
    worse = (ra / rl - 1) * 100
    data = {"left": [round(float(v), 4) for v in left],
            "adj": [round(float(v), 4) for v in adj]}
    import json as _json
    panel = f'''          <div class="hook" id="hook">
            <div class="hk-bar"><span class="micro">Try it first · 20 parts</span><span class="micro" id="hk-status"></span></div>
            <div class="hk-body">
              <p class="hk-q">Your machine makes a part, and it comes out {first:.1f}&nbsp;mm too big. Do you adjust the machine by {first:.1f}&nbsp;mm to make up for it?</p>
              <button type="button" data-pick="adj" aria-pressed="false">Adjust it</button><button type="button" data-pick="left" aria-pressed="false">Leave it alone</button>
              <svg class="hk-dots" viewBox="0 0 420 110" role="img" aria-label="The next 20 parts, how far each one lands from the target size"><line x1="0" x2="420" y1="55" y2="55" stroke="var(--rule-strong)" stroke-dasharray="4 4"/><text x="0" y="50" fill="var(--ink-dim)" font-family="IBM Plex Mono,monospace" font-size="10">target</text></svg>
            </div>
            <div class="hk-tiles" hidden>
              <div><span class="micro">Left alone · typical miss, mm</span><b class="ok">±{rl:.2f}</b></div>
              <div><span class="micro">Adjusted every part · typical miss, mm</span><b class="alarm">±{ra:.2f}</b></div>
            </div>
            <p class="hk-after" hidden></p>
            <script type="application/json" id="hk-data">{_json.dumps(data)}</script>
          </div>
          <script>
          (() => {{
            const box = document.getElementById("hook"), svg = box.querySelector("svg");
            const D = JSON.parse(document.getElementById("hk-data").textContent);
            const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
            const NS = "http://www.w3.org/2000/svg", X = i => 14 + i * 20.5, Y = v => 55 - v * 60;
            const said = {{
              adj: "Say you keep doing that after every part. You adjusted 20 times, and your parts came out {worse:.0f} % more scattered than if you had left the machine alone. This level shows why.",
              left: "Good instinct. Adjusting after every part would have left your parts {worse:.0f} % more scattered than leaving the machine alone. Most people adjust. This level shows why."
            }};
            function draw(key, cls, delay) {{
              D[key].forEach((v, i) => {{
                const c = document.createElementNS(NS, "circle");
                c.setAttribute("cx", X(i)); c.setAttribute("cy", Y(Math.max(-.85, Math.min(.85, v))));
                c.setAttribute("r", 4); c.setAttribute("fill", cls === "ok" ? "var(--signal-ok)" : "var(--signal-alarm)");
                c.style.opacity = still ? 1 : 0; svg.appendChild(c);
                if (!still) setTimeout(() => {{ c.style.transition = "opacity .2s"; c.style.opacity = 1; }}, delay + i * 70);
              }});
            }}
            box.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {{
              if (box.dataset.done) return;
              box.dataset.done = 1;
              const pick = b.dataset.pick;
              box.querySelectorAll("button").forEach(x => {{ x.disabled = true; x.setAttribute("aria-pressed", x === b); }});
              draw(pick, pick === "adj" ? "alarm" : "ok", 0);
              draw(pick === "adj" ? "left" : "adj", pick === "adj" ? "ok" : "alarm", 20 * 70 + 300);
              const st = document.getElementById("hk-status");
              st.textContent = pick === "adj" ? "adjusted 20×" : "left alone";
              st.className = "micro " + (pick === "adj" ? "alarm" : "ok");
              setTimeout(() => {{
                box.querySelector(".hk-tiles").hidden = false; box.parentElement.querySelectorAll(".hk-note[hidden]").forEach(n => n.hidden = false);
                const a = box.querySelector(".hk-after"); a.textContent = said[pick]; a.hidden = false;
              }}, still ? 0 : 2 * 20 * 70 + 400);
            }}));
          }})();
          </script>'''
    return hook_row(panel, [
        ("How to read it", 'Each dot is one part. Above the dashed line it came out too big, below it too small.'
         '<span class="hk-key"><i class="ok">●</i> machine left alone</span>'
         '<span class="hk-key"><i class="alarm">●</i> adjusted after every part</span>'),
        ("You have done this", "The shower runs a little cold, so you turn it hot. Now it is too hot, so you"
         " turn it back. The water was fine all along: the pipes wobble, and every turn adds a swing of"
         " your own."),
        ("The name for it", 'Engineers call this tampering. <a href="#s5">Section 1.5</a> runs it on many'
         " more parts and measures the damage."),
    ])


def quiz_hook(bar, q, picks, tiles, said, end, notes, hid="hook"):
    """A question panel: pick an answer, then computed tiles and a reply tailored
    to the pick. picks = [(key, label)], tiles = [(label, value, cls)],
    said = {key: reply}; end is appended to every reply."""
    import json as _json
    btns = "".join(f'<button type="button" data-pick="{k}" aria-pressed="false">{lab}</button>' for k, lab in picks)
    tl = "".join(f'<div><span class="micro">{lab}</span><b class="{c}">{v}</b></div>' for lab, v, c in tiles)
    panel = f"""          <div class="hook" id="{hid}">
            <div class="hk-bar"><span class="micro">{bar}</span></div>
            <div class="hk-body">
              <p class="hk-q">{q}</p>
              {btns}
            </div>
            <div class="hk-tiles" hidden>{tl}</div>
            <p class="hk-after" hidden></p>
          </div>
          <script>
          (() => {{
            const box = document.getElementById("{hid}");
            const said = {_json.dumps(said, ensure_ascii=False)}, end = {_json.dumps(end, ensure_ascii=False)};
            box.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {{
              box.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
              box.querySelector(".hk-tiles").hidden = false; box.parentElement.querySelectorAll(".hk-note[hidden]").forEach(n => n.hidden = false);
              const a = box.querySelector(".hk-after"); a.textContent = said[b.dataset.pick] + end; a.hidden = false;
            }}));
          }})();
          </script>"""
    if notes is None:  # mid-level hook: the section's own margin notes stay
        return f'          <div class="hook-row">\n{panel}\n          </div>'
    return hook_row(panel, notes)


def hook_02():
    from math import comb
    flips, heads = 10, 8
    p = sum(comb(flips, k) for k in range(heads, flips + 1)) / 2 ** flips
    one_in = round(1 / p)
    return quiz_hook(
        "Quick question",
        f"You flip a coin {flips} times and get {heads} heads. Is the coin unfair?",
        [("yes", "Yes"), ("no", "No"), ("cant", "Can't tell yet")],
        [(f"A fair coin, {heads}+ heads in {flips}", f"{p*100:.1f} %", ""),
         ("That is about", f"1 in {one_in}", "")],
        {"yes": f"Most people say yes. But a perfectly fair coin does this about 1 time in {one_in}.",
         "no": f"Fair enough, but you can't be sure of that either: a slightly unfair coin would give {heads} heads more often.",
         "cant": f"That is the honest answer. A perfectly fair coin does this about 1 time in {one_in}."},
        " Telling luck from a real change, and saying how sure you are, is what this course is about."
        " This level starts with what a percentage like that actually means.",
        [("Before you pick", "In the long run a fair coin lands heads half the time. Decide whether"
          f" {flips} flips is a long run."),
         ("You have done this", "A friend turns up late three times this month, and you decide they are"
          " always late. Three is a short run too. It might be them, or it might be the traffic."),
         ("The name for it", f"The {p*100:.1f}&nbsp;% is how often a perfectly fair coin gives {heads} or"
          f" more heads in {flips} flips. Statisticians call a number like that a p-value."
          ' <a href="level-07.html">Level 7</a> puts it to work; this level builds what it stands on.')])


def _out_of_spec(sd, tol):
    from scipy.stats import norm
    return 2 * norm.sf(tol / sd)


def hook_03():
    tol, sa, sb = 0.10, 0.02, 0.05
    pa, pb = _out_of_spec(sa, tol), _out_of_spec(sb, tol)
    return quiz_hook(
        "Quick question",
        f"Two machines both make parts that average exactly 50.00&nbsp;mm. The customer accepts"
        f" {50-tol:.2f} to {50+tol:.2f}&nbsp;mm. Are the two machines equally good?",
        [("yes", "Yes"), ("no", "No"), ("cant", "Can't tell yet")],
        [(f"Machine A, typical miss ±{sa:.2f} mm · rejects per million", f"{pa*1e6:.1f}", "ok"),
         (f"Machine B, typical miss ±{sb:.2f} mm · rejects per million", f"{pb*1e6:,.0f}".replace(",", " "), "alarm")],
        {"yes": "Same average, very different machines.",
         "no": "Right, though the average alone could not tell you that.",
         "cant": "That is the honest answer: the average leaves out how far the parts scatter."},
        (f" Give machine A a typical miss of ±{sa:.2f}\u00a0mm and machine B ±{sb:.2f}\u00a0mm, and B's"
         " parts fail about " + f"{float(f'{pb/pa:.2g}'):,.0f}".replace(",", " ") + " times as often. This level builds"
         " the three numbers that describe a pile of parts: where it sits, how wide it is, and its shape."),
        [("Before you pick", "An average tells you where the parts land as a group. Think about what"
          " it leaves out."),
         ("You have done this", "Two buses both arrive on time on average. One is always within a"
          " minute; the other swings ten minutes either way. You know which one you would rather catch."),
         ("The name for it", 'The width of the scatter is the standard deviation. <a href="#s3">Section'
          " 3.3</a> shows why it is worked out with squares.")])


def hook_04():
    from math import comb
    from itertools import product
    one = 2 / 6
    sums = [sum(r) for r in product(range(1, 7), repeat=5)]
    five = sum(15 <= t <= 20 for t in sums) / len(sums)
    return quiz_hook(
        "Quick question",
        "Which is more likely to land between 3 and 4: one roll of a die, or the average of five rolls?",
        [("one", "One roll"), ("five", "Average of five"), ("same", "About the same")],
        [("One roll lands on 3 or 4", f"{one*100:.0f} %", ""),
         ("Average of five lands in 3 to 4", f"{five*100:.0f} %", "ok")],
        {"one": "Most people pick the single roll, or call it even.",
         "five": "Right.",
         "same": "Most people call it even."},
        f" The average of five lands there {five/one:.1f} times as often: high and low rolls cancel, so"
        " averages crowd toward the middle. That crowding is what every control chart is built on.",
        [("Before you pick", "A die shows 1 to 6, each face equally likely. The average of five rolls"
          " can be anything from 1 to 6 in steps of a fifth."),
         ("You have done this", "One online review can say anything. The average of fifty reviews"
          " rarely sits at either extreme: the odd ones cancel out."),
         ("The name for it", "Averages crowding toward the middle is the central limit theorem at work."
          ' <a href="#s3">Section 4.3</a> measures how fast the crowd tightens.')])


def hook_05():
    from scipy.stats import t as _t, norm
    n, xbar, s = 5, 50.02, 0.03
    h5 = _t.ppf(0.975, n - 1) * s / n ** 0.5
    n2 = 20
    h20 = _t.ppf(0.975, n2 - 1) * s / n2 ** 0.5
    poll = norm.ppf(0.975) * (0.25 / 1000) ** 0.5 * 100
    return quiz_hook(
        "Quick question",
        f"You measure {n} parts. Their average is {xbar:.2f}&nbsp;mm and they scatter by about"
        f" {s:.2f}&nbsp;mm. How close is {xbar:.2f} to the machine's true average?",
        [("exact", "It is the true average"), ("close", "Within a thousandth"), ("range", "Somewhere in a range")],
        [(f"True average, {n} parts · 95 % range, mm", f"±{h5:.3f}", ""),
         (f"Same scatter, {n2} parts · 95 % range, mm", f"±{h20:.3f}", "ok")],
        {"exact": f"It is only a guess from {n} parts. Another {n} would give another average.",
         "close": f"Closer than {n} parts can promise.",
         "range": "Right, and the range can be worked out."},
        f" With {n} parts the true average could sit anywhere in a band ±{h5:.3f}&nbsp;mm wide. Measure"
        f" {n2} and the band shrinks to ±{h20:.3f}. This level is about drawing that band honestly.".replace("&nbsp;", " "),
        [("Before you pick", "Five parts are a small handful. Think about what a different five would"
          " have shown."),
         ("You have done this", f"A poll of 1&nbsp;000 people says 52&nbsp;%, plus or minus {poll:.0f}"
          " points. That plus or minus is the same kind of range."),
         ("The name for it", 'That range is a confidence interval. <a href="#s2">Section 5.2</a> tests'
          " whether its 95&nbsp;% keeps its promise.")])


def hook_06():
    from scipy.stats import norm
    p = 2 * norm.sf(3)
    hrs = 1 / p
    return quiz_hook(
        "Quick question",
        "Your chart checks the process once an hour. Nothing is wrong with the process. How long, on"
        " average, until the chart raises an alarm anyway?",
        [("never", "Never"), ("day", "About a day"), ("weeks", "About two weeks")],
        [("Chance of an alarm on any one point", f"{p*100:.2f} %", ""),
         ("Average wait for a false alarm, hours", f"{hrs:.0f}", "alarm")],
        {"never": "It will, sooner or later: a steady process still lands outside now and then.",
         "day": "Longer than that.",
         "weeks": "Right."},
        f" On average the first false alarm comes after {hrs:.0f} hours, about {hrs/24:.0f} days. The"
        " limits were drawn to buy exactly those odds. This level shows where they come from.",
        [("Before you pick", "A steady process still wobbles. The chart's limits are drawn wide, so"
          " the wobble rarely reaches them."),
         ("You have done this", "A smoke alarm that never goes off by mistake would also be slow to"
          " notice a real fire. Every alarm trades one mistake against the other."),
         ("The name for it", 'That rare mistake is a false alarm. <a href="#s3">Section 6.3</a> finds'
          f" where the 1 in {hrs:.0f} comes from.")])


def hook_07():
    from scipy.stats import norm
    n = 5
    d = n ** 0.5
    p = norm.sf(3 - d) + norm.cdf(-3 - d)
    return quiz_hook(
        "Quick question",
        f"The machine starts making parts slightly bigger, by about as much as its normal wobble. Your"
        f" chart plots the average of {n} parts each hour. Will the next point catch it?",
        [("yes", "Yes, right away"), ("likely", "Probably not"), ("never", "Never")],
        [("Chance the next point catches it", f"{p*100:.0f} %", "alarm"),
         ("Average wait for the alarm, hours", f"{1/p:.1f}", "")],
        {"yes": "Most people expect so.",
         "likely": "Right.",
         "never": "It will, but slowly."},
        f" The next point catches it only {p*100:.0f}&nbsp;% of the time; on average the alarm takes"
        f" {1/p:.1f} hours, and every part made meanwhile is off. A quiet chart is not proof that"
        " nothing changed.".replace("&nbsp;", " "),
        [("Before you pick", "The change is small but real: every part from now on comes out bigger."),
         ("You have done this", "A smoke alarm that sounds only for thick smoke stays quiet while the"
          " toast burns. Quiet does not mean fine."),
         ("The name for it", "The chance a chart catches a real change is its power."
          ' <a href="#s2">Section 7.2</a> prices it.')])


def hook_08():
    from scipy.stats import norm
    cpk, run = 0.8, 50
    p = 2 * norm.sf(3 * cpk)
    allpass = (1 - p) ** run
    return quiz_hook(
        "Quick question",
        f"Your last {run} parts were all inside the customer's limits. Is the process good enough?",
        [("yes", "Yes"), ("likely", "Probably"), ("cant", "Can't tell from that")],
        [(f"A process making {p*100:.1f} % bad parts passes {run} in a row", f"{allpass*100:.0f} %", "alarm"),
         ("Bad parts it makes per million", f"{p*1e6:,.0f}".replace(",", " "), "alarm")],
        {"yes": "Most people say yes.",
         "likely": "Most people lean that way.",
         "cant": "Right."},
        f" A process that makes {p*100:.1f}&nbsp;% bad parts still passes {run} in a row"
        f" {allpass*100:.0f}&nbsp;% of the time. Passing parts cannot tell you the rate; the spread"
        " measured against the limits can.".replace("&nbsp;", " "),
        [("Before you pick", "The customer's limits are the two lines every part must land between."),
         ("You have done this", "A month with no crash does not prove a safe driver. A month is a short"
          " run for a rare event."),
         ("The name for it", "The score that turns spread and limits into a defect rate is Cpk."
          ' <a href="#s4">Section 8.4</a> converts it into bad parts per million.')])


def hook_09():
    from spclab.detection import DET_EWMA, DET_SHEW, SHIFT_AT
    start, a, b = SHIFT_AT + 1, DET_SHEW + 1, DET_EWMA + 1
    return quiz_hook(
        "Quick question",
        f"A cutting tool starts to wear at hour {start}, and parts grow a little bigger every hour."
        " Chart A judges each hour on its own. Chart B keeps a running score of recent hours. Both raise"
        " false alarms equally rarely. How much sooner does B sound the alarm?",
        [("same", "About the same time"), ("bit", "An hour or two"), ("much", "Much sooner")],
        [("Chart A, each hour alone · alarm at hour", f"{a}", "alarm"),
         ("Chart B, running score · alarm at hour", f"{b}", "ok")],
        {"same": "Most people expect a tie.",
         "bit": "More than that.",
         "much": "Right."},
        f" B caught the drift {a-b} hours sooner, while every single part still looked normal. This"
        " level builds the chart with a memory.",
        [("Before you pick", "Both charts see the same parts. Only their memory differs."),
         ("You have done this", "You spot a slow leak not from one drip but from a puddle that keeps"
          " growing. The puddle remembers every drip."),
         ("The name for it", "Chart B is an EWMA chart, short for exponentially weighted moving average."
          ' <a href="#s3">Section 9.3</a> builds it.')])


def hook_10():
    from scipy.stats import binom
    n, rate, today = 200, 0.02, 9
    ucl = n * rate + 3 * (n * rate * (1 - rate)) ** 0.5
    p = binom.sf(today - 1, n, rate)
    return quiz_hook(
        "Quick question",
        f"Your line normally makes about {rate*100:.0f} bad parts in every 100. Yesterday"
        f" {round(n*rate)} of {n} were bad. Today {today} of {n}. Has the process got worse?",
        [("yes", "Yes"), ("no", "No"), ("cant", "Can't tell yet")],
        [(f"Alarm line, bad parts in {n}", f"{ucl:.1f}", ""),
         (f"Days an unchanged process gives {today} or more", f"{p*100:.1f} %", "")],
        {"yes": "It looks that way, but the chart would not call it.",
         "no": "Maybe, but you cannot be sure of that either.",
         "cant": "That is the honest answer."},
        f" {today} is inside the alarm line of {ucl:.1f}. An unchanged process does this on about 1 day"
        f" in {round(1/p)}: unusual, worth a look, not yet proof. This level is about charts for counts.",
        [("Before you pick", "Counts of bad parts bounce from day to day even when nothing changes."),
         ("You have done this", "Two burnt pizzas one night and five the next feels like a trend. With"
          " small counts, doubling by luck is easy."),
         ("The name for it", "Charts for counted bad parts are p-charts and np-charts."
          ' <a href="#s3">Section 10.3</a> says which one to use when.')])


def hook_11():
    from spclab.relationships import FIT, HALF_CI, HALF_PI, X0
    n, y0 = FIT["n"], FIT["intercept"] + FIT["slope"] * X0
    return quiz_hook(
        "Quick question",
        f"{n} test cuts show the surface gets rougher as you cut faster. The fitted line says"
        f" {y0:.2f}&nbsp;µm at {X0:.0f}&nbsp;m/min, and you are 95&nbsp;% sure of that average to within"
        f" ±{HALF_CI:.2f}&nbsp;µm. Will the next part you cut there land within ±{HALF_CI:.2f} of the line?",
        [("yes", "Yes"), ("wider", "No, it needs a wider range"), ("cant", "Can't say")],
        [("The average at that speed, µm", f"±{HALF_CI:.3f}", "ok"),
         ("One next part, µm", f"±{HALF_PI:.3f}", "alarm")],
        {"yes": "Most people say yes.",
         "wider": "Right.",
         "cant": "It can be worked out."},
        f" The average is pinned down to ±{HALF_CI:.3f}&nbsp;µm, but a single part still carries its own"
        f" wobble: ±{HALF_PI:.3f}&nbsp;µm, {HALF_PI/HALF_CI:.1f} times wider. More test cuts shrink the first"
        " range, never the second.".replace("&nbsp;", " "),
        [("Before you pick", "Each test cut landed a little off the line. The line is the average trend."),
         ("You have done this", "A weather app can know next month's average temperature well and still"
          " get tomorrow wrong."),
         ("The name for it", "The narrow range is a confidence interval, the wide one a prediction interval."
          ' <a href="#s4">Section 11.4</a> sets them side by side.')])


def hook_12():
    from spclab.experiments import OFAT
    return quiz_hook(
        "Quick question",
        "Two knobs: pressure and temperature, and a lower result is better. You find the best"
        " temperature with pressure set low, then the best pressure at that temperature. Have you found"
        " the best setting?",
        [("yes", "Yes"), ("close", "Close enough"), ("no", "Not necessarily")],
        [("One knob at a time settles on", f"{OFAT['chosen_y']:.1f}", "alarm"),
         ("Best setting, never tried", f"{OFAT['optimum_y']:.1f}", "ok")],
        {"yes": "Most people say yes.",
         "close": "It can be well off.",
         "no": "Right."},
        f" Here one knob at a time stops at {OFAT['chosen_y']:.1f}; the best setting gives"
        f" {OFAT['optimum_y']:.1f}, and the method never tries it, because what one knob does depends on"
        " where the other is set. This level changes settings on purpose, the right way.",
        [("Before you pick", "Each knob has a low and a high setting, so there are four combinations."),
         ("You have done this", "You find the best route to work, then the best time to leave on that"
          " route. The best time on another route might beat both."),
         ("The name for it", "When one knob changes what the other does, that is an interaction."
          ' <a href="#s3">Section 12.3</a> measures it.')])

def _mid(bar, q, picks, tiles, said, end):
    # replies go through textContent, so entities must already be characters
    return quiz_hook(bar, q, picks, tiles, said, end.replace("&nbsp;", "\u00a0"), None, hid="hook2")


def mid_01():
    return _mid("Before you read on",
        "The same 240 measurements, drawn twice as a bar chart: once with 4 bars, once with 52."
        " Will the two pictures tell the same story?",
        [("yes", "Yes, same data"), ("no", "No")],
        [("With 4 bars", "one lump", ""), ("With 52 bars", "a comb", "")],
        {"yes": "Same data, but not the same story.", "no": "Right."},
        " Four bars shows a single lump; fifty-two shows a row of spikes. The bar width is a"
        " setting you chose, and it changes what the picture seems to say.")


def mid_02():
    from scipy.stats import norm
    p = 2 * norm.sf(3)
    arl = 1 / p
    early = 1 - (1 - p) ** 100
    late = (1 - p) ** round(2 * arl)
    return _mid("Before you read on",
        f"A chart false-alarms about once in {arl:.0f} points on average. What is the chance its"
        " first false alarm comes before point 100?",
        [("none", "Almost none"), ("quarter", "About a quarter"), ("half", "About half")],
        [("First false alarm before point 100", f"{early*100:.0f} %", "alarm"),
         (f"Not until after point {round(2*arl)}", f"{late*100:.0f} %", "")],
        {"none": "Most people say almost none.", "quarter": "Right.", "half": "Less than that."},
        f" {arl:.0f} is an average, not a schedule: about {early*100:.0f}&nbsp;% of the time the first"
        f" false alarm comes before point 100, and {late*100:.0f}&nbsp;% of the time it waits past"
        f" point {round(2*arl)}.".replace("&nbsp;", " "))


def mid_03():
    n = 12
    share = (n - 1) / n
    return _mid("Before you read on",
        f"You work out the spread of {n} parts, averaging their squared distances from the mean by"
        f" dividing by {n}. Over many samples, does that come out too small, about right, or too big?",
        [("small", "Too small"), ("right", "About right"), ("big", "Too big")],
        [("Average result, share of the true value", f"{share*100:.1f} %", "alarm"),
         ("Divide by this instead and it comes out right", f"{n-1}", "ok")],
        {"small": "Right.", "right": "Most people say so.", "big": "The other way."},
        f" It comes out too small on average, at {share*100:.1f}&nbsp;% of the truth: the parts sit"
        f" closer to their own average than to the true one. Dividing by {n-1} instead of {n}"
        " fixes it.".replace("&nbsp;", " "))


def mid_04():
    first = 2 ** 2
    again = first ** 2
    return _mid("Before you read on",
        f"Averaging {first} parts halves the wobble of a single part. How many parts do you need"
        " to halve it again?",
        [("eight", f"{2*first}"), ("sixteen", f"{again}"), ("never", "You can't")],
        [("Halve the wobble once", f"{first} parts", ""), ("Halve it again", f"{again} parts", "alarm")],
        {"eight": "Most people say so.", "sixteen": "Right.", "never": "You can, but it gets expensive."},
        f" Halving it again takes {again} parts, not {2*first}: the wobble shrinks with the square"
        " root of the count. Each extra part helps less than the one before.")


def mid_05():
    from scipy.stats import t as _t, norm
    n = 5
    z = norm.ppf(0.975)
    miss = 2 * _t.sf(z, n - 1)
    fix = _t.ppf(0.975, n - 1)
    return _mid("Before you read on",
        f"You build a “95&nbsp;%” range for the true average from {n} parts, using the usual"
        f" multiplier {z:.2f} and the spread of those same {n} parts. How often does the range miss?",
        [("five", "5 %, as promised"), ("more", "More often"), ("less", "Less often")],
        [("Promised misses", "5 %", ""), (f"Actual misses, multiplier {z:.2f}", f"{miss*100:.1f} %", "alarm")],
        {"five": "Most people trust the label.", "more": "Right.", "less": "The other way."},
        f" It misses {miss*100:.1f}&nbsp;% of the time, not 5&nbsp;%: {n} parts often guess the spread"
        f" too small. Widen the multiplier to {fix:.2f} and the promise holds again.".replace("&nbsp;", " "))


def mid_06():
    from scipy.stats import norm
    p3, p2 = 2 * norm.sf(3), 2 * norm.sf(2)
    return _mid("Before you read on",
        f"Limits drawn 3 steps out give a false alarm about once in {1/p3:.0f} points. Pull them in"
        " to 2 steps. How many more false alarms?",
        [("two", "Twice as many"), ("five", "About 5 times"), ("more", f"About {p2/p3:.0f} times")],
        [("Limits at 3 steps: one false alarm per", f"{1/p3:.0f} points", ""),
         ("Limits at 2 steps: one per", f"{1/p2:.0f} points", "alarm")],
        {"two": "Far more than that.", "five": "More than that.", "more": "Right."},
        f" One step closer and false alarms come {p2/p3:.0f} times as often. The tails of the bell"
        " thin out fast, so where you draw the line matters enormously.")


def mid_07():
    from spclab.evidence import ARL0_ALL, ARL0_ONE_RULE
    k = ARL0_ONE_RULE / ARL0_ALL
    return _mid("Before you read on",
        f"With one rule, your chart false-alarms about once in {ARL0_ONE_RULE:.0f} points. Switch on"
        " four extra pattern rules. Now?",
        [("same", "About the same"), ("double", "Twice as often"), ("more", f"About {k:.0f} times as often")],
        [("One rule: a false alarm every", f"{ARL0_ONE_RULE:.0f} points", ""),
         ("All rules: a false alarm every", f"{ARL0_ALL:.0f} points", "alarm")],
        {"same": "Each rule adds its own false alarms.", "double": "More than that.", "more": "Right."},
        f" False alarms come {k:.1f} times as often. Every extra rule buys sensitivity and pays for it"
        " in alarms; this section prices each one.")


def mid_08():
    from scipy.stats import norm
    centred = 2 * norm.sf(3)
    shifted = norm.sf(2) + norm.cdf(-4)
    return _mid("Before you read on",
        "A process just fits the customer's limits. Its average slides toward one limit by one step"
        " of its scatter; the scatter stays the same width. Bad parts go up by how much?",
        [("third", "About a third more"), ("double", "Double"), ("more", f"About {shifted/centred:.0f} times")],
        [("Centred · bad parts per million", f"{centred*1e6:,.0f}".replace(",", " "), ""),
         ("Slid one step · bad parts per million", f"{round(shifted*1e6, -2):,.0f}".replace(",", " "), "alarm")],
        {"third": "Far more than that.", "double": "More than that.", "more": "Right."},
        f" Bad parts go up {shifted/centred:.1f} times, almost all of them over the near limit. The"
        " far side barely notices; the near side is the one you fail.")


def mid_09():
    lam, k = 0.2, 10
    w = lam * (1 - lam) ** k
    return _mid("Before you read on",
        f"The running score counts the newest hour for {lam*100:.0f}&nbsp;% and the past for the"
        f" rest. How much does the hour from {k} hours ago still count?",
        [("none", "Nothing, it's forgotten"), ("little", "A little"), ("same", "As much as the newest")],
        [("Newest hour counts", f"{lam*100:.0f} %", ""), (f"{k} hours ago counts", f"{w*100:.1f} %", "ok")],
        {"none": "Not quite: it fades but never vanishes.", "little": "Right.", "same": "No, it fades."},
        f" It still counts {w*100:.1f}&nbsp;%. Old hours fade but never vanish, so a small drift that"
        " repeats keeps adding up in the score.".replace("&nbsp;", " "))


def mid_10():
    import math as _m
    p, n = 0.04, 50
    lcl = p - 3 * _m.sqrt(p * (1 - p) / n)
    need = _m.floor(9 * (1 - p) / p) + 1
    return _mid("Before you read on",
        f"Your line makes {p*100:.0f}&nbsp;% bad parts, and you chart batches of {n}. If the line gets"
        " better, can the chart show it?",
        [("yes", "Yes"), ("no", "No"), ("big", "Only for a big gain")],
        [(f"Lower alarm line, batches of {n}", f"{lcl*100:.1f} %".replace("-", "−"), "alarm"),
         ("Smallest batch with a lower line", f"{need}", "")],
        {"yes": "Most people say so.", "no": "Right.", "big": "Not even then."},
        f" The lower line works out at {lcl*100:.1f}&nbsp;%".replace("-", "−") + ", below zero"
        f", so no count can ever cross it."
        f" The chart only warns when things get worse. Batches of {need} or more fix that.".replace("&nbsp;", " "))


def mid_11():
    from spclab.relationships import R2_PLAIN, R2_WITH_NOISE
    k = max(R2_WITH_NOISE)
    return _mid("Before you read on",
        f"A fitted line explains {R2_PLAIN*100:.1f}&nbsp;% of the scatter. Add {k} columns of pure"
        " random numbers to the fit. What happens to that score?",
        [("up", "It goes up"), ("same", "It stays"), ("down", "It goes down")],
        [("The real fit", f"{R2_PLAIN*100:.1f} %", ""), (f"Plus {k} junk columns", f"{R2_WITH_NOISE[k]*100:.1f} %", "alarm")],
        {"up": "Right.", "same": "Most people expect that.", "down": "Most people expect that."},
        f" It rises to {R2_WITH_NOISE[k]*100:.1f}&nbsp;% on pure junk. The score can only go up as you"
        " add columns, so a higher score is not a better model.".replace("&nbsp;", " "))


def mid_12():
    from spclab.experiments import CURVED
    return _mid("Before you read on",
        f"Four corner runs average {CURVED['factorial_mean']:.1f}. Straight-line thinking says the"
        " middle setting should give the same. What do runs in the middle give?",
        [("same", f"About {CURVED['factorial_mean']:.1f}"), ("other", "Something else")],
        [("Corners predict for the middle", f"{CURVED['factorial_mean']:.1f}", ""),
         (f"Middle, measured · {CURVED['n_centre']} runs", f"{CURVED['centre_mean']:.1f}", "alarm")],
        {"same": "Most people say so.", "other": "Right."},
        f" The middle gives {CURVED['centre_mean']:.1f}. The response bends between the ends, and"
        " runs at the corners alone can never show it; a few runs in the middle can.")


CHAPTERS = {
    "level-01.html": {
        "number": 1, "word": "one",
        "before": "nothing — this is where the curriculum starts",
        "after": "Level 2 — chance, and what a percentage claims",
        "estimate": "5 sections · 1 act · 1 interactive · ~8 min read",
        "toc": [("1.1", "s1", "Nothing repeats",
                 "twelve parts off one machine, and no two the same"),
                ("1.2", "s2", "A histogram is an instrument",
                 "bin width is a setting, and it changes the answer"),
                ("1.3", "s3", "The histogram throws away the order",
                 "the same numbers twice: identical histogram, different process"),
                ("1.4", "s4", "Two kinds of variation",
                 "common cause and special cause, and why they demand opposites"),
                ("1.5", "s5", "Reacting to noise makes it worse",
                 "Deming's funnel: correcting every part doubles the variance")],
        "sections": chapter_01,
        "mid": {"s2": mid_01},
        "hook": hook_01,
        "plain": {
            "s1": "Make the same part twelve times and you get twelve slightly different"
                  " sizes. That is normal. Nothing is broken.",
            "s2": "A histogram is a bar chart of how often each size turns up. How wide"
                  " you make the bars changes the picture, so never trust just one.",
            "s3": "A steady machine and a slowly drifting one can make exactly the same"
                  " set of sizes. Only the order the parts came out in tells them apart.",
            "s4": "Some wobble is just the machine being a machine. Some has a cause you"
                  " can find, like a worn tool. The two need opposite responses.",
            "s5": "If you nudge the machine every time a part comes out a bit off, your"
                  " parts get more scattered, not less.",
        },
    },
    "level-02.html": {
        "number": 2, "word": "two",
        "before": "Level 1 — variation, and why reacting to it backfires",
        "after": "Level 3 — centre and spread",
        "estimate": "5 sections · 1 act · 1 interactive · ~8 min read",
        "toc": [("2.1", "s1", "A long-run frequency",
                 "a proportion describes a process, never the next part"),
                ("2.2", "s2", "The gap grows, the rate settles",
                 "one sequence read twice — there is no law of averages"),
                ("2.3", "s3", "The coin has no memory",
                 "independence, shown as an absence"),
                ("2.4", "s4", "Expectation",
                 "a balance point the die does not have"),
                ("2.5", "s5", "What a percentage claims",
                 tex(r"1-(1-\alpha)^{1/\alpha}") + " — and why 370 is not a deadline")],
        "sections": chapter_02,
        "mid": {"s5": mid_02},
        "hook": hook_02,
        "plain": {
            "s1": "A number like “99.73 % inside the limits” describes what a process"
                  " does over thousands of parts. It says nothing certain about the next one.",
            "s2": "Flip a coin more and more: the share of heads creeps toward half, but"
                  " the gap between heads and tails can keep growing. Nothing evens out.",
            "s3": "A coin has no memory. After five heads in a row, the next flip is"
                  " still a coin flip.",
            "s4": "The expected value is the long-run average. For a die it is 3.5, a"
                  " number the die can never actually show.",
            "s5": "A chart that false-alarms “once in 370 points” can alarm on the"
                  " fifth point or the nine-hundredth. 370 is an average, not a schedule.",
        },
    },
    "level-05.html": {
        "number": 5, "word": "five",
        "before": "Level 4 — the average is predictable",
        "after": "Level 6 — limits are a hypothesis test",
        "estimate": "5 sections · 1 act · 1 interactive · ~8 min read",
        "toc": [("5.1", "s1", "Every number here is an estimate",
                 "the standard error is the size of being wrong"),
                ("5.2", "s2", "What “ninety-five percent” has to earn",
                 "coverage is counted, not claimed"),
                ("5.3", "s3", "Why t exists",
                 "1.96 delivers " + f"{COVER_Z[SUBGROUP_N]*100:.0f}" + " % at five parts, not 95"),
                ("5.4", "s4", "Precision has a price",
                 "halving an interval costs four times the parts"),
                ("5.5", "s5", "Including ours",
                 tex("d_2") + " is simulated, so it has a standard error too")],
        "sections": chapter_05,
        "mid": {"s3": mid_05},
        "hook": hook_05,
        "plain": {
            "s1": "Nobody ever sees a process’s true average or spread. Every number on a chart"
                  " is a guess from a handful of parts, and you can work out how far such"
                  " guesses usually miss.",
            "s2": "A “95 percent” range should catch the true value 95 times in 100. Draw a"
                  " range from each of many samples and count how many actually catch it.",
            "s3": "With only five parts you must guess the spread too, and small samples often"
                  " guess it too small. Ranges built that way miss more often than promised, so"
                  " they must reach further out.",
            "s4": "To make an estimate twice as precise you need about four times as many"
                  " parts, not twice as many. Precision gets expensive fast.",
            "s5": "Even the fixed numbers this site uses come from simulation, so they are"
                  " guesses too, with their own error. Pinning one down very precisely takes a"
                  " huge number of tries.",
        },
    },
    "level-06.html": {
        "number": 6, "word": "six",
        "before": "Level 5 — estimation, and what an estimate costs",
        "after": "Level 7 — evidence, and the other way to be wrong",
        "estimate": "7 sections · 1 interactive · 2 acts · ~11 min read",
        "toc": [("6.1", "s1", "A curve that is a claim",
                 "why the bell is a hypothesis about the process, not the parts"),
                ("6.2", "s2", "Pricing ±3σ",
                 "the integral between the limits, evaluated as they move"),
                ("6.3", "s3", "Where the price hides",
                 "the tails are 70× smaller than the chart — stretch the axis to see them"),
                ("6.4", "s4", "The chart is that test, repeated",
                 "limits turned on their side, and why boring is the goal"),
                ("6.5", "s5", "How good is the σ estimate?",
                 tex(r"\bar R / d_2") + " — the bridge from a range to a standard deviation"),
                ("6.6", "s6", "Where the constants come from",
                 tex(r"d_2, A_2, D_3, D_4") + " — simulated, never looked up"),
                ("6.7", "s7", "Building the chart",
                 "the " + tex(r"\bar{X}") + "–R pair from 25 subgroups, one multiplication per limit")],
        "sections": chapter_06,
        "mid": {"s2": mid_06},
        "hook": hook_06,
        "plain": {
            "s1": "The bell curve behind a control chart is a claim: that the process has not"
                  " changed. It is a claim about the process, never about a single part.",
            "s2": "Put two limits around the middle of the curve and slide them outward. At"
                  " three steps of spread on each side, almost all of the curve sits inside."
                  " Nobody picked that share; the curve sets it.",
            "s3": "The thin slivers outside the limits are too small to see until you stretch"
                  " the picture. Together they mean a steady process still gives a false alarm"
                  " about once in 370 points.",
            "s4": "A control chart runs that same check on every new group of parts. A point"
                  " outside the limits is not a bad part. It says something changed, so go and"
                  " find it.",
            "s5": "On a real line nobody knows the true spread, so the chart estimates it from"
                  " how far apart the parts in each group are. With only twenty-five groups that"
                  " estimate is still a little loose.",
            "s6": "The fixed numbers printed on every chart form are not copied from a book"
                  " here. Each one is worked out by simulation, then checked against the"
                  " published table.",
            "s7": "Take twenty-five groups of five parts. Chart each group’s average on top and"
                  " its range underneath. Read the bottom chart first: if it is wrong, so are"
                  " the top chart’s limits.",
        },
    },
    "level-03.html": {
        "number": 3, "word": "three",
        "before": "Level 2 — chance, and what a percentage claims",
        "after": "Level 4 — the average is predictable",
        "estimate": "5 sections · 1 act · 1 interactive · ~8 min read",
        "toc": [("3.1", "s1", "Twelve parts, twelve numbers",
                 "every reading differs and nothing is broken"),
                ("3.2", "s2", "The mean is a balance point",
                 "the one position where the deviations cancel"),
                ("3.3", "s3", "Spread has to be squared first",
                 "why averaging the deviations cannot work"),
                ("3.4", "s4", "A shape nobody chose",
                 "twelve parts to twenty thousand, and a bell arrives"),
                ("3.5", "s5", "You never measure everything",
                 "sample against process, and why the divisor is n − 1")],
        "sections": chapter_03,
        "mid": {"s5": mid_03},
        "hook": hook_03,
        "plain": {
            "s1": "Twelve parts off one machine, same tool and same person, all measure a"
                  " little differently. That spread is normal, and a few numbers can sum it up"
                  " instead of twelve.",
            "s2": "The average is a balance point: the one spot where the parts above it and"
                  " the parts below it pull equally hard. Slide a guess along until the two"
                  " sides cancel, and you have found it.",
            "s3": "You cannot measure spread by averaging how far each part sits from the"
                  " average, because the ups and downs cancel out. Square each distance first,"
                  " average them, then take the square root.",
            "s4": "Twelve parts show no shape. Measure thousands off the same machine and a"
                  " bell curve appears that nobody asked for, made by many small causes adding"
                  " up.",
            "s5": "Your twelve parts only estimate the machine’s true average and spread;"
                  " another twelve would give other answers. Samples also sit a little tighter"
                  " than the truth, so the usual formula divides by one fewer part to make up"
                  " for it.",
        },
    },
    "level-04.html": {
        "number": 4, "word": "four",
        "before": "Level 3 — centre and spread",
        "after": "Level 5 — estimation, and what an estimate costs",
        "estimate": "5 sections · 1 act · 1 interactive · ~9 min read",
        "toc": [("4.1", "s1", "One part tells you nothing",
                 "one die, ten rolls, then ten thousand"),
                ("4.2", "s2", "Averaging makes a shape",
                 "a flat die becomes a bell by averaging alone"),
                ("4.3", "s3", "The law",
                 "two numbers agreeing to three decimals"),
                ("4.4", "s4", "What averaging buys",
                 "why subgroups of four and five, and never fifty"),
                ("4.5", "s5", "Reading the bell",
                 f"areas in sigmas: where {Z95:.2f}, {TAIL_K[2]*100:.1f} % and {TAIL3_PPM} ppm come from")],
        "sections": chapter_04,
        "mid": {"s4": mid_04},
        "hook": hook_04,
        "plain": {
            "s1": "Roll a die ten times and some faces turn up far too often. Roll it ten"
                  " thousand times and every face settles near one roll in six. Nobody arranged"
                  " that.",
            "s2": "A single die has no bell shape: every face is equally likely. Average a few"
                  " dice at a time and the averages pile up into a bell. The averaging made the"
                  " shape.",
            "s3": "How much an average wobbles can be worked out before you measure anything:"
                  " it shrinks in a fixed way as you average more parts. That rule is what makes"
                  " a control chart possible.",
            "s4": "Averaging more parts makes the average steadier, but each extra part helps"
                  " less than the one before. That is why factories average four or five parts"
                  " at a time, rather than fifty.",
            "s5": "On any bell curve, the share of parts within a given distance of the middle"
                  " is fixed, once you count distance in steps of the curve’s own spread. Far"
                  " out, a tiny sliver always remains.",
        },
    },
    "level-07.html": {
        "number": 7, "word": "seven",
        "before": "Level 6 — limits are a hypothesis test",
        "after": "Level 8 — capability",
        "estimate": "5 sections · 1 act · 1 interactive · ~9 min read",
        "toc": [("7.1", "s1", "The other way to be wrong",
                 "α is crying wolf; β is staying silent, and nobody counts it"),
                ("7.2", "s2", "Power",
                 "one point, one chance — and how small a chance"),
                ("7.3", "s3", "The chart throws evidence away",
                 "a verdict is not the same as a p-value"),
                ("7.4", "s4", "Four rules, one at a time",
                 "each rule priced, against a figure published in 1987"),
                ("7.5", "s5", "So is it worth it",
                 "the cost is fixed; the benefit is the shift you fear")],
        "sections": chapter_07,
        "mid": {"s4": mid_07},
        "hook": hook_07,
        "plain": {
            "s1": "A chart can be wrong two ways: it can raise a false alarm, or it can stay"
                  " quiet when the machine really has moved. Everyone counts the first. Almost"
                  " nobody counts the second.",
            "s2": "Each point gets one chance to spot a change, and for a small change that"
                  " chance is poor. Even once the average has moved right onto the limit, the"
                  " next point is only a coin toss.",
            "s3": "A point just inside the limit is rare enough to deserve a second look, but"
                  " the chart calls it fine and moves on. Inside or outside is all it keeps.",
            "s4": "Four extra rules look for patterns across several points. Switch them on one"
                  " at a time: each catches a real change sooner, and each brings more false"
                  " alarms.",
            "s5": "The extra rules always cost the same in false alarms. Against a small, slow"
                  " drift they pay for themselves. Against a big sudden jump they buy almost"
                  " nothing, since the basic chart already sees it.",
        },
    },
    "level-10.html": {
        "number": 10, "word": "ten",
        "before": "Level 9 — detection, and memory beating sensitivity",
        "after": "Level 11 — relationships, and the seam to MSA",
        "estimate": "6 sections · 1 act · 1 interactive · ~9 min read",
        "toc": [("10.1", "s1", "The spread is not a free parameter",
                 "for a count, the mean fixes the standard deviation"),
                ("10.2", "s2", "Same mean, different scatter",
                 "a variance ratio you get for free"),
                ("10.3", "s3", "Four charts, two questions",
                 "np, p, c, u — and nothing else to remember"),
                ("10.4", "s4", "When the limits have to breathe",
                 "the average-n shortcut, priced"),
                ("10.5", "s5", "Where the lower limit goes",
                 tex(r"n\bar{p} > k^{2}(1-\bar{p})") + ", not the rule of thumb"),
                ("10.6", "s6", "Annex — capability when the shape is wrong",
                 "the normal tail understates a count tail")],
        "sections": chapter_10,
        "mid": {"s5": mid_10},
        "hook": hook_10,
        "plain": {
            "s1": "Measure a part and you must check its spread as well as its average. Count"
                  " bad parts and the average alone sets how much the count should bounce"
                  " around.",
            "s2": "Two lines can make the same share of bad parts on average. If one line’s"
                  " rate shifts between batches, its counts scatter wider than they should, and"
                  " its chart raises false alarms.",
            "s3": "There are four charts for counted data. You pick one by answering two"
                  " questions: are you counting bad parts or flaws on a part, and is the batch"
                  " size always the same?",
            "s4": "When batch sizes change, the alarm lines should sit closer together for big"
                  " batches and wider apart for small ones. One fixed set of lines for every"
                  " batch gives many false alarms.",
            "s5": "When bad parts are rare and batches small, the lower alarm line drops below"
                  " zero, so the chart can only warn that things got worse. The section works"
                  " out how big a batch fixes that.",
            "s6": "The bell-curve shortcut for “how often will we get this many bad parts?”"
                  " gives too small an answer for counts. It makes the process look safer than"
                  " it really is.",
        },
    },
    "level-11.html": {
        "number": 11, "word": "eleven",
        "before": "Level 10 — counting, not measuring",
        "after": "Level 12 — experiments, and the arc closes",
        "estimate": "5 sections · 1 act · 1 interactive · ~9 min read",
        "toc": [("11.1", "s1", "One identity, three names",
                 "regression, ANOVA and a gauge study are one subtraction"),
                ("11.2", "s2", "Least squares is a claim",
                 "the closed form sits at the minimum, not near it"),
                ("11.3", "s3", "R² is a ratio, not a grade",
                 "it rises for nothing, and it cannot see a curve"),
                ("11.4", "s4", "Two intervals that are not the same interval",
                 "one 1 inside a square root, and what it costs to ignore"),
                ("11.5", "s5", "The same total, split four ways",
                 "part, operator, interaction — and the seam to MSA")],
        "sections": chapter_11,
        "mid": {"s3": mid_11},
        "hook": hook_11,
        "plain": {
            "s1": "Fitting a line through points, comparing groups, and checking a measuring"
                  " tool all do the same sum: split the total scatter into pieces. Only the"
                  " names of the pieces change.",
            "s2": "The best-fit line is the one whose misses, squared and added up, come out"
                  " smallest. Tilt it to any other slope and that total grows, by an amount you"
                  " can work out.",
            "s3": "The score for how well a line fits rises even when you add pure junk. It"
                  " also stays high when a straight line is forced through a curve. Only the"
                  " leftover misses show the problem.",
            "s4": "Predicting the average at a setting and predicting the next single part are"
                  " two different answers. The next part always gets a wider range, because more"
                  " data never removes its own wobble.",
            "s5": "Several people measure the same parts more than once, and the total scatter"
                  " splits into the parts, the people, and the tool repeating itself. That is"
                  " how a measuring tool gets checked.",
        },
    },
    "level-12.html": {
        "number": 12, "word": "twelve",
        "before": "Level 11 — relationships, and the seam to MSA",
        "after": "nothing — this is where the arc closes",
        "estimate": "6 sections · 1 act · 1 interactive · ~9 min read",
        "toc": [("12.1", "s1", "Changing things on purpose",
                 "one term in the model is the whole subject"),
                ("12.2", "s2", "One factor at a time, with perfect measurements",
                 "it stops at the wrong corner, and noise is not the reason"),
                ("12.3", "s3", "The interaction it cannot estimate",
                 "unidentifiable, which is stronger than imprecise"),
                ("12.4", "s4", "Screening: width, bought with aliasing",
                 "seven factors in eight runs, and the price as a table"),
                ("12.5", "s5", "Curvature, and why the corners cannot see it",
                 "the bend is constant across corners, not absent"),
                ("12.6", "s6", "Twelve levels",
                 "what the arc was for")],
        "sections": chapter_12,
        "mid": {"s5": mid_12},
        "hook": hook_12,
        "plain": {
            "s1": "Until now the course watched a process. Here you change its settings on"
                  " purpose. If one setting changes what another does, testing them one at a"
                  " time can lead you to the wrong answer.",
            "s2": "Tune the temperature, lock it, then tune the pressure. Even with perfect"
                  " readings this falls short, because it never tries the high-pressure, low-"
                  " temperature setting that gives the best result.",
            "s3": "To see how two settings work together you need all four combinations, and"
                  " one at a time never tries them all. Testing all four corners also pins down"
                  " each setting better.",
            "s4": "To find which of many settings matter, you can run a small fraction of every"
                  " combination. The cost: each setting’s effect gets mixed up with certain"
                  " pairs, and you know which pairs before you start.",
            "s5": "Testing only the high and low ends of each setting cannot tell whether the"
                  " result bends in between. Add a few runs in the middle, and a gap between"
                  " middle and ends shows the bend.",
            "s6": "Twelve levels, one idea: every number on a chart comes from reasoning you"
                  " can check yourself. Each level raised a question that the next one answered.",
        },
    },
    "level-08.html": {
        "number": 8, "word": "eight",
        "before": "Level 7 — evidence, and the other way to be wrong",
        "after": "Level 9 — detection",
        "estimate": "4 sections · 1 interactive · 2 acts · ~8 min read",
        "toc": [("8.1", "s1", "Two distributions on one axis",
                 "the customer speaks in limits, the process in spread"),
                ("8.2", "s2", "Cp is pure geometry",
                 "tolerance over six sigma, and no probability in it"),
                ("8.3", "s3", "The near side is the one you fail",
                 "the mean drifts, the spread does not, the number collapses"),
                ("8.4", "s4", "Every Cpk is a promise about defect rate",
                 "1.33 against 1.67 is two orders of magnitude of scrap")],
        "sections": chapter_08,
        "mid": {"s3": mid_08},
        "hook": hook_08,
        "plain": {
            "s1": "The customer draws two lines, and parts between them pass. The machine makes"
                  " parts with its own natural scatter. Put both on one ruler and you see"
                  " whether the scatter fits. Here it does not.",
            "s2": "The first score is a plain width comparison: how much room the customer’s"
                  " limits leave against the machine’s scatter. Tighten the scatter and the"
                  " score goes up.",
            "s3": "Let the machine’s average slide toward one limit. The scatter stays the same"
                  " width, but the score drops, because bad parts spill over the nearer limit"
                  " first.",
            "s4": "Every capability score stands for a count of bad parts per million. Two"
                  " scores that look close can differ enormously in scrap.",
        },
    },
    "level-09.html": {
        "number": 9, "word": "nine",
        "before": "Level 8 — capability",
        "after": "Level 10 — counting, not measuring",
        "estimate": "5 sections · 3 acts · 1 interactive · ~10 min read",
        "toc": [("9.1", "s1", "The most expensive failure mode",
                 "every single measurement of a drift looks acceptable"),
                ("9.2", "s2", "A chart with no memory",
                 "43 subgroups late, and 2.6 sigma of movement"),
                ("9.3", "s3", "A statistic that remembers",
                 "one part new, four parts memory, same alarm budget"),
                ("9.4", "s4", "The same eighty subgroups again",
                 "caught at 34, with the mean only 0.8 sigma off"),
                ("9.5", "s5", "One drift is an anecdote",
                 "44 subgroups against 10, and what the trade means")],
        "sections": chapter_09,
        "mid": {"s3": mid_09},
        "hook": hook_09,
        "plain": {
            "s1": "A slow drift is the costliest problem a machine can have, because each part"
                  " on its own still looks fine. Here a standard chart watches the average start"
                  " to creep, and says nothing.",
            "s2": "The standard chart judges each point alone and then forgets it, so it raises"
                  " the alarm long after the drift began. Every part made in between came from a"
                  " changed process.",
            "s3": "This chart keeps a running score: each new result counts for a fifth, and"
                  " the past keeps the rest. Its limits are set so it gives false alarms no more"
                  " often than the first chart.",
            "s4": "On the same eighty results, random ups and downs cancel out in the running"
                  " score but the drift keeps adding up. It sounds the alarm far sooner, on a"
                  " point the standard chart would ignore.",
            "s5": "One run could be luck, so test thousands of sudden jumps. The chart with a"
                  " memory catches them several times sooner, with no extra false alarms.",
        },
    },
}


# ---------------------------------------------------------------- assembly


def build_main(spec: dict, keep: dict) -> str:
    """Assemble one chapter from its spec."""
    n = spec["number"]
    figs = keep["figs"]

    def fig(name):
        f = figs.get(name)
        if f is None:
            sys.exit(f"chapterise: figure {name} missing (have: {sorted(figs)})")
        f = re.sub(r"<figure[^>]*>", "<figure>", f, count=1)
        # tap a figure to open it full size: on a phone its labels are 9px
        return re.sub(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>',
                      lambda m: f'<a class="zoom" href="{m[1]}">{m[0]}</a>', f)

    def watch(mp4, poster, label, caption):
        """A referenced act that is not this section's subject.

        It was a 340px margin card, which measured 323x182 on screen - an
        unwatchable player for a 1920-wide render, where an axis label is a
        smear. It is now a collapsed player in the text block: a poster strip
        closed, the full text-block width open. Compact by default, watchable on
        demand, and no JavaScript. The media path is lifted from the figure being
        demoted so it cannot drift.
        """
        src = next((s for s in figs.values() if mp4 in s), None)
        if src is None:
            sys.exit(f"chapterise: no figure to demote for {mp4}")
        path = re.search(r'src="([^"]+' + re.escape(mp4) + r')"', src).group(1)
        dur = re.search(r"(\d+:\d\d)", caption)
        return ('      <details class="act">\n'
                '        <summary>\n'
                '          <span class="thumb-wrap">'
                f'<img class="thumb" src="posters/{poster}.jpg" alt="" loading="lazy">'
                '</span>\n'
                '          <span class="meta">'
                f'<span class="k">{label}</span>'
                f'<span class="cap">{caption}</span></span>\n'
                f'          <span class="cue">play{" · " + dur.group(1) if dur else ""}</span>\n'
                '        </summary>\n'
                '        <video controls playsinline preload="none" '
                f'poster="posters/{poster}.jpg">\n'
                f'          <source src="{path}" type="video/mp4">\n'
                f'          <track kind="captions" src="captions/{poster}.vtt" srclang="en" '
                'label="English">\n'
                '        </video>\n'
                '      </details>')

    K = {**keep, "fig": fig, "watch": watch}

    sections = list(spec["sections"](K))

    # the head counts "1 act · 1 interactive"; say which row holds them, so the
    # two most inviting things on the page can be found from the top
    def tags(anchor):
        body = "\n".join(next((b for a, _, _, b in sections if a == anchor), []))
        out = [label for label, probe in (("act", "<video"), ("interactive", 'class="lab"'))
               if probe in body]
        return "".join(f'<span class="tag">{t}</span>' for t in out)

    toc_items = "\n".join(
        f'          <li><span class="n">{num}</span><a href="#{anchor}">{title}{tags(anchor)}'
        f'<span class="sub">{sub}</span></a></li>'
        for num, anchor, title, sub in spec["toc"])

    L = []
    A = L.append
    A("  <main>")
    A('    <header class="ch">')
    A('      <div class="leaf">')
    A("        <div>")
    A(f'          <p class="ch-no">Level {n} · chapter {spec["word"]}</p>')
    A('          <h1 class="page-title"></h1>')
    A('          <p class="dek page-dek"></p>')
    if spec.get("hook"):
        A(spec["hook"]())
    A("        </div>")
    A("      </div>")
    A('      <div class="toc">')
    A('        <div class="toc-head"><span class="micro">What this chapter derives</span>'
      f'<span class="micro est">{spec["estimate"]}</span></div>')
    A('        <p class="toc-chain"><span class="micro">after</span> '
      f'{spec["before"].rstrip(".")}<span class="sep">·</span>'
      f'<span class="micro">leads to</span> {spec["after"].rstrip(".")}</p>')
    A("        <ol>")
    A(toc_items)
    A("        </ol>")
    A("      </div>")
    A("    </header>")

    for anchor, num, title, blocks in sections:
        A(f'    <section id="{anchor}">')
        A('      <div class="leaf">')
        A("        <div>")
        A(f'          <span class="sec-no">{num}</span>')
        A(f"          <h2>{title}</h2>")
        if anchor in spec.get("plain", {}):
            A(f'{P}<div class="plain"><span class="micro">In plain words</span>'
              f'<p>{spec["plain"][anchor]}</p></div>')
        if anchor in spec.get("mid", {}):
            A(spec["mid"][anchor]())
        for b in blocks:
            A(b)
        A("        </div>")
        A("      </div>")
        A("    </section>")

    A("    " + keep["next"])
    A("  </main>")
    # Figures are numbered in reading order, whatever order the page-source kept
    # them in. Nothing in the prose cites a figure number, so this is safe.
    seq = iter(range(1, 100))
    return re.sub(r'(class="(?:fignum|k)">[Ff]igure )\d+\.\d+',
                  lambda m: f"{m.group(1)}{n}.{next(seq)}", "\n".join(L))


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = pathlib.Path(sys.argv[1])
    spec = CHAPTERS.get(p.name)
    if spec is None:
        sys.exit(f"chapterise: no chapter defined for {p.name} "
                 f"(have: {', '.join(sorted(CHAPTERS))})")

    # The pre-chapter source is tracked in the repo. The transform is not
    # idempotent, so it must never read its own output: regenerating from the
    # generated page would chapterise a chapter. These sources lived in /tmp for
    # one session, which is cleared at boot - a build input that does not survive
    # a reboot is not a build input.
    source = pathlib.Path(__file__).resolve().parent / "page-sources" / p.name
    if not source.exists():
        sys.exit(f"chapterise: no page source at {source}")
    html = source.read_text()

    if ".sec-no" not in html:
        html = html.replace("</style>", CHAPTER_CSS + "</style>", 1)
    html = html.replace("font-family:var(--serif);font-size:21px;",
                        "font-family:var(--serif);font-size:var(--body);")
    if "--body:21px" not in html:
        html = html.replace("    --measure:27em;", "    --body:21px;\n    --measure:27em;", 1)
    # the breakout band predates the chapter grammar; the page width is derived now
    html = re.sub(r"  @media \(min-width:1440px\)\{\n    :root\{ --figure:64rem \}\n"
                  r"    \.wrap\{ max-width:84rem \}\n  \}\n"
                  r"  @media \(min-width:1800px\)\{\n    :root\{ --figure:94rem \}\n"
                  r"    \.wrap\{ max-width:110rem \}\n  \}\n", "", html)

    keep = extract(html)
    new_main = build_main(spec, keep)

    old = html[html.index("<main"):html.index("</main>") + len("</main>")]
    html = html.replace(old, new_main, 1)

    # the standalone opener now duplicates the chapter opener: fold it in
    m = re.search(r'  <header class="opener">.*?</header>\n\n', html, re.S)
    if m:
        block = m.group(0)
        html = html.replace(block, "", 1)
        title = re.search(r"<h1>(.*?)</h1>", block, re.S)
        dek = re.search(r'<p class="dek">(.*?)</p>', block, re.S)
        if title:
            html = html.replace('<h1 class="page-title"></h1>',
                                f"<h1>{title.group(1).strip()}</h1>", 1)
        if dek:
            html = html.replace('<p class="dek page-dek"></p>',
                                f'<p class="dek">{dek.group(1).strip()}</p>', 1)

    p.write_text(html)
    print(f"{p.name}: chapter {spec['number']} — {len(spec['toc'])} sections, "
          f"{len(keep['figs'])} figures preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
