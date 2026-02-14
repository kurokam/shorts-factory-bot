import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from ai import generate_story, generate_capcut_prompts

TOKEN = os.getenv("BOT_TOKEN")

# Story genres and durations
GENRES = {
    "horror_short": ("horror", "30"),
    "horror_60": ("horror", "60"),
    "horror_120": ("horror", "120"),
    "mystery_short": ("mystery", "30"),
    "mystery_60": ("mystery", "60"),
    "mystery_120": ("mystery", "120")
}

def start(update: Update, context: CallbackContext):
    keyboard = []
    for cmd in GENRES:
        keyboard.append([InlineKeyboardButton(cmd.replace("_", " ").title(), callback_data=cmd)])
    keyboard.append([InlineKeyboardButton("CapCut Prompts", callback_data="capcut")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose a story type:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    data = query.data
    if data == "capcut":
        query.edit_message_text(text="Please generate a story first using one of the genres.")
        return
    
    genre, duration = GENRES[data]
    story = generate_story(genre, duration)
    
    if story:
        query.edit_message_text(text=f"Generated story ({genre}, {duration}s):\n\n{story}")
        prompts = generate_capcut_prompts(story)
        prompt_text = "\n".join([f"{p['scene']}: {p['prompt']}" for p in prompts])
        query.message.reply_text(f"CapCut Prompts:\n{prompt_text}")
    else:
        query.edit_message_text(text="❌ AI failed to generate story.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()