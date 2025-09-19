import os, sys, json
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    sys.exit("Missing GOOGLE_API_KEY in environment.")

client = genai.Client(api_key=API_KEY)

STORY = (
    "Ibad saw Aisha across the crowded schoolyard, and his heart *POW!* skipped a beat. "
    "[She's...an angel!] He clumsily rushed towards her, tripping over his own feet – *THUD!* "
    "Aisha giggled, her laughter like wind chimes. \"H-hello!\" Ibad stammered, face burning crimson."
)

PROMPT = f"""
You are an expert manga character + scene analyst.

Goal (UNGUIDED DISCOVERY):
- Read STORY and FREELY discover the most important features needed to build strong manga characters and panels.
- Prioritize **importance** (what truly matters for consistent character depiction & paneling).
- Auto-invent a **schema** of fields; keep it concise and production-ready.
- If multiple similar fields arise, merge and rank by importance.

Hard rules:
- Output **JSON only** in the format below.
- Each feature should have: name, description, example (short), importance (1–5), confidence (0–1), and scope ("character" | "scene" | "both").
- Provide a "discovered_schema" list (ordered by importance), and a compact "rationale".

Output (JSON only):
{{
  "discovered_schema": [
    {{"field": "string", "why": "1-line reason", "importance": 1}},
    ...
  ],
  "features": [
    {{
      "name": "string",            # normalized key e.g. hair_style, eye_style, iconic_sound
      "description": "string",
      "example": "string",
      "importance": 1,
      "confidence": 0.0,
      "scope": "character|scene|both"
    }},
    ...
  ],
  "rationale": "brief notes on merges, dropped ideas, and prioritization"
}}

Here is the STORY:
{STORY}
"""

chat = client.chats.create(model="gemini-2.0-flash")
resp = chat.send_message(PROMPT)

text = resp.text
start, end = text.find("{"), text.rfind("}")
if start == -1 or end == -1 or end <= start:
    print("No valid JSON found.\nRaw output:\n", text); sys.exit(1)
try:
    data = json.loads(text[start:end+1])
except json.JSONDecodeError as e:
    print("JSON decode error:", e, "\nRaw output:\n", text); sys.exit(1)

print(json.dumps(data, ensure_ascii=False, indent=2))
