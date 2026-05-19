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
    ChatMemberHandler,
    filters
)

# ADMINS
ADMINS = [
    7638053663,
    2116668482
]

# BOT TOKEN
TOKEN = os.getenv("BOT_TOKEN")

# STORES CHANNELS
channels = set()

# LAST BROADCAST IDS
last_messages = {}

# BUTTON DATA
broadcast_data = {
    "button_text": "",
    "button_url": ""
}

# STATS
stats = {
    "sent": 0,
    "failed": 0
}

# ADMIN CHECK
def admin_only(user_id):
    return user_id in ADMINS

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = """
🚀 PRIVATE BROADCAST BOT ACTIVE

Commands:

/broadcast YOUR MESSAGE

/button TEXT | URL

/deletebroadcast

/channels

/stats

/subs

Send image directly to broadcast photo + caption.
"""

    await update.message.reply_text(text)

# AUTO DETECT CHANNELS
async def detect_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type in ["channel", "supergroup"]:

        channels.add(chat.id)

# BOT ADDED EVENT
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type not in ["channel", "supergroup"]:
        return

    channels.add(chat.id)

    try:

        text = f"""
✅ Bot Added Successfully

📢 Channel:
{chat.title}

🆔 Chat ID:
{chat.id}
"""

        for admin in ADMINS:

            await context.bot.send_message(
                chat_id=admin,
                text=text
            )

    except Exception as e:
        print(e)

# BUTTON COMMAND
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

# BROADCAST MESSAGE
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = " ".join(context.args)

    if not text:

        await update.message.reply_text(
            "❌ Send message"
        )

        return

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

# DELETE LAST BROADCAST
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

# CHANNEL LIST
async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = "\n".join(
        [str(x) for x in channels]
    )

    if not text:
        text = "No channels connected"

    await update.message.reply_text(text)

# STATS
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = f"""
📊 Analytics

Connected Chats: {len(channels)}

Sent Posts: {stats['sent']}

Failed Posts: {stats['failed']}
"""

    await update.message.reply_text(text)

# SUBSCRIBER COUNT
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

# PHOTO BROADCAST
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

# APP
app = ApplicationBuilder().token(TOKEN).build()

# COMMANDS
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("deletebroadcast", deletebroadcast))
app.add_handler(CommandHandler("channels", channels_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("subs", subs))

# AUTO DETECT CHANNELS
app.add_handler(MessageHandler(filters.ALL, detect_channels))

# BOT ADDED EVENT
app.add_handler(
    ChatMemberHandler(
        bot_added,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

# PHOTO HANDLER
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_handler
    )
)

print("🚀 Bot Running...")

app.run_polling()
