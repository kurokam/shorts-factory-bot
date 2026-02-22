import os
import tempfile
import random
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
Write a viral YouTube Shorts facts script in English.

STRICT RULES:
- DO NOT write titles.
- DO NOT write labels like Hook, Fact, Scene.
- DO NOT number anything.
- DO NOT explain.
- DO NOT add extra words.
- First line must be a powerful hook sentence.
- After that give short punchy facts.
- Each sentence on a new line.
- Only narration text.

Topic: {topic}
Length: about {duration} seconds.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    story = response.choices[0].message.content.strip()
    story = split_story_lines(story)
    return clean_story(story)

import re

def clean_story(text):
    lines = text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        # hook, fact, scene gibi başlayanları temizle
        if re.match(r"^(hook|fact|scene|\d+)", line.lower()):
            continue

        # colon içeren açıklamaları at
        if ":" in line and len(line.split()) < 6:
            continue

        if len(line) > 5:
            cleaned.append(line)

    return "\n".join(cleaned)

def split_story_lines(story):

    sentences = story.replace("?", ".").replace("!", ".").split(".")
    lines = []

    for s in sentences:
        s = s.strip()
        if len(s) > 8:
            lines.append(s)

    return "\n".join(lines)


def generate_scene_prompts(story):

    lines = [line.strip() for line in story.split("\n") if len(line.strip()) > 5]

    scene_prompts = []

    for line in lines:
        prompt = f"""
Ultra realistic cinematic scene.

Depict: {line}

Hyper detailed, volumetric lighting, depth of field,
epic atmosphere, dramatic shadows, 8k, film still.
No text, no subtitles.
"""
        scene_prompts.append(prompt.strip())

    return scene_prompts



def generate_image(scene, index, topic=None):

    import os
    import random
    import requests
    from PIL import Image
    from io import BytesIO

    # 1️⃣ Prompt temizleme (Pexels için optimize)
    clean = scene.replace(".", "").replace(",", "")
    words = clean.split()[:6]  # ilk 6 kelime
    query = " ".join(words)

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": os.getenv("PEXELS_API_KEY")
    }

    params = {
        "query": query,
        "per_page": 5,  # random için 5 sonuç al
        "orientation": "portrait"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Pexels API error")

    data = response.json()

    # 2️⃣ Fallback (hiç sonuç yoksa)
    if not data.get("photos"):
        if topic:
            params["query"] = topic
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

        if not data.get("photos"):
            raise Exception("No image found even after fallback")

    # 3️⃣ Random görsel seç
    photo = random.choice(data["photos"])

    # 4️⃣ Daha kaliteli versiyon
    image_url = photo["src"].get("large2x") or photo["src"]["large"]

    img_response = requests.get(image_url)
    image = Image.open(BytesIO(img_response.content)).convert("RGB")

    # 5️⃣ Shorts format (9:16)
    target_width = 768
    target_height = 1024

    image = image.resize((target_width, target_height))

    file_path = f"scene_{index}.jpg"
    image.save(file_path, quality=95)

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

def generate_tags(topic):
    prompt = f"""
Generate YouTube Shorts tags.
Only comma separated.
No hashtags.
Max 20.
English only.
Topic: {topic}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    tags_text = response.choices[0].message.content.strip()
    raw_tags = [t.strip() for t in tags_text.split(",")]

    return clean_tags(raw_tags)

import re

def clean_tags(tags):

    cleaned = []

    for tag in tags:
        tag = tag.strip()

        # hashtag kaldır
        tag = tag.replace("#", "")

        # özel karakter temizle
        tag = re.sub(r"[^a-zA-Z0-9\s]", "", tag)

        # çok uzunsa at
        if len(tag) > 30:
            continue

        if len(tag) > 2:
            cleaned.append(tag)

    # max 15 tag (YouTube güvenli sınır)
    return cleaned[:15]


# ---------------- TELEGRAM COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 AI Shorts Bot Ready!\n\n"
        "/topic <konu>\n"
        "/duration <saniye>\n"
        "/style <normal/dark/money>\n"
        "/upload <on/off>"
    )


async def set_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        duration = int(context.args[0])
        context.user_data["duration"] = duration
        await update.message.reply_text(f"⏱ Duration set to {duration} seconds.")
    except:
        await update.message.reply_text("❌ Example: /duration 45")

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    style = context.args[0].lower()

    if style not in ["normal", "dark", "money"]:
        await update.message.reply_text("❌ Use: normal / dark / money")
        return

    context.user_data["style"] = style
    await update.message.reply_text(f"🎬 Style set to {style}")

async def set_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.args[0].lower()

    if mode not in ["on", "off"]:
        await update.message.reply_text("❌ Use: /upload on or off")
        return

    context.user_data["upload"] = mode
    await update.message.reply_text(f"📤 Upload mode: {mode}")


async def set_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    duration = context.user_data.get("duration", 45)
    style = context.user_data.get("style", "normal")
    upload_mode = context.user_data.get("upload", "off")

    await update.message.reply_text("🧠 Generating script...")

    story = generate_story(topic, duration)
    scenes = story.split("\n")
    voice = generate_voice(story)

    await update.message.reply_text("🎨 Generating images...")

    images = []
    for i, scene in enumerate(scenes):
        images.append(generate_image(scene, i, topic))

    video = build_video(images, voice)

    if upload_mode == "on":
        await update.message.reply_text("🚀 Uploading to YouTube...")
        video_id = upload_video(video, title=topic)
        await update.message.reply_text(
            f"✅ Uploaded!\nhttps://youtube.com/watch?v={video_id}"
        )
    else:
        await update.message.reply_text("✅ Video created (upload off).")


# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duration", set_duration))
    app.add_handler(CommandHandler("style", set_style))
    app.add_handler(CommandHandler("upload", set_upload))
    app.add_handler(CommandHandler("topic", set_topic))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
