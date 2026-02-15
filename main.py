import os
import tempfile
import subprocess
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from groq import Groq
from youtube_manager import upload_video
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ---------------- AI FUNCTIONS ---------------- #

def generate_story(topic, duration):
    prompt = f"""
{duration} saniyelik sinematik ve gerçekçi YouTube Shorts hikayesi yaz.
Konu: {topic}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def generate_scene_prompts(story, scene_count):
    prompt = f"""
Bu hikayeyi {scene_count} sahneye böl.
Her satır bir sahne için görsel üretim promptu olsun.
Sadece prompt ver, numara koyma.
Hikaye:
{story}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    scenes = response.choices[0].message.content.split("\n")
    return [s.strip() for s in scenes if len(s.strip()) > 10]


def generate_image(prompt, index):
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_API_KEY')}"
    }

    payload = {
        "inputs": f"{prompt}, cinematic lighting, ultra realistic, 9:16 vertical",
        "options": {"wait_for_model": True}
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"HF Error: {response.text}")

    image = Image.open(BytesIO(response.content))

    # 9:16 crop
    image = image.resize((768, 1024))

    file_path = f"scene_{index}.png"
    image.save(file_path)

    return file_path



def generate_voice(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1"
    }

    response = requests.post(url, json=data, headers=headers)

    with open("voice.mp3", "wb") as f:
        f.write(response.content)

    return "voice.mp3"


def build_video(image_paths, audio_path, duration_per_scene):
    input_txt = "inputs.txt"

    with open(input_txt, "w") as f:
        for img in image_paths:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_scene}\n")

    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", input_txt,
        "-i", audio_path,
        "-vf", "scale=1080:1920",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "final.mp4",
        "-y"
    ])

    return "final.mp4"


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

    await update.message.reply_text("🧠 Hikaye üretiliyor...")

    story = generate_story(topic, duration)

    await update.message.reply_text("🎨 Görseller hazırlanıyor...")

    scenes = generate_scene_prompts(story, max(3, duration // 10))

    images = []
    for i, scene in enumerate(scenes):
        images.append(generate_image(scene, i))

    await update.message.reply_text("🎙 Ses oluşturuluyor...")

    voice = generate_voice(story)

    await update.message.reply_text("🎬 Video oluşturuluyor...")

    video = build_video(images, voice, duration // len(images))

    await update.message.reply_text("🚀 YouTube'a yükleniyor...")

    video_id = upload_video(video, topic, story, tags=["shorts", "ai", topic])

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
