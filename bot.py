from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot_data = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
✅ Auto Post Bot Started

Commands:

/setmessage Your Message
/setlink Your Link
/startpost
/stoppost
"""
    await update.message.reply_text(text)

# SET MESSAGE
async def setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = " ".join(context.args)

    if not message:
        await update.message.reply_text("❌ Send a message")
        return

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["message"] = message

    await update.message.reply_text("✅ Message Saved")

# SET LINK
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    link = " ".join(context.args)

    if not link:
        await update.message.reply_text("❌ Send a link")
        return

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["link"] = link

    await update.message.reply_text("✅ Link Saved")

# START POST
async def startpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in bot_data:
        bot_data[chat_id] = {}

    bot_data[chat_id]["active"] = True

    await update.message.reply_text("🚀 Auto Posting Started")

# STOP POST
async def stoppost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in bot_data:
        bot_data[chat_id]["active"] = False

    await update.message.reply_text("🛑 Auto Posting Stopped")

# AUTO POST LOOP
async def autopost(application):
    while True:

        for chat_id, data in bot_data.items():

            if data.get("active"):

                message = data.get("message", "")
                link = data.get("link", "")

                text = f"{message}\n\n{link}"

                try:
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text=text
                    )

                except Exception as e:
                    print(e)

        await asyncio.sleep(60)

# MAIN
async def post_init(application):
    asyncio.create_task(autopost(application))

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setmessage", setmessage))
app.add_handler(CommandHandler("setlink", setlink))
app.add_handler(CommandHandler("startpost", startpost))
app.add_handler(CommandHandler("stoppost", stoppost))

print("Bot Running...")

app.run_polling()
