"""Level 7's mastery loop is a contract about the served page, so test the page.

`test_level07_mastery.py` already proves the numbers. What it cannot see is the
page: whether the prose still reads without touching the challenge, whether the
prediction is asked before the act that answers it, whether the costs the learner
reads came from Python or were recomputed in the browser.

Those are DOM facts, so these tests parse `level-07.html` into a tree and ask
questions of the tree. Asserting on a template string instead would pass on a
page that never renders, which is the vacuous gate this file exists to avoid.

Three tests at the end read the page script as text on purpose. "No `innerHTML`",
"every storage access is guarded" and "watched only on `ended`" are statements
about the code, not about the rendered tree, and the contract names all three.

    PYTHONPATH=src .venv/bin/pytest tests/test_level07_page.py -q
"""
from __future__ import annotations

import json
import pathlib
import re
from html.parser import HTMLParser

import pytest

from spclab.level07_mastery import (
    CASE_FIELDS,
    CASE_SEEDS,
    OPTION_LABELS,
    PRINTED_DECIMALS,
    challenge_case,
)

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "level-07.html"

# `html.parser` reports these as start tags and never closes them.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

WECO_TASK = "https://spc.amohdnaw.xyz/app#g-weco"


# --------------------------------------------------------------- a minimal DOM
class Node:
    """One element, its attributes, its children and its place in the document.

    `order` is a document-order counter rather than a line number, so "does the
    prediction come before Act A" is a comparison of two integers even when both
    live on the same line.
    """

    def __init__(self, tag, attrs, parent, order):
        self.tag = tag
        self.attrs = {k: (v if v is not None else "") for k, v in attrs}
        self.parent = parent
        self.children = []
        self.order = order
        self.data = []

    def __repr__(self):
        ident = self.attrs.get("id") or self.attrs.get("class") or ""
        return f"<{self.tag} {ident}>".replace("  ", " ")

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()

    def find_all(self, tag=None, cls=None, **attrs):
        out = []
        for node in self.walk():
            if tag and node.tag != tag:
                continue
            if cls and cls not in node.classes:
                continue
            if any(node.attrs.get(k) != v for k, v in attrs.items()):
                continue
            out.append(node)
        return out

    def find(self, *args, **kwargs):
        found = self.find_all(*args, **kwargs)
        return found[0] if found else None

    def by_id(self, ident):
        node = self.find(id=ident)
        assert node is not None, f"#{ident} is not in the page"
        return node

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def text(self):
        parts = list(self.data)
        for child in self.children:
            parts.append(child.text())
        return re.sub(r"\s+", " ", "".join(parts)).strip()


class Tree(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], None, 0)
        self.stack = [self.root]
        self.count = 0
        self.feed(source)

    def _node(self, tag, attrs):
        self.count += 1
        node = Node(tag, attrs, self.stack[-1], self.count)
        self.stack[-1].children.append(node)
        return node

    def handle_starttag(self, tag, attrs):
        node = self._node(tag, attrs)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._node(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].data.append(data)


SOURCE = PAGE.read_text()
DOM = Tree(SOURCE).root
MAIN = DOM.find("main")
assert MAIN is not None, f"{PAGE.name} has no <main>"


def _prose():
    """The chapter's own paragraphs: a direct child of a `.leaf` content block."""
    return [p for p in MAIN.find_all("p")
            if p.parent.tag == "div" and "leaf" in p.parent.parent.classes]


def _acts():
    """The two act players, in document order."""
    return sorted(MAIN.find_all("video"), key=lambda v: v.order)


def _mp4(video):
    source = video.find("source")
    return source.attrs["src"].rsplit("/", 1)[-1] if source else video.attrs.get("src", "")


def _act(name):
    return next(v for v in _acts() if _mp4(v) == name)


def _cases():
    block = DOM.by_id("level07-cases")
    assert block.tag == "script", "the case bank must be a data block, not markup"
    assert block.attrs.get("type") == "application/json"
    return json.loads(block.text())


def _script():
    """The page's own JavaScript, concatenated. The JSON data block is not code."""
    return "\n".join(s.text() for s in DOM.find_all("script")
                     if s.attrs.get("type") != "application/json")


