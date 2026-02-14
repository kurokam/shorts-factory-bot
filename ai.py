import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def generate_story(category: str, duration: int) -> str:
    prompt = f"""
Create a realistic {category} story for YouTube Shorts.
Language: English.
Total length: about {duration} seconds.
Return ONLY this format (no extra text):

Scene 1 - cinematic visual prompt
Scene 2 - cinematic visual prompt
Scene 3 - cinematic visual prompt
Scene 4 - cinematic visual prompt
"""

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a professional horror/mystery short-form video director."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }

    r = requests.post(GROQ_URL, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    return data["choices"][0]["message"]["content"]
