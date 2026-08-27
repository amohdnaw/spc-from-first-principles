#!/usr/bin/env python3
"""Speak one line with Kokoro, write a wav. Runs in its own interpreter.

Kokoro needs torch, which is 1.5 GB. Keeping it out of the render venv means
`spc-lab/.venv` stays small and reproducible, and the heavy optional dependency
lives in one place that can be deleted without touching the project:

    python3 -m venv ~/tts-lab/venv
    ~/tts-lab/venv/bin/pip install kokoro soundfile \
      --extra-index-url https://download.pytorch.org/whl/cpu

The --extra-index-url is not optional. Without it pip installs the CUDA build
of torch — 5.3 GB, on a machine with no NVIDIA GPU.

    kokoro_say.py --text "…" --out line.wav [--voice am_michael] [--speed 0.92]
    kokoro_say.py --selftest
"""
from __future__ import annotations

import argparse
import sys

VOICE = "am_michael"   # chosen by measurement — see specs/narration-voice.md
SPEED = 0.92
RATE = 24_000


def synth(text: str, out: str, voice: str, speed: float) -> float:
    import warnings

    warnings.filterwarnings("ignore")
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    chunks = [audio for _, _, audio in pipe(text, voice=voice, speed=speed)]
    if not chunks:
        raise SystemExit(f"kokoro produced no audio for: {text[:60]!r}")
    audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
    sf.write(out, audio, RATE)
    return len(audio) / RATE

def serve() -> int:
    """Load the model once, then synthesize a line per request.

    A nine-act build speaks 213 lines. Loading Kokoro per line costs about
    eight seconds each — half an hour of the build spent importing torch. This
    keeps one process alive and talks to it in JSON lines:

        in : {"text": "...", "out": "/path/line.wav", "voice": "...", "speed": 0.92}
        out: {"ok": true, "duration": 3.42}   or   {"ok": false, "error": "..."}
    """
    import json
    import warnings

    warnings.filterwarnings("ignore")
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    print(json.dumps({"ready": True}), flush=True)

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
            chunks = [a for _, _, a in pipe(req["text"],
                                            voice=req.get("voice", VOICE),
                                            speed=float(req.get("speed", SPEED)))]
            if not chunks:
                raise ValueError("kokoro produced no audio")
            audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
            sf.write(req["out"], audio, RATE)
            print(json.dumps({"ok": True, "duration": len(audio) / RATE}), flush=True)
        except Exception as exc:                              # noqa: BLE001
            print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}),
                  flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text")
    ap.add_argument("--out")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--speed", type=float, default=SPEED)
    ap.add_argument("--serve", action="store_true",
                    help="stay alive and synthesize a line per JSON request on stdin")
    ap.add_argument("--selftest", action="store_true",
                    help="synthesize one line to /tmp and print its duration")
    a = ap.parse_args()

    if a.serve:
        return serve()

    if a.selftest:
        d = synth("Three sigma is not a matter of taste.", "/tmp/kokoro_selftest.wav",
                  a.voice, a.speed)
        print(f"ok — {a.voice} @{a.speed}: {d:.2f}s to /tmp/kokoro_selftest.wav")
        return 0

    if not a.text or not a.out:
        ap.error("--text and --out are required unless --serve or --selftest")
    print(f"{synth(a.text, a.out, a.voice, a.speed):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
