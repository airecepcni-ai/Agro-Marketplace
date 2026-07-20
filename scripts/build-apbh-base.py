#!/usr/bin/env python3
"""Build the 40s base master cut for the APBH ad (b-roll only, 1080p 16:9, no audio)."""
import subprocess, sys
from pathlib import Path

SRC = "output/apbh-ad/source/APBH-PRO-600.mp4"
OUT = "output/apbh-ad/base-master.mp4"

# (start_seconds, duration_seconds, label)
SEGMENTS = [
    (33.5, 4.0, "hero-side"),
    (28.5, 3.5, "aerial-1"),
    (25.5, 3.0, "tine-detail"),
    (47.0, 4.0, "roller"),
    (44.0, 3.5, "hydraulic"),
    (41.5, 3.0, "spring"),
    (58.5, 3.5, "rear-working"),
    (128.5, 4.0, "soil-throw"),
    (150.5, 4.0, "hero-tire"),
    (145.5, 4.0, "aerial-beauty"),
    (164.0, 3.5, "endcard"),
]

cmd = ["ffmpeg", "-hide_banner", "-y"]
for start, dur, _ in SEGMENTS:
    cmd += ["-ss", str(start), "-t", str(dur), "-i", SRC]

# Scale each to 1080p 16:9, normalise fps/sar, then concat
filt = []
labels = []
for i in range(len(SEGMENTS)):
    filt.append(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,setsar=1,fps=25,format=yuv420p[v{i}]")
    labels.append(f"[v{i}]")
filt.append("".join(labels) + f"concat=n={len(SEGMENTS)}:v=1:a=0[vout]")

cmd += ["-filter_complex", ";".join(filt),
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]

print("Building base master (40s, 1080p)...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERROR:\n", r.stderr[-2000:])
    sys.exit(1)

# Report
probe = subprocess.run(["ffprobe","-v","error","-show_entries",
    "format=duration:stream=width,height","-of","default=noprint_wrappers=1",OUT],
    capture_output=True, text=True)
print(probe.stdout)
print(f"Base master built: {OUT}")
