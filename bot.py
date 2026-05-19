from flask import Flask
from threading import Thread

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot Running"

def run():
    app_web.run(host='0.0.0.0', port=10000)

Thread(target=run).start()

import asyncio
import os

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

ADMIN_ID = 7638053663

TOKEN = os.getenv("BOT_TOKEN")

channels = set()

last_messages = {}

broadcast_data = {
    "button_text": "",
    "button_url": ""
}

stats = {
    "sent": 0,
    "failed": 0
}

def admin_only(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = """
🚀 Broadcast Bot Active

Commands:

/broadcast MESSAGE

/button TEXT | URL

/deletebroadcast

/channels

/stats

/subs
"""

    await update.message.reply_text(text)

async def detect_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type in ["channel", "supergroup"]:

        channels.add(chat.id)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    data = " ".join(context.args)

    if "|" not in data:

        await update.message.reply_text(
            "Use:\n/button TEXT | URL"
        )

        return

    text, url = data.split("|")

    broadcast_data["button_text"] = text.strip()

    broadcast_data["button_url"] = url.strip()

    await update.message.reply_text(
        "✅ Button Saved"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = " ".join(context.args)

    keyboard = None

    if broadcast_data["button_text"]:

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    broadcast_data["button_text"],
                    url=broadcast_data["button_url"]
                )
            ]
        ])

    success = 0

    failed = 0

    for channel_id in channels:

        try:

            msg = await context.bot.send_message(
                chat_id=channel_id,
                text=text,
                reply_markup=keyboard
            )

            last_messages[channel_id] = msg.message_id

            success += 1

            stats["sent"] += 1

        except Exception as e:

            print(e)

            failed += 1

            stats["failed"] += 1

    await update.message.reply_text(
        f"✅ Sent to {success} chats\n❌ Failed: {failed}"
    )

async def deletebroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    deleted = 0

    for channel_id, msg_id in last_messages.items():

        try:

            await context.bot.delete_message(
                chat_id=channel_id,
                message_id=msg_id
            )

            deleted += 1

        except:
            pass

    await update.message.reply_text(
        f"🗑 Deleted from {deleted} chats"
    )

async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = "\n".join(
        [str(x) for x in channels]
    )

    if not text:
        text = "No channels found"

    await update.message.reply_text(text)

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = f"""
📊 Stats

Channels: {len(channels)}

Sent: {stats['sent']}

Failed: {stats['failed']}
"""

    await update.message.reply_text(text)

async def subs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    total = 0

    result = ""

    for channel_id in channels:

        try:

            count = await context.bot.get_chat_member_count(
                channel_id
            )

            total += count

            result += f"{channel_id} → {count}\n"

        except:
            pass

    result += f"\nTotal Subs: {total}"

    await update.message.reply_text(result)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    if not update.message.photo:
        return

    photo = update.message.photo[-1].file_id

    caption = update.message.caption or ""

    keyboard = None

    if broadcast_data["button_text"]:

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    broadcast_data["button_text"],
                    url=broadcast_data["button_url"]
                )
            ]
        ])

    success = 0

    for channel_id in channels:

        try:

            msg = await context.bot.send_photo(
                chat_id=channel_id,
                photo=photo,
                caption=caption,
                reply_markup=keyboard
            )

            last_messages[channel_id] = msg.message_id

            success += 1

        except Exception as e:
            print(e)

    await update.message.reply_text(
        f"✅ Photo Sent to {success} chats"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("deletebroadcast", deletebroadcast))
app.add_handler(CommandHandler("channels", channels_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("subs", subs))

app.add_handler(MessageHandler(filters.ALL, detect_channels))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

print("🚀 Bot Running...")

app.run_polling()
