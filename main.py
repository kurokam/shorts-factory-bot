import os
import tempfile
import subprocess
import requests
from gtts import gTTS
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
from io import BytesIO
import urllib.parse
from groq import Groq
from youtube_manager import upload_video
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # örnek voice (Rachel)
ELEVEN_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
client = Groq(api_key=GROQ_API_KEY)


# ---------------- AI FUNCTIONS ---------------- #

def generate_story(topic, duration):
    prompt = f"""
Create a viral YouTube Shorts script in English.

Format:
- Start with a powerful 1 sentence hook.
- Then give 4-6 shocking, mind-blowing facts.
- Short punchy sentences.
- Each sentence separate line.
- No numbering.
- No explanations.
- No titles.
- Only narration text.

Topic: {topic}
Length: about {duration} seconds.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def generate_scene_prompts(story, scene_count):
    prompt = f"""
Divide this story into {scene_count} visual scenes.

Each line must be a realistic cinematic image generation prompt in English.
No numbers.
No explanations.
Only visual prompts.

Story:
{story}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    scenes = response.choices[0].message.content.split("\n")
    return [s.strip() for s in scenes if len(s.strip()) > 15]



def generate_image(prompt, index):

    query = prompt.split(",")[0][:50]

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": os.getenv("PEXELS_API_KEY")
    }

    params = {
        "query": query,
        "per_page": 1,
        "orientation": "portrait"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Pexels API error")

    data = response.json()

    if not data["photos"]:
        raise Exception("No image found")

    image_url = data["photos"][0]["src"]["large"]

    img_response = requests.get(image_url)
    image = Image.open(BytesIO(img_response.content))
    image = image.resize((768, 1024))

    file_path = f"scene_{index}.jpg"
    image.save(file_path)

    return file_path


import re
from gtts import gTTS

def generate_voice(text):

    text = re.sub(r"[^\w\s\n]", "", text)
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 3]

    combined_text = ". ".join(lines)  # doğal durak etkisi

    tts = gTTS(text=combined_text, lang="en")
    output_file = "voice.mp3"
    tts.save(output_file)

    return output_file


from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def build_video(images, audio_file):

    audio = AudioFileClip(audio_file)
    total_audio_duration = audio.duration

    image_count = len(images)
    duration_per_image = total_audio_duration / image_count

    clips = []
    for img in images:
        clip = ImageClip(img).set_duration(duration_per_image)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    output_path = "final_video.mp4"
    video.write_videofile(output_path, fps=24)

    return output_path


# ---------------- TELEGRAM COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 AI Shorts Bot\n\n"
        "/sure 60\n"
        "/konu Terk edilmiş hastane"
    )


async def set_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["duration"] = int(context.args[0])
    await update.message.reply_text("✅ Süre kaydedildi.")


async def set_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    duration = context.user_data.get("duration", 60)

    await update.message.reply_text("🧠 Generating script...")

    # 1️⃣ Hikaye üret
    story = generate_story(topic, duration)

    # 2️⃣ Sahne promptları üret
    scenes = generate_scene_prompts(story, max(3, duration // 10))

    # 3️⃣ Sadece hikayeyi sese çevir
    voice = generate_voice(story)

    await update.message.reply_text("🎨 Generating images...")

    images = []
    for i, scene in enumerate(scenes):
        images.append(generate_image(scene, i))

    await update.message.reply_text("🎬 Building video...")

    video = build_video(images, voice)

    await update.message.reply_text("🚀 YouTube'a yükleniyor...")

    video_id = upload_video(
        video,
        title=topic,
        description=f"{topic} | AI Generated Shorts",
        tags=["shorts", "AI", topic]
    )

    await update.message.reply_text(
        f"✅ Yüklendi!\nhttps://youtube.com/watch?v={video_id}"
    )


# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sure", set_duration))
    app.add_handler(CommandHandler("konu", set_topic))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
