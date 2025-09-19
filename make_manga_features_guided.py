import os
import re
import sys
import json
import argparse
from dotenv import load_dotenv
from google import genai

# -----------------------------
# Config & schema
# -----------------------------
DISCOVERED_FIELDS = [
    # character-focused
    "emotion",               # label (infatuation, amusement)
    "body_inner",            # heartbeat, blush, breath, dizziness
    "action",                # noticed, rushed, tripped, giggled, stammered
    "appearance_key",        # short visual tag: "angelic", "rumpled uniform"

    # scene-focused
    "setting",               # "crowded schoolyard"
    "sound_effect",          # list of SFX tokens only: ["POW","THUD","HAH"]
    "atmosphere_mood",       # "romantic, comedic, lively"
    "space_proximity",       # "crowded / close / far"
    "pace_rhythm",           # "fast cuts; pause then close-up"
    "symbolism_motif",       # "wind-chime laughter", "sparkles", "halo"

    # universal per-cue metadata
    "cue_strength",          # 0–5
    "who_or_where",          # "Ibad" | "Aisha" | "ambient"
    "trigger_event",         # "seeing Aisha", "loses footing"
    "panel_suggestion"       # one-line draw note
]

DEFAULT_STORY = (
    "Ibad saw Aisha across the crowded schoolyard, and his heart *POW!* skipped a beat. "
    "He clumsily rushed towards her, tripping over his own feet — *THUD!* "
    "Aisha giggled, her laughter like wind chimes. \"H-hello!\" he stammered, blushing."
)

PREFERRED_ACTIONS = ["noticed", "rushed", "tripped", "giggled", "stammered"]

# -----------------------------
# Prompt builder
# -----------------------------
def build_prompt(story: str) -> str:
    return f"""
You are an expert manga sensory director. Extract structured SENSE data from STORY
using the exact field names in DISCOVERED_FIELDS. Do not invent fields or rename them.

Rules:
- Only include a field if supported by STORY; omit missing/irrelevant fields.
- Use short, production-ready values (no long prose).
- Prefer atomic cues (e.g., emotion='infatuation', who_or_where='Ibad').
- sound_effect must be a list of uppercase SFX tokens only (e.g., ["POW","THUD","HAH"]).
- Every sense object must include who_or_where and trigger_event.
- cue_strength is 0–5 by salience (loud SFX 5; major emotions 4–5; minor/ambient 1–3).
- Provide 2–6 sense objects, each focused and non-duplicative.

DISCOVERED_FIELDS = {DISCOVERED_FIELDS}

Output (JSON only; no commentary):
{{
  "schema": {DISCOVERED_FIELDS},
  "senses": [
    {{
      "emotion": "...",
      "body_inner": "...",
      "action": "...",
      "appearance_key": "...",
      "setting": "...",
      "sound_effect": ["..."],
      "atmosphere_mood": "...",
      "space_proximity": "...",
      "pace_rhythm": "...",
      "symbolism_motif": "...",
      "cue_strength": 0,
      "who_or_where": "Ibad | Aisha | ambient",
      "trigger_event": "...",
      "panel_suggestion": "..."
    }}
  ],
  "summary": {{
    "dominant_senses": ["..."],
    "notes": "brief normalization decisions"
  }}
}}

STORY:
{story}
""".strip()

# -----------------------------
# Normalization helpers
# -----------------------------
def norm_sfx(lst):
    if not isinstance(lst, list):
        return None
    out = []
    for t in lst:
        if not isinstance(t, str):
            continue
        tok = re.sub(r'[^A-Za-z!]+', '', t).upper()
        if tok:
            out.append(tok)
    # dedupe + keep stable order by sorting
    out = sorted(set(out))
    return out or None

