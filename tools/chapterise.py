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

  /* A referenced act, collapsed. Closed it is a poster strip; open it is a player
     at the full text-block width. The previous version was a 340px margin card,
     which measured 323x182 on screen - not a player, a thumbnail with controls. */
  .act{border-top:1px solid var(--rule);margin:40px 0 0}
  .act > summary{display:flex;gap:18px;align-items:center;cursor:pointer;
    padding:16px 0;list-style:none}
  .act > summary::-webkit-details-marker{display:none}
  .act > summary::marker{content:""}
  .act > summary:hover .k{color:var(--ink-bright)}
  .act .thumb{width:180px;height:auto;flex:none;display:block;border:1px solid var(--rule)}
  .act .meta{min-width:0}
  .act .k{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);display:block;margin-bottom:5px}
  .act .cap{font-size:17px;line-height:1.45;color:var(--ink-dim);display:block;
    max-width:52ch;text-wrap:pretty}
  .act .cue{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-dim);margin-left:auto;flex:none;white-space:nowrap}
  .act[open] > summary .thumb{display:none}
  .act[open] > summary .cue{color:var(--accent)}
  .act video{display:block;width:100%;height:auto;background:var(--ground);
    margin:0 0 8px;max-width:min(100%,calc(68vh * 16 / 9))}
  @media(max-width:640px){ .act > summary{flex-wrap:wrap} .act .thumb{width:120px} }
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
    /* a note that must not float (it holds something wide) */
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
                    "      " + K["fig"]("21_l2_null_distribution.png"),
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
                         " inside it.",
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
                    "      " + K["fig"]("22_l2_rbar_plumbing.png"),
        ]),
        ("s6", "6.6", "Where the constants come from", [
                    para(tex(r"d_2") + " is the expected range of n standard normals. "
                         + tex(r"A_2") + ", " + tex(r"D_3") + " and " + tex(r"D_4") + " are the numbers"
                         " printed on every shop-floor chart form. None of them is looked up here: each"
                         " one is simulated, and then checked against the published table in a test suite."
                         " If the simulation and the table ever disagreed, the test would fail rather than"
                         " the page quietly lying.",
                         datanote(("d₂ at n = 5", "2.326"), ("A₂ at n = 5", "0.577"),
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
                 datanote(("divisor", "n − 1"), k="why not n")),
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
            "      " + K["fig"]("11_l1_dice_to_bell.png"),
        ]),
        ("s3", "4.3", "The law", [
            para("Two numbers, measured separately, agree to three decimals: the spread of the"
                 " averages, and one die's spread divided by the root of the count. That agreement"
                 " is the law, and it is the reason a control chart can exist at all.",
                 datanote(("agreement", "3 decimals"), k="measured, not assumed")),
            "      " + K["eq"],
        ]),
        ("s4", "4.4", "What averaging buys", [
            para("Put subgroup size along the bottom and the spread of the mean up the side, with"
                 " sigma set to one, then walk the subgroup size from one to twenty-five. At"
                 " twenty-five parts the spread of the mean is a fifth of one part's spread — the"
                 " root is doing all the work.",
                 datanote(("2nd part buys", "half the error"), ("25th part buys", "0.004 σ"),
                          k="the shape of the deal")),
            para("But look at the shape of what you are buying. The second part halves your"
                 " uncertainty; the twenty-fifth buys four thousandths of a sigma. Averaging is"
                 " cheap at the start and almost free of value at the end, which is why subgroups"
                 " of four and five are everywhere and subgroups of fifty are not."),
            para("It is also why a control chart plots subgroup means rather than parts: a shift"
                 " that hides inside single measurements moves a mean far enough to see.",
                 note("spoken · 2:04", text="“A shift that hides inside single parts moves a mean"
                      " far enough to see.”", speak=True, serif=True)),
            "      " + K["sys"],
            "      " + K["fig"]("12_l1_sqrt_n.png"),
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
            "      " + K["fig"]("31_l3_two_voices.png"),
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
                 datanote(("Cpk", "0.80"), ("leak", "8 198 ppm"), ("in plain counting", "1 in 122"),
                          k="what the drift costs")),
            para("That leak is 8,198 parts per million, and at this scale you cannot see it. So"
                 " stretch the vertical axis until it is visible: the peak leaves the frame, and"
                 " the tail is what we came for. The index itself is only the near gap, measured"
                 " in three sigmas.",
                 note("spoken · 1:36", text="“8,198 parts per million is the same sentence as 1 in"
                      " 122 parts.”", speak=True, serif=True)),
        ]),
        ("s4", "8.4", "Every Cpk is a promise about defect rate", [
            para("Parts per million up the side, on a logarithmic scale, because it spans five"
                 " decades. Walk Cpk upward from 0.6 and read the promise off the curve. Every"
                 " figure here is computed at render time by the same function the test suite"
                 " checks — nothing is read off a table.",
                 datanote(("Cpk 1.00", "1 350 ppm"), ("Cpk 1.33", "33.04 ppm"),
                          ("Cpk 1.67", "0.27 ppm"), k="the promise")),
            para("Which is why the difference between 1.33 and 1.67 is not a rounding argument. It"
                 " is two orders of magnitude of scrap. A capability index is a defect rate"
                 " wearing a friendlier number."),
            K["watch"]("SPCGallery.mp4", "gallery", "figure 8.4",
                       "The overview act: a chart and its limits drawing themselves from the data,"
                       " and where capability geometry sits among them."),
            "      " + K["sys"],
            "      " + K["fig"]("32_l3_cpk_to_ppm.png"),
        ]),
    ]


