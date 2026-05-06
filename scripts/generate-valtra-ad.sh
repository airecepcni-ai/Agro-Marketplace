#!/usr/bin/env bash
# Valtra tractor ad — 4-clip Seedance 2 series
set -euo pipefail
cd "$(dirname "$0")/.."
source .env

API="https://api.kie.ai"
MODEL="bytedance/seedance-2"
OUTPUT_DIR="output/valtra-ad-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"
LOG="logs/kie-api.jsonl"

TRACTOR="https://lh3.googleusercontent.com/d/1BOp-ct1oYx_sTV3qwZPWjYKJKhvA47L6"
FORESTRY="https://lh3.googleusercontent.com/d/19R93VJN0tigt88sK6SpnCjFQmGFIugEj"
UNDERBODY="https://lh3.googleusercontent.com/d/1TIG2ceB9LyFSXoZuBeRc5XS7V3at4Erm"

submit_clip() {
  local name=$1
  local prompt=$2
  local images_json=$3

  echo "[$name] Submitting..."
  local resp
  resp=$(PROMPT="$prompt" IMGS="$images_json" python3 -c "
import json, os, subprocess
body = json.dumps({
  'model': '${MODEL}',
  'callBackUrl': '',
  'input': {
    'prompt': os.environ['PROMPT'],
    'image_input': json.loads(os.environ['IMGS']),
    'aspect_ratio': '16:9',
    'duration': 15,
    'resolution': '720p',
    'output_format': 'mp4'
  }
})
r = subprocess.run(
  ['curl','-sS','-H','Authorization: Bearer ${KIE_API_KEY}',
   '-H','Content-Type: application/json','-d',body,
   '${API}/api/v1/jobs/createTask'],
  capture_output=True, text=True
)
print(r.stdout)
")

  local task_id
  task_id=$(echo "$resp" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
data=d.get('data') or {}
print(data.get('taskId',''))
" 2>/dev/null || echo "")

  if [ -z "$task_id" ]; then
    echo "[$name] ERROR: $resp"
    return 1
  fi

  echo "{\"timestamp\":\"$(date -u +%FT%TZ)\",\"endpoint\":\"POST /api/v1/jobs/createTask\",\"model\":\"${MODEL}\",\"clip\":\"${name}\",\"taskId\":\"${task_id}\",\"state\":\"queuing\"}" >> "$LOG"
  echo "[$name] taskId=$task_id — polling..."

  for i in $(seq 1 72); do
    sleep 30
    local poll state
    poll=$(curl -sS -H "Authorization: Bearer $KIE_API_KEY" \
      "$API/api/v1/jobs/recordInfo?taskId=$task_id")
    state=$(echo "$poll" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print((d.get('data') or {}).get('state','unknown'))
" 2>/dev/null || echo "unknown")

    case "$state" in
      success)
        local url
        url=$(echo "$poll" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
rj=(d.get('data') or {}).get('resultJson','')
parsed=json.loads(rj) if isinstance(rj,str) and rj else (rj or {})
urls=parsed.get('resultUrls') or parsed.get('urls') or []
if isinstance(urls,list) and urls: print(urls[0])
else:
  for v in (parsed.values() if isinstance(parsed,dict) else []):
    if isinstance(v,str) and v.startswith('http'): print(v); break
" 2>/dev/null || echo "")
        echo "[$name] DONE"
        echo "$poll" > "$OUTPUT_DIR/${name}_task.json"
        if [ -n "$url" ]; then
          curl -sS -o "$OUTPUT_DIR/${name}.mp4" "$url"
          echo "[$name] Saved → $OUTPUT_DIR/${name}.mp4"
          echo "[$name] URL: $url"
        fi
        echo "{\"timestamp\":\"$(date -u +%FT%TZ)\",\"clip\":\"${name}\",\"taskId\":\"${task_id}\",\"state\":\"success\",\"url\":\"${url}\"}" >> "$LOG"
        return 0 ;;
      fail)
        echo "[$name] FAILED: $poll"
        echo "$poll" > "$OUTPUT_DIR/${name}_failed.json"
        return 1 ;;
      *) echo "[$name] state=$state (attempt $i/72)..." ;;
    esac
  done
  echo "[$name] TIMEOUT"
  return 1
}

echo "════════════════════════════════════════"
echo "Valtra ad — 4 clips × Seedance 2 (16:9)"
echo "Output: $OUTPUT_DIR"
echo "════════════════════════════════════════"

# ── CLIP 1: Farmer sleeping, dream begins ─────────────────────────────────────
PROMPT_1="15 seconds product advertisement video, photorealistic, warm dreamlike atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a plain white t-shirt, lying asleep in a cozy dark bedroom — white bedding, drawn curtains, soft bedside lamp glow. Face relaxed and peaceful.

[00:00] Medium shot — he lies still, breathing slowly. Room is quiet and dark.

[00:05] Warm golden-amber dream mist slowly rises from the bed around him, softly glowing. His eyebrows rise slightly as if dreaming intensely.

[00:10] Camera gently floats upward and backward. The mist thickens. A glowing silhouette of the @(img1) (Valtra — large red agricultural tractor) materializes faintly in the golden mist above him, dreamlike and ethereal.

Voiceover: 'Are you also dreaming about a new tractor?'

Tone is warm, peaceful, slightly magical. Lighting is soft bedroom ambient with growing golden dream glow. Photorealistic quality, smooth slow camera movement throughout. Steady, no sharp cuts."

# ── CLIP 2: Assembly sequence in dream void ───────────────────────────────────
PROMPT_2="15 seconds product advertisement video, photorealistic, dark dramatic dream sequence. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a white t-shirt and grey pajama pants, floating weightlessly in a dark void — infinite black space, no ground. He looks around slowly in wonder.

[00:00] He floats in darkness, slowly turning. Camera begins a steady clockwise orbit around him, moving smoothly.

[00:04] Large mechanical parts of the @(img1) (Valtra tractor — red bodywork, large rear wheels, engine housing, cab structure) begin flying in from all directions. Parts lock into place with satisfying metallic impacts. Warm amber industrial light glows on each metal surface.

[00:09] Camera continues orbiting as more components rapidly assemble — axles, hood, cab frame taking shape around him. He watches with wide eyes and open mouth in amazement.

[00:13] Camera pulls back slowly to reveal the nearly complete tractor taking form, glowing in the dark void. The man is surrounded by the assembling machine.

Tone is dramatic and awe-inspiring. Dark void with warm amber glow on metal surfaces. Smooth orbiting camera movement throughout. Maintain product design from @(img1) unchanged."

# ── CLIP 3: Cabin protection snaps into place ────────────────────────────────
PROMPT_3="15 seconds product advertisement video, photorealistic, dark dramatic atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, sitting proudly in the open cab of the fully assembled @(img1) (Valtra tractor — large red agricultural tractor) floating in a dark void with warm amber rim lighting on all metal surfaces.

[00:00] Front-right angle on the assembled tractor. The man sits with hands on the steering wheel.

[00:04] The @(img2) (forestry cabin protection — heavy steel protective cage frame structure) flies in rapidly from above and snaps powerfully into position over the cab with a metallic clunk. Brief sparks flash at connection points.

[00:08] The @(img3) (underbody protection — heavy steel skid plate) swings in from below and locks firmly underneath the machine with another deep satisfying impact.

[00:11] Camera slowly pulls back and orbits right to reveal the fully equipped tractor in final configuration, gleaming in the void.

Voiceover: 'This dream can become a reality.'

Tone is powerful, satisfying, complete. Warm amber industrial lighting. Smooth deliberate camera movement. Maintain exact product designs from all reference images."

# ── CLIP 4: Reality reveal — he drives into sunset ───────────────────────────
PROMPT_4="15 seconds product advertisement video, photorealistic, warm golden hour atmosphere. A middle-aged white Czech man with short light-brown hair and slight stubble, wearing a flannel shirt and jeans, sitting in the cab of the @(img1) (Valtra tractor — large red agricultural tractor with forestry protection frame) in a wide open Czech agricultural landscape — rolling hills, golden wheat fields, treeline on the horizon.

[00:00] Close-up of his face, eyes closed. He slowly opens his eyes and blinks. Confusion — then a wide smile of disbelief spreads across his face as he realizes where he is.

[00:05] He looks down at his hands on the steering wheel, then around the cab interior. He laughs softly and shakes his head in amazed joy.

[00:09] He starts the engine — the tractor rumbles powerfully to life. He shifts into gear and begins moving forward across the golden field.

[00:12] Camera pulls back steadily and rises as the tractor drives away into the warm glowing sunset. Dust rises slowly behind the rear wheels. Golden light fills the frame.

Tone is joyful, warm, triumphant. Rich golden hour lighting, warm amber and orange tones. Smooth camera pull-back. Photorealistic quality."

# ── Submit all 4 in parallel ─────────────────────────────────────────────────
IMGS1="[\"$TRACTOR\"]"
IMGS2="[\"$TRACTOR\"]"
IMGS3="[\"$TRACTOR\",\"$FORESTRY\",\"$UNDERBODY\"]"
IMGS4="[\"$TRACTOR\"]"

submit_clip "clip1-dream-begins"    "$PROMPT_1" "$IMGS1" &
submit_clip "clip2-assembly"        "$PROMPT_2" "$IMGS2" &
submit_clip "clip3-cabin-snaps-on"  "$PROMPT_3" "$IMGS3" &
submit_clip "clip4-reality-sunset"  "$PROMPT_4" "$IMGS4" &

wait

echo "════════════════════════════════════════"
echo "DONE. Results in: $OUTPUT_DIR"
DONE=$(ls "$OUTPUT_DIR"/*.mp4 2>/dev/null | wc -l | tr -d ' ')
echo "$DONE / 4 clips downloaded"
echo "Check exact credits: https://kie.ai/logs"
echo "════════════════════════════════════════"
