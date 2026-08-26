#!/usr/bin/env python3
"""Make the site's two voices available to Manim.

The pages self-host EB Garamond and IBM Plex Mono as woff2. Manim renders text
through Pango, which reads installed system fonts and cannot load woff2 — so
without this step every video falls back to Pango's default sans and matches
NEITHER of the two voices in DESIGN.md. The ground colour was sampled from the
renders so video and page bleed seamlessly; type was the remaining seam.

This converts the repo's own woff2 files (not a download, not a distro package,
so the video uses byte-identical outlines to what the browser gets) into ttf
under ~/.local/share/fonts/spclab/ and refreshes the font cache.

Per-user on purpose: no root, and nothing outside $HOME changes.

    python3 tools/install-fonts.py            # convert + refresh cache
    python3 tools/install-fonts.py --check    # report only, exit 1 if missing
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

REPO_FONTS = pathlib.Path(__file__).resolve().parents[2] / "fonts"
DEST = pathlib.Path.home() / ".local/share/fonts/spclab"

# families the scenes ask for by name, and must therefore resolve
REQUIRED = ("EB Garamond", "IBM Plex Mono")


def resolvable() -> dict[str, bool]:
    """Which required families can Pango actually see right now?"""
    try:
        out = subprocess.run(["fc-list", ":", "family"], capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {f: False for f in REQUIRED}
    seen = {p.strip().lower() for line in out.splitlines() for p in line.split(",")}
    return {f: f.lower() in seen for f in REQUIRED}


def convert() -> list[pathlib.Path]:
    from fontTools.ttLib.woff2 import decompress  # needs brotli

    sources = sorted(REPO_FONTS.glob("*.woff2"))
    if not sources:
        sys.exit(f"no woff2 files in {REPO_FONTS} — is this the portfolio repo?")

    DEST.mkdir(parents=True, exist_ok=True)
    made = []
    for src in sources:
        out = DEST / f"{src.stem}.ttf"
        decompress(str(src), str(out))
        made.append(out)
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report resolvable families and exit non-zero if any are missing")
    args = ap.parse_args()

    if args.check:
        state = resolvable()
        for fam, ok in state.items():
            print(f"  {'ok  ' if ok else 'MISSING'}  {fam}")
        return 0 if all(state.values()) else 1

    made = convert()
    for p in made:
        print(f"  converted  {p.name:34s} {p.stat().st_size / 1024:7.1f} KB")

    subprocess.run(["fc-cache", "-f", str(DEST)], check=True, capture_output=True)

    state = resolvable()
    print()
    for fam, ok in state.items():
        print(f"  {'ok  ' if ok else 'MISSING'}  {fam}")
    if not all(state.values()):
        print("\nfc-cache ran but a family is still unresolvable — check fontconfig.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
