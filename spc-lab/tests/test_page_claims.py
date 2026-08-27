"""The index makes three counted claims about the curriculum. Pin them to reality.

`index.html` opens with "twelve levels, six written - sixteen minutes of narrated
video". Every one of those numbers was typed by hand, and the runtime had already
drifted twice: it read "eleven minutes" at five acts, "fourteen" at six, and was
still saying fourteen when the six acts totalled 16:14.

A typed number beside a measurable one is a claim waiting to go stale, so it gets
the same treatment as the constants: computed from source, asserted here.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]
INDEX = REPO / "index.html"

WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}


def _claim() -> str:
    hero = re.search(r'<span class="micro"[^>]*>An interactive curriculum[^<]*</span>',
                     INDEX.read_text())
    assert hero, "the index no longer opens with the curriculum claim"
    return hero.group(0)


def _spelled(claim: str, unit: str) -> int:
    m = re.search(rf"(\w+) {unit}", claim)
    assert m, f"no spelled number before {unit!r} in: {claim}"
    word = m.group(1).lower()
    assert word in WORDS, f"unspelled or unknown number {word!r} before {unit!r}"
    return WORDS[word]


def _act_seconds(mp4: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(mp4)],
        capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def test_written_levels_matches_the_pages_that_exist():
    """"six written" must equal the level pages actually written."""
    pages = sorted(REPO.glob("level-[0-9][0-9].html"))
    # a redirect stub is not a written level; a chapter has numbered sections
    written = [p for p in pages if 'class="sec-no"' in p.read_text()]
    assert _spelled(_claim(), "written") == len(written), (
        f"index claims {_spelled(_claim(), 'written')} written, "
        f"found {len(written)}: {[p.name for p in written]}"
    )


def test_total_levels_matches_the_rail():
    """"twelve levels" must equal the slots on the level rail."""
    rail = re.search(r'<nav class="rail".*?</nav>', INDEX.read_text(), re.S)
    slots = len(re.findall(r"<(?:a|span)[^>]*class=\"lv", rail.group(0))) if rail else 0
    if slots == 0:  # the index carries spine cards rather than a rail
        slots = len(re.findall(r'class="lv-num', INDEX.read_text()))
    assert _spelled(_claim(), "levels") == slots, (
        f"index claims {_spelled(_claim(), 'levels')} levels, rail shows {slots}"
    )


def test_runtime_claim_matches_the_rendered_acts():
    """The spoken runtime is the sum of the level acts, floored to the minute."""
    acts = sorted((REPO / "spc-lab/media/videos").glob("level*_scene/1080p60/*.mp4"))
    assert acts, "no level acts rendered - cannot check the runtime claim"
    total = sum(_act_seconds(a) for a in acts)
    claimed = _spelled(_claim(), "minutes")
    assert claimed == int(total // 60), (
        f"index claims {claimed} minutes; {len(acts)} level acts total "
        f"{int(total)//60} min {int(total)%60:02d} s"
    )
