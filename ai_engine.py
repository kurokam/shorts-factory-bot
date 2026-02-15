import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_story(topic, duration):
    prompt = f"""
{duration} saniyelik YouTube Shorts korku hikayesi yaz.
Gerçekçi, sinematik ve sürükleyici olsun.
Konu: {topic}
"""

    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def generate_scene_prompts(story, scene_count):
    prompt = f"""
Bu hikayeyi {scene_count} sahneye böl.
Her sahne için sadece görsel üretim promptu ver.
Sinematik, gerçekçi, karanlık stil.
Hikaye:
{story}
"""

    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}]
    )

    scenes = response.choices[0].message.content.split("\n")
    return [s for s in scenes if len(s) > 10]
