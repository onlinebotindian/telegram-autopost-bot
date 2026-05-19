import os
import json
import asyncio
import threading
from flask import Flask
from telegram import (
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== BOT CONFIG ==================

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

ADMINS = [
    6800970170,
    2116668482
]

CHANNELS_FILE = "channels.json"

# ================== FILES ==================

if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "w") as f:
        json.dump([], f)

with open(CHANNELS_FILE, "r") as f:
    channels = json.load(f)

broadcast_messages = []

waiting_broadcast = set()
waiting_forward = set()

# ================== SAVE CHANNELS ==================

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ================== FLASK ==================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ================== START ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    buttons = [
        ["📢 Broadcast", "📨 Forward"],
        ["📊 Analytics", "📂 Channels"],
        ["🗑 Delete Last", "❌ Cancel"]
    ]

    await update.message.reply_text(
        "✅ Control Panel",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True
        )
    )

# ================== BUTTONS ==================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    text = update.message.text

    if text == "📢 Broadcast":

        waiting_broadcast.add(user_id)

        await update.message.reply_text(
            "📨 Send message to broadcast"
        )

    elif text == "📨 Forward":

        waiting_forward.add(user_id)

        await update.message.reply_text(
            "📨 Forward any message now"
        )

    elif text == "📊 Analytics":

        await update.message.reply_text(
            f"📊 Total Connected Channels: {len(channels)}"
        )

    elif text == "📂 Channels":

        if not channels:

            await update.message.reply_text(
                "❌ No channels connected"
            )

            return

        msg = "📂 Connected Channels\n\n"

        for ch in channels:
            msg += f"{ch}\n"

        await update.message.reply_text(msg)

    elif text == "🗑 Delete Last":

        deleted = 0

        for chat_id, msg_id in broadcast_messages:

            try:
                await context.bot.delete_message(
                    chat_id,
                    msg_id
                )
                deleted += 1
            except:
                pass

        broadcast_messages.clear()

        await update.message.reply_text(
            f"🗑 Deleted {deleted} messages"
        )

    elif text == "❌ Cancel":

        waiting_broadcast.discard(user_id)
        waiting_forward.discard(user_id)

        await update.message.reply_text(
            "❌ Cancelled"
        )

# ================== HANDLE BROADCAST ==================

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    # ---------- BROADCAST ----------

    if user_id in waiting_broadcast:

        waiting_broadcast.remove(user_id)

        sent = 0
        failed = 0

        progress = await update.message.reply_text(
            "📡 Broadcasting Started..."
        )

        for chat_id in channels:

            try:

                if update.message.text:

                    msg = await context.bot.send_message(
                        chat_id,
                        update.message.text
                    )

                else:

                    msg = await update.message.copy(chat_id)

                broadcast_messages.append(
                    (chat_id, msg.message_id)
                )

                sent += 1

            except Exception as e:
                print(e)
                failed += 1

            try:
                await progress.edit_text(
                    f"📡 Broadcasting...\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
                )
            except:
                pass

        await progress.edit_text(
            f"✅ Broadcast Completed\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
        )

    # ---------- FORWARD ----------

    elif user_id in waiting_forward:

        waiting_forward.remove(user_id)

        sent = 0
        failed = 0

        progress = await update.message.reply_text(
            "📨 Forwarding Started..."
        )

        for chat_id in channels:

            try:

                msg = await update.message.forward(chat_id)

                broadcast_messages.append(
                    (chat_id, msg.message_id)
                )

                sent += 1

            except Exception as e:
                print(e)
                failed += 1

            try:
                await progress.edit_text(
                    f"📨 Forwarding...\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
                )
            except:
                pass

        await progress.edit_text(
            f"✅ Forward Completed\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
        )

# ================== AUTO CONNECT CHANNEL ==================

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.my_chat_member.chat

    if chat.type not in ["channel", "supergroup"]:
        return

    chat_id = chat.id

    if chat_id not in channels:

        channels.append(chat_id)

        save_channels()

        for admin in ADMINS:

            try:
                await context.bot.send_message(
                    admin,
                    f"✅ New Channel Connected\n\n📢 {chat.title}\n🆔 {chat_id}"
                )
            except:
                pass

# ================== MAIN ==================

threading.Thread(
    target=run_web
).start()

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))

telegram_app.add_handler(
    MessageHandler(
        filters.UpdateType.MY_CHAT_MEMBER,
        bot_added
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.ALL & ~filters.COMMAND,
        handle_broadcast
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        buttons
    )
)

print("🚀 Bot Running...")

telegram_app.run_polling()
