#!/usr/bin/env python3
"""Build 4 styled/formatted versions of the APBH Pro 420 Facebook ad.

V1  16:9  lower-thirds
V2  1:1   title cards
V3  4:5   feature callouts
V4  9:16  cinematic minimal

Overlays rendered as full-canvas transparent PNGs (Pillow), composited with
timed alpha fades in ffmpeg. Non-16:9 formats use blurred-pad framing so no
footage is cropped. Audio = royalty-free 'Inspired' (Kevin MacLeod, CC-BY 4.0).
"""
import subprocess, sys, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/home/user/Agro-Marketplace")
MASTER = ROOT / "output/apbh-ad/base-master.mp4"
MUSIC = ROOT / "output/apbh-ad/music/Inspired.mp3"
OVDIR = ROOT / "output/apbh-ad/overlays"
OUTDIR = ROOT / "output/apbh-ad/final"
OVDIR.mkdir(parents=True, exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)

DUR = 40.4
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BLUE   = (20, 60, 150)
BLUEA  = (20, 60, 150, 235)
WHITE  = (255, 255, 255, 255)
SCRIM  = (8, 16, 34, 175)

def font(bold, size):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def tsize(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1], b[1]

def shadow_text(img, pos, text, f, fill=WHITE, anchor="la", blur=6, sh=(0,0,0,190)):
    """Draw text with a soft drop shadow onto RGBA img."""
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    d.text((pos[0]+3, pos[1]+4), text, font=f, fill=sh, anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)
    d2 = ImageDraw.Draw(img)
    d2.text(pos, text, font=f, fill=fill, anchor=anchor)

def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)

