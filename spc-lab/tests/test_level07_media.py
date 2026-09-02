"""What the Level 7 acts have to be as files, not as animations.

The scene tests check the numbers on screen. Nothing checked the artifact the
browser actually downloads, and every failure that has cost time on this site
lived there: a poster grabbed at 62 % of runtime that landed on an empty
transition frame, a `moov` atom written after `mdat` so the first play would not
seek, a caption file left behind from a previous cut of the act, and an mp4 with
no audio in it at all.

So the deliverable gets asserted directly: resolution, frame rate, decoded
audio, container layout, cues, poster, and a manifest that records what the
build chose. The manifest is the part with no other witness — the poster time
comes out of a scorer that runs once, at build time, and a number no gate can
read is a number that can quietly go wrong again.

Scoped to Level 7's two acts on purpose. The other nine were rendered before
these gates existed and would fail on the manifest they have never had; widening
the scope is the pilot's job, not this file's.
"""
from __future__ import annotations

import json
import pathlib
import re
import struct
import subprocess
from collections import Counter

import numpy as np
import pytest
from PIL import Image

from spclab.voice_check import DECODE_RATE, decode_pcm

LAB = pathlib.Path(__file__).resolve().parents[1]
REPO = LAB.parent

#: class name -> (scene module, poster/caption stem)
ACTS = {
    "Level07": ("level07_scene", "level07"),
    "Level07Case": ("level07_case_scene", "level07-case"),
}

CUE = re.compile(
    r"(\d\d):(\d\d):(\d\d)\.(\d\d\d) --> (\d\d):(\d\d):(\d\d)\.(\d\d\d)")


def _mp4(klass: str) -> pathlib.Path:
    scene = ACTS[klass][0]
    return LAB / f"media/videos/{scene}/1080p60/{klass}.mp4"


