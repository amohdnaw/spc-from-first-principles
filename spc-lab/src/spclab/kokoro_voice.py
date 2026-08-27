"""A manim-voiceover speech service backed by Kokoro, running locally.

Why this exists: `manim_voiceover` ships gtts / azure / elevenlabs / gemini /
openai / pyttsx3 / recorder. gTTS is the only one that needs no key, and it
speaks at a median 209 Hz — measurably the wrong voice for a technical
explainer, and the reason the acts sounded like a station announcement.
Kokoro's `am_michael` measures 118 Hz at 143 wpm, which is inside the band an
American male explainer occupies. The measurement is in
`specs/narration-voice.md`.

Kokoro needs torch, so it runs in its own interpreter rather than in the render
venv — see `tools/kokoro_say.py`. This class only shells out to it and hands
manim-voiceover the resulting wav, which keeps `spc-lab/.venv` small and makes
the 1.5 GB dependency deletable without touching the project.

Cache: manim-voiceover keys on the line's text plus `input_data`, so the voice
and speed are part of the key. Changing either re-speaks; changing neither
re-uses. A full nine-act rebuild therefore only pays for lines that changed.
"""
from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
from pathlib import Path

from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService

VOICE = os.environ.get("SPCLAB_KOKORO_VOICE", "am_michael")
SPEED = float(os.environ.get("SPCLAB_KOKORO_SPEED", "0.92"))

# Where the interpreter that has torch lives. Overridable, because a machine
# that keeps kokoro somewhere else should not have to edit this file.
WORKER_PYTHON = Path(os.environ.get(
    "SPCLAB_KOKORO_PYTHON", str(Path.home() / "tts-lab/venv/bin/python")))
WORKER_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "kokoro_say.py"


class _Worker:
    """One long-lived kokoro process, spoken to in JSON lines.

    213 lines across nine acts, and loading the model costs about eight seconds
    each time — half an hour of a build spent importing torch. So the model is
    loaded once and the process stays up for the whole render.
    """

    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            [str(WORKER_PYTHON), str(WORKER_SCRIPT), "--serve"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        ready = self.proc.stdout.readline()
        if '"ready"' not in ready:
            err = self.proc.stderr.read()[-800:] if self.proc.stderr else ""
            raise RuntimeError(f"kokoro worker did not start: {ready!r}\n{err}")
        atexit.register(self.close)

    def say(self, text: str, out: Path, voice: str, speed: float) -> float:
        if self.proc.poll() is not None:
            raise RuntimeError("kokoro worker died mid-render")
        self.proc.stdin.write(json.dumps(
            {"text": text, "out": str(out), "voice": voice, "speed": speed}) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read()[-800:] if self.proc.stderr else ""
            raise RuntimeError(f"kokoro worker stopped answering\n{err}")
        res = json.loads(line)
        if not res.get("ok"):
            raise RuntimeError(f"kokoro failed on {text[:70]!r}: {res.get('error')}")
        if not out.exists():
            raise RuntimeError(f"kokoro reported success but wrote nothing to {out}")
        return float(res["duration"])

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=10)
            except Exception:                                  # noqa: BLE001
                self.proc.kill()


_WORKER: "_Worker | None" = None


def _worker() -> _Worker:
    global _WORKER
    if _WORKER is None:
        _WORKER = _Worker()
    return _WORKER


class KokoroService(SpeechService):
    """Local neural TTS. No key, no network at render time, no quota."""

    def __init__(self, voice: str = VOICE, speed: float = SPEED, **kwargs: object) -> None:
        if not WORKER_PYTHON.exists():
            raise RuntimeError(
                f"kokoro interpreter not found at {WORKER_PYTHON}.\n"
                "Install it, or point SPCLAB_KOKORO_PYTHON at one that has kokoro:\n"
                "  python3 -m venv ~/tts-lab/venv\n"
                "  ~/tts-lab/venv/bin/pip install kokoro soundfile "
                "--extra-index-url https://download.pytorch.org/whl/cpu\n"
                "(the extra index is not optional — without it pip installs the "
                "5.3 GB CUDA build of torch)")
        if not WORKER_SCRIPT.exists():
            raise RuntimeError(f"missing worker script: {WORKER_SCRIPT}")
        self.voice = voice
        self.speed = speed
        super().__init__(**kwargs)

    def generate_from_text(self, text: str, cache_dir=None, path=None, **kwargs) -> dict:
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "kokoro",
            "voice": self.voice,
            "speed": self.speed,
        }

        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached

        stem = self.get_audio_basename(input_data) if path is None else Path(path).stem
        wav_path = Path(cache_dir) / f"{stem}.wav"
        wav_path.parent.mkdir(parents=True, exist_ok=True)

        _worker().say(input_text, wav_path, self.voice, self.speed)

        # manim-voiceover expects mp3 elsewhere in the pipeline
        audio_path = f"{stem}.mp3"
        if shutil.which("ffmpeg"):
            mp3 = Path(cache_dir) / audio_path
            conv = subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", str(wav_path),
                 "-c:a", "libmp3lame", "-q:a", "3", str(mp3)],
                capture_output=True, text=True, timeout=300,
            )
            if conv.returncode != 0 or not mp3.exists():
                raise RuntimeError(f"mp3 conversion failed: {conv.stderr[-400:]}")
            wav_path.unlink(missing_ok=True)
        else:
            audio_path = wav_path.name

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
