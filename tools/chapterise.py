#!/usr/bin/env python3
"""Turn a level page into a textbook chapter (DESIGN.md §3, 'The level page is a chapter').

Rebuilds <main> from a chapter spec while preserving, byte for byte, the blocks that
already carry verified content: the KaTeX equation, the interactive lab, the SYS note,
every figure, and the next-level link. Nothing is re-typeset or re-rendered here.

    python3 tools/chapterise.py level-06.html
"""
from __future__ import annotations
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
  .toc-chain{font-family:var(--serif);font-size:17px;color:var(--ink-dim);margin:14px 0 0;
    display:flex;flex-wrap:wrap;gap:0 8px;align-items:baseline}
  .toc-chain .sep{color:var(--rule-strong);padding:0 4px}
  .toc .sub{display:block;font-size:15px;color:var(--ink-dim);line-height:1.4}

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
  .lead::first-letter{initial-letter:2;font-weight:600;color:var(--ink-bright);margin-right:.08em}

  /* margin notes: instrument voice, level with the paragraph they annotate.
     Below the margin breakpoint they simply follow the prose at measure width. */
  .note{display:block;font-family:var(--mono);font-size:12.5px;line-height:1.6;
    color:var(--ink-dim);border-left:1px solid var(--rule);padding-left:14px;
    margin:0 0 26px;max-width:var(--measure);text-indent:0}
  .note .k{display:block;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;
    font-size:11px;margin-bottom:5px}
  .note .v{color:var(--ink-bright);font-size:21px;font-variant-numeric:tabular-nums}
  .note em{font-family:var(--serif);font-style:italic;font-size:17px;color:var(--ink);
    line-height:1.45;display:block;font-variant-numeric:oldstyle-nums}
  .note.speak{border-left-color:var(--accent)}
  .note.data .row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;
    align-items:baseline;padding:3px 0;border-bottom:1px solid rgba(42,49,56,.6);min-width:0}
  .note.data .row:last-child{border-bottom:0}
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
  /* a margin figure - Tufte's one case for a figure outside the main flow */
  .note.watch video{display:block;width:100%;height:auto;margin:8px 0;border:1px solid var(--rule)}
  .note.watch:hover .k{color:var(--ink-bright)}

  /* figures take the whole text block and share its left edge */
  figure,.figpair{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  figure video{max-width:min(100%,calc(68vh * 16 / 9))}

  @media (min-width:1500px){
    :root{ --body:26px; --marg:340px; }
    /* the note floats into the margin at its position in the flow. This is the
       whole trick: no row of its own, so no hole beside it. */
    /* tufte-css's mechanism: a negative right margin pulls the float out of the
       text column so it consumes no horizontal space there. Without it the float
       lives inside the 702px paragraph and shortens every line beside it, which
       destroys the measure the whole design is built on. */
    .note{float:right;clear:right;width:var(--marg);max-width:var(--marg);
      margin:0 calc(-1 * (var(--marg) + var(--marg-gap))) 26px 0;
      position:relative;z-index:1}
    /* the demoted act carries a player: it stays in the flow at block width */
    .note.nofloat{float:none;width:auto;max-width:var(--measure);margin-top:34px}
    .leaf > div::after{content:"";display:block;clear:both}
  }
"""

def tex(latex: str) -> str:
    """Inline maths, rendered by tools/typeset.mjs.

    EB Garamond has no combining hat and no subscript digits, so a literal
    "sigma-hat" arrives on screen as sigma followed by a stray caret, and a
    subscript falls back mid-word to another font. Anything mathematical inside
    serif prose goes through KaTeX instead of hoping for the glyph.
    """
    return '<span class="tex" data-tex="' + latex + '"></span>'


# ---------------------------------------------------------------- chapter specs
LEVEL6 = {
    "number": 6,
    "word": "six",
    "before": ("Level 4 — the average is predictable.", "You need σ⁄√n to be here."),
    "after": ("Level 8 — capability.", "In control is not the same as good enough."),
    "estimate": "6 sections · 1 interactive · 2 acts · ~9 min read",
    "toc": [
        ("6.1", "s1", "A curve that is a claim",
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
    ],
}


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
    out["lab"] = take_div(body, body.index('<div class="lab">'))
    out["sys"] = block(r'<aside class="sys">.*?</aside>', "sys note")
    out["next"] = block(r'<a class="next".*?</a>', "next link")

    figs = {}
    for m in re.finditer(r'<figure[^>]*>.*?</figure>', body, re.S):
        f = m.group(0)
        src = re.search(r'(?:<img src|<source src)="([^"]+)"', f)
        if src:
            figs[src.group(1).split("/")[-1]] = f
    out["figs"] = figs
    return out


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


def build_main(spec: dict, keep: dict) -> str:
    """Assemble the chapter.

    Note placement follows the book convention: a margin note is emitted
    immediately after the paragraph it annotates, so the float lands level with
    its referent. Figures sit in the flow at full text-block width.
    """
    n = spec["number"]
    figs = keep["figs"]

    def fig(name):
        f = figs.get(name)
        if f is None:
            sys.exit(f"chapterise: figure {name} missing")
        return re.sub(r"<figure[^>]*>", "<figure>", f, count=1)

    toc_items = "\n".join(
        f'          <li><span class="n">{num}</span><a href="#{anchor}">{title}'
        f'<span class="sub">{sub}</span></a></li>'
        for num, anchor, title, sub in spec["toc"])

    P = "          "   # prose indent
    L = []
    A = L.append
    A("  <main>")

    # ---- chapter opener -------------------------------------------------
    A('    <header class="ch">')
    A('      <div class="leaf">')
    A("        <div>")
    A(f'          <p class="ch-no">Level {n} · chapter {spec["word"]}</p>')
    A('          <h1 class="page-title"></h1>')
    A('          <p class="dek page-dek"></p>')
    A("        </div>")
    A("      </div>")
    A('      <div class="toc">')
    A('        <div class="toc-head"><span class="micro">What this chapter derives</span>'
      f'<span class="micro est">{spec["estimate"]}</span></div>')
    A('        <p class="toc-chain"><span class="micro">after</span> '
      f'{spec["before"][0].rstrip(".")}<span class="sep">·</span>'
      f'<span class="micro">leads to</span> {spec["after"][0].rstrip(".")}</p>')
    A("        <ol>")
    A(toc_items)
    A("        </ol>")
    A("      </div>")
    A("    </header>")

    def section(anchor, num, title, blocks):
        A(f'    <section id="{anchor}">')
        A('      <div class="leaf">')
        A("        <div>")
        A(f'          <span class="sec-no">{num}</span>')
        A(f"          <h2>{title}</h2>")
        for b in blocks:
            A(b)
        A("        </div>")
        A("      </div>")
        A("    </section>")

    def para(text, *notes, lead=False):
        """A paragraph, with its margin notes injected after the first sentence."""
        cls = ' class="lead"' if lead else ""
        if notes:
            m = re.search(r"(?<=[.?!])\s", text)
            cut = m.end() if m else len(text)
            text = text[:cut] + "".join(notes) + text[cut:]
        return f"{P}<p{cls}>{text}</p>"

    # ---- 6.1 -----------------------------------------------------------
    section("s1", "6.1", "A curve that is a claim", [
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
        "      " + fig("21_l2_null_distribution.png"),
    ])

    # ---- 6.2 -----------------------------------------------------------
    section("s2", "6.2", "Pricing ±3σ", [
        para("Put a pair of limits on that curve and sweep them outward from the centre. At"
             " every position the question has an exact answer: how much of the distribution"
             " is inside? Not looked up in a table — it is the integral of the curve between"
             " the limits, evaluated as they move.",
             datanote(("in-control", "99.73 %"), ("outside", "0.27 %"),
                      k="what three sigma is worth")),
        para("Stop at three sigma and the answer is 99.73%. Nobody chose that number. It is"
             " simply what ±3σ is worth, and everything the process should ever do lives"
             " inside it.",
             note("Φ", text="The standard normal CDF, computed from erf — not a table."),
             note("spoken · 0:38", text="“Ninety-nine point seven three percent. Nobody "
                  "chose that number.”", speak=True, serif=True)),
        "      " + keep["eq"],
        "  " + keep["lab"],
        "      " + fig("Level06.mp4"),
    ])

    # ---- 6.3 -----------------------------------------------------------
    section("s3", "6.3", "Where the price hides", [
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
    ])

    # ---- 6.4 -----------------------------------------------------------
    section("s4", "6.4", "The chart is that test, repeated", [
        para("A control chart is not a new idea on top of this one. It is the same test, run"
             " again on every subgroup, forever. The limits are the boundary we just drew,"
             " turned on its side. Every point inside is the process agreeing with the null"
             " hypothesis, and that is what boring looks like. Boring is the goal.",
             note("allowed by H₀", v="1 in 370")),
        para("Then one point steps outside — say 4.1σ above the centre line, where the null"
             " allows one point in 370. That point is not a bad part, and scrapping it changes"
             " nothing. It is evidence against the hypothesis that nothing changed. The"
             " correct response is to go and find what did.",
             note("the violation", v="4.1 σ"),
             note("spoken · 2:09", text="“This is not a bad part, and scrapping it changes "
                  "nothing. It is evidence against the hypothesis that nothing changed.”",
                  speak=True, serif=True)),
        "      " + keep["sys"],
    ])

    # ---- 6.5 -----------------------------------------------------------
    section("s5", "6.5", "How good is the σ estimate?", [
        para("Everything so far assumed we know σ. On a real line we do not — we estimate it,"
             " usually from the average range of the subgroups divided by a constant. That"
             " estimate is unbiased on average, but a chart built from twenty-five subgroups"
             " carries real fuzz in its own limits, which is why Phase I needs enough data"
             " before the limits mean anything.",
             datanote(("sigma-hat from ranges", "R̄ / d₂"),
                      ("at 25 subgroups", "±0.075 σ", "spread in the estimate itself"),
                      k="estimating sigma")),
        "      " + fig("22_l2_rbar_plumbing.png"),
    ])

    # ---- 6.6 -----------------------------------------------------------
    section("s6", "6.6", "Where the constants come from", [
        para(tex(r"d_2") + " is the expected range of n standard normals. "
             + tex(r"A_2") + ", " + tex(r"D_3") + " and " + tex(r"D_4") + " are the numbers"
             " printed on every shop-floor chart form. None of them is looked up here: each"
             " one is simulated, and then checked against the published table in a test suite."
             " If the simulation and the table ever disagreed, the test would fail rather than"
             " the page quietly lying.",
             datanote(("d₂ at n = 5", "2.326"), ("A₂ at n = 5", "0.577"),
                      ("simulated", "400 000", "subgroups, checked against AIAG Table B"),
                      k="the constants")),
        '        <div class="note watch nofloat"><span class="k">watch · figure 6.4</span>'
        '<video controls playsinline preload="none" poster="posters/constants.jpg">'
        '<source src="spc-lab/media/videos/scenes2/1080p60/ConstantsAct.mp4" type="video/mp4">'
        '<track kind="captions" src="captions/constants.vtt" srclang="en" label="English" default>'
        "</video><em>Where the constants come from — " + tex(r"d_2") + " simulated from 400 000 subgroups, "
        "landing on the published value.</em></div>",
        '      <div class="figpair">',
        "      " + fig("01_d2.png"),
        "      " + fig("02_A2_D3_D4.png"),
        "      </div>",
    ])

    A("    " + keep["next"])
    A("  </main>")
    return "\n".join(L)


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = pathlib.Path(sys.argv[1])
    html = p.read_text()

    if ".sec-no" not in html:
        html = html.replace("</style>", CHAPTER_CSS + "</style>", 1)
    # body size becomes a token so the wide-viewport step can move it
    html = html.replace("font-family:var(--serif);font-size:21px;",
                        "font-family:var(--serif);font-size:var(--body);")
    if "--body:21px" not in html:
        html = html.replace("    --measure:27em;", "    --body:21px;\n    --measure:27em;", 1)

    keep = extract(html)
    spec = LEVEL6
    new_main = build_main(spec, keep)

    # carry the existing headline and dek into the opener
    old = html[html.index("<main"):html.index("</main>") + len("</main>")]
    head = html[:html.index("<main")]
    title = re.search(r'<h1[^>]*>(.*?)</h1>', head, re.S)
    dek = re.search(r'<p class="dek"[^>]*>(.*?)</p>', head, re.S)
    if title:
        new_main = new_main.replace('<h1 class="page-title"></h1>',
                                    f'<h1>{title.group(1).strip()}</h1>')
    if dek:
        new_main = new_main.replace('<p class="dek page-dek"></p>',
                                    f'<p class="dek">{dek.group(1).strip()}</p>')

    html = html.replace(old, new_main, 1)
    p.write_text(html)
    print(f"{p.name}: rebuilt as a chapter — {len(spec['toc'])} sections, "
          f"{len(keep['figs'])} figures preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
