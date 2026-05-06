#!/usr/bin/env python3
"""Valtra tractor ad — v2, 3 clips, Czech voiceover, metallic black tractor."""
import json, os, time, subprocess, sys, threading
from datetime import datetime
from pathlib import Path

API = "https://api.kie.ai"
MODEL = "bytedance/seedance-2"
KEY = os.environ.get("KIE_API_KEY", "")
if not KEY:
    env_path = Path(__file__).parent.parent / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("KIE_API_KEY="):
            KEY = line.split("=", 1)[1].strip()
            break

if not KEY:
    sys.exit("ERROR: KIE_API_KEY not set")

OUTPUT_DIR = Path("output/valtra-ad-v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path("logs/kie-api.jsonl")

# Original red tractor (for dream silhouette in clip 1)
TRACTOR  = "https://lh3.googleusercontent.com/d/1BOp-ct1oYx_sTV3qwZPWjYKJKhvA47L6"
# Assembled metallic black Valtra (reference for clips 2 & 3)
ASSEMBLED = "https://lh3.googleusercontent.com/d/1yEHNlnGsBmH9TMFKpKnrQ-Zp8_5QMh88"

clips = [
    {
        "name": "clip1-dream-begins",
        "images": [TRACTOR],
        "prompt": """15 seconds product advertisement video, photorealistic, warm dreamlike atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a plain white t-shirt, lying asleep in a cozy dark bedroom — white bedding, drawn curtains, soft bedside lamp glow.

[00:00] Quick medium shot — he lies still, breathing slowly. Room is quiet and dark. Only 2 seconds on this.

[00:02] Warm golden-amber dream mist immediately begins rising from the bed, softly glowing. His eyebrows rise as if dreaming intensely. The mist thickens fast.

[00:06] Camera floats upward and backward quickly. Mist swirls and glows. A bright glowing silhouette of the @(img1) (Valtra — large agricultural tractor) materializes boldly in the golden mist above him, dreamlike and ethereal.

[00:10] The tractor silhouette grows vivid and golden. Camera keeps rising. The man's face shows wonder.

Voiceover in Czech: Také sníte o novém traktoru?

Tone is warm, slightly magical, fast-moving. Soft bedroom light with growing golden dream glow. Smooth camera movement. No long pauses.""",
    },
    {
        "name": "clip2-assembly",
        "images": [ASSEMBLED],
        "prompt": """15 seconds product advertisement video, photorealistic, dark dramatic dream sequence. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a white t-shirt and grey pajama pants, floating weightlessly in a dark void — infinite black space, no ground.

[00:00] He floats in darkness slowly turning. Camera begins a steady clockwise orbit around him.

[00:04] Large mechanical parts of the @(img1) (Valtra tractor — metallic black bodywork, large rear wheels, engine housing, cab structure, with VALTRA lettering on the side) begin flying in from all directions. Parts lock into place with satisfying metallic impacts. Warm amber light glows on each black metal surface as parts connect.

[00:09] Camera continues orbiting as more components assemble rapidly — axles, hood, cab frame. He watches with wide eyes and open mouth in amazement.

[00:13] Camera pulls back to reveal the fully assembled metallic black Valtra tractor glowing in the dark void. Clean — no attachments, no cage, no implements behind it. The VALTRA name gleams on the side.

Tone is dramatic and awe-inspiring. Dark void with warm amber glow on black metal surfaces. Smooth orbiting camera movement. Maintain exact product design from @(img1). Tractor is metallic black with VALTRA branding. No red colour anywhere on tractor.""",
    },
    {
        "name": "clip3-reality-sunset",
        "images": [ASSEMBLED],
        "prompt": """15 seconds product advertisement video, photorealistic, warm golden hour atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a flannel shirt and jeans, sitting in the cab of the @(img1) (Valtra tractor — metallic black agricultural tractor, VALTRA lettering on side, no attachments, no cage, no implements) in a wide open Czech agricultural landscape — rolling hills, golden wheat fields, treeline on the horizon.

[00:00] Close-up of his face — eyes closed, peaceful. He slowly opens his eyes and blinks. Confusion, then a wide smile of disbelief spreads across his face.

[00:05] He looks down at his hands on the steering wheel, then around the cab. He laughs softly and shakes his head in amazed joy.

[00:09] He starts the engine — the tractor rumbles powerfully to life. He shifts into gear and moves forward across the golden field.

[00:12] Camera pulls back steadily and rises as the metallic black Valtra drives away into the warm glowing sunset. Dust rises behind the rear wheels. Golden light fills the frame.

Voiceover in Czech: Tento sen se může stát skutečností.

Tone is joyful, warm, triumphant. Rich golden hour lighting. Tractor is metallic black, clean, no attachments behind it. Smooth camera pull-back. Photorealistic quality.""",
    },
]

def curl(method, url, data=None):
    cmd = ["curl", "-sS", "-H", f"Authorization: Bearer {KEY}",
           "-H", "Content-Type: application/json", "-X", method]
    if data:
        cmd += ["-d", json.dumps(data)]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"[curl] Non-JSON: {r.stdout[:300]}")
        return None

