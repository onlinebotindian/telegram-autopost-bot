import json
import os
import asyncio
import threading
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
)

# ================= BOT TOKEN =================

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

# ================= FILES =================

CHANNELS_FILE = "channels.json"

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= LOAD CHANNELS =================

if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
else:
    channels = []

# ================= SAVE CHANNELS =================

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ================= STATES =================

waiting_broadcast = set()
waiting_forward = set()

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
            InlineKeyboardButton("📩 Forward", callback_data="forward"),
        ],
        [
            InlineKeyboardButton("📂 Channels", callback_data="channels"),
            InlineKeyboardButton("🗑 Delete Last", callback_data="delete"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "✅ Bot Active\n\n"
        "Add bot as admin in channels.\n"
        "Then use buttons below."
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

# ================= BUTTONS =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "broadcast":
        waiting_broadcast.add(user_id)
        await query.message.reply_text(
            "📢 Send message to broadcast."
        )

    elif query.data == "forward":
        waiting_forward.add(user_id)
        await query.message.reply_text(
            "📩 Forward any message now."
        )

    elif query.data == "channels":

        if not channels:
            text = "❌ No channels connected."
        else:
            text = "📂 Connected Channels:\n\n"
            for ch in channels:
                text += f"{ch}\n"

        await query.message.reply_text(text)

    elif query.data == "delete":

        deleted = 0

        for ch in channels:
            try:
                await context.bot.delete_message(
                    chat_id=ch,
                    message_id=context.user_data.get("last_msg")
                )
                deleted += 1
            except:
                pass

        await query.message.reply_text(
            f"🗑 Deleted from {deleted} channels."
        )

# ================= HANDLE MESSAGES =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # ===== BROADCAST =====

    if user_id in waiting_broadcast:

        waiting_broadcast.remove(user_id)

        success = 0
        failed = 0

        sent_message_id = None

        for ch in channels:

            try:
                msg = await context.bot.send_message(
                    chat_id=ch,
                    text=update.message.text
                )

                sent_message_id = msg.message_id
                success += 1

            except:
                failed += 1

        context.user_data["last_msg"] = sent_message_id

        await update.message.reply_text(
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

        sent_message_id = None

        for ch in channels:

            try:
                msg = await update.message.forward(
                    chat_id=ch
                )

                sent_message_id = msg.message_id
                success += 1

            except:
                failed += 1

        context.user_data["last_msg"] = sent_message_id

        await update.message.reply_text(
            f"✅ Forward Completed\n\n"
            f"✔ Success: {success}\n"
            f"❌ Failed: {failed}"
        )

        return

# ================= BOT ADDED TO CHANNEL =================

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

# ================= ERROR HANDLER =================

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

    print("🌐 Flask Started")

    # EVENT LOOP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # TELEGRAM APP
    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CallbackQueryHandler(buttons)
    )

    telegram_app.add_handler(
        ChatMemberHandler(
            bot_added,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message
        )
    )

    telegram_app.add_error_handler(error_handler)

    print("🚀 Telegram Bot Running")

    telegram_app.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )
