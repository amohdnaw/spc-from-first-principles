#!/usr/bin/env bash
# Render every act, then produce the three things the website needs from each:
# the 1080p60 mp4, a WebVTT caption track, and a poster frame.
#
#   ./build-media.sh              silent, correctly paced (fast, no network)
#   SPCLAB_VOICE=1 ./build-media.sh   narrated + captions (needs network for gTTS)
#   SPCLAB_VOICE=1 SPCLAB_VOICE_SERVICE=recorder ./build-media.sh   your own voice
#
# Posters are not taken at a fixed timestamp: an earlier version grabbed 62% of
# runtime and landed on an empty transition frame in SPCGallery. Each poster is
# now chosen by scoring candidate frames on how much non-background pixel area
# they carry, and taking the best.
set -euo pipefail
cd "$(dirname "$0")"

VENV=.venv/bin
QUALITY="${QUALITY:--qh}"
OUTDIR=media/videos
POSTERS=../posters
CAPTIONS=../captions
LOGS=media/logs

# scene file : class : poster name
SCENES=(
  "level01_scene:Level01:level01"
  "level02_scene:Level02:level02"
  "level03_scene:Level03:level03"
  "level04_scene:Level04:level04"
  "level05_scene:Level05:level05"
  "level06_scene:Level06:level06"
  "level07_scene:Level07:level07"
  "level07_case_scene:Level07Case:level07-case"
  "level08_scene:Level08:level08"
  "level09_scene:Level09:level09"
  "scenes:SPCGallery:gallery"
  "scenes2:ConstantsAct:constants"
  "scenes2:EWMAMemory:ewma"
)

mkdir -p "$POSTERS" "$CAPTIONS"
echo "voice=${SPCLAB_VOICE:-0} service=${SPCLAB_VOICE_SERVICE:-kokoro} quality=$QUALITY"
echo

# ONLY=Level01 ./build-media.sh rebuilds one act (plus its poster and captions)
# instead of all ten. Re-rendering nine unchanged acts to fix one is 20 wasted
# minutes and a chance to break something that was working.
for entry in "${SCENES[@]}"; do
  if [ -n "${ONLY:-}" ] && [ "${entry#*:}" != "${ONLY}:"* ]; then
    case "$entry" in *":${ONLY}:"*) ;; *) continue ;; esac
  fi
  IFS=: read -r file klass poster <<<"$entry"
  printf '=== %-14s %s\n' "$klass" "(src/spclab/$file.py)"

  mkdir -p "$LOGS"
  log="$LOGS/$klass.log"
  PYTHONPATH=src $VENV/manim "$QUALITY" --disable_caching \
    "src/spclab/$file.py" "$klass" >"$log" 2>&1 \
    || { echo "   RENDER FAILED — tail of $log:"; tail -20 "$log"; exit 1; }

  # narration.py is allowed to fall back from Kokoro to gTTS when the torch
  # interpreter is missing, so a voice problem does not stop a build. Shipping
  # that fallback is a different thing: the act would be in the wrong voice
  # while the manifest below still said kokoro. This script used to send the
  # render to /dev/null, which is exactly how the sibling MSA site shipped an
  # act in gTTS for five days with every other artifact correct.
  if grep -q 'kokoro unavailable' "$log"; then
    echo "   KOKORO FELL BACK TO gTTS — refusing to ship:"
    grep 'kokoro unavailable' "$log" | sed 's/^/     /'
    exit 1
  fi

  mp4=$(find "$OUTDIR/$file" -name "$klass.mp4" -not -path '*partial*' | head -1)
  [ -z "$mp4" ] && { echo "   no mp4 produced"; exit 1; }

  # Move the moov atom to the front. Manim's ffmpeg writes it after mdat, so a
  # browser opening the file over HTTP has no index until it has range-fetched
  # the tail — which shows up as the first play stuttering or refusing to seek,
  # and then being fine once cached. The re-mux is a stream copy: the video and
  # audio bytes are identical, only the container layout changes.
  if ! ffprobe -v error -show_entries format_tags -of default=nw=1 "$mp4" >/dev/null 2>&1; then
    echo "   ffprobe failed on $mp4"; exit 1
  fi
  ffmpeg -v error -i "$mp4" -c copy -movflags +faststart "${mp4%.mp4}.fs.mp4" -y \
    || { echo "   FASTSTART REMUX FAILED"; exit 1; }
  mv -f "${mp4%.mp4}.fs.mp4" "$mp4"
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4")
  has_audio=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$mp4" | head -1)

  # captions: manim-voiceover drops an .srt beside the mp4; browsers want WebVTT
  srt="${mp4%.mp4}.srt"
  if [ -f "$srt" ]; then
    { echo "WEBVTT"; echo; sed -E 's/([0-9]{2}:[0-9]{2}:[0-9]{2}),([0-9]{3})/\1.\2/g' "$srt"; } \
      > "$CAPTIONS/$poster.vtt"
    cues=$(grep -c ' --> ' "$CAPTIONS/$poster.vtt" || true)
  else
    cues=0
  fi

  # poster: best of 11 candidate frames by ink coverage. The same pass writes
  # the build manifest, because it is the only place that knows what the poster
  # scorer chose — and a poster time no gate can read is a poster time that can
  # silently go back to landing on an empty transition frame.
  PYTHONPATH=src $VENV/python - \
    "$mp4" "$POSTERS/$poster.jpg" "${mp4%.mp4}.manifest.json" \
    "$file" "$klass" "$poster" "${SPCLAB_VOICE_SERVICE:-kokoro}" \
    "${SPCLAB_VOICE:-0}" "$cues" <<'PY'
