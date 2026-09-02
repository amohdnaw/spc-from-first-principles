"""The voice gate for the Level 7 pilot.

The sibling MSA site shipped an act narrated in gTTS instead of Kokoro
`am_michael`, and every other artifact was correct: right duration, right
captions, right poster, right frames. The only wrong thing was the sound,
because `narration.py` falls back on purpose and the warning went somewhere
nobody read.

These tests listen. They decode the mp4 the site serves and measure it, so the
check is independent of the plumbing that produced it — a refactor of the speech
service, the worker interpreter or the build script cannot fool them.

The estimator is calibrated first, against tones whose answer is known. A
measurement gate on an unverified instrument is worth nothing: it would pass a
gTTS render as happily as a Kokoro one if the autocorrelator were wrong.

Scoped to `level07_scene` and `level07_case_scene`. The other acts are still
silent by design and are not this pilot's promise.
"""
from __future__ import annotations

import functools
import json
import pathlib
import subprocess
import wave

import numpy as np
import pytest

from spclab.voice_check import (
    BAND_HIGH_HZ, BAND_LOW_HZ, F0_MAX_HZ, F0_MIN_HZ, KNOWN_SERVICES,
    decode_pcm, median_f0,
)

LAB = pathlib.Path(__file__).resolve().parents[1]

ACTS = {
    "Level07": "level07_scene",
    "Level07Case": "level07_case_scene",
}


def _mp4(klass: str) -> pathlib.Path:
    return LAB / f"media/videos/{ACTS[klass]}/1080p60/{klass}.mp4"


@functools.lru_cache(maxsize=None)
def _measured(klass: str) -> dict:
    """One pass over an act's audio, reused by every assertion about it."""
    mp4 = _mp4(klass)
    assert mp4.exists(), f"{klass}: {mp4} is missing"
    return median_f0(mp4)


def _manifest(klass: str) -> dict:
    path = _mp4(klass).with_suffix(".manifest.json")
    assert path.exists(), f"{klass}: no build manifest beside the mp4"
    return json.loads(path.read_text())


def _tone(path: pathlib.Path, hz: float, rate: int = 24000) -> pathlib.Path:
    t = np.arange(int(rate * 1.5)) / rate
    # a couple of harmonics, so it is not a pure sine the autocorrelator finds
    # trivially, and an envelope so some frames are quiet
    sig = (np.sin(2 * np.pi * hz * t)
           + 0.5 * np.sin(4 * np.pi * hz * t)
           + 0.25 * np.sin(6 * np.pi * hz * t))
    sig *= 0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t)
    pcm = (sig / np.abs(sig).max() * 32000).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return path


# ------------------------------------------------- the estimator itself first
@pytest.mark.parametrize("hz", [90.0, 118.0, 150.0, 209.0, 300.0])
def test_the_estimator_recovers_a_known_tone(tmp_path, hz):
    got = median_f0(_tone(tmp_path / f"tone_{int(hz)}.wav", hz))["median_f0"]
    assert got == pytest.approx(hz, rel=0.04), f"measured {got:.1f} for a {hz} tone"


def test_the_estimator_refuses_silence(tmp_path):
    f = tmp_path / "silence.wav"
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(np.zeros(24000, dtype=np.int16).tobytes())
    with pytest.raises(ValueError):
        median_f0(f)


def test_the_decoder_refuses_a_video_with_no_audio(tmp_path):
    """The other half of the instrument: a silent mp4 must raise, not measure.

    Without this the audio assertions below could be vacuous — a file with no
    stream to decode has no frames to fail on.
    """
    mute = tmp_path / "mute.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi",
         "-i", "color=c=black:s=64x64:d=1:r=10", "-pix_fmt", "yuv420p",
         str(mute), "-y"], check=True)
    with pytest.raises(ValueError, match="no decodable audio stream"):
        decode_pcm(mute)


def test_the_band_excludes_gtts_and_includes_am_michael():
    """The two numbers the band exists to separate, from specs/narration-voice.md."""
    assert BAND_LOW_HZ <= 118.0 <= BAND_HIGH_HZ, "am_michael must be inside"
    assert not (BAND_LOW_HZ <= 209.0 <= BAND_HIGH_HZ), "gTTS must be outside"
    assert F0_MIN_HZ < BAND_LOW_HZ and BAND_HIGH_HZ < F0_MAX_HZ, (
        "the search range has to be wider than the band, or a voice outside it "
        "gets clipped to the edge and measures as a pass")


# ------------------------------------------------------ then the real renders
@pytest.mark.parametrize("klass", sorted(ACTS))
def test_the_act_has_decodable_audio_bytes(klass):
    pcm = decode_pcm(_mp4(klass))
    assert len(pcm) > 0, f"{klass}: no decoded audio bytes"


@pytest.mark.parametrize("klass", sorted(ACTS))
def test_the_act_is_actually_narrated(klass):
    """Guards the direction a pitch check cannot: an act with no speech at all.

    A silent render would pass a band check by having no voiced frames to
    measure, so the fraction is asserted rather than assumed.
    """
    r = _measured(klass)
    assert r["voiced_fraction"] > 0.25, (
        f"{klass}: only {r['voiced_fraction']*100:.0f} % of frames are voiced — "
        "is the narration actually there?")
    assert r["seconds"] > 30, f"{klass}: {r['seconds']:.0f} s is too short"


@pytest.mark.parametrize("klass", sorted(ACTS))
def test_the_manifest_names_a_service_this_gate_can_measure(klass):
    service = _manifest(klass)["service"]
    assert service in KNOWN_SERVICES, (
        f"{klass}: manifest names voice service {service!r}, which is none of "
        f"{list(KNOWN_SERVICES)} — an unmeasured service is an unchecked voice")


@pytest.mark.parametrize("klass", sorted(ACTS))
def test_a_kokoro_act_sits_in_the_explainer_band(klass):
    """Only asserted while the manifest claims kokoro, and that is the point.

    The claim and the measurement have to agree. If the build ever falls back to
    gTTS while still writing `kokoro`, this is what fails: gTTS measures around
    209 Hz and am_michael 118, and the band between them has no overlap.
    """
    service = _manifest(klass)["service"]
    if service != "kokoro":
        pytest.skip(f"{klass} was rendered with {service}, not kokoro")
    r = _measured(klass)
    assert r["in_band"], (
        f"{klass}: median F0 {r['median_f0']:.1f} Hz is outside "
        f"{BAND_LOW_HZ:.0f}-{BAND_HIGH_HZ:.0f} Hz while the manifest says "
        "kokoro. gTTS measures around 209 — this render is in the wrong voice.")
