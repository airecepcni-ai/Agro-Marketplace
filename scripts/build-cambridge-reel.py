#!/usr/bin/env python3
"""Build a <=20s 9:16 Facebook Reel for LandStal Cambridge rollers.
Native 9:16 phone clips, hook-first structure, Czech overlays + CTA, silent."""
import subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/home/user/Agro-Marketplace")
SDIR = ROOT / "output/cambridge/source"
OVDIR = ROOT / "output/cambridge/overlays"
OUT = ROOT / "output/cambridge/Cambridge-reel.mp4"
OVDIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 25
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BLUE=(23,74,168,235); WHITE=(255,255,255,255); SCRIM=(8,16,34,180)

# file, in, dur
SEG = [
    ("c4", 6.0, 3.0),   # hook: rings rolling soil
    ("c5", 3.5, 2.6),   # wide hero reveal
    ("c2", 1.5, 2.5),   # rear rings action
    ("c1", 6.0, 2.5),   # ring/spring detail
    ("c1",54.0, 2.6),   # soil firmed
    ("c3", 5.0, 2.6),   # ring detail
    ("c5", 7.0, 3.4),   # wide hero + CTA
]
starts=[]; t=0.0
for _,_,d in SEG: starts.append(t); t+=d
TOTAL=t

def font(b,s): return ImageFont.truetype(FB if b else FR, s)
_D=ImageDraw.Draw(Image.new("RGBA",(10,10)))
def tw(txt,f): return _D.textbbox((0,0),txt,font=f)[2]
def fit(txt,bold,maxs,maxw,mins=32):
    s=maxs
    while s>mins and tw(txt,font(bold,s))>maxw: s-=2
    return font(bold,s)
def wrap(txt,f,maxw):
    words=txt.split(); lines=[]; cur=""
    for w in words:
        t2=(cur+" "+w).strip()
        if tw(t2,f)<=maxw: cur=t2
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines
def shadow(img,pos,txt,f,fill=WHITE,anchor="ma",blur=6):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text((pos[0]+3,pos[1]+4),txt,font=f,fill=(0,0,0,200),anchor=anchor)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(pos,txt,font=f,fill=fill,anchor=anchor)

def make(kind,title,sub=None,cta=None):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img); cx=W//2
    if kind=="hook":
        f=fit(title,True,96,W-120)
        lines=wrap(title,f,W-120)
        lh=int(f.size*1.15); total=lh*len(lines); yc=470
        d.rectangle([0,yc-70,W,yc+total+40],fill=(6,12,28,140))
        for i,l in enumerate(lines):
            shadow(img,(cx,yc+i*lh),l,f,blur=7)
    elif kind=="lower":
        f=fit(title,True,84,W-120); y=H-540
        d.rectangle([0,y-30,W,y+f.size+40],fill=(6,12,28,120))
        shadow(img,(cx,y),title,f)
    elif kind=="chip":
        f=fit(title,True,64,W-230); wtxt=tw(title,f); y=H-500
        half=min(wtxt//2+46,(W-40)//2)
        d.rounded_rectangle([cx-half,y-26,cx+half,y+f.size+34],radius=22,fill=BLUE)
        shadow(img,(cx,y),title,f,blur=4)
    elif kind=="endcta":
        d.rectangle([0,H//2-250,W,H//2+250],fill=SCRIM)
        f1=fit(title,True,104,W-140); shadow(img,(cx,H//2-210),title,f1)
        if sub:
            f2=fit(sub,False,52,W-160); shadow(img,(cx,H//2-210+f1.size+20),sub,f2,fill=(220,230,255,255))
        if cta:
            fc=fit(cta,True,60,W-160)
            yb=H//2+70
            wc=tw(cta,fc); half=min(wc//2+42,(W-40)//2)
            d.rounded_rectangle([cx-half,yb-24,cx+half,yb+fc.size+30],radius=20,fill=BLUE)
            shadow(img,(cx,yb),cta,fc,blur=4)
    return img

OVER=[  # kind,t0,t1,title,sub,cta
    ("hook",  0.2, 3.0, "Perfektní seťové lůžko?", None, None),
    ("lower", 3.2, 5.6, "Cambridge válce · LandStal", None, None),
    ("chip", 10.7,13.2, "Urovná · Rozdrtí · Utuží", None, None),
    ("endcta",15.9,TOTAL,"Cambridge válce","LandStal","Máte zájem? Napište nám!"),
]
ov=[]
for i,o in enumerate(OVER):
    kind,t0,t1,ti,su,ct=o
    p=OVDIR/f"ov_{i}.png"; make(kind,ti,su,ct).save(p); ov.append((p,t0,t1))

cmd=["ffmpeg","-hide_banner","-y"]
for fn,ins,dur in SEG:
    cmd+=["-ss",f"{ins}","-t",f"{dur}","-i",str(SDIR/f"{fn}.mp4")]
n=len(SEG)
cmd+=["-f","lavfi","-t",f"{TOTAL}","-i","anullsrc=r=44100:cl=stereo"]
for p,t0,t1 in ov:
    cmd+=["-loop","1","-t",f"{t1-t0:.3f}","-i",str(p)]

filt=[]; vl=[]
for i,(fn,ins,dur) in enumerate(SEG):
    filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},fps={FPS},setsar=1,format=yuv420p[v{i}]")
    vl.append(f"[v{i}]")
filt.append("".join(vl)+f"concat=n={n}:v=1:a=0[vcat]")

prev="[vcat]"; F=0.35; midx=n
for j,(p,t0,t1) in enumerate(ov):
    idx=midx+1+j; dur=t1-t0; fo=max(0.0,dur-F)
    filt.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d={F}:alpha=1,"
                f"fade=t=out:st={fo:.3f}:d={F}:alpha=1,setpts=PTS-STARTPTS+{t0:.3f}/TB[o{j}]")
    out=f"[c{j}]" if j<len(ov)-1 else "[vout]"
    filt.append(f"{prev}[o{j}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'{out}")
    prev=out

cmd+=["-filter_complex",";".join(filt),
      "-map","[vout]","-map",f"{midx}:a",
      "-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
      "-r",str(FPS),"-c:a","aac","-b:a","128k","-t",f"{TOTAL}",
      "-movflags","+faststart",str(OUT)]

print(f"Building Cambridge reel ({TOTAL:.1f}s, {W}x{H})...")
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode!=0: print("ERROR:\n",r.stderr[-2600:])
else: print(f"Done: {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")