import json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
from PIL import Image
mp4, out, manifest, scene, klass, poster, service, voice, cues = sys.argv[1:10]
info = json.loads(subprocess.run(
    ['ffprobe','-v','error','-show_format','-show_streams','-of','json',mp4],
    capture_output=True,text=True,check=True).stdout)
vid = next(s for s in info['streams'] if s['codec_type'] == 'video')
aud = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
dur = float(info['format']['duration'])
num, den = vid['r_frame_rate'].split('/')
def ink(p):
    im = Image.open(p).convert('RGB').resize((320,180))
    px = list(im.getdata()); bg = Counter(px).most_common(1)[0][0]
    return sum(1 for c in px if max(abs(c[i]-bg[i]) for i in range(3)) > 18)/len(px)
best = (-1, dur/2)
with tempfile.TemporaryDirectory() as td:
    for i in range(4, 15):
        t = round(dur*i/16, 2)
        f = f'{td}/{i}.jpg'
        subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',mp4,'-frames:v','1','-q:v','3',f,'-y'],check=True)
        s = ink(f)
        if s > best[0]: best = (s, t)
subprocess.run(['ffmpeg','-v','error','-ss',str(best[1]),'-i',mp4,'-frames:v','1','-q:v','4',out,'-y'],check=True)
Path(manifest).write_text(json.dumps({
    'scene': scene,
    'klass': klass,
    'mp4': Path(mp4).name,
    'service': service,
    'voice': voice not in ('', '0', 'false', 'no', 'off'),
    'duration': round(dur, 3),
    'width': vid['width'],
    'height': vid['height'],
    'fps': round(float(num)/float(den), 3),
    'audio_codec': aud['codec_name'] if aud else None,
    'poster': f'posters/{poster}.jpg',
    'poster_time': best[1],
    'poster_ink': round(best[0], 5),
    'captions': f'captions/{poster}.vtt' if int(cues) else None,
    'cues': int(cues),
}, indent=2) + '\n')
print(f"   poster t={best[1]}s ink={best[0]*100:.1f}%  manifest {Path(manifest).name}")
PY

  printf '   %.1fs  audio=%s  captions=%s cues\n' "$dur" "${has_audio:-none}" "$cues"
done

echo
echo "done. posters -> $POSTERS  captions -> $CAPTIONS"
