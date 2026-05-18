from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Auto Post Bot Active\n\n"
        "Commands:\n"
        "/setmessage Your Message\n"
        "/setlink Your Link\n"
        "/startpost\n"
        "/stoppost"
    )

# Set message
async def setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("❌ Give message")
        return

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["message"] = text

    await update.message.reply_text("✅ Message Saved")

# Set link
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    link = " ".join(context.args)

    if not link:
        await update.message.reply_text("❌ Give link")
        return

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["link"] = link

    await update.message.reply_text("✅ Link Saved")

# Start posting
async def startpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["active"] = True

    await update.message.reply_text("🚀 Auto Posting Started")

# Stop posting
async def stoppost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in bot_data:
        bot_data[chat_id]["active"] = False

    await update.message.reply_text("🛑 Auto Posting Stopped")

# Background auto post loop
async def autopost(app):
    while True:
        for chat_id, data in bot_data.items():

            if data.get("active"):

                message = data.get("message", "Default Message")
                link = data.get("link", "")

                final_text = f"{message}\n\n{link}"

                try:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=final_text
                    )

                except Exception as e:
                    print(e)

        await asyncio.sleep(60)

# Main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmessage", setmessage))
    app.add_handler(CommandHandler("setlink", setlink))
    app.add_handler(CommandHandler("startpost", startpost))
    app.add_handler(CommandHandler("stoppost", stoppost))

    asyncio.create_task(autopost(app))

    print("Bot Running...")

    await app.run_polling()

asyncio.run(main())
