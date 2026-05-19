import os
import json
import asyncio
import threading
from datetime import datetime

from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ChatMemberHandler
)

# ================= BOT CONFIG =================

BOT_TOKEN = "YOUR_BOT_TOKEN"

ADMINS = [123456789, 2116668482]

CHANNELS_FILE = "channels.json"
USERS_FILE = "users.json"

# ================= LOAD DATA =================

def load_data(file_name):
    try:
        with open(file_name, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f)

channels = load_data(CHANNELS_FILE)
users = load_data(USERS_FILE)

# ================= FLASK =================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running Successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ================= BUTTONS =================

def main_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
        ],
        [
            InlineKeyboardButton("📨 Forward", callback_data="forward")
        ],
        [
            InlineKeyboardButton("📊 Analytics", callback_data="analytics")
        ],
        [
            InlineKeyboardButton("📁 Channels", callback_data="channels")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in users:
        users.append(user_id)
        save_data(USERS_FILE, users)

    text = f"""
🚀 Auto Broadcast Bot Online

👥 Users: {len(users)}
📢 Channels: {len(channels)}

Select an option below:
"""

    await update.message.reply_text(
        text,
        reply_markup=main_buttons()
    )

# ================= BUTTON HANDLER =================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in ADMINS:
        return

    data = query.data

    if data == "broadcast":
        context.user_data["mode"] = "broadcast"

        await query.message.reply_text(
            "📢 Send message to broadcast to all users."
        )

    elif data == "forward":
        context.user_data["mode"] = "forward"

        await query.message.reply_text(
            "📨 Forward any message now."
        )

    elif data == "analytics":

        text = f"""
📊 Bot Analytics

👥 Total Users: {len(users)}
📢 Connected Channels: {len(channels)}
🕒 Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
"""

        await query.message.reply_text(text)

    elif data == "channels":

        if len(channels) == 0:
            text = "❌ No connected channels."
        else:
            text = "📢 Connected Channels:\n\n"

            for ch in channels:
                text += f"• {ch['title']} ({ch['id']})\n"

        await query.message.reply_text(text)

# ================= AUTO CHANNEL DETECT =================

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type not in ["channel", "supergroup"]:
        return

    found = False

    for ch in channels:
        if ch["id"] == chat.id:
            found = True
            break

    if not found:

        channels.append({
            "id": chat.id,
            "title": chat.title
        })

        save_data(CHANNELS_FILE, channels)

        for admin in ADMINS:
            try:
                await context.bot.send_message(
                    admin,
                    f"""
✅ Bot Added Successfully

📢 Channel: {chat.title}
🆔 Chat ID: {chat.id}
"""
                )
            except:
                pass

# ================= BROADCAST =================

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    mode = context.user_data.get("mode")

    if not mode:
        return

    success = 0
    failed = 0

    progress = await update.message.reply_text(
        "🚀 Broadcast Started..."
    )

    if mode == "broadcast":

        for user in users:

            try:
                await context.bot.send_message(
                    chat_id=user,
                    text=update.message.text
                )

                success += 1

            except:
                failed += 1

    elif mode == "forward":

        for user in users:

            try:
                await update.message.forward(
                    chat_id=user
                )

                success += 1

            except:
                failed += 1

    await progress.edit_text(
        f"""
✅ Broadcast Completed

✔ Success: {success}
❌ Failed: {failed}
"""
    )

    context.user_data["mode"] = None

# ================= ERROR HANDLER =================

async def error_handler(update, context):

    print(f"Error: {context.error}")

    for admin in ADMINS:
        try:
            await context.bot.send_message(
                admin,
                f"⚠️ Bot Error:\n{context.error}"
            )
        except:
            pass

# ================= MAIN =================

if __name__ == "__main__":

    threading.Thread(target=run_web).start()

    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))

    telegram_app.add_handler(
        CallbackQueryHandler(button_click)
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
            broadcast_message
        )
    )

    telegram_app.add_error_handler(error_handler)

    print("🚀 Bot Running...")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

telegram_app.run_polling()
