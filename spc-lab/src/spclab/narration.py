"""Narration layer — one script, two renders.

The problem this solves: the original acts played 10-13 animations in 15
seconds, about 1.2s per beat, with 3-5s of total pause. Nothing held long
enough to read. Fixing that by hand-tuning `run_time` and `self.wait()` means
tuning twice — once for the silent cut and again if narration is ever added,
because a spoken line dictates how long its beat must last.

So the narration script *is* the pacing. Every beat is wrapped in `self.say`:

    with self.say("Choose limits at three sigma and you have defined a test."):
        self.play(Create(limits), run_time=1.2)

- `SPCLAB_VOICE=1` renders real speech and the block holds until the line ends.
- Unset renders silent, and the block holds for exactly as long as that line
  *would* have taken to speak.

Same source, same pacing, audio optional. Nothing to re-tune.

    # silent, correctly paced
    PYTHONPATH=src .venv/bin/manim -qh src/spclab/level2_scene.py Level2

    # narrated
    SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/spclab/level2_scene.py Level2

Swapping the synthetic voice for a real one is a one-line change in
`_speech_service` — see SPCLAB_VOICE_SERVICE below.
"""
from __future__ import annotations

import os
from contextlib import contextmanager

# Words per minute for an explainer read. 150 is unhurried technical narration;
# 3Blue1Brown sits around 140-160.
WPM = 150.0

# Minimum a beat may occupy even if the line is very short, and the breath
# added after every line so beats do not collide.
MIN_BEAT = 1.4
TAIL_PAUSE = 0.45

VOICE = os.environ.get("SPCLAB_VOICE", "").strip().lower() in {"1", "true", "yes", "on"}
SERVICE = os.environ.get("SPCLAB_VOICE_SERVICE", "gtts").strip().lower()


def spoken_duration(text: str) -> float:
    """How long `text` takes to read aloud, in seconds."""
    words = len([w for w in text.split() if w.strip()])
    return max(MIN_BEAT, words / (WPM / 60.0) + TAIL_PAUSE)


if VOICE:
    from manim_voiceover import VoiceoverScene as _Base
else:
    from manim import Scene as _Base


def _speech_service():
    """The voice. gTTS is the default because it needs no key and no model.

    To narrate in your own voice instead:
        sudo apt install portaudio19-dev          # pyaudio needs this
        .venv/bin/pip install "manim-voiceover[recorder]"
        SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=recorder .venv/bin/manim ...
    RecorderService prompts you per line and caches each take, so a re-render
    reuses the audio and only re-records lines whose text changed.
    """
    if SERVICE == "recorder":
        from manim_voiceover.services.recorder import RecorderService
        return RecorderService(trim_buffer_end=50, trim_buffer_start=50)
    from manim_voiceover.services.gtts import GTTSService
    # en-GB reads a little slower and flatter than en-US, which suits
    # technical narration.
    return GTTSService(lang="en", tld="co.uk")


class _SilentTracker:
    """Stands in for the voiceover tracker when rendering without audio."""

    __slots__ = ("duration",)

    def __init__(self, duration: float) -> None:
        self.duration = duration


class NarratedScene(_Base):
    """Scene base that understands `with self.say(...)`."""

    def setup(self) -> None:
        super().setup()
        if VOICE:
            self.set_speech_service(_speech_service())

    @contextmanager
    def say(self, text: str):
        """Hold the enclosed animations for as long as `text` takes to speak."""
        if VOICE:
            with self.voiceover(text=text) as tracker:
                yield tracker
            return

        target = spoken_duration(text)
        start = self.renderer.time
        yield _SilentTracker(target)
        elapsed = self.renderer.time - start
        if elapsed < target:
            self.wait(target - elapsed)

    def beat(self, seconds: float = 0.6) -> None:
        """A deliberate pause between sections, voiced or not."""
        self.wait(seconds)
