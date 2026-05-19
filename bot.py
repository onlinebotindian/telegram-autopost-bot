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
    ChatMemberHandler,
)

# ================= TOKEN =================

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

# ================= FILES =================

CHANNELS_FILE = "channels.json"

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running Successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= LOAD CHANNELS =================

if os.path.exists(CHANNELS_FILE):

    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)

else:
    channels = []

# ================= SAVE =================

def save_channels():

    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ================= STATES =================

waiting_broadcast = set()
waiting_forward = set()

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "✅ Bot Active\n\n"
        "Commands:\n\n"
        "/broadcast - Broadcast message\n"
        "/forward - Forward message\n"
        "/channels - Show connected channels\n"
        "/analytics - Bot analytics\n"
        "/delete - Delete last broadcast"
    )

    await update.message.reply_text(text)

# ================= ANALYTICS =================

async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "📊 Bot Analytics\n\n"

    if not channels:

        text += "❌ No channels connected."

    else:

        total_subscribers = 0

        for ch in channels:

            try:

                chat = await context.bot.get_chat(ch)

                members = await context.bot.get_chat_member_count(ch)

                total_subscribers += members

                text += (
                    f"📂 {chat.title}\n"
                    f"👥 Subscribers: {members}\n"
                    f"🆔 {ch}\n\n"
                )

            except:

                text += f"❌ Failed To Fetch {ch}\n\n"

        text += f"👥 Total Subscribers: {total_subscribers}"

    await update.message.reply_text(text)

# ================= CHANNELS =================

async def show_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not channels:

        text = "❌ No channels connected."

    else:

        text = "📂 Connected Channels:\n\n"

        for ch in channels:
            text += f"{ch}\n"

    await update.message.reply_text(text)

# ================= BROADCAST =================

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    waiting_broadcast.add(update.effective_user.id)

    await update.message.reply_text(
        "📢 Send message to broadcast."
    )

# ================= FORWARD =================

async def forward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    waiting_forward.add(update.effective_user.id)

    await update.message.reply_text(
        "📩 Forward any message now."
    )

# ================= DELETE =================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sent_messages = context.user_data.get("sent_messages", [])

    if not sent_messages:

        await update.message.reply_text(
            "❌ No broadcast found."
        )

        return

    deleted = 0

    for msg in sent_messages:

        try:

            await context.bot.delete_message(
                chat_id=msg["chat_id"],
                message_id=msg["message_id"]
            )

            deleted += 1

        except:
            pass

    await update.message.reply_text(
        f"🗑 Deleted from {deleted} channels."
    )

# ================= HANDLE MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # ===== BROADCAST =====

    if user_id in waiting_broadcast:

        waiting_broadcast.remove(user_id)

        success = 0
        failed = 0

        total = len(channels)

        progress = await update.message.reply_text(
            "📢 Broadcasting Started..."
        )

        sent_messages = []

        for index, ch in enumerate(channels, start=1):

            try:

                msg = await context.bot.send_message(
                    chat_id=ch,
                    text=update.message.text
                )

                sent_messages.append({
                    "chat_id": ch,
                    "message_id": msg.message_id
                })

                success += 1

            except:

                failed += 1

            percent = int((index / total) * 100)

            try:

                await progress.edit_text(
                    f"📢 Broadcasting...\n\n"
                    f"📊 Progress: {percent}%\n"
                    f"✔ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )

            except:
                pass

        context.user_data["sent_messages"] = sent_messages

        await progress.edit_text(
            f"✅ Broadcast Completed\n\n"
            f"✔ Success: {success}\n"
            f"❌ Failed: {failed}"
        )

        return

    # ===== FORWARD =====

    if user_id in waiting_forward:

        waiting_forward.remove(user_id)

        success = 0
        failed = 0

        total = len(channels)

        progress = await update.message.reply_text(
            "📩 Forward Started..."
        )

        sent_messages = []

        for index, ch in enumerate(channels, start=1):

            try:

                msg = await update.message.forward(
                    chat_id=ch
                )

                sent_messages.append({
                    "chat_id": ch,
                    "message_id": msg.message_id
                })

                success += 1

            except:

                failed += 1

            percent = int((index / total) * 100)

            try:

                await progress.edit_text(
                    f"📩 Forwarding...\n\n"
                    f"📊 Progress: {percent}%\n"
                    f"✔ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )

            except:
                pass

        context.user_data["sent_messages"] = sent_messages

        await progress.edit_text(
            f"✅ Forward Completed\n\n"
            f"✔ Success: {success}\n"
            f"❌ Failed: {failed}"
        )

        return

# ================= BOT ADDED =================

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type == "channel":

        if chat.id not in channels:

            channels.append(chat.id)

            save_channels()

            try:

                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=(
                        f"✅ New Channel Connected\n\n"
                        f"{chat.title}\n"
                        f"ID: {chat.id}"
                    )
                )

            except:
                pass

# ================= ERROR =================

async def error_handler(update, context):

    error_text = str(context.error)

    if "Conflict" in error_text:
        return

    print(error_text)

# ================= MAIN =================

if __name__ == "__main__":

    # START FLASK
    flask_thread = threading.Thread(target=run_web)
    flask_thread.daemon = True
    flask_thread.start()

    print("🌐 Flask Running")

    # EVENT LOOP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # TELEGRAM APP
    telegram_app = Application.builder().token(BOT_TOKEN).build()

    # COMMANDS
    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("broadcast", broadcast_command)
    )

    telegram_app.add_handler(
        CommandHandler("forward", forward_command)
    )

    telegram_app.add_handler(
        CommandHandler("channels", show_channels)
    )

    telegram_app.add_handler(
        CommandHandler("analytics", analytics)
    )

    telegram_app.add_handler(
        CommandHandler("delete", delete_command)
    )

    # BOT ADDED
    telegram_app.add_handler(
        ChatMemberHandler(
            bot_added,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    # MESSAGE HANDLER
    telegram_app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message
        )
    )

    # ERROR HANDLER
    telegram_app.add_error_handler(error_handler)

    print("🚀 Telegram Bot Running")

    telegram_app.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )
