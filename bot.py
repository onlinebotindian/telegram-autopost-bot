from flask import Flask
from threading import Thread
import os
import json
import asyncio

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler
)

# ---------------- KEEP ALIVE ---------------- #

web = Flask(__name__)

@web.route('/')
def home():
    return "Bot Running Successfully"

def run():
    web.run(host="0.0.0.0", port=10000)

Thread(target=run).start()

# ---------------- CONFIG ---------------- #

TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [
    7638053663,
    2116668482
]

CHANNELS_FILE = "channels.json"

# ---------------- LOAD CHANNELS ---------------- #

if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        CHANNELS = json.load(f)
else:
    CHANNELS = {}

# ---------------- SAVE CHANNELS ---------------- #

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(CHANNELS, f)

# ---------------- STATES ---------------- #

WAITING_BROADCAST = set()
WAITING_FORWARD = set()

LAST_MESSAGES = {}

# ---------------- MENU ---------------- #

menu = ReplyKeyboardMarkup(
    [
        ["📢 Broadcast", "📨 Forward"],
        ["📊 Analytics", "📂 Channels"],
        ["🗑 Delete Last", "❌ Cancel"]
    ],
    resize_keyboard=True
)

# ---------------- ADMIN CHECK ---------------- #

def is_admin(user_id):
    return user_id in ADMINS

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    text = f"""
🚀 ADVANCED BROADCAST PANEL

📢 Connected Channels: {len(CHANNELS)}

Choose an option below 👇
"""

    await update.message.reply_text(
        text,
        reply_markup=menu
    )

# ---------------- BOT ADDED ---------------- #

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type not in ["channel", "supergroup"]:
        return

    CHANNELS[str(chat.id)] = chat.title

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

# ---------------- BUTTON PANEL ---------------- #

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text
    user = update.effective_user.id

    # BROADCAST

    if text == "📢 Broadcast":

        WAITING_BROADCAST.add(user)

        await update.message.reply_text(
            "📨 Send message to broadcast"
        )

    # FORWARD

    elif text == "📨 Forward":

        WAITING_FORWARD.add(user)

        await update.message.reply_text(
            "📨 Forward any Telegram post"
        )

    # ANALYTICS

    elif text == "📊 Analytics":

        await update.message.reply_text(
            f"""
📊 Analytics

📢 Total Connected Channels: {len(CHANNELS)}
"""
        )

    # CHANNEL LIST

    elif text == "📂 Channels":

        txt = ""

        for cid, name in CHANNELS.items():
            txt += f"📢 {name}\n🆔 {cid}\n\n"

        if txt == "":
            txt = "❌ No connected channels"

        await update.message.reply_text(txt)

    # DELETE LAST

    elif text == "🗑 Delete Last":

        deleted = 0

        for cid, msgid in LAST_MESSAGES.items():

            try:

                await context.bot.delete_message(
                    int(cid),
                    msgid
                )

                deleted += 1

            except:
                pass

        await update.message.reply_text(
            f"🗑 Deleted from {deleted} channels"
        )

    # CANCEL

    elif text == "❌ Cancel":

        WAITING_BROADCAST.discard(user)
        WAITING_FORWARD.discard(user)

        await update.message.reply_text(
            "❌ Cancelled"
        )

# ---------------- TEXT BROADCAST ---------------- #

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in WAITING_BROADCAST:
        return

    WAITING_BROADCAST.discard(user)

    sent = 0
    failed = 0

    progress = await update.message.reply_text(
        "🚀 Broadcasting..."
    )

    for cid in CHANNELS:

        try:

            m = await context.bot.send_message(
                int(cid),
                update.message.text
            )

            LAST_MESSAGES[cid] = m.message_id

            sent += 1

        except:
            failed += 1

    await progress.edit_text(
        f"""
✅ Broadcast Completed

✅ Sent: {sent}
❌ Failed: {failed}
"""
    )

# ---------------- FORWARD BROADCAST ---------------- #

async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in WAITING_FORWARD:
        return

    WAITING_FORWARD.discard(user)

    sent = 0
    failed = 0

    progress = await update.message.reply_text(
        "🚀 Forwarding Post..."
    )

    for cid in CHANNELS:

        try:

            m = await context.bot.forward_message(
                chat_id=int(cid),
                from_chat_id=update.message.chat.id,
                message_id=update.message.message_id
            )

            LAST_MESSAGES[cid] = m.message_id

            sent += 1

        except:
            failed += 1

    await progress.edit_text(
        f"""
✅ Forward Broadcast Completed

✅ Sent: {sent}
❌ Failed: {failed}
"""
    )

# ---------------- ERROR HANDLER ---------------- #

async def error_handler(update, context):

    print(f"ERROR: {context.error}")

# ---------------- MAIN ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_error_handler(error_handler)

# START COMMAND
app.add_handler(CommandHandler("start", start))

# BUTTON MENU
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        buttons
    )
)

# BROADCAST TEXT
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        broadcast_text
    )
)

# FORWARD POSTS
app.add_handler(
    MessageHandler(
        filters.ALL,
        forward_post
    )
)

# AUTO CHANNEL CONNECT
app.add_handler(
    ChatMemberHandler(
        bot_added,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

print("🚀 Bot Running...")

# ---------------- PYTHON 3.14 FIX ---------------- #

asyncio.set_event_loop(asyncio.new_event_loop())

# ---------------- START BOT ---------------- #

app.run_polling(
    drop_pending_updates=True
)
