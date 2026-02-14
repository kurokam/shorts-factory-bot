import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from ai import generate_story

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Shorts Factory Bot\n\n"
        "Choose a story with one click:\n\n"
        "/horror30 - Horror story (30s)\n"
        "/horror60 - Horror story (60s)\n"
        "/mystery30 - Mystery story (30s)\n"
        "/mystery60 - Mystery story (60s)\n\n"
        "The bot works in groups too."
    )

async def horror30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating horror story (30s)...")
    story = generate_story("horror", 30)
    await update.message.reply_text(story)

async def horror60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating horror story (60s)...")
    story = generate_story("horror", 60)
    await update.message.reply_text(story)

async def mystery30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating mystery story (30s)...")
    story = generate_story("mystery", 30)
    await update.message.reply_text(story)

async def mystery60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating mystery story (60s)...")
    story = generate_story("mystery", 60)
    await update.message.reply_text(story)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("horror30", horror30))
    app.add_handler(CommandHandler("horror60", horror60))
    app.add_handler(CommandHandler("mystery30", mystery30))
    app.add_handler(CommandHandler("mystery60", mystery60))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
