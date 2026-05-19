from flask import Flask
from threading import Thread
import asyncio
import json
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------- BOT TOKEN ----------------
BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"
OWNER_ID = 7638053663 # replace with your telegram id

# ---------------- FILES ----------------
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
LAST_BROADCAST_FILE = "last_broadcast.json"

# ---------------- LOAD DATA ----------------
def load_data(file_name):
    if os.path.exists(file_name):
        try:
            with open(file_name, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f)

users = load_data(USERS_FILE)
channels = load_data(CHANNELS_FILE)

# ---------------- FLASK KEEP ALIVE ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users:
        users.append(user_id)
        save_data(USERS_FILE, users)

    text = """
🤖 Auto Post Bot Active

Commands:
/broadcast
/forward
/analytics
/deletebroadcast
/addchannel
/removechannel
/channels
"""

    await update.message.reply_text(text)

# ---------------- ADD CHANNEL ----------------
async def addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    try:
        channel_id = context.args[0]

        if channel_id not in channels:
            channels.append(channel_id)
            save_data(CHANNELS_FILE, channels)

        await update.message.reply_text(f"✅ Added Channel:\n{channel_id}")

    except:
        await update.message.reply_text(
            "Usage:\n/addchannel -100xxxxxxxxxx"
        )

# ---------------- REMOVE CHANNEL ----------------
async def removechannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    try:
        channel_id = context.args[0]

        if channel_id in channels:
            channels.remove(channel_id)
            save_data(CHANNELS_FILE, channels)

        await update.message.reply_text(f"❌ Removed:\n{channel_id}")

    except:
        await update.message.reply_text(
            "Usage:\n/removechannel -100xxxxxxxxxx"
        )

# ---------------- CHANNEL LIST ----------------
async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not channels:
        await update.message.reply_text("No channels added")
        return

    msg = "📢 Channels:\n\n"

    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)
            members = await context.bot.get_chat_member_count(ch)

            msg += f"• {chat.title}\n"
            msg += f"ID: {ch}\n"
            msg += f"Subscribers: {members}\n\n"

        except:
            msg += f"• {ch}\n\n"

    await update.message.reply_text(msg)

# ---------------- ANALYTICS ----------------
async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    total_users = len(users)
    total_channels = len(channels)

    text = f"""
📊 BOT ANALYTICS

👤 Users: {total_users}
📢 Channels: {total_channels}

"""

    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)
            members = await context.bot.get_chat_member_count(ch)

            text += f"""
📌 {chat.title}
👥 Subscribers: {members}

"""

        except:
            text += f"{ch}\n"

    await update.message.reply_text(text)

# ---------------- BROADCAST ----------------
broadcast_mode = {}

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    broadcast_mode[update.effective_user.id] = "broadcast"

    await update.message.reply_text(
        "📨 Send message to broadcast"
    )

# ---------------- FORWARD ----------------
async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    broadcast_mode[update.effective_user.id] = "forward"

    await update.message.reply_text(
        "➡️ Forward a message"
    )

# ---------------- DELETE LAST BROADCAST ----------------
async def deletebroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not os.path.exists(LAST_BROADCAST_FILE):
        await update.message.reply_text("No broadcast data found")
        return

    with open(LAST_BROADCAST_FILE, "r") as f:
        data = json.load(f)

    deleted = 0

    for item in data:
        try:
            await context.bot.delete_message(
                chat_id=item["chat_id"],
                message_id=item["message_id"]
            )
            deleted += 1
        except:
            pass

    await update.message.reply_text(
        f"🗑 Deleted from {deleted} channels"
    )

# ---------------- HANDLE MESSAGES ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        return

    if user_id not in broadcast_mode:
        return

    mode = broadcast_mode[user_id]

    progress = await update.message.reply_text(
        "⏳ Starting..."
    )

    success = 0
    failed = 0

    saved_messages = []

    total = len(channels)
    current = 0

    for ch in channels:
        current += 1

        try:
            if mode == "broadcast":
                sent = await context.bot.send_message(
                    chat_id=ch,
                    text=update.message.text
                )

            else:
                sent = await context.bot.forward_message(
                    chat_id=ch,
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )

            saved_messages.append({
                "chat_id": ch,
                "message_id": sent.message_id
            })

            success += 1

        except:
            failed += 1

        percent = int((current / total) * 100)

        bar = "█" * int(percent / 10)
        empty = "░" * (10 - int(percent / 10))

        try:
            await progress.edit_text(
                f"""
📡 Broadcasting...

[{bar}{empty}] {percent}%

✅ Success: {success}
❌ Failed: {failed}
"""
            )
        except:
            pass

    with open(LAST_BROADCAST_FILE, "w") as f:
        json.dump(saved_messages, f)

    del broadcast_mode[user_id]

    await progress.edit_text(
        f"""
✅ Broadcast Completed

📢 Sent: {success}
❌ Failed: {failed}
"""
    )

# ---------------- MAIN ----------------
telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("broadcast", broadcast))
telegram_app.add_handler(CommandHandler("forward", forward))
telegram_app.add_handler(CommandHandler("analytics", analytics))
telegram_app.add_handler(CommandHandler("addchannel", addchannel))
telegram_app.add_handler(CommandHandler("removechannel", removechannel))
telegram_app.add_handler(CommandHandler("channels", channels_list))
telegram_app.add_handler(CommandHandler("deletebroadcast", deletebroadcast))

telegram_app.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
)

# ---------------- RUN ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        print("🚀 Telegram Bot Running")

        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(
            drop_pending_updates=True
        )

        while True:
            await asyncio.sleep(100)

    loop.run_until_complete(main())