def snap_action(s):
    if not isinstance(s, str):
        return None
    s_low = s.lower()
    # strict snaps first
    for p in PREFERRED_ACTIONS:
        if p in s_low:
            return p
    # heuristics
    if "saw" in s_low or "see" in s_low or "look" in s_low:
        return "noticed"
    if "rush" in s_low or "run" in s_low or "hurry" in s_low:
        return "rushed"
    if "trip" in s_low or "fall" in s_low or "slip" in s_low:
        return "tripped"
    if "giggl" in s_low or "laugh" in s_low:
        return "giggled"
    if "stammer" in s_low or "stutter" in s_low:
        return "stammered"
    return s.strip()

def clamp_strength(v):
    try:
        iv = int(v)
    except Exception:
        return None
    return max(0, min(5, iv))

def move_metaphors_to_symbolism(sense):
    # move common metaphor keywords from appearance_key -> symbolism_motif
    if "appearance_key" not in sense:
        return
    val = sense.get("appearance_key")
    if not isinstance(val, str) or not val.strip():
        return
    metaphors = ["sparkle", "sparkles", "halo", "wind chime", "wind-chime", "wind chimes"]
    val_low = val.lower()
    if any(m in val_low for m in metaphors):
        # append or set symbolism_motif
        existing = sense.get("symbolism_motif")
        if existing and isinstance(existing, str):
            if val not in existing:
                sense["symbolism_motif"] = f"{existing}; {val}"
        else:
            sense["symbolism_motif"] = val
        # optionally trim appearance_key
        # keep appearance_key only if something non-metaphoric remains
        # (simple heuristic: if it only mentions metaphors, drop it)
        if any(m in val_low for m in metaphors) and not re.search(r'\b(hair|eyes?|uniform|face|clothes?|figure|build)\b', val_low):
            sense.pop("appearance_key", None)

def normalize_output(data, fields):
    senses = data.get("senses", [])
    cleaned = []
    for s in senses:
        # keep only known fields
        s2 = {k: v for k, v in s.items() if k in fields}

        # normalize SFX
        if "sound_effect" in s2:
            sfx = norm_sfx(s2["sound_effect"])
            if sfx is None:
                s2.pop("sound_effect", None)
            else:
                s2["sound_effect"] = sfx

        # normalize action
        if "action" in s2 and isinstance(s2["action"], str):
            s2["action"] = snap_action(s2["action"])

        # clamp cue_strength
        if "cue_strength" in s2:
            cs = clamp_strength(s2["cue_strength"])
            if cs is None:
                s2.pop("cue_strength", None)
            else:
                s2["cue_strength"] = cs

        # move metaphors from appearance_key if needed
        move_metaphors_to_symbolism(s2)

        # drop empty strings
        for k in list(s2.keys()):
            if isinstance(s2[k], str) and not s2[k].strip():
                s2.pop(k, None)

        # enforce required fields
        if not s2.get("who_or_where") or not s2.get("trigger_event"):
            # skip incomplete cues
            continue

        cleaned.append(s2)

    data["senses"] = cleaned
    data["schema"] = fields
    return data

# -----------------------------
# Gemini call & JSON parsing
# -----------------------------
def call_model(story: str):
    prompt = build_prompt(story)
    # env + client
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("Missing GOOGLE_API_KEY in environment.")
    client = genai.Client(api_key=api_key)

    chat = client.chats.create(model="gemini-2.0-flash")
    resp = chat.send_message(prompt)

    text = resp.text or ""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        print("No valid JSON found.\nRaw output:\n", text)
        sys.exit(1)

    try:
        data = json.loads(text[start:end+1])
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Raw model output:\n", text)
        sys.exit(1)

    return data

# -----------------------------
# CLI
# -----------------------------
def read_story_from_args() -> str:
    parser = argparse.ArgumentParser(description="Guided manga senses extractor")
    parser.add_argument("--story", type=str, help="Story text (overrides default)")
    parser.add_argument("--story-file", type=str, help="Path to a text file containing story")
    args = parser.parse_args()

    if args.story:
        return args.story

    if args.story_file:
        if not os.path.isfile(args.story_file):
            sys.exit(f"Story file not found: {args.story_file}")
        with open(args.story_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    return DEFAULT_STORY

def main():
    story = read_story_from_args()
    data = call_model(story)
    data = normalize_output(data, DISCOVERED_FIELDS)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