# ------------------------------------------------ 1. reading stays open
def test_the_chapter_prose_precedes_the_mastery_form_and_stays_outside_it():
    prose = _prose()
    assert len(prose) >= 15, f"only {len(prose)} chapter paragraphs found"

    forms = MAIN.find_all("form")
    assert forms, "the mastery loop has no form"

    inside = [p.text()[:60] for p in prose
              if any(a.tag == "form" for a in p.ancestors())]
    assert not inside, "chapter prose is inside a form:\n  " + "\n  ".join(inside)

    for section in MAIN.find_all("section"):
        own_prose = [p for p in prose if section in list(p.ancestors())]
        own_forms = [f for f in forms if section in list(f.ancestors())]
        if own_prose and own_forms:
            assert min(p.order for p in own_prose) < min(f.order for f in own_forms), (
                f"section {section.attrs.get('id')} opens with a form, not prose")

    nav = MAIN.find("a", cls="next")
    assert nav is not None and not any(a.tag == "form" for a in nav.ancestors()), (
        "the next-level link is inside the mastery form")
    blocked = [repr(n) for n in MAIN.walk()
               if "disabled" in n.attrs or n.attrs.get("aria-disabled") == "true"]
    assert not blocked, "the served page disables controls: " + ", ".join(blocked)


# ------------------------------------------------ 2. predict before you are told
def test_the_prediction_is_asked_before_act_a():
    predict = DOM.by_id("m-predict")
    radios = [i for i in predict.find_all("input") if i.attrs.get("type") == "radio"]
    assert len(radios) >= 2, "a prediction with one option is not a prediction"
    assert len({r.attrs.get("name") for r in radios}) == 1, "the radios are not one group"
    assert predict.order < _act("Level07.mp4").order, (
        "Act A plays before the page asks for a prediction")


# ------------------------------------------------ 3. media the page can fall back from
def test_each_act_has_a_poster_and_the_caption_track_it_has_a_file_for():
    acts = _acts()
    assert len(acts) == 2, f"expected Act A and Act B, found {len(acts)} players"

    tracked = 0
    for video in acts:
        poster = video.attrs.get("poster", "")
        assert poster and (REPO / poster).exists(), f"{_mp4(video)}: poster {poster!r}"
        vtt = f"captions/{pathlib.Path(poster).stem}.vtt"
        tracks = [t.attrs.get("src") for t in video.find_all("track")
                  if t.attrs.get("kind") == "captions"]
        if (REPO / vtt).exists():
            assert tracks == [vtt], f"{_mp4(video)} should caption from {vtt}, has {tracks}"
            assert (REPO / vtt).stat().st_size > 0, f"{vtt} is empty"
            tracked += 1
        else:
            assert not tracks, f"{_mp4(video)} claims captions but {vtt} does not exist"
    assert tracked, "no act carries captions, so this gate is checking nothing"


# ------------------------------------------------ 4. Python owns every number
def test_the_case_block_carries_the_whole_seed_bank_priced_in_python():
    data = _cases()
    assert data["printed_decimals"] == PRINTED_DECIMALS
    assert data["case_fields"] == list(CASE_FIELDS)
    assert data["option_labels"] == dict(OPTION_LABELS)
    assert [int(s) for s in data["seeds"]] == list(CASE_SEEDS)
    assert sorted(int(s) for s in data["cases"]) == sorted(CASE_SEEDS)

    for seed in CASE_SEEDS:
        served = data["cases"][str(seed)]
        truth = challenge_case(seed)
        assert served["answer"] == truth["answer"], f"seed {seed}: wrong winner served"
        assert served["deciding_field"] == truth["deciding_field"]
        assert served["deciding_field"] in CASE_FIELDS
        assert served["surface_story"] == truth["surface_story"]
        assert [o["id"] for o in served["options"]] == [o["id"] for o in truth["options"]]
        for option, expect in zip(served["options"], truth["options"]):
            assert option["label"] == expect["label"]
            assert option["printed"] == f"{expect['expected_cost']:.{PRINTED_DECIMALS}f}", (
                f"seed {seed} {option['id']}: cost not printed by Python")
        printed = {name: served["printed_fields"][name] for name in CASE_FIELDS}
        assert all(printed.values()), f"seed {seed}: an unpriced case field"


def test_no_cost_winner_or_ratio_is_computed_in_javascript():
    code = _script()
    body = code[code.index("level07-cases"):] if "level07-cases" in code else code
    for banned in ("Math.min", "Math.max", "Math.sqrt", "Math.log", "toFixed",
                   "expected_cost *", "/ arl0"):
        assert banned not in body, f"the page computes in JavaScript: {banned}"
    for label in OPTION_LABELS.values():
        assert label not in code, f"option label retyped in JavaScript: {label!r}"
    for field in CASE_FIELDS:
        assert f'"{field}"' not in code and f"'{field}'" not in code, (
            f"case field retyped in JavaScript: {field!r}")