def chapter_09(K):
    return [
        ("s1", "9.1", "The most expensive failure mode", [
            para("Slow drift is the most expensive failure mode in manufacturing, because every"
                 " single measurement of it looks acceptable. Here is a Shewhart chart with limits"
                 " at ±3σ, which buys one false alarm in 370 subgroups.",
                 datanote(("false alarm budget", "1 in 370"), ("drift rate", "0.06 σ / subgroup"),
                          k="the setup"), lead=True),
            para("The first twenty subgroups are noise around the target. Then the mean starts"
                 " walking at 0.06 sigma per subgroup — slow enough that no single measurement"
                 " looks wrong, and the chart carries on saying nothing."),
            "      " + K["fig"]("Level09.mp4"),
        ]),
        ("s2", "9.2", "A chart with no memory", [
            para("The first violation lands at subgroup 64. That is 43 subgroups after the drift"
                 " began, by which time the mean has moved 2.6 sigma and every part in between was"
                 " made by a process nobody knew had changed.",
                 datanote(("drift starts", "subgroup 20"), ("first alarm", "subgroup 64"),
                          ("mean moved by then", "2.6 σ"), k="what it cost")),
            para("Each point was judged on its own and then forgotten. That is the whole weakness,"
                 " and it is not a tuning problem: the chart has no memory.",
                 note("spoken · 1:12", text="“Each point was judged on its own and then forgotten."
                      " That is the whole weakness.”", speak=True, serif=True)),
        ]),
        ("s3", "9.3", "A statistic that remembers", [
            para("Same process, same data, same false-alarm budget — and a statistic that"
                 " remembers. Each new subgroup gets a fifth of the weight and the running"
                 " statistic keeps the rest: with lambda at 0.2 that is one part new and four"
                 " parts memory.",
                 datanote(("lambda", "0.20"), ("weighting", "1 new : 4 memory"),
                          k="how much it keeps")),
            para("Its limits are not ±3. They are calibrated by simulation until this chart cries"
                 " wolf exactly as rarely as the last one — one alarm in 370 quiet subgroups"
                 " against 370, so the comparison that follows is fair."),
            "      " + K["eq"],
            "      " + K["fig"]("EWMAMemory.mp4"),
        ]),
        ("s4", "9.4", "The same eighty subgroups again", [
            para("While the process is quiet the statistic wanders near zero, because new noise"
                 " keeps cancelling old noise. Once the drift starts the noise still cancels but"
                 " the drift does not: it is the same direction every time, so it adds up.",
                 datanote(("crosses at", "subgroup 34"), ("mean off by", "0.8 σ"),
                          ("raw point there", "+2.48 σ"), k="caught early")),
            para("It crosses the limit at subgroup 34, with the mean only 0.8 sigma off and the raw"
                 " measurement sitting at +2.48 sigma — a number no Shewhart chart would look at"
                 " twice. The other chart waited until subgroup 64, thirty subgroups later."),
            "      " + K["fig"]("42_l4_race.png"),
        ]),
        ("s5", "9.5", "One drift is an anecdote", [
            para("That is one drift. Run thousands of them and the average wait to detect a one"
                 " sigma shift comes out at 44 subgroups for the Shewhart rule and 10 for this"
                 " one. Divide them: 4.4 times sooner, bought with no extra false alarms at all.",
                 datanote(("Shewhart ARL", "44"), ("EWMA ARL", "10"), ("speed-up", "4.4×"),
                          k="thousands of drifts")),
            para("That trade — sensitivity bought without paying in false alarms — is the whole of"
                 " detection theory.",
                 note("spoken · 3:41", text="“4.4 times sooner, bought with no extra false alarms"
                      " at all.”", speak=True, serif=True)),
            "      " + K["sys"],
            "      " + K["fig"]("41_l4_arl.png"),
        ]),
        ("s6", "9.6", "Rules that read the run", [
            para("A limit is not the only evidence on a chart. Four more rules read the run rather"
                 " than the point — two of three beyond 2σ, four of five beyond 1σ, eight in a row"
                 " on one side of centre — and each of them catches a pattern that no single point"
                 " would fail.",
                 datanote(("rules", "4"), ("what they read", "the run"), k="beyond one point")),
            para("Every rule you add buys sensitivity and pays in false alarms, and the arithmetic"
                 " of that trade is Level 7's subject rather than this one's."),
            K["watch"]("WERules.mp4", "werules", "figure 9.5",
                       "The four rules firing on a series built to trip all of them."),
            "      " + K["fig"]("07_western_electric.png"),
        ]),
    ]


