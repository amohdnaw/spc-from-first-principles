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
  /* ---------- chapter grammar (DESIGN.md §3, added 2026-08-27) ----------
     A level page is a chapter: opener, contents, numbered sections, and an
     outer column holding the section's chart plus the margin apparatus. */
  .ch-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.16em;
    text-transform:uppercase;color:var(--accent);margin:0 0 18px}

  .toc{border-top:1px solid var(--rule-strong);border-bottom:1px solid var(--rule);
    padding:22px 0 24px;margin:8px 0 0}
  .toc-head{display:flex;gap:18px;align-items:baseline;margin:0 0 14px;flex-wrap:wrap}
  .toc-head .est{margin-left:auto}
  .toc ol{list-style:none;margin:0;padding:0;display:grid;
    grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:2px 48px}
  .toc li{display:grid;grid-template-columns:44px 1fr;gap:10px;padding:7px 0;
    border-bottom:1px solid rgba(42,49,56,.55)}
  .toc .n{font-family:var(--mono);font-size:13px;color:var(--accent);padding-top:.35em}
  .toc a{color:var(--ink);text-decoration:none;font-size:19px}
  .toc a:hover{color:var(--accent)}
  .toc .sub{display:block;font-size:15px;color:var(--ink-dim);line-height:1.4}

  .sec-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.14em;
    color:var(--accent);display:block;margin-bottom:10px}
  main h2{font-family:var(--serif);font-size:33px;font-weight:600;line-height:1.12;
    color:var(--ink-bright);margin:0 0 14px;max-width:26em}
  /* the first paragraph of the chapter opens like a book */
  .lead::first-letter{initial-letter:2;font-weight:600;color:var(--ink-bright);margin-right:.08em}

  /* margin apparatus: instrument voice only */
  .side{font-family:var(--mono);font-size:12.5px;line-height:1.6;color:var(--ink-dim);
    display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:0 32px}
  .note{border-left:1px solid var(--rule);padding-left:14px;margin:0 0 26px}
  .note .k{display:block;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;
    font-size:11px;margin-bottom:5px}
  .note .v{color:var(--ink-bright);font-size:21px;font-variant-numeric:tabular-nums}
  .note em{font-family:var(--serif);font-style:italic;font-size:17px;color:var(--ink);
    line-height:1.45;display:block;font-variant-numeric:oldstyle-nums}
  .note.speak{border-left-color:var(--accent)}
  /* an act this section references but is not about */
  .note.watch{display:block;text-decoration:none;color:inherit;border-left-color:var(--accent)}
  .note.watch img{display:block;width:100%;height:auto;margin:8px 0;border:1px solid var(--rule)}
  .note.watch:hover .k{color:var(--ink-bright)}

  /* a player must not eat a whole screen: bound its width by a height budget so the
     16:9 box stays intact instead of letterboxing */
  figure video{max-width:min(100%,calc(68vh * 16 / 9))}

  @media (min-width:1500px){
    :root{ --body:26px }
    /* the spread: argument left, chart and apparatus in the outer column */
    .leaf{display:grid;grid-template-columns:minmax(0,var(--measure)) minmax(0,1fr);
      gap:56px;align-items:start}
    .leaf > .side,.leaf > .leaf-fig{grid-column:2}
    .side{grid-template-columns:1fr;max-width:340px}
    .leaf-fig{margin-top:8px}
    .leaf-fig figure{margin-top:0;max-width:100%}
    .leaf-fig figure + figure{margin-top:40px}
    .leaf > div > p,.leaf > div > .eq{max-width:var(--measure)}
  }
  @media (min-width:1900px){ .leaf{gap:64px} }
