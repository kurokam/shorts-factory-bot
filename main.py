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
from groq import Groq
import re

# ---------------- ENV ---------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
client = Groq(api_key=GROQ_API_KEY)

# ---------------- AI / Video Fonksiyonları ---------------- #

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
    return story

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
    clean = scene.replace(".", "").replace(",", "")
    words = clean.split()[:6]
    query = " ".join(words)

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 5, "orientation": "portrait"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception("Pexels API error")

    data = response.json()
    if not data.get("photos") and topic:
        params["query"] = topic
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if not data.get("photos"):
            raise Exception("No image found even after fallback")

    photo = random.choice(data["photos"])
    image_url = photo["src"].get("large2x") or photo["src"]["large"]

    img_response = requests.get(image_url)
    image = Image.open(BytesIO(img_response.content)).convert("RGB")
    image = image.resize((768, 1024))

    file_path = f"scene_{index}.jpg"
    image.save(file_path, quality=95)
    return file_path

def generate_voice(text):
    text = re.sub(r"[^\w\s\n]", "", text)
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 3]
    combined_text = ". ".join(lines)
    tts = gTTS(text=combined_text, lang="en")
    output_file = "voice.mp3"
    tts.save(output_file)
    return output_file

def build_video(images, audio_file):
    audio = AudioFileClip(audio_file)
    duration_per_image = audio.duration / len(images)
    clips = [ImageClip(img).set_duration(duration_per_image) for img in images]
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)
    output_path = "final_video.mp4"
    video.write_videofile(output_path, fps=24)
    return output_path

def generate_tags(topic):
    prompt = f"Generate 15 YouTube Shorts tags for topic: {topic}, English only, comma separated"
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    tags_text = response.choices[0].message.content.strip()
    tags = [re.sub(r"[^a-zA-Z0-9\s]", "", t.strip()) for t in tags_text.split(",")]
    return tags[:15]

# ---------------- YouTube Upload ---------------- #
def upload_video(video_path, title, description, tags=None):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "28"
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    return response["id"]

# ---------------- TELEGRAM COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 AI Shorts Bot Ready!\n"
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
    if not context.args:
        await update.message.reply_text("❌ Enter topic: /topic space facts")
        return

    topic = " ".join(context.args)
    duration = context.user_data.get("duration", 45)
    style = context.user_data.get("style", "normal")
    upload_mode = context.user_data.get("upload", "off")

    await update.message.reply_text("🧠 Generating script...")
    story = generate_story(topic, duration)
    scenes = story.split("\n")
    voice = generate_voice(story)

    await update.message.reply_text("🎨 Generating images...")
    images = [generate_image(scene, i, topic) for i, scene in enumerate(scenes)]

    await update.message.reply_text("🎬 Building video...")
    video = build_video(images, voice)

    if upload_mode == "on":
        await update.message.reply_text("🚀 Uploading to YouTube...")
        try:
            video_id = upload_video(
                video, title=topic, description=story, tags=generate_tags(topic)
            )
            await update.message.reply_text(f"✅ Uploaded!\nhttps://youtube.com/watch?v={video_id}")
        except Exception as e:
            if "uploadLimitExceeded" in str(e):
                await update.message.reply_text("⚠️ YouTube upload limiti doldu.")
            else:
                await update.message.reply_text("❌ YouTube upload hatası oluştu.")
            print(e)
    else:
        await update.message.reply_text("✅ Video created (upload off).")

# ---------------- MAIN ---------------- #

async def error_handler(update, context):
    print(f"Exception: {context.error}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duration", set_duration))
    app.add_handler(CommandHandler("style", set_style))
    app.add_handler(CommandHandler("upload", set_upload))
    app.add_handler(CommandHandler("topic", set_topic))
    app.add_error_handler(error_handler)

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
