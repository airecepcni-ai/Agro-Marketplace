#!/usr/bin/env python3
"""Valtra tractor ad — 4-clip Seedance 2 series."""
import json, os, time, subprocess, sys
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
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

OUTPUT_DIR = Path("output") / f"valtra-ad-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path("logs/kie-api.jsonl")

TRACTOR  = "https://lh3.googleusercontent.com/d/1BOp-ct1oYx_sTV3qwZPWjYKJKhvA47L6"
FORESTRY = "https://lh3.googleusercontent.com/d/19R93VJN0tigt88sK6SpnCjFQmGFIugEj"
UNDERBODY= "https://lh3.googleusercontent.com/d/1TIG2ceB9LyFSXoZuBeRc5XS7V3at4Erm"

# ── Prompts ───────────────────────────────────────────────────────────────────
clips = [
    {
        "name": "clip1-dream-begins",
        "images": [TRACTOR],
        "prompt": """15 seconds product advertisement video, photorealistic, warm dreamlike atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a plain white t-shirt, lying asleep in a cozy dark bedroom — white bedding, drawn curtains, soft bedside lamp glow. Face relaxed and peaceful.

[00:00] Medium shot — he lies still, breathing slowly. Room is quiet and dark.

[00:05] Warm golden-amber dream mist slowly rises from the bed around him, softly glowing. His eyebrows rise slightly as if dreaming intensely.

[00:10] Camera gently floats upward and backward. The mist thickens and swirls. A glowing silhouette of the @(img1) (Valtra — large red agricultural tractor) materializes faintly in the golden mist above him, dreamlike and ethereal.

Voiceover: Are you also dreaming about a new tractor?

Tone is warm, peaceful, slightly magical. Lighting is soft bedroom ambient with growing golden dream glow. Photorealistic quality, smooth slow camera movement throughout. Steady, no sharp cuts.""",
    },
    {
        "name": "clip2-assembly",
        "images": [TRACTOR],
        "prompt": """15 seconds product advertisement video, photorealistic, dark dramatic dream sequence. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a white t-shirt and grey pajama pants, floating weightlessly in a dark void — infinite black space, no ground. He looks around slowly in wonder.

[00:00] He floats in darkness slowly turning. Camera begins a steady clockwise orbit around him, moving smoothly.

[00:04] Large mechanical parts of the @(img1) (Valtra tractor — red bodywork, large rear wheels, engine housing, cab structure) begin flying in from all directions. Parts lock into place with satisfying metallic impacts. Warm amber industrial light glows on each metal surface as they connect.

[00:09] Camera continues orbiting as more components rapidly assemble — axles, hood, cab frame taking shape around him. He watches with wide eyes and open mouth in amazement.

[00:13] Camera slowly pulls back to reveal the nearly complete tractor glowing in the dark void. The man stands surrounded by the assembling machine.

Tone is dramatic and awe-inspiring. Dark void with warm amber glow on metal surfaces. Smooth orbiting camera movement. Maintain product design from @(img1) unchanged throughout.""",
    },
    {
        "name": "clip3-cabin-snaps-on",
        "images": [TRACTOR, FORESTRY, UNDERBODY],
        "prompt": """15 seconds product advertisement video, photorealistic, dark dramatic atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, sitting proudly in the open cab of the fully assembled @(img1) (Valtra tractor — large red agricultural tractor) floating in a dark void with warm amber rim lighting on all metal surfaces.

[00:00] Front-right angle on the assembled tractor. The man sits with hands on the steering wheel, smiling with pride.

[00:04] The @(img2) (forestry cabin protection — heavy steel protective cage frame structure) flies in rapidly from above and snaps powerfully into position over the cab with a deep metallic clunk. Brief sparks flash at connection points.

[00:08] The @(img3) (underbody protection — heavy steel skid plate) swings in swiftly from below and locks firmly underneath the machine with another satisfying heavy impact.

[00:11] Camera slowly pulls back and orbits right, revealing the fully equipped tractor in its final configuration, gleaming against the dark void.

Voiceover: This dream can become a reality.

Tone is powerful, satisfying, complete. Warm amber industrial lighting. Smooth deliberate camera movement. Maintain exact product designs from all reference images unchanged.""",
    },
    {
        "name": "clip4-reality-sunset",
        "images": [TRACTOR],
        "prompt": """15 seconds product advertisement video, photorealistic, warm golden hour atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a flannel shirt and jeans, sitting in the cab of the @(img1) (Valtra tractor — large red agricultural tractor with forestry protection frame) in a wide open Czech agricultural landscape — rolling hills, golden wheat fields, treeline on the horizon.

[00:00] Close-up of his face — eyes closed, peaceful. He slowly opens his eyes and blinks. Confusion, then a wide smile of disbelief spreads across his face as he realizes where he is.

[00:05] He looks down at his hands on the steering wheel, then around the cab interior. He laughs softly and shakes his head in amazed joy.

[00:09] He starts the engine — the tractor rumbles powerfully to life. He shifts into gear and begins moving forward across the golden field.

[00:12] Camera pulls back steadily and rises as the tractor drives away into the warm glowing sunset. Dust rises slowly behind the rear wheels. Golden light fills the frame.

Tone is joyful, warm, triumphant. Rich golden hour lighting, warm amber and orange tones. Smooth camera pull-back. Photorealistic quality throughout.""",
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
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
        print(f"[curl] Non-JSON response: {r.stdout[:300]}")
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
        print(f"[{name}] SUBMIT ERROR: empty/non-JSON response")
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
            print(f"[{name}] poll error: empty response ({i}/{max_attempts})")
            continue
        state = (resp.get("data") or {}).get("state", "unknown")
        print(f"[{name}] state={state} ({i}/{max_attempts})")
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

# ── Run ───────────────────────────────────────────────────────────────────────
print("=" * 50)
print(f"Valtra ad — {len(clips)} clips × Seedance 2 (16:9 · 15s each)")
print(f"Output: {OUTPUT_DIR}")
print("=" * 50)

import threading

task_ids = {}
results = {}

def run_clip(clip):
    name = clip["name"]
    task_id = submit(clip)
    if task_id:
        task_ids[name] = task_id
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
    status = "" if url else ""
    print(f"  {status} {name}")
print(f"Output folder: {OUTPUT_DIR}")
print("Confirm credits: https://kie.ai/logs")
print("=" * 50)
