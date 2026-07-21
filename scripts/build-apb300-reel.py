#!/usr/bin/env python3
"""Build a <=20s 9:16 Facebook Reel for the APB300 first-customer-test.
Mixes portrait photos (Ken Burns) + native-9:16 phone videos, Czech overlays,
natural ambient audio (no added music)."""
import subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/home/user/Agro-Marketplace")
SRC = ROOT / "output/apb300/source/APB 300 Test"
OVDIR = ROOT / "output/apb300/overlays"
OUT = ROOT / "output/apb300/APB300-reel.mp4"
OVDIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 25
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BLUE  = (23, 74, 168, 235)
WHITE = (255, 255, 255, 255)
SCRIM = (8, 16, 34, 175)

def V(n): return str(SRC / f"WhatsApp Video 2026-07-20 at 4.57.34 PM{n}.mp4")
def P(n): return str(SRC / f"WhatsApp Image 2026-07-20 at 4.57.3{n}.jpeg")

# type, file, in, dur
SEG = [
    ("photo", P("5 PM"),       0.0, 2.6),   # ph07 hero front 3/4
    ("video", V(""),           3.0, 2.6),   # vid01 tractor pulling
    ("video", V(" (1)"),       2.0, 2.4),   # vid02 tines close-up
    ("video", V(" (10)"),      0.0, 1.8),   # vid11 wet-soil detail
    ("photo", P("4 PM (6)"),   0.0, 2.6),   # ph06 side profile beauty
    ("video", V(" (5)"),       4.0, 2.6),   # vid06 tractor working moody
    ("video", V(" (9)"),       8.0, 2.6),   # vid10 wide field pass
    ("photo", P("4 PM (2)"),   0.0, 2.4),   # ph02 Valtra + cultivator hero
]
starts, t = [], 0.0
for _,_,_,d in SEG:
    starts.append(t); t += d
TOTAL = t

# ── overlays ────────────────────────────────────────────────────────────────
def font(b,s): return ImageFont.truetype(FONT_BOLD if b else FONT_REG, s)
def shadow(img,pos,txt,f,fill=WHITE,anchor="ma",blur=6):
    lay = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(lay); d.text((pos[0]+3,pos[1]+4), txt, font=f, fill=(0,0,0,190), anchor=anchor)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(pos, txt, font=f, fill=fill, anchor=anchor)

def make_overlay(kind, title, sub=None):
    img = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(img)
    cx = W//2
    if kind == "title":
        d.rectangle([0, H-560, W, H], fill=(6,12,28,120))
        shadow(img,(cx,H-430), title, font(True,120))
        shadow(img,(cx,H-290), sub, font(False,50), fill=(225,233,255,255))
    elif kind == "chip":
        f=font(True,66); tw=d.textbbox((0,0),title,font=f)[2]
        y=H-430
        d.rounded_rectangle([cx-tw//2-46, y-26, cx+tw//2+46, y+96], radius=22, fill=BLUE)
        shadow(img,(cx,y), title, f, blur=4)
    elif kind == "endbrand":
        d.rectangle([0, H//2-190, W, H//2+190], fill=SCRIM)
        shadow(img,(cx,H//2-140), title, font(True,118))
        shadow(img,(cx,H//2+30), sub, font(True,64), fill=(255,224,130,255))
    return img

OVER = [  # kind, t0, t1, title, sub
    ("title",    0.2, 2.6, "APB300", "První testování u zákazníka"),
    ("chip",     7.7, 9.4, "Podmínky: lehce mokré", None),
    ("chip",    12.1,14.6, "Zvládá i vlhké podmínky", None),
    ("endbrand",17.3,TOTAL,"LandStal", "APB300"),
]
ov_files=[]
for i,(kind,t0,t1,ti,su) in enumerate(OVER):
    p = OVDIR / f"ov_{i}.png"; make_overlay(kind,ti,su).save(p)
    ov_files.append((p,t0,t1))

def has_audio(path):
    r = subprocess.run(["ffprobe","-v","error","-select_streams","a","-show_entries",
        "stream=index","-of","csv=p=0",path], capture_output=True, text=True)
    return bool(r.stdout.strip())

# ── ffmpeg build ────────────────────────────────────────────────────────────
cmd = ["ffmpeg","-hide_banner","-y"]
for typ,f,ins,dur in SEG:
    if typ=="photo":
        cmd += ["-i", f]          # single frame; zoompan d=frames expands it
    else:
        cmd += ["-ss",f"{ins}","-t",f"{dur}","-i",f]
n_seg = len(SEG)
for p,_,_ in ov_files:
    # overlay window duration = t1-t0
    pass
for i,(p,t0,t1) in enumerate(ov_files):
    cmd += ["-loop","1","-t",f"{t1-t0:.3f}","-i",str(p)]

filt=[]; vlabels=[]; alabels=[]
for i,(typ,f,ins,dur) in enumerate(SEG):
    frames=round(dur*FPS)
    if typ=="photo":
        filt.append(
            f"[{i}:v]scale=1350:2400:force_original_aspect_ratio=increase,crop=1350:2400,"
            f"zoompan=z='min(1.0+0.09*on/{frames},1.09)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
            f"setsar=1,format=yuv420p[v{i}]")
        filt.append(f"aevalsrc=0:d={dur}:s=44100:channel_layout=stereo[a{i}]")
    else:
        filt.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"fps={FPS},setsar=1,format=yuv420p[v{i}]")
        if has_audio(f):
            filt.append(f"[{i}:a]atrim=0:{dur},asetpts=N/SR/TB,"
                        f"aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        else:
            filt.append(f"aevalsrc=0:d={dur}:s=44100:channel_layout=stereo[a{i}]")
    vlabels.append(f"[v{i}]"); alabels.append(f"[a{i}]")

inter="".join(f"{vlabels[i]}{alabels[i]}" for i in range(n_seg))
filt.append(f"{inter}concat=n={n_seg}:v=1:a=1[vcat][aout]")

# overlays
prev="[vcat]"; F=0.35
for j,(p,t0,t1) in enumerate(ov_files):
    idx = n_seg + j
    dur=t1-t0; fo=max(0.0,dur-F)
    filt.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d={F}:alpha=1,"
                f"fade=t=out:st={fo:.3f}:d={F}:alpha=1,"
                f"setpts=PTS-STARTPTS+{t0:.3f}/TB[ov{j}]")
    out = f"[o{j}]" if j<len(ov_files)-1 else "[vout]"
    filt.append(f"{prev}[ov{j}]overlay=0:0:eof_action=pass:"
                f"enable='between(t,{t0:.3f},{t1:.3f})'{out}")
    prev=out
filt.append(f"[aout]afade=t=in:st=0:d=0.3,afade=t=out:st={TOTAL-0.4:.2f}:d=0.4[afin]")

cmd += ["-filter_complex",";".join(filt),
        "-map","[vout]","-map","[afin]",
        "-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
        "-r",str(FPS),"-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT)]

print(f"Building APB300 reel ({TOTAL:.1f}s, {W}x{H})...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode!=0:
    print("FFMPEG ERROR:\n", r.stderr[-2600:])
else:
    print(f"Done: {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")
