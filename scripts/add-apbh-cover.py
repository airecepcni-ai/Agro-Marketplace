#!/usr/bin/env python3
"""Prepend a ~0.2s hero cover frame to each APBH ad version (FB thumbnail hook)."""
import subprocess, os
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path("/home/user/Agro-Marketplace")
PHOTO = "/root/.claude/uploads/8908e378-a568-5cdb-b420-98e1c664fa6a/0c7f1983-IMG_0992.jpeg"
FINAL = ROOT / "output/apbh-ad/final"
OUT   = ROOT / "output/apbh-ad/final-cover"
COVDIR= ROOT / "output/apbh-ad/covers"
OUT.mkdir(parents=True, exist_ok=True)
COVDIR.mkdir(parents=True, exist_ok=True)

COVER_DUR = 0.2

# version -> (W, H, framing mode matching the video)
VERSIONS = {
    "v1": (1920, 1080, "fill"),
    "v2": (1080, 1080, "pad"),
    "v3": (1080, 1350, "pad"),
    "v4": (1080, 1920, "pad"),
}

def make_cover(W, H, mode):
    im = Image.open(PHOTO).convert("RGB")
    if mode == "fill":
        s = max(W/im.width, H/im.height)
        r = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
        l, t = (r.width-W)//2, (r.height-H)//2
        return r.crop((l, t, l+W, t+H))
    # blurred pad (fit width, blurred cover background)
    s = max(W/im.width, H/im.height)
    bg = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l, t = (bg.width-W)//2, (bg.height-H)//2
    bg = bg.crop((l, t, l+W, t+H)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.9)
    fw = W; fh = round(im.height * W / im.width)
    fg = im.resize((fw, fh), Image.LANCZOS)
    canvas = bg.copy()
    canvas.paste(fg, (0, (H-fh)//2))
    return canvas

for v, (W, H, mode) in VERSIONS.items():
    cov = COVDIR / f"cover_{v}.png"
    make_cover(W, H, mode).save(cov)
    final = FINAL / f"APBH-Pro-420_{v}.mp4"
    out = OUT / f"APBH-Pro-420_{v}.mp4"

    cmd = [
        "ffmpeg", "-hide_banner", "-y",
        "-loop", "1", "-framerate", "25", "-t", str(COVER_DUR), "-i", str(cov),
        "-f", "lavfi", "-t", str(COVER_DUR), "-i", "anullsrc=r=44100:cl=stereo",
        "-i", str(final),
        "-filter_complex",
        f"[0:v]scale={W}:{H},setsar=1,fps=25,format=yuv420p[cv];"
        f"[2:v]scale={W}:{H},setsar=1,fps=25,format=yuv420p[mv];"
        f"[cv][mv]concat=n=2:v=1:a=0[vout];"
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo[sa];"
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo[ma];"
        f"[sa][ma]concat=n=2:v=0:a=1[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-r", "25", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out),
    ]
    print(f"[{v}] prepending cover -> {out.name} ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[{v}] ERROR:\n", r.stderr[-1800:])
    else:
        dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1", str(out)], capture_output=True, text=True).stdout.strip()
        print(f"[{v}] done ({float(dur):.2f}s, {os.path.getsize(out)/1e6:.1f} MB)")