# ------------------------------------------------ 5. failure states are announced
def test_retry_and_saved_progress_speak_through_a_live_region():
    for ident in ("m-verdict", "m-save-status"):
        node = DOM.by_id(ident)
        assert node.attrs.get("aria-live") in {"polite", "assertive"}, (
            f"#{ident} has no aria-live")
        assert node.attrs.get("role") == "status", f"#{ident} is not a status region"
    retry = DOM.by_id("m-retry")
    assert retry.tag == "button" and "Retry with new data" in retry.text()
    assert DOM.by_id("m-verdict").order < retry.order, "the retry precedes its verdict"


# ------------------------------------------------ 6. secondary paths, after the decision
def test_the_secondary_paths_follow_the_decision_they_serve():
    decision = DOM.by_id("m-verdict").order
    secondary = DOM.by_id("m-secondary")
    assert secondary.order > decision, "the secondary paths precede the decision"

    text = secondary.text()
    assert "Use this when…" in text, "no field answer"
    assert "Evidence" in text, "no evidence path"
    for cited in ("spclab.level07_mastery", "test_level07_mastery.py"):
        assert cited in text, f"evidence does not name {cited}"

    link = secondary.find("a", href=WECO_TASK)
    assert link is not None, f"no link to {WECO_TASK}"
    assert link.attrs.get("target") == "_blank"
    assert "noopener" in link.attrs.get("rel", "")
    assert "Open the WECO task" in link.text()


# ------------------------------------------------ 7. a caption is a claim about its image
CAPTIONS = {
    "l07_1_two_errors.png": ("Figure 7.2",
                             ("power", "shift"), ("written down twice", "histogram", "bin")),
    "l07_2_the_trade.png": ("Figure 7.3",
                            ("Western Electric", "false alarm"), ("funnel", "Deming")),
}


@pytest.mark.parametrize("image", sorted(CAPTIONS))
def test_the_repaired_captions_describe_their_own_image(image):
    number, required, forbidden = CAPTIONS[image]
    figure = next((f for f in MAIN.find_all("figure")
                   if any(image in (i.attrs.get("src") or "") for i in f.find_all("img"))), None)
    assert figure is not None, f"no figure shows {image}"
    caption = figure.find("figcaption")
    assert caption is not None, f"{image} has no caption"
    fignum = caption.find("span", cls="fignum").text()
    assert fignum == number, f"{image} is labelled {fignum!r}, expected {number!r}"

    said = caption.find("span", cls="figtext").text()
    for word in required:
        assert word.lower() in said.lower(), f"{number} never mentions {word!r}: {said!r}"
    for word in forbidden:
        assert word.lower() not in said.lower(), (
            f"{number} describes a different figure ({word!r}): {said!r}")


# ------------------------------------------------ the three code clauses
def test_the_page_never_writes_generated_content_as_html():
    code = _script()
    for banned in ("innerHTML", "outerHTML", "document.write", "insertAdjacentHTML"):
        assert banned not in code, f"generated content written as HTML: {banned}"
    for needed in ("textContent", "createElement", "appendChild"):
        assert needed in code, f"the case card is not built from nodes: {needed} missing"


def test_every_storage_access_is_inside_a_try():
    code = _script()
    hits = [m.start() for m in re.finditer(r"localStorage", code)]
    assert hits, "the page never touches storage, so progress is never saved"

    guarded = []
    for m in re.finditer(r"\btry\s*\{", code):
        depth, i = 0, m.end() - 1
        while i < len(code):
            if code[i] == "{":
                depth += 1
            elif code[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        guarded.append((m.start(), i))
    for hit in hits:
        assert any(lo < hit < hi for lo, hi in guarded), (
            f"unguarded storage access at offset {hit}: "
            f"{code[max(0, hit - 60):hit + 40]!r}")
    assert "Progress was not saved." in code, "a storage failure says nothing"


def test_an_act_is_marked_watched_only_when_it_ends():
    code = _script()
    listened = set(re.findall(r"addEventListener\(\s*['\"]([a-z]+)['\"]", code))
    assert "ended" in listened, "nothing listens for the end of an act"
    for event in ("play", "playing", "timeupdate", "loadedmetadata", "canplay",
                  "loadeddata", "pause", "progress", "error"):
        assert event not in listened, f"the page listens for {event!r} on media"
