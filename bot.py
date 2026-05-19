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
    ChatMemberHandler,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"
OWNER_ID = 7638053663

USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
LAST_BROADCAST_FILE = "last_broadcast.json"

# ================= LOAD/SAVE =================

def load_data(file):

    if os.path.exists(file):

        try:
            with open(file, "r") as f:
                return json.load(f)

        except:
            return []

    return []

def save_data(file, data):

    with open(file, "w") as f:
        json.dump(data, f)

users = load_data(USERS_FILE)
channels = load_data(CHANNELS_FILE)

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in users:

        users.append(user_id)
        save_data(USERS_FILE, users)

    text = """
🤖 AUTO POST BOT ACTIVE

Commands:

/broadcast
/forward
/analytics
/channels
/deletebroadcast
"""

    await update.message.reply_text(text)

# ================= AUTO DETECT CHANNEL =================

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        chat = update.effective_chat

        if not chat:
            return

        if chat.type not in ["channel", "supergroup"]:
            return

        channel_id = chat.id

        if str(channel_id) not in channels:

            channels.append(str(channel_id))
            save_data(CHANNELS_FILE, channels)

        members = await context.bot.get_chat_member_count(chat.id)

        await context.bot.send_message(
            OWNER_ID,
            f"""
✅ CHANNEL DETECTED

📢 {chat.title}
🆔 {channel_id}
👥 Subscribers: {members}
"""
        )

        print(f"Detected: {chat.title}")

    except Exception as e:
        print(e)

# ================= CHANNELS =================

async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not channels:

        await update.message.reply_text(
            "No channels detected"
        )

        return

    msg = "📢 CHANNELS\n\n"

    for ch in channels:

        try:

            chat = await context.bot.get_chat(int(ch))

            members = await context.bot.get_chat_member_count(
                int(ch)
            )

            msg += f"""
📌 {chat.title}
👥 Subscribers: {members}
🆔 {ch}

"""

        except:

            msg += f"""
❌ {ch}

"""

    await update.message.reply_text(msg)

# ================= ANALYTICS =================

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

    total_subscribers = 0

    for ch in channels:

        try:

            chat = await context.bot.get_chat(int(ch))

            members = await context.bot.get_chat_member_count(
                int(ch)
            )

            total_subscribers += members

            text += f"""
📌 {chat.title}
👥 Subscribers: {members}

"""

        except:
            pass

    text += f"\n🔥 Total Subscribers: {total_subscribers}"

    await update.message.reply_text(text)

# ================= MODES =================

broadcast_mode = {}

# ================= BROADCAST =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    broadcast_mode[update.effective_user.id] = "broadcast"

    await update.message.reply_text(
        "📨 Send message to broadcast"
    )

# ================= FORWARD =================

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    broadcast_mode[update.effective_user.id] = "forward"

    await update.message.reply_text(
        "➡️ Forward a message"
    )

# ================= DELETE BROADCAST =================

async def deletebroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not os.path.exists(LAST_BROADCAST_FILE):

        await update.message.reply_text(
            "No broadcast found"
        )

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

# ================= HANDLE MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        return

    if user_id not in broadcast_mode:
        return

    mode = broadcast_mode[user_id]

    success = 0
    failed = 0
    current = 0

    total = len(channels)

    progress = await update.message.reply_text(
        "🚀 Starting..."
    )

    sent_messages = []

    for ch in channels:

        current += 1

        try:

            if mode == "broadcast":

                if update.message.text:

                    sent = await context.bot.send_message(
                        chat_id=int(ch),
                        text=update.message.text
                    )

                elif update.message.photo:

                    sent = await context.bot.send_photo(
                        chat_id=int(ch),
                        photo=update.message.photo[-1].file_id,
                        caption=update.message.caption
                    )

                elif update.message.video:

                    sent = await context.bot.send_video(
                        chat_id=int(ch),
                        video=update.message.video.file_id,
                        caption=update.message.caption
                    )

                else:
                    continue

            else:

                sent = await context.bot.forward_message(
                    chat_id=int(ch),
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )

            sent_messages.append({
                "chat_id": int(ch),
                "message_id": sent.message_id
            })

            success += 1

        except Exception as e:

            print(e)
            failed += 1

        percent = int((current / total) * 100)

        filled = int(percent / 10)

        bar = "█" * filled + "░" * (10 - filled)

        try:

            await progress.edit_text(
                f"""
📡 Broadcasting

[{bar}] {percent}%

✅ Success: {success}
❌ Failed: {failed}
"""
            )

        except:
            pass

    with open(LAST_BROADCAST_FILE, "w") as f:
        json.dump(sent_messages, f)

    del broadcast_mode[user_id]

    await progress.edit_text(
        f"""
✅ BROADCAST COMPLETED

📢 Success: {success}
❌ Failed: {failed}
"""
    )

# ================= MAIN =================

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("broadcast", broadcast))
telegram_app.add_handler(CommandHandler("forward", forward))
telegram_app.add_handler(CommandHandler("analytics", analytics))
telegram_app.add_handler(CommandHandler("channels", channels_list))
telegram_app.add_handler(CommandHandler("deletebroadcast", deletebroadcast))

telegram_app.add_handler(
    MessageHandler(
        filters.ALL & ~filters.COMMAND,
        handle_message
    )
)

telegram_app.add_handler(
    ChatMemberHandler(
        bot_added,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

# ================= RUN =================

if __name__ == "__main__":

    Thread(target=run_web).start()

    print("🚀 Telegram Bot Running")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        telegram_app.initialize()
    )

    loop.run_until_complete(
        telegram_app.start()
    )

    loop.run_until_complete(
        telegram_app.updater.start_polling(
            drop_pending_updates=True
        )
    )

    loop.run_forever()