def submit(clip):
    name = clip["name"]
    body = {
        "model": MODEL,
        "callBackUrl": "",
        "input": {
            "prompt": clip["prompt"],
            "image_input": clip["images"],
            "aspect_ratio": "16:9",
            "duration": 15,
            "resolution": "720p",
            "output_format": "mp4",
        },
    }
    resp = curl("POST", f"{API}/api/v1/jobs/createTask", body)
    if not resp:
        print(f"[{name}] SUBMIT ERROR: empty response")
        return None
    data = resp.get("data") or {}
    task_id = data.get("taskId", "")
    if not task_id:
        print(f"[{name}] SUBMIT ERROR (code={resp.get('code')}): {resp.get('msg', resp)}")
        return None
    print(f"[{name}] taskId={task_id}")
    LOG_FILE.open("a").write(json.dumps({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoint": "POST /api/v1/jobs/createTask",
        "model": MODEL, "clip": name, "taskId": task_id, "state": "queuing",
    }) + "\n")
    return task_id

def poll(name, task_id, max_attempts=90):
    for i in range(1, max_attempts + 1):
        time.sleep(30)
        resp = curl("GET", f"{API}/api/v1/jobs/recordInfo?taskId={task_id}")
        if not resp:
            print(f"[{name}] poll error ({i}/{max_attempts})")
            continue
        state = (resp.get("data") or {}).get("state", "unknown")
        print(f"[{name}] state={state} ({i}/{max_attempts})", flush=True)
        if state == "success":
            rj = (resp.get("data") or {}).get("resultJson", "")
            parsed = json.loads(rj) if isinstance(rj, str) and rj else (rj or {})
            urls = parsed.get("resultUrls") or parsed.get("urls") or []
            url = urls[0] if urls else next(
                (v for v in (parsed.values() if isinstance(parsed, dict) else [])
                 if isinstance(v, str) and v.startswith("http")), "")
            if url:
                out = OUTPUT_DIR / f"{name}.mp4"
                subprocess.run(["curl", "-sS", "-o", str(out), url])
                print(f"[{name}] Saved → {out}")
                print(f"[{name}] URL: {url}")
            LOG_FILE.open("a").write(json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "clip": name, "taskId": task_id, "state": "success", "url": url,
            }) + "\n")
            return url
        elif state == "fail":
            print(f"[{name}] FAILED: {resp}")
            return None
    print(f"[{name}] TIMEOUT")
    return None

print("=" * 50)
print(f"Valtra ad v2 — {len(clips)} clips × Seedance 2 (16:9 · 15s each)")
print(f"Output: {OUTPUT_DIR}")
bal = curl("GET", f"{API}/api/v1/chat/credit")
print(f"Credits: {(bal or {}).get('data', '?')}")
print("=" * 50)

results = {}

def run_clip(clip):
    name = clip["name"]
    task_id = submit(clip)
    if task_id:
        results[name] = poll(name, task_id)

threads = [threading.Thread(target=run_clip, args=(c,)) for c in clips]
for t in threads:
    t.start()
for t in threads:
    t.join()

print("=" * 50)
done = sum(1 for v in results.values() if v)
print(f"DONE — {done}/{len(clips)} clips downloaded")
for name, url in results.items():
    status = "✓" if url else "✗"
    print(f"  {status} {name}")
bal2 = curl("GET", f"{API}/api/v1/chat/credit")
print(f"Credits remaining: {(bal2 or {}).get('data', '?')}")
print(f"Output folder: {OUTPUT_DIR}")
print("=" * 50)