def _probe(mp4: pathlib.Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams",
         "-of", "json", str(mp4)],
        capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    info["video"] = next(s for s in info["streams"] if s["codec_type"] == "video")
    info["audio"] = next(
        (s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return info


def _fps(stream: dict, key: str = "r_frame_rate") -> float:
    num, den = stream[key].split("/")
    return float(num) / float(den)


def _atoms(mp4: pathlib.Path) -> list[str]:
    """The top-level box names, in the order they appear in the file."""
    names: list[str] = []
    with mp4.open("rb") as fh:
        while True:
            head = fh.read(8)
            if len(head) < 8:
                break
            size, name = struct.unpack(">I4s", head)
            names.append(name.decode("latin-1"))
            if size == 1:                      # 64-bit extended size
                size = struct.unpack(">Q", fh.read(8))[0]
                fh.seek(size - 16, 1)
            elif size == 0:                    # runs to end of file
                break
            else:
                fh.seek(size - 8, 1)
    return names


def _vtt(klass: str) -> pathlib.Path:
    return REPO / f"captions/{ACTS[klass][1]}.vtt"


def _cues(vtt: pathlib.Path) -> list[tuple[float, float, str]]:
    lines = vtt.read_text().splitlines()
    cues = []
    for i, line in enumerate(lines):
        m = CUE.search(line)
        if not m:
            continue
        f = [int(g) for g in m.groups()]
        start = f[0] * 3600 + f[1] * 60 + f[2] + f[3] / 1000
        end = f[4] * 3600 + f[5] * 60 + f[6] + f[7] / 1000
        text = " ".join(l.strip() for l in lines[i + 1:i + 6]
                        if l.strip() and not CUE.search(l))
        cues.append((start, end, text))
    return cues


def _ink(path: pathlib.Path) -> float:
    """Fraction of non-background pixels — the build's own poster scorer."""
    with Image.open(path) as im:
        px = np.asarray(im.convert("RGB").resize((320, 180))).reshape(-1, 3)
    bg = np.array(Counter(map(tuple, px)).most_common(1)[0][0])
    return float((np.abs(px.astype(int) - bg).max(axis=1) > 18).mean())


def _manifest(klass: str) -> dict:
    path = _mp4(klass).with_suffix(".manifest.json")
    assert path.exists(), (
        f"{klass}: no build manifest at {path.relative_to(REPO)} — "
        "re-render the act with ./build-media.sh")
    return json.loads(path.read_text())


@pytest.fixture(scope="module", params=sorted(ACTS))
def act(request):
    klass = request.param
    mp4 = _mp4(klass)
    assert mp4.exists(), (
        f"{klass}: {mp4.relative_to(REPO)} is missing. The 1080p60 mp4s are "
        "tracked in this repo, so a missing act is a lost deliverable.")
    return klass, mp4


# ------------------------------------------------------------------ the frame
def test_the_act_is_1920x1080_at_60_fps(act):
    klass, mp4 = act
    v = _probe(mp4)["video"]
    assert (v["width"], v["height"]) == (1920, 1080), (
        f"{klass}: {v['width']}x{v['height']}, not 1920x1080")
    assert _fps(v) == pytest.approx(60.0, abs=0.01), (
        f"{klass}: container frame rate {v['r_frame_rate']}, not 60/1")
    assert _fps(v, "avg_frame_rate") == pytest.approx(60.0, abs=0.5), (
        f"{klass}: average frame rate {_fps(v, 'avg_frame_rate'):.2f} — the "
        "act was re-encoded or has dropped frames")


# ------------------------------------------------------------------ the sound
def test_the_act_carries_an_audio_stream_that_decodes(act):
    """A silent act is the failure this whole pilot exists to stop shipping.

    The stream is decoded rather than merely listed, because a container can
    name an audio track that no browser can play, and because the length of the
    decoded PCM is the only thing that catches audio that stops a minute in.
    """
    klass, mp4 = act
    info = _probe(mp4)
    assert info["audio"] is not None, (
        f"{klass}: no audio stream. Render with "
        "SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=kokoro ./build-media.sh")
    pcm = decode_pcm(mp4)
    assert pcm, f"{klass}: the audio stream decoded to nothing"
    seconds = len(pcm) / 2 / DECODE_RATE
    duration = float(info["format"]["duration"])
    assert seconds == pytest.approx(duration, rel=0.02), (
        f"{klass}: {seconds:.0f} s of audio under {duration:.0f} s of video — "
        "the track is truncated")


# -------------------------------------------------------------- the container
def test_the_act_is_faststart(act):
    """`moov` before `mdat`, or the first play cannot seek until the tail lands.

    Manim's ffmpeg writes the index last; `build-media.sh` re-muxes it forward.
    This is the gate on that re-mux still happening.
    """
    klass, mp4 = act
    atoms = _atoms(mp4)
    assert "moov" in atoms and "mdat" in atoms, f"{klass}: atoms {atoms}"
    assert atoms.index("moov") < atoms.index("mdat"), (
        f"{klass}: moov comes after mdat — the faststart re-mux did not run. "
        f"atoms: {atoms}")


# --------------------------------------------------------------- the captions
def test_the_act_has_captions_that_fit_inside_it(act):
    klass, mp4 = act
    vtt = _vtt(klass)
    assert vtt.exists(), f"{klass}: no {vtt.relative_to(REPO)}"
    text = vtt.read_text()
    assert text.startswith("WEBVTT"), f"{vtt.name}: not a WebVTT file"
    cues = _cues(vtt)
    assert len(cues) >= 20, (
        f"{vtt.name}: {len(cues)} cues for a narrated act — the caption track "
        "is empty or partial")
    assert all(t for _, _, t in cues), f"{vtt.name}: a cue with no words in it"
    assert all(e > s for s, e, _ in cues), f"{vtt.name}: a cue that ends first"
    starts = [s for s, _, _ in cues]
    assert starts == sorted(starts), f"{vtt.name}: cues are out of order"

    duration = float(_probe(mp4)["format"]["duration"])
    last = max(e for _, e, _ in cues)
    assert last <= duration + 0.5, (
        f"{vtt.name}: last cue ends at {last:.0f} s but the act is only "
        f"{duration:.0f} s — these captions belong to a different cut")


# ----------------------------------------------------------------- the poster
def test_the_poster_is_a_frame_with_something_on_it(act):
    """The poster is scored, not sampled at a fixed fraction of runtime.

    An earlier version took 62 % of runtime and landed on an empty transition
    frame in SPCGallery, which is why ink coverage is asserted rather than mere
    existence: a black frame is a valid, non-empty, useless jpeg.
    """
    klass, _ = act
    poster = REPO / f"posters/{ACTS[klass][1]}.jpg"
    assert poster.exists() and poster.stat().st_size > 0, (
        f"{klass}: poster {poster.name} missing or empty")
    with Image.open(poster) as im:
        assert im.format == "JPEG", f"{poster.name}: {im.format}, not JPEG"
        assert im.size == (1920, 1080), f"{poster.name}: {im.size}"
    ink = _ink(poster)
    assert ink > 0.01, (
        f"{poster.name}: {ink*100:.2f} % of pixels differ from the background — "
        "the scorer picked, or something overwrote, a near-empty frame")


# --------------------------------------------------------------- the manifest
def test_the_manifest_records_what_the_build_actually_produced(act):
    klass, mp4 = act
    m = _manifest(klass)
    for key in ("scene", "service", "duration", "poster_time", "cues"):
        assert key in m, f"{klass}: manifest has no {key!r}"

    assert m["scene"] == ACTS[klass][0], f"{klass}: manifest names {m['scene']}"
    assert m["klass"] == klass
    assert isinstance(m["service"], str) and m["service"], (
        f"{klass}: manifest names no voice service")

    info = _probe(mp4)
    duration = float(info["format"]["duration"])
    assert m["duration"] == pytest.approx(duration, rel=0.01), (
        f"{klass}: manifest says {m['duration']:.1f} s, the file is "
        f"{duration:.1f} s — the manifest is stale")
    assert (m["width"], m["height"]) == (1920, 1080)
    assert m["fps"] == pytest.approx(_fps(info["video"]), abs=0.01), (
        f"{klass}: manifest says {m['fps']} fps, the file says "
        f"{_fps(info['video']):.3f}")
    assert m["audio_codec"] == (info["audio"] or {}).get("codec_name"), (
        f"{klass}: manifest says audio {m['audio_codec']!r}, the file has "
        f"{(info['audio'] or {}).get('codec_name')!r}")

    assert 0 < m["poster_time"] < duration, (
        f"{klass}: poster taken at {m['poster_time']} s of a {duration:.0f} s act")
    assert m["poster_ink"] > 0.01, (
        f"{klass}: the winning poster candidate scored {m['poster_ink']*100:.2f} % "
        "ink, so every candidate frame was near-empty")
    assert (REPO / m["poster"]).exists(), f"{klass}: manifest poster {m['poster']}"

    assert m["cues"] == len(_cues(_vtt(klass))), (
        f"{klass}: manifest counts {m['cues']} cues, "
        f"{ACTS[klass][1]}.vtt carries {len(_cues(_vtt(klass)))}")
    assert m["captions"] == f"captions/{ACTS[klass][1]}.vtt"