def wrap(draw, text, f, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tsize(draw, t, f)[0] <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# ── Element content + timing (absolute master timeline) ─────────────────────
def elements_for(version):
    base = [
        dict(key="brand", t0=0.5, t1=5.6, kind="brand",
             title="APBH Pro 420", sub="Kombinovaný radličkový kypřič"),
        dict(key="feat1", t0=8.3, t1=12.6, kind="feature", text="Těžký válec"),
        dict(key="feat2", t0=12.9, t1=17.8, kind="feature", text="Hydraulické nastavení hloubky"),
        dict(key="feat3", t0=22.5, t1=27.2, kind="feature", text="Připraveno na těžké podmínky"),
        dict(key="cta",   t0=30.3, t1=37.9, kind="cta",  text="Brzy k vyzkoušení na vašem poli"),
        dict(key="endtag",t0=38.3, t1=40.3, kind="endtag", text="LandStal CZ"),
    ]
    if version == "v4":  # cinematic minimal
        return [
            dict(key="brand", t0=0.6, t1=5.8, kind="brand",
                 title="APBH Pro 420", sub="Kombinovaný radličkový kypřič"),
            dict(key="feat1", t0=9.0, t1=14.0, kind="feature", text="Těžký válec"),
            dict(key="feat2", t0=14.3, t1=18.5, kind="feature", text="Hydraulické nastavení hloubky"),
            dict(key="cta",   t0=30.3, t1=38.2, kind="cta", text="Brzy k vyzkoušení\nna vašem poli"),
        ]
    return base

# ── Per-version renderers ───────────────────────────────────────────────────
def render(version, W, H, el, fgrect):
    """Return a full-canvas RGBA overlay for one element.
    fgrect = (fx, fy, fw, fh) footage band within canvas (for placing text off the blur)."""
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(img)
    k = el["kind"]

    if version == "v1":  # 16:9 lower-thirds
        barx = 90
        if k == "brand":
            f1, f2 = font(True, 96), font(False, 46)
            y = H - 250
            d.rectangle([0, y-40, W, H], fill=(6,12,28,150))
            d.rectangle([barx-28, y+6, barx-14, y+180], fill=BLUEA)
            shadow_text(img, (barx, y), el["title"], f1)
            shadow_text(img, (barx, y+118), el["sub"], f2)
        elif k in ("feature",):
            f1 = font(True, 66)
            tw = tsize(d, el["text"], f1)[0]
            y = H - 170
            rounded(d, [barx-24, y-22, barx+tw+40, y+92], 16, BLUEA)
            shadow_text(img, (barx, y), el["text"], f1, blur=4)
        elif k == "cta":
            f1 = font(True, 78)
            tw = tsize(d, el["text"], f1)[0]
            y = H - 150
            d.rectangle([0, y-34, W, y+118], fill=BLUEA)
            shadow_text(img, (W//2, y), el["text"], f1, anchor="ma", blur=4)
        elif k == "endtag":
            f1 = font(True, 54)
            shadow_text(img, (W//2, H-120), el["text"], f1, anchor="ma", blur=5)

    elif version == "v2":  # 1:1 title cards (centered scrim)
        cx = W//2
        if k == "brand":
            f1, f2 = font(True, 104), font(False, 50)
            box_h = 250
            cy = H//2
            d.rectangle([0, cy-box_h//2, W, cy+box_h//2], fill=SCRIM)
            shadow_text(img, (cx, cy-70), el["title"], f1, anchor="ma")
            shadow_text(img, (cx, cy+55), el["sub"], f2, anchor="ma")
        elif k in ("feature","cta"):
            big = k == "cta"
            f1 = font(True, 74 if not big else 82)
            lines = wrap(d, el["text"], f1, W-160)
            lh = tsize(d, "Ay", f1)[1] + 26
            total = lh*len(lines)
            cy = H//2
            d.rectangle([0, cy-total//2-40, W, cy+total//2+40], fill=SCRIM)
            for i,l in enumerate(lines):
                shadow_text(img, (cx, cy-total//2 + i*lh), l, f1, anchor="ma",
                            fill=WHITE if not big else (255,222,120,255))
        elif k == "endtag":
            f1 = font(True, 58)
            shadow_text(img, (cx, H-130), el["text"], f1, anchor="ma")

    elif version == "v3":  # 4:5 feature callouts (chips over footage band)
        fx, fy, fw, fh = fgrect
        cx = W//2
        if k == "brand":
            f1, f2 = font(True, 82), font(False, 42)
            y = fy + 40
            tw = max(tsize(d, el["title"], f1)[0], tsize(d, el["sub"], f2)[0])
            rounded(d, [cx-tw//2-40, y-24, cx+tw//2+40, y+150], 20, SCRIM)
            shadow_text(img, (cx, y), el["title"], f1, anchor="ma")
            shadow_text(img, (cx, y+96), el["sub"], f2, anchor="ma", fill=(210,225,255,255))
        elif k == "feature":
            f1 = font(True, 60)
            lines = wrap(d, el["text"], f1, fw-120)
            lh = tsize(d, "Ay", f1)[1] + 20
            total = lh*len(lines)
            y = fy + fh - total - 70
            # leading blue marker + chip
            maxw = max(tsize(d,l,f1)[0] for l in lines)
            rounded(d, [cx-maxw//2-46, y-24, cx+maxw//2+34, y+total+24], 18, BLUEA)
            d.ellipse([cx-maxw//2-34, y+total//2-8, cx-maxw//2-18, y+total//2+8], fill=WHITE)
            for i,l in enumerate(lines):
                shadow_text(img, (cx+8, y+i*lh), l, f1, anchor="ma", blur=3)
        elif k == "cta":
            f1 = font(True, 66)
            lines = wrap(d, el["text"], f1, W-120)
            lh = tsize(d, "Ay", f1)[1]+22
            total = lh*len(lines)
            y = H - total - 90
            d.rectangle([0, y-40, W, H], fill=BLUEA)
            for i,l in enumerate(lines):
                shadow_text(img, (cx, y+i*lh), l, f1, anchor="ma", blur=3)
        elif k == "endtag":
            f1 = font(True, 56)
            shadow_text(img, (cx, H-150), el["text"], f1, anchor="ma")

    elif version == "v4":  # 9:16 cinematic (text in bands)
        fx, fy, fw, fh = fgrect
        cx = W//2
        top_band_cy = fy//2
        bot_band_cy = fy + fh + (H - (fy+fh))//2
        if k == "brand":
            f1, f2 = font(True, 92), font(False, 44)
            shadow_text(img, (cx, top_band_cy-70), el["title"], f1, anchor="ma", blur=8)
            shadow_text(img, (cx, top_band_cy+40), el["sub"], f2, anchor="ma",
                        fill=(220,230,255,255), blur=6)
        elif k == "feature":
            f1 = font(True, 60)
            lines = wrap(d, el["text"], f1, W-140)
            lh = tsize(d,"Ay",f1)[1]+18
            total = lh*len(lines)
            y = bot_band_cy - total//2
            # thin accent line
            d.rectangle([cx-70, y-40, cx+70, y-32], fill=(255,255,255,220))
            for i,l in enumerate(lines):
                shadow_text(img, (cx, y+i*lh), l, f1, anchor="ma", blur=6)
        elif k == "cta":
            f1 = font(True, 74)
            lines = el["text"].split("\n")
            lh = tsize(d,"Ay",f1)[1]+22
            total = lh*len(lines)
            y = bot_band_cy - total//2
            for i,l in enumerate(lines):
                shadow_text(img, (cx, y+i*lh), l, f1, anchor="ma",
                            fill=(255,224,130,255), blur=6)
    return img

# ── Framing (returns list of filter strings ending in [base]) ───────────────
def framing(version):
    if version == "v1":
        return ["[0:v]scale=1920:1080,setsar=1[base]"], (1920,1080), (0,0,1920,1080)
    if version == "v2":
        W,H = 1080,1080; fh = round(1080*H/1920) if False else round(1080*1080/1920)
        fh = round(1080*1080/1920)  # 608
        fy = (H-fh)//2
        f = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=22:2,eq=brightness=-0.05:saturation=0.85[bg]",
             f"[0:v]scale={W}:-2[fg]",
             f"[bg][fg]overlay=0:{fy}:format=auto,setsar=1[base]"]
        return f, (W,H), (0,fy,W,fh)
    if version == "v3":
        W,H = 1080,1350; fh = round(1080*1080/1920); fy=(H-fh)//2
        f = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=22:2,eq=brightness=-0.05:saturation=0.85[bg]",
             f"[0:v]scale={W}:-2[fg]",
             f"[bg][fg]overlay=0:{fy}:format=auto,setsar=1[base]"]
        return f, (W,H), (0,fy,W,fh)
    if version == "v4":
        W,H = 1080,1920; fh = round(1080*1080/1920); fy=560
        f = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=26:2,eq=brightness=-0.06:saturation=0.82[bg]",
             f"[0:v]scale={W}:-2[fg]",
             f"[bg][fg]overlay=0:{fy}:format=auto,setsar=1[base]"]
        return f, (W,H), (0,fy,W,fh)

# ── Build one version ───────────────────────────────────────────────────────
def build(version):
    frames, (W,H), fgrect = framing(version)
    els = elements_for(version)

    # render + save overlay PNGs
    ov_files = []
    for el in els:
        img = render(version, W, H, el, fgrect)
        p = OVDIR / f"{version}_{el['key']}.png"
        img.save(p)
        ov_files.append((p, el))

    # ffmpeg inputs
    cmd = ["ffmpeg","-hide_banner","-y","-i", str(MASTER)]
    for p, el in ov_files:
        dur = el["t1"] - el["t0"]
        cmd += ["-loop","1","-t", f"{dur:.3f}","-i", str(p)]
    music_idx = 1 + len(ov_files)
    cmd += ["-i", str(MUSIC)]

    filt = list(frames)
    prev = "[base]"
    F = 0.4
    for i,(p,el) in enumerate(ov_files):
        idx = i+1
        dur = el["t1"]-el["t0"]
        fo = max(0.0, dur - F)
        filt.append(
            f"[{idx}:v]format=rgba,fade=t=in:st=0:d={F}:alpha=1,"
            f"fade=t=out:st={fo:.3f}:d={F}:alpha=1,"
            f"setpts=PTS-STARTPTS+{el['t0']:.3f}/TB[ov{i}]")
        out = f"[c{i}]" if i < len(ov_files)-1 else "[vout]"
        filt.append(
            f"{prev}[ov{i}]overlay=0:0:eof_action=pass:"
            f"enable='between(t,{el['t0']:.3f},{el['t1']:.3f})'{out}")
        prev = out
    # audio
    filt.append(
        f"[{music_idx}:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=1.2,afade=t=out:st={DUR-2.2:.2f}:d=2.0,"
        f"volume=0.9[aout]")

    out_path = OUTDIR / f"APBH-Pro-420_{version}.mp4"
    cmd += ["-filter_complex", ";".join(filt),
            "-map","[vout]","-map","[aout]",
            "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
            "-r","25","-c:a","aac","-b:a","192k","-t", f"{DUR}",
            "-movflags","+faststart", str(out_path)]

    print(f"[{version}] building {W}x{H} -> {out_path.name} ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[{version}] FFMPEG ERROR:\n", r.stderr[-2500:])
        return None
    print(f"[{version}] done: {out_path}")
    return out_path

if __name__ == "__main__":
    targets = sys.argv[1:] or ["v1","v2","v3","v4"]
    built = []
    for v in targets:
        p = build(v)
        if p: built.append(p)
    print("\n=== BUILT ===")
    for p in built:
        sz = os.path.getsize(p)/1e6
        print(f"  {p.name}  ({sz:.1f} MB)")
