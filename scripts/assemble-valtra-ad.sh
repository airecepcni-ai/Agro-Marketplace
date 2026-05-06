#!/usr/bin/env bash
# Assembles all 4 Valtra clips into a final ad with dramatic music on clip 2.
# Usage: ./scripts/assemble-valtra-ad.sh [music_file.mp3]
# If no music file given, downloads a free royalty-free dramatic track.
set -euo pipefail
cd "$(dirname "$0")/.."

CLIP1="output/valtra-clip1-test/clip1-dream-begins.mp4"
OUTDIR="output/valtra-ad-final"
CLIP2="$OUTDIR/clip2-assembly.mp4"
CLIP3="$OUTDIR/clip3-cabin-snaps-on.mp4"
CLIP4="$OUTDIR/clip4-reality-sunset.mp4"
FINAL="$OUTDIR/valtra-ad-FINAL.mp4"
MUSIC="${1:-}"

echo "════════════════════════════════════════"
echo "Valtra Ad — Assembly"
echo "════════════════════════════════════════"

# Check all clips exist
for f in "$CLIP1" "$CLIP2" "$CLIP3" "$CLIP4"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing clip: $f"
    echo "Run generate-valtra-clips-2-4.py first."
    exit 1
  fi
done

# Download dramatic music if not provided
if [ -z "$MUSIC" ]; then
  MUSIC="$OUTDIR/dramatic-music.mp3"
  if [ ! -f "$MUSIC" ]; then
    echo "Downloading royalty-free dramatic track (Kevin MacLeod — Stormfront)..."
    curl -sS -L \
      "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Stormfront.mp3" \
      -o "$MUSIC" || {
      echo "Download failed. Please provide a music file:"
      echo "  ./scripts/assemble-valtra-ad.sh /path/to/music.mp3"
      exit 1
    }
    echo "Music saved: $MUSIC"
  fi
fi

echo "Music: $MUSIC"

# Step 1 — Normalise all clips to same codec/resolution/fps
echo ""
echo "[1/4] Normalising clips..."
for clip in "$CLIP1" "$CLIP2" "$CLIP3" "$CLIP4"; do
  base=$(basename "$clip" .mp4)
  norm="$OUTDIR/${base}_norm.mp4"
  ffmpeg -y -i "$clip" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
    -r 24 -c:v libx264 -preset fast -crf 18 \
    -c:a aac -ar 44100 -ac 2 \
    "$norm" -loglevel error
  echo "  Normalised: $norm"
done

# Step 2 — Add dramatic music to clip 2 (assembly scene)
# Music is mixed under any existing audio at 0.8 volume; original audio stays at 0.3
echo ""
echo "[2/4] Adding dramatic music to clip 2 (assembly)..."
CLIP2_NORM="$OUTDIR/clip2-assembly_norm.mp4"
CLIP2_MUSIC="$OUTDIR/clip2-assembly_music.mp4"
ffmpeg -y \
  -i "$CLIP2_NORM" \
  -i "$MUSIC" \
  -filter_complex \
    "[0:a]volume=0.3[orig];
     [1:a]atrim=0:15,asetpts=PTS-STARTPTS,volume=0.85[mus];
     [orig][mus]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -ar 44100 \
  -shortest \
  "$CLIP2_MUSIC" -loglevel error
echo "  Done: $CLIP2_MUSIC"

# Step 3 — Concatenate: clip1 + clip2(music) + clip3 + clip4
echo ""
echo "[3/4] Concatenating all 4 clips..."
CLIP1_NORM="$OUTDIR/clip1-dream-begins_norm.mp4"
CLIP3_NORM="$OUTDIR/clip3-cabin-snaps-on_norm.mp4"
CLIP4_NORM="$OUTDIR/clip4-reality-sunset_norm.mp4"

# Write concat list
CONCAT_LIST="$OUTDIR/concat.txt"
cat > "$CONCAT_LIST" <<EOF
file '$(realpath "$CLIP1_NORM")'
file '$(realpath "$CLIP2_MUSIC")'
file '$(realpath "$CLIP3_NORM")'
file '$(realpath "$CLIP4_NORM")'
EOF

ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST" \
  -c:v libx264 -preset fast -crf 17 \
  -c:a aac -ar 44100 -ac 2 \
  "$FINAL" -loglevel error

# Step 4 — Cleanup intermediate files
echo ""
echo "[4/4] Cleaning up intermediate files..."
rm -f "$OUTDIR"/*_norm.mp4 "$OUTDIR/clip2-assembly_music.mp4" "$CONCAT_LIST"

echo ""
echo "════════════════════════════════════════"
echo "FINAL AD: $FINAL"
SIZE=$(du -sh "$FINAL" | cut -f1)
echo "File size: $SIZE"
DURATION=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | xargs printf "%.1f")
echo "Duration: ${DURATION}s"
echo "════════════════════════════════════════"