"""

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
        ("6.5", "s5", "How good is σ̂?",
         "R̄/d₂ — the bridge from a range to a standard deviation"),
        ("6.6", "s6", "Where the constants come from",
         "d₂, A₂, D₃, D₄ — simulated, never looked up"),
    ],
}


def extract(html: str) -> dict:
    """Pull the blocks that must survive untouched."""
    body = html[html.index("<main"):html.index("</main>")]
    out = {}

    def block(pattern, name, flags=re.S):
        m = re.search(pattern, body, flags)
        if not m:
            sys.exit(f"chapterise: could not find {name}")
        return m.group(0)

    out["eq"] = block(r'<div class="eq">.*?</div>\s*</div>', "equation block")
    # the lab: balanced enough to take by its own closing comment-free shape
    lab_start = body.index('<div class="lab">')
    lab_end = body.index('<aside class="sys">')
    out["lab"] = body[lab_start:lab_end].rstrip()
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
    cls = "note speak" if speak else "note"
    inner = f'<span class="k">{k}</span>'
    if v:
        inner += f'<span class="v">{v}</span>'
    if text:
        inner += f"<em>{text}</em>" if serif else text
    return f'        <div class="{cls}">{inner}</div>'


def build_main(spec: dict, keep: dict) -> str:
    n = spec["number"]
    figs = keep["figs"]

    def fig(name, wide=True):
        f = figs.get(name)
        if f is None:
            sys.exit(f"chapterise: figure {name} missing")
        return re.sub(r'<figure[^>]*>',
                      '<figure class="wide">' if wide else '<figure>', f, count=1)

    toc_items = "\n".join(
        f'          <li><span class="n">{num}</span><a href="#{anchor}">{title}'
        f'<span class="sub">{sub}</span></a></li>'
        for num, anchor, title, sub in spec["toc"])

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
    A('        <div class="side">')
    A(note("before this", text=f'{spec["before"][0]} {spec["before"][1]}'))
    A(note("after this", text=f'{spec["after"][0]} {spec["after"][1]}'))
    A(note("watch instead", text="The whole chapter is also a narrated act — figure 6.1.",
           serif=True))
    A("        </div>")
    A("      </div>")
    A('      <div class="toc">')
    A('        <div class="toc-head"><span class="micro">What this chapter derives</span>'
      f'<span class="micro est">{spec["estimate"]}</span></div>')
    A("        <ol>")
    A(toc_items)
    A("        </ol>")
    A("      </div>")
    A("    </header>")

    # ---- 6.1 -----------------------------------------------------------
    A('    <section id="s1">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.1</span>')
    A("          <h2>A curve that is a claim</h2>")
    A('          <p class="lead">Level 4 told us which distribution every subgroup mean is'
      " drawn from, so long as nothing about the process has changed. Draw that"
      " distribution and you have not drawn a picture of your parts. You have drawn a"
      " claim.</p>")
    A("          <p>The claim is that the process is unchanged — one stable stream, every"
      " subgroup mean pulled from the same curve. That is the null hypothesis, and it is"
      " worth being pedantic about what it is a hypothesis <em>about</em>. Not this part."
      " Not this batch. The process.</p>")
    A("          <p>Everything that follows in this chapter is a consequence of taking that"
      " claim seriously enough to test it.</p>")
    A("        </div>")
    A('        <div class="side">')
    A(note("H₀ — the null", text="The process is unchanged: every subgroup mean is drawn "
           "from one distribution."))
    A(note("not H₀", text="A statement about any individual part. A part is never in or "
           "out of control."))
    A(note("spoken · 0:11", text="“That curve is the null hypothesis. Not an assumption "
           "about the parts, but a claim about the process.”", speak=True, serif=True))
    A("        </div>")
    A('        <div class="leaf-fig">')
    A("      " + fig("21_l2_null_distribution.png", wide=False))
    A("        </div>")
    A("      </div>")
    A("    </section>")

    # ---- 6.2 -----------------------------------------------------------
    A('    <section id="s2">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.2</span>')
    A("          <h2>Pricing ±3σ</h2>")
    A("          <p>Put a pair of limits on that curve and sweep them outward from the"
      " centre. At every position the question has an exact answer: how much of the"
      " distribution is inside? Not looked up in a table — it is the integral of the curve"
      " between the limits, evaluated as they move.</p>")
    A("          <p>Stop at three sigma and the answer is 99.73%. Nobody chose that number."
      " It is simply what ±3σ is worth, and everything the process should ever do lives"
      " inside it.</p>")
    A("      " + keep["eq"])
    A("        </div>")
    A('        <div class="side">')
    A(note("in-control area", v="99.73 %"))
    A(note("outside", v="0.27 %"))
    A(note("Φ", text="The standard normal CDF, computed from erf — not a table."))
    A(note("spoken · 0:38", text="“Ninety-nine point seven three percent. Nobody chose "
           "that number.”", speak=True, serif=True))
    A("        </div>")
    A("      </div>")
    A("  " + keep["lab"])
    A("      " + fig("Level06.mp4"))
    A("    </section>")

    # ---- 6.3 -----------------------------------------------------------
    A('    <section id="s3">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.3</span>')
    A("          <h2>Where the price hides</h2>")
    A("          <p>The whole of the rest — the part that makes the chart worth running —"
      " is out in the tails, and at the scale of the last figure you cannot see it at all."
      " So stretch the vertical axis and let the tails grow. The peak goes straight out of"
      " frame, which is the point: the tails are about seventy times smaller than anything"
      " else on the chart.</p>")
    A("          <p>Each wing is one tenth of one percent of everything, and there are two"
      " of them. Together they are the tail integral, and it has a closed form: 0.0027."
      " Invert it and the bet is priced — one false alarm in 370 subgroups.</p>")
    A("        </div>")
    A('        <div class="side">')
    A(note("each wing", v="0.135 %"))
    A(note("both wings", v="0.0027"))
    A(note("false alarm", v="1 in 370"))
    A(note("axis stretch", v="×70", text="needed before the tails are visible at all."))
    A("        </div>")
    A("      </div>")
    A("    </section>")

    # ---- 6.4 -----------------------------------------------------------
    A('    <section id="s4">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.4</span>')
    A("          <h2>The chart is that test, repeated</h2>")
    A("          <p>A control chart is not a new idea on top of this one. It is the same"
      " test, run again on every subgroup, forever. The limits are the boundary we just"
      " drew, turned on its side. Every point inside is the process agreeing with the null"
      " hypothesis, and that is what boring looks like. Boring is the goal.</p>")
    A("          <p>Then one point steps outside — say 4.1σ above the centre line, where"
      " the null allows one point in 370. That point is not a bad part, and scrapping it"
      " changes nothing. It is evidence against the hypothesis that nothing changed. The"
      " correct response is to go and find what did.</p>")
    A("      " + keep["sys"])
    A("        </div>")
    A('        <div class="side">')
    A(note("the violation", v="4.1 σ"))
    A(note("allowed by H₀", v="1 in 370"))
    A(note("spoken · 2:09", text="“This is not a bad part, and scrapping it changes "
           "nothing. It is evidence against the hypothesis that nothing changed.”",
           speak=True, serif=True))
    A("        </div>")
    A("      </div>")
    A("    </section>")

    # ---- 6.5 -----------------------------------------------------------
    A('    <section id="s5">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.5</span>')
    A("          <h2>How good is σ̂?</h2>")
    A("          <p>Everything so far assumed we know σ. On a real line we do not — we"
      " estimate it, usually from the average range of the subgroups divided by a"
      " constant. That estimate is unbiased on average, but a chart built from twenty-five"
      " subgroups carries real fuzz in its own limits, which is why Phase I needs enough"
      " data before the limits mean anything.</p>")
    A("        </div>")
    A('        <div class="side">')
    A(note("σ̂ from ranges", v="R̄ / d₂"))
    A(note("at 25 subgroups", v="±0.075 σ", text="spread in the estimate itself."))
    A("        </div>")
    A('        <div class="leaf-fig">')
    A("      " + fig("22_l2_rbar_plumbing.png", wide=False))
    A("        </div>")
    A("      </div>")
    A("    </section>")

    # ---- 6.6 -----------------------------------------------------------
    A('    <section id="s6">')
    A('      <div class="leaf">')
    A("        <div>")
    A('          <span class="sec-no">6.6</span>')
    A("          <h2>Where the constants come from</h2>")
    A("          <p>d₂ is the expected range of n standard normals. A₂, D₃ and D₄ are the"
      " numbers printed on every shop-floor chart form. None of them is looked up here:"
      " each one is simulated, and then checked against the published table in a test"
      " suite. If the simulation and the table ever disagreed, the test would fail rather"
      " than the page quietly lying.</p>")
    A("        </div>")
    A('        <div class="side">')
    A(note("d₂ at n = 5", v="2.326"))
    A(note("A₂ at n = 5", v="0.577"))
    A(note("simulated", v="400 000", text="subgroups, checked against AIAG Table B."))
    A('        <a class="note watch" href="spc-lab/media/videos/scenes2/1080p60/ConstantsAct.mp4">'
      '<span class="k">watch · figure 6.4</span>'
      '<img src="posters/constants.jpg" alt="Where the constants come from" loading="lazy">'
      "<em>Where the constants come from — d₂ simulated from 400 000 subgroups, landing on "
      "the published value.</em></a>")
    A("        </div>")
    A("      </div>")
    A('      <div class="figpair">')
    A("      " + fig("01_d2.png", wide=False))
    A("      " + fig("02_A2_D3_D4.png", wide=False))
    A("      </div>")
    A("    </section>")

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
