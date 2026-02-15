import os
import re
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- ENVIRONMENT ---------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# ---------------- STORY GENERATION ---------------- #
def generate_story(topic, duration):
    return f"Once upon a time, in a {topic}, a young girl explored and experienced adventures over {duration} seconds."

def generate_scene_prompts(story, num_scenes):
    sentences = story.split(". ")
    prompts = []
    for i in range(num_scenes):
        prompt = sentences[i % len(sentences)]
        prompts.append(prompt)
    return prompts

# ---------------- IMAGE GENERATION ---------------- #
def generate_image(prompt, index):
    query = prompt.split(",")[0][:50]
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "orientation": "portrait"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(response.text)
        raise Exception("Pexels API error")
    data = response.json()
    if not data["photos"]:
        raise Exception("No image found")

    image_url = data["photos"][0]["src"]["large"]
    img_response = requests.get(image_url)
    image = Image.open(BytesIO(img_response.content)).resize((768, 1024))

    file_path = f"scene_{index}.jpg"
    image.save(file_path)
    return file_path

# ---------------- VOICE GENERATION ---------------- #
def generate_voice(text):
    clean_text = re.sub(r"[^\w\s]", "", text)
    tts = gTTS(clean_text, lang="en")
    output_file = "voice.mp3"
    tts.save(output_file)
    return output_file

# ---------------- VIDEO BUILD ---------------- #
def build_video(images, audio_file, duration_per_image):
    clips = [ImageClip(img).set_duration(duration_per_image) for img in images]
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)
    output_path = "final_video.mp4"
    video.write_videofile(output_path, fps=24)
    return output_path

# ---------------- YOUTUBE UPLOAD (placeholder) ---------------- #
def upload_video(video_file, title, description="", tags=[]):
    return "dQw4w9WgXcQ"

# ---------------- TELEGRAM COMMANDS ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Forest 30s", callback_data="topic_forest_30"),
            InlineKeyboardButton("Forest 60s", callback_data="topic_forest_60"),
        ],
        [
            InlineKeyboardButton("Hospital 30s", callback_data="topic_hospital_30"),
            InlineKeyboardButton("Hospital 60s", callback_data="topic_hospital_60"),
        ],
        [
            InlineKeyboardButton("Beach 30s", callback_data="topic_beach_30"),
            InlineKeyboardButton("Beach 60s", callback_data="topic_beach_60"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎬 AI Shorts Bot (English)\nSelect topic & duration:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # callback_data format: topic_<topic>_<duration>
    parts = data.split("_")
    topic = parts[1]
    duration = int(parts[2])

    context.user_data["duration"] = duration
    context.user_data["topic"] = topic

    await query.edit_message_text(f"✅ Selected topic: {topic}, duration: {duration}s\nGenerating video...")

    # AI Shorts production
    story = generate_story(topic, duration)
    scenes = generate_scene_prompts(story, max(3, duration // 10))
    images = [generate_image(scene, i) for i, scene in enumerate(scenes)]
    voice = generate_voice(story)
    video = build_video(images, voice, duration // len(images))

    video_id = upload_video(video, title=topic, description=f"{topic} | AI Short", tags=["shorts", "AI", topic])
    await query.edit_message_text(f"✅ Uploaded!\nhttps://youtube.com/watch?v={video_id}")

# ---------------- MAIN ---------------- #
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
