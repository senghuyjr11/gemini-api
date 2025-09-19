# make_manga_profile.py
import os, json, sys
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    sys.exit("Missing GOOGLE_API_KEY in environment.")

client = genai.Client(api_key=API_KEY)

# ---------- STATIC INPUT ----------
STORY = (
    "Ibad saw Aisha across the crowded schoolyard, and his heart *POW!* skipped a "
    "beat. [She's...an angel!] He clumsily rushed towards her, tripping over his "
    "own feet – *THUD!* Aisha giggled, her laughter like wind chimes. \"H-hello!\" "
    "Ibad stammered, face burning crimson. Aisha smiled, and Ibad knew, with "
    "absolute certainty, that his life had irrevocably changed. GYAa!"
)

# ---------- PROMPT TO MODEL ----------
PROMPT = """
You are an expert manga character designer and world-builder.
I will give you a short manga story. 
Your job is to:
1. Identify all named or implied characters.
2. Design your own structured schema (fields + values) that best captures each character’s personality, appearance, and manga-style attributes.
3. The schema should balance visual traits, emotional traits, and iconic story elements (e.g., poses, sounds, objects, or expressions).
4. Output everything in valid JSON only with this format:

{{
  "schema": {{ "field1": "description", "field2": "...", ... }},
  "characters": [
     {{ "character_name": "...", "properties": {{ ... }} }},
     {{ "character_name": "...", "properties": {{ ... }} }}
  ],
  "notes": "brief explanation of why you chose these fields"
}}

Here is the story:
{story}
""".format(story=STORY)



# ---------- CALL GEMINI (STATIC, NO FLASK/STREAMING) ----------
chat = client.chats.create(model="gemini-2.0-flash")
resp = chat.send_message(PROMPT)

# ---------- PARSE & PRINT PRETTY JSON ----------
text = resp.text.strip()
try:
    data = json.loads(text)
except json.JSONDecodeError:
    # If the model added extra text, try to salvage the JSON block:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        data = json.loads(text[start:end+1])
    else:
        raise

print(json.dumps(data, ensure_ascii=False, indent=2))
