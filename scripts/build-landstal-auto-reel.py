#!/usr/bin/env python3
"""Build a <=20s 9:16 reel for the LandStal x AgXeed autonomous cultivation clip.
Source was corrupted past ~54s; uses salvaged head. Blurred-pad 9:16, Czech
overlays, silent (music added later)."""
import subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/home/user/Agro-Marketplace")
SRC = ROOT / "output/reel-new/salvage.mp4"
OVDIR = ROOT / "output/reel-new/overlays"
OUT = ROOT / "output/reel-new/LandStal-auto-reel.mp4"
OVDIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 25
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BLUE = (23, 74, 168, 235); WHITE=(255,255,255,255); SCRIM=(8,16,34,180)

# in, dur  (from salvage.mp4)
SEG = [
    (1.5, 2.7),   # opener robot+cultivator
    (8.0, 2.0),   # AgXeed brand
    (16.9,2.2),   # LiDAR sensor
    (20.7,2.2),   # roller working
    (23.3,1.9),   # hydraulics/tech
    (29.2,2.5),   # tines dramatic
    (43.3,3.0),   # aerial wide
    (50.4,2.5),   # robot hero wide
]
starts=[]; t=0.0
for _,d in SEG: starts.append(t); t+=d
TOTAL=t

def font(b,s): return ImageFont.truetype(FB if b else FR, s)
def shadow(img,pos,txt,f,fill=WHITE,anchor="ma",blur=6):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text((pos[0]+3,pos[1]+4),txt,font=f,fill=(0,0,0,190),anchor=anchor)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(pos,txt,font=f,fill=fill,anchor=anchor)

def make(kind,title,sub=None):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img); cx=W//2
    if kind=="title":
        lines=title.split("\n")
        d.rectangle([0,H-620,W,H],fill=(6,12,28,120))
        y=H-500
        for i,l in enumerate(lines):
            shadow(img,(cx,y+i*130),l,font(True,104))
        if sub: shadow(img,(cx,y+len(lines)*130+18),sub,font(False,48),fill=(225,233,255,255))
    elif kind=="chip":
        f=font(True,64); tw=d.textbbox((0,0),title,font=f)[2]; y=H-430
        d.rounded_rectangle([cx-tw//2-46,y-26,cx+tw//2+46,y+94],radius=22,fill=BLUE)
        shadow(img,(cx,y),title,f,blur=4)
    elif kind=="endbrand":
        d.rectangle([0,H//2-190,W,H//2+190],fill=SCRIM)
        shadow(img,(cx,H//2-140),title,font(True,120))
        if sub: shadow(img,(cx,H//2+40),sub,font(True,58),fill=(255,224,130,255))
    return img

OVER=[  # kind,t0,t1,title,sub
    ("title",   0.2, 2.7, "BUDOUCNOST\nZPRACOVÁNÍ PŮDY","LandStal × AgXeed"),
    ("chip",    4.8, 6.9, "Bez řidiče", None),
    ("chip",   11.1,13.5, "Autonomně · Přesně · Efektivně", None),
    ("endbrand",16.6,TOTAL,"LandStal","× AgXeed"),
]
ov=[]
for i,(k,t0,t1,ti,su) in enumerate(OVER):
    p=OVDIR/f"ov_{i}.png"; make(k,ti,su).save(p); ov.append((p,t0,t1))

cmd=["ffmpeg","-hide_banner","-y"]
for ins,dur in SEG:
    cmd+=["-ss",f"{ins}","-t",f"{dur}","-i",str(SRC)]
n=len(SEG)
cmd+=["-f","lavfi","-t",f"{TOTAL}","-i","anullsrc=r=44100:cl=stereo"]  # silent track
for p,t0,t1 in ov:
    cmd+=["-loop","1","-t",f"{t1-t0:.3f}","-i",str(p)]

filt=[]; vl=[]
for i,(ins,dur) in enumerate(SEG):
    filt.append(
        f"[{i}:v]split=2[b{i}][g{i}];"
        f"[b{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"boxblur=24:2,eq=brightness=-0.05:saturation=0.85[bb{i}];"
        f"[g{i}]scale={W}:-2,setsar=1[gg{i}];"
        f"[bb{i}][gg{i}]overlay=0:(H-h)/2,fps={FPS},setsar=1,format=yuv420p[v{i}]")
    vl.append(f"[v{i}]")
filt.append("".join(vl)+f"concat=n={n}:v=1:a=0[vcat]")

prev="[vcat]"; F=0.35; music_idx=n
for j,(p,t0,t1) in enumerate(ov):
    idx=music_idx+1+j; dur=t1-t0; fo=max(0.0,dur-F)
    filt.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d={F}:alpha=1,"
                f"fade=t=out:st={fo:.3f}:d={F}:alpha=1,"
                f"setpts=PTS-STARTPTS+{t0:.3f}/TB[o{j}]")
    out=f"[c{j}]" if j<len(ov)-1 else "[vout]"
    filt.append(f"{prev}[o{j}]overlay=0:0:eof_action=pass:"
                f"enable='between(t,{t0:.3f},{t1:.3f})'{out}")
    prev=out

cmd+=["-filter_complex",";".join(filt),
      "-map","[vout]","-map",f"{music_idx}:a",
      "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
      "-r",str(FPS),"-c:a","aac","-b:a","128k","-t",f"{TOTAL}",
      "-movflags","+faststart",str(OUT)]

print(f"Building LandStal auto reel ({TOTAL:.1f}s, {W}x{H})...")
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode!=0:
    print("FFMPEG ERROR:\n",r.stderr[-2600:])
else:
    print(f"Done: {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")
