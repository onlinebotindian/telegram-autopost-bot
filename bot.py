import json
import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

CHANNELS_FILE = "channels.json"

app = Flask(__name__)

# ---------------- FLASK ----------------

@app.route("/")
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- LOAD CHANNELS ----------------

if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
else:
    channels = []

# ---------------- SAVE ----------------

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ---------------- STATES ----------------

waiting_broadcast = set()
waiting_forward = set()
last_posts = {}

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✅ Bot Active\n\n"
        "Commands:\n"
        "/broadcast\n"
        "/forward\n"
        "/channels\n"
        "/analytics\n"
        "/delete"
    )

    await update.message.reply_text(text)

# ---------------- CHANNEL AUTO DETECT ----------------

async def detect_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "channel":
        if chat.id not in channels:
            channels.append(chat.id)
            save_channels()

# ---------------- CHANNELS ----------------

async def show_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not channels:
        await update.message.reply_text("No channels connected.")
        return

    text = "📂 Connected Channels\n\n"

    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)
            text += f"• {chat.title}\n{ch}\n\n"
        except:
            pass

    await update.message.reply_text(text)

# ---------------- ANALYTICS ----------------

async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not channels:
        await update.message.reply_text("No channels connected.")
        return

    text = "📊 Analytics\n\n"

    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)

            try:
                members = await context.bot.get_chat_member_count(ch)
            except:
                members = "Hidden"

            text += (
                f"📢 {chat.title}\n"
                f"👥 Subscribers: {members}\n"
                f"🆔 {ch}\n\n"
            )

        except:
            pass

    await update.message.reply_text(text)

# ---------------- BROADCAST ----------------

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting_broadcast.add(update.effective_user.id)
    await update.message.reply_text("📢 Send message to broadcast.")

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_broadcast:
        return

    waiting_broadcast.remove(user_id)

    sent = 0
    failed = 0

    progress = await update.message.reply_text(
        f"📢 Broadcasting...\n\n✅ Sent: 0\n❌ Failed: 0"
    )

    for ch in channels:
        try:
            msg = await context.bot.send_message(
                chat_id=ch,
                text=update.message.text
            )

            last_posts[ch] = msg.message_id

            sent += 1

        except:
            failed += 1

        try:
            await progress.edit_text(
                f"📢 Broadcasting...\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
            )
        except:
            pass

    await progress.edit_text(
        f"✅ Broadcast Completed\n\n✅ Success: {sent}\n❌ Failed: {failed}"
    )

# ---------------- FORWARD ----------------

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting_forward.add(update.effective_user.id)
    await update.message.reply_text("📩 Forward any post now.")

async def do_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_forward:
        return

    waiting_forward.remove(user_id)

    sent = 0
    failed = 0

    progress = await update.message.reply_text(
        f"📩 Forwarding...\n\n✅ Sent: 0\n❌ Failed: 0"
    )

    for ch in channels:
        try:
            msg = await context.bot.forward_message(
                chat_id=ch,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )

            last_posts[ch] = msg.message_id

            sent += 1

        except:
            failed += 1

        try:
            await progress.edit_text(
                f"📩 Forwarding...\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
            )
        except:
            pass

    await progress.edit_text(
        f"✅ Forward Completed\n\n✅ Success: {sent}\n❌ Failed: {failed}"
    )

# ---------------- DELETE LAST ----------------

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deleted = 0

    for ch, msg_id in last_posts.items():
        try:
            await context.bot.delete_message(ch, msg_id)
            deleted += 1
        except:
            pass

    await update.message.reply_text(
        f"🗑 Deleted posts from {deleted} channels."
    )

# ---------------- MAIN ----------------

async def main():
    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("broadcast", broadcast))
    telegram_app.add_handler(CommandHandler("forward", forward))
    telegram_app.add_handler(CommandHandler("channels", show_channels))
    telegram_app.add_handler(CommandHandler("analytics", analytics))
    telegram_app.add_handler(CommandHandler("delete", delete_last))

    telegram_app.add_handler(
        MessageHandler(filters.ChatType.CHANNEL, detect_channel)
    )

    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)
    )

    telegram_app.add_handler(
        MessageHandler(~filters.COMMAND, do_forward)
    )

    print("🚀 Bot Running...")

    await telegram_app.run_polling()

# ---------------- RUN ----------------

threading.Thread(target=run_web).start()

asyncio.run(main())
