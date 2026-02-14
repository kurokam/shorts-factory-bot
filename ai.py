import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_story(genre="horror", duration="30"):
    """
    Generate story text using Groq API
    genre: horror, mystery, etc.
    duration: seconds
    """
    prompt = f"Generate a {duration} second {genre} short story in English."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "groq-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                             headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        story_text = result['choices'][0]['message']['content']
        return story_text
    else:
        print(f"❌ AI request failed: {response.text}")
        return None

def generate_capcut_prompts(story_text):
    """
    Convert story into scene-prompt list for CapCut
    Returns list of dict: [{"scene": "Scene 1", "prompt": "..."}]
    """
    scenes = []
    sentences = story_text.split(". ")
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            scenes.append({
                "scene": f"Scene {i+1}",
                "prompt": sentence.strip()
            })
    return scenes