CHAPTERS = {
    "level-06.html": {
        "number": 6, "word": "six",
        "before": "Level 4 — the average is predictable",
        "after": "Level 8 — capability",
        "estimate": "6 sections · 1 interactive · 2 acts · ~9 min read",
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
                 tex(r"d_2, A_2, D_3, D_4") + " — simulated, never looked up")],
        "sections": chapter_06,
    },
    "level-03.html": {
        "number": 3, "word": "three",
        "before": "Level 2 — chance, not yet written",
        "after": "Level 4 — the average is predictable",
        "estimate": "5 sections · 1 act · ~7 min read",
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
    },
    "level-04.html": {
        "number": 4, "word": "four",
        "before": "Level 3 — centre and spread",
        "after": "Level 6 — limits are a hypothesis test",
        "estimate": "4 sections · 1 act · ~6 min read",
        "toc": [("4.1", "s1", "One part tells you nothing",
                 "one die, ten rolls, then ten thousand"),
                ("4.2", "s2", "Averaging makes a shape",
                 "a flat die becomes a bell by averaging alone"),
                ("4.3", "s3", "The law",
                 "two numbers agreeing to three decimals"),
                ("4.4", "s4", "What averaging buys",
                 "why subgroups of four and five, and never fifty")],
        "sections": chapter_04,
    },
    "level-08.html": {
        "number": 8, "word": "eight",
        "before": "Level 7 — evidence and decisions, not yet written",
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
    },
    "level-09.html": {
        "number": 9, "word": "nine",
        "before": "Level 8 — capability",
        "after": "Level 10 — counting, not measuring, not yet written",
        "estimate": "6 sections · 3 acts · ~9 min read",
        "toc": [("9.1", "s1", "The most expensive failure mode",
                 "every single measurement of a drift looks acceptable"),
                ("9.2", "s2", "A chart with no memory",
                 "43 subgroups late, and 2.6 sigma of movement"),
                ("9.3", "s3", "A statistic that remembers",
                 "one part new, four parts memory, same alarm budget"),
                ("9.4", "s4", "The same eighty subgroups again",
                 "caught at 34, with the mean only 0.8 sigma off"),
                ("9.5", "s5", "One drift is an anecdote",
                 "44 subgroups against 10, and what the trade means"),
                ("9.6", "s6", "Rules that read the run",
                 "four rules that judge the series, not the point")],
        "sections": chapter_09,
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
        return re.sub(r"<figure[^>]*>", "<figure>", f, count=1)

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
                f'          <img class="thumb" src="posters/{poster}.jpg" alt="" loading="lazy">\n'
                '          <span class="meta">'
                f'<span class="k">{label}</span>'
                f'<span class="cap">{caption}</span></span>\n'
                f'          <span class="cue">play{" · " + dur.group(1) if dur else ""}</span>\n'
                '        </summary>\n'
                '        <video controls playsinline preload="none" '
                f'poster="posters/{poster}.jpg">\n'
                f'          <source src="{path}" type="video/mp4">\n'
                f'          <track kind="captions" src="captions/{poster}.vtt" srclang="en" '
                'label="English" default>\n'
                '        </video>\n'
                '      </details>')

    K = {**keep, "fig": fig, "watch": watch}

    toc_items = "\n".join(
        f'          <li><span class="n">{num}</span><a href="#{anchor}">{title}'
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

    for anchor, num, title, blocks in spec["sections"](K):
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

    A("    " + keep["next"])
    A("  </main>")
    return "\n".join(L)


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = pathlib.Path(sys.argv[1])
    spec = CHAPTERS.get(p.name)
    if spec is None:
        sys.exit(f"chapterise: no chapter defined for {p.name} "
                 f"(have: {', '.join(sorted(CHAPTERS))})")
    html = p.read_text()

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
