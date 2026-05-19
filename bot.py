import os
import json
import asyncio
import threading

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)

# ================= TOKEN =================

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

# ================= ADMINS =================

ADMINS = [2116668482]

# ================= FILES =================

CHANNELS_FILE = "channels.json"

# ================= LOAD CHANNELS =================

try:
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
except:
    channels = []

# ================= SAVE =================

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ================= FLASK =================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
        ],
        [
            InlineKeyboardButton("📨 Forward", callback_data="forward")
        ],
        [
            InlineKeyboardButton("📊 Channels", callback_data="channels")
        ]
    ]

    await update.message.reply_text(
        f"""
🚀 Broadcast Bot Online

📢 Connected Channels: {len(channels)}

Select Option Below
""",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= BUTTONS =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in ADMINS:
        return

    if query.data == "broadcast":

        context.user_data["mode"] = "broadcast"

        await query.message.reply_text(
            "📢 Send message to broadcast."
        )

    elif query.data == "forward":

        context.user_data["mode"] = "forward"

        await query.message.reply_text(
            "📨 Forward any post now."
        )

    elif query.data == "channels":

        if len(channels) == 0:

            txt = "❌ No Channels Connected"

        else:

            txt = "📢 Connected Channels\n\n"

            for ch in channels:
                txt += f"• {ch['title']}\n"

        await query.message.reply_text(txt)

# ================= AUTO CONNECT =================

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type != "channel":
        return

    already = False

    for ch in channels:
        if ch["id"] == chat.id:
            already = True

    if not already:

        channels.append({
            "id": chat.id,
            "title": chat.title
        })

        save_channels()

        for admin in ADMINS:

            try:

                await context.bot.send_message(
                    admin,
                    f"""
✅ New Channel Connected

📢 {chat.title}
🆔 {chat.id}
"""
                )

            except:
                pass

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    mode = context.user_data.get("mode")

    if not mode:
        return

    success = 0
    failed = 0

    msg = await update.message.reply_text(
        "🚀 Broadcasting..."
    )

    # ================= TEXT =================

    if mode == "broadcast":

        for ch in channels:

            try:

                await context.bot.send_message(
                    chat_id=ch["id"],
                    text=update.message.text
                )

                success += 1

            except Exception as e:

                print(e)
                failed += 1

    # ================= FORWARD =================

    elif mode == "forward":

        for ch in channels:

            try:

                await context.bot.forward_message(
                    chat_id=ch["id"],
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )

                success += 1

            except Exception as e:

                print(e)
                failed += 1

    await msg.edit_text(
        f"""
✅ Broadcast Completed

✔ Success: {success}
❌ Failed: {failed}
"""
    )

    context.user_data["mode"] = None

# ================= ERROR =================

async def error_handler(update, context):

    error_text = str(context.error)

    print(error_text)

    if "Conflict" in error_text:
        return

# ================= MAIN =================

if __name__ == "__main__":

    threading.Thread(target=run_web).start()

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

    print("🚀 Bot Running...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    telegram_app.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )
