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
    ]


def chapter_11(K):
    from spclab.relationships import (
        ADJ_WITH_NOISE, CURVED_FIT, CURVED_RUN, FIT, GAUGE, HALF_CI, HALF_PI,
        MSA_SITE, OPERATORS, PARTS, R2_PLAIN, R2_WITH_NOISE, REPEATS,
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
            para("The line is not drawn by eye and it is not fitted by iteration: it is"
                 " the slope that minimises the sum of squared residuals, and the closed"
                 " form lands exactly at that minimum rather than near it.",
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
                 datanote((f"at {X0:.0f} m/min", ""),
                          ("the mean response", f"±{HALF_CI:.3f}"),
                          ("one new reading", f"±{HALF_PI:.3f}"),
                          ("ratio", f"×{HALF_PI/HALF_CI:.2f}"),
                          k="95 % half-widths"), lead=True),
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
                 " boundary rather than summarising it badly. It continues at the"
                 f' <a href="{MSA_SITE}" target="_blank" rel="noopener">MSA platform</a>,'
                 " which runs these studies; the sibling curriculum that explains them"
                 " the way this one explains control charts is not written yet.",
                 note("the seam", text="This site never teaches gauge acceptance, and "
                      "the MSA side never teaches control limits. One link each way.")),
        ]),
    ]


def chapter_10(K):
    from spclab.counting import (
        C_AT, C_BAR, DISPERSION_BATCHED, DISPERSION_CLEAN, MISCLASS, NP_THRESHOLD,
        N_CONST, N_FOR_LCL, P_AT_CONST, P_BAR, TAIL, UNIT_DEFECT, UNIT_ITEM,
        CHART_TABLE,
    )
    folklore = int(round(5.0 / P_BAR))
    return [
        ("s1", "10.1", "The spread is not a free parameter", [
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
            para("There is a threshold and it is exact. The lower limit clears zero only"
                 " while " + tex(r"n\bar{p} > k^{2}(1-\bar{p})") + f", which at three"
                 f" sigma is {NP_THRESHOLD:.2f}. At four per cent defective that means"
                 f" subgroups of {N_FOR_LCL} — not the {folklore} the familiar"
                 " “np̄ ≥ 5” rule of thumb allows.",
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
            para(f"The true probability is {TAIL['ratio']:.1f} times what the normal"
                 " approximation reports. Quoting a normal-based ppm on count data is"
                 " therefore not a rounding error — it understates the risk by a factor"
                 " you would notice. The approximation improves as the counts grow; it"
                 " is wrong where attribute data usually lives.",
                 note("so what to do", text="Use the exact tail. It is one incomplete "
                      "beta, and this site already had one for Level 5.")),
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
                 " sits almost entirely inside them.",
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
                 f" instead of {ARL0_ONE_RULE:.0f}. That figure was published in 1987 as"
                 f" {CHAMP_WOODALL_ARL0}, and the simulation here was not told about it"
                 " — it reproduces it from the rules themselves.",
                 note("corroboration", text="Champ &amp; Woodall, 1987. Agreement with "
                      "a number derived elsewhere is worth more than internal "
                      "consistency.")),
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
            para("An interval is the estimate plus and minus a margin. Build one from"
                 " every sample and it is the <em>interval</em> that moves; the truth"
                 " stays where it is. So the way to check a confidence level is not to"
                 " argue about it — it is to count.",
                 note("not the parameter", text="The interval varies from sample to "
                      "sample. The mean it is chasing does not."), lead=True),
            para("Draw an interval per sample and mark the ones that missed. On a shop"
                 " floor you would never know which kind you were holding, and that is"
                 " precisely the point: the confidence level is a property of the"
                 " procedure, not of the interval in your hand.",
                 datanote(("intervals drawn", "40"),
                          ("nominal", f"{CONF*100:.0f} %"),
                          ("counted", f"{COVER_T[n]*100:.1f} %"),
                          k=f"samples of {n}, {nc(chr(116))} quantile")),
            "      " + K["fig"]("l05_1_coverage.png"),
            "      " + K["fig"]("Level05.mp4"),
        ]),
        ("s3", "5.3", "Why t exists", [
            para("Here is where a textbook quietly cheats. The margin needs σ, and σ is"
                 " no better known than the mean — it is estimated from the same five"
                 " parts. Use 1.96 anyway and count what you actually get.",
                 datanote(*[(f"{nc(chr(110))} = {k}", f"{COVER_Z[k]*100:.1f} %") for k in SIZES],
                          k="a “95 %” interval built with 1.96"), lead=True),
            para(f"At {n} parts the interval that advertises ninety-five delivers"
                 f" {COVER_Z[n]*100:.1f}. The margin is too narrow because <em>s</em> is"
                 " itself uncertain, and a quantile taken from a normal curve does not"
                 " know that. Replace it with one that knows how few parts it was built"
                 " from.",
                 note("the substitution", text="Not a correction bolted on. It is what "
                      "the arithmetic gives when the spread is estimated too.")),
            "      " + K["eq"],
            para(f"At {n} parts that quantile is {T_AT[n]:.3f} rather than 1.960, and"
                 f" the count lands where it belongs — at every sample size, not just"
                 f" the comfortable ones.",
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
            para("Level 1 ended with a shape nobody chose. Putting a number on that shape"
                 " means saying something like “99.73 % inside”, and before this curriculum"
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
                 " quantity divided by the number of flips, so the same hundredfold"
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
                 " The variance is exactly doubled and stays doubled — the spread the"
                 " customer receives is √2 times wider, bought with a full shift of"
                 " conscientious work."),
            "      " + K["eq"],
            para("Noise is not a signal, and answering it is how you add variation rather"
                 " than remove it. Everything from here — the limits, the capability"
                 " arithmetic, the detection theory — is machinery for knowing which kind you"
                 " are looking at before you touch anything.",
                 note("spoken · 2:41", text="“Answering it is how you add variation rather"
                      " than remove it.”", speak=True, serif=True)),
            "      " + K["fig"]("l01_2_tampering.png"),
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
            "      " + K["fig"]("l04_2_sqrt_n.png"),
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
            "      " + K["fig"]("l08_2_cpk_to_ppm.png"),
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
            "      " + K["fig"]("l09_2_race.png"),
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
            "      " + K["fig"]("l09_1_arl.png"),
        ]),
    ]


CHAPTERS = {
    "level-01.html": {
        "number": 1, "word": "one",
        "before": "nothing — this is where the curriculum starts",
        "after": "Level 2 — chance, and what a percentage claims",
        "estimate": "5 sections · 1 act · ~7 min read",
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
    },
    "level-02.html": {
        "number": 2, "word": "two",
        "before": "Level 1 — variation, and a shape nobody chose",
        "after": "Level 3 — centre and spread",
        "estimate": "5 sections · 1 act · ~7 min read",
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
    },
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
        "before": "Level 2 — chance, and what a percentage claims",
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
    "level-07.html": {
        "number": 7, "word": "seven",
        "before": "Level 6 — limits are a hypothesis test",
        "after": "Level 8 — capability",
        "estimate": "5 sections · 1 act · ~8 min read",
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
    },
    "level-10.html": {
        "number": 10, "word": "ten",
        "before": "Level 9 — detection, and memory beating sensitivity",
        "after": "Level 11 — relationships, and the seam to MSA",
        "estimate": "6 sections · 1 interactive · ~9 min read",
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
    },
    "level-11.html": {
        "number": 11, "word": "eleven",
        "before": "Level 10 — counting, not measuring",
        "after": "Level 12 — experiments, not yet written",
        "estimate": "5 sections · 1 interactive · ~9 min read",
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
