# make_manga_profile_guided.py
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

# ---------- GUIDED PROMPT ----------
# ---------- GUIDED PROMPT ----------
PROMPT = """
You are an expert manga character designer and world-builder.

Task:
- Read the STORY and identify all characters.
- Use the guided list of features below to build a structured schema for character profiles.
- Try to cover most of the listed features, but you may drop features that are irrelevant OR add new ones if they feel necessary to represent the character well.
- Be flexible: accuracy and natural manga expression are more important than forcing every field.

Guided Feature List (reference, not strict):
1. archetype
2. visual_age
3. hair_style
4. eye_style
5. eye_shape
6. eye_color
7. clothing_style
8. body_type
9. emotional_expression
10. expression_default
11. emotional_core
12. relationship_dynamics
13. internal_monologue
14. manga_tropes
15. defining_object
16. iconic_sound / sound_effect
17. signature_pose / pose_signature
18. key_expression
19. personality_traits
20. romantic_interest_indicator
21. defining_mannerism
22. iconic_object
23. panel_focus
24. background_element
25. color_palette
26. distinguishing_features
27. posture
28. manga_style_notes

Output format (JSON only):

{{
  "schema": {{ "field1": "description of field purpose", "field2": "...", ... }},
  "characters": [
    {{ "character_name": "...", "properties": {{ ... }} }},
    {{ "character_name": "...", "properties": {{ ... }} }}
  ],
  "notes": "Explain which guided features you used, skipped, or added and why."
}}

Here is the story:
{story}
""".format(story=STORY)


# ---------- CALL GEMINI ----------
chat = client.chats.create(model="gemini-2.0-flash")
resp = chat.send_message(PROMPT)

# ---------- PARSE & PRINT PRETTY JSON ----------
text = resp.text

# Try to extract the JSON substring between the first { and last }
start = text.find("{")
end = text.rfind("}")

if start != -1 and end != -1 and end > start:
    json_str = text[start:end+1]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Raw model output:\n", text)
        sys.exit(1)
else:
    print("No valid JSON found in response.")
    print("Raw model output:\n", text)
    sys.exit(1)

print(json.dumps(data, ensure_ascii=False, indent=2))

