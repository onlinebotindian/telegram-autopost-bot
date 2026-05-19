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
    return "Bot Running"

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

# ---------------- SAVE ---------------- #

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

Choose option below 👇
"""

    await update.message.reply_text(
        text,
        reply_markup=menu
    )

# ---------------- AUTO CONNECT ---------------- #

async def auto_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type not in ["channel", "supergroup"]:
        return

    CHANNELS[str(chat.id)] = chat.title

    save_channels()

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

# ---------------- BUTTONS ---------------- #

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
            "📨 Forward any post"
        )

    # ANALYTICS

    elif text == "📊 Analytics":

        await update.message.reply_text(
            f"""
📊 Analytics

📢 Channels: {len(CHANNELS)}
"""
        )

    # CHANNELS

    elif text == "📂 Channels":

        txt = ""

        for cid, name in CHANNELS.items():
            txt += f"📢 {name}\n🆔 {cid}\n\n"

        if txt == "":
            txt = "No channels connected"

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
            f"🗑 Deleted from {deleted} chats"
        )

    # CANCEL

    elif text == "❌ Cancel":

        WAITING_BROADCAST.discard(user)
        WAITING_FORWARD.discard(user)

        await update.message.reply_text(
            "❌ Cancelled"
        )

# ---------------- BROADCAST TEXT ---------------- #

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in WAITING_BROADCAST:
        return

    WAITING_BROADCAST.discard(user)

    sent = 0
    failed = 0

    msg = await update.message.reply_text(
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

    await msg.edit_text(
        f"""
✅ Broadcast Complete

✅ Sent: {sent}
❌ Failed: {failed}
"""
    )

# ---------------- FORWARD ---------------- #

async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in WAITING_FORWARD:
        return

    if not update.message.forward_origin:
        return

    WAITING_FORWARD.discard(user)

    sent = 0
    failed = 0

    progress = await update.message.reply_text(
        "🚀 Forwarding..."
    )

    for cid in CHANNELS:

        try:

            m = await context.bot.forward_message(
                int(cid),
                update.message.chat.id,
                update.message.message_id
            )

            LAST_MESSAGES[cid] = m.message_id

            sent += 1

        except:
            failed += 1

    await progress.edit_text(
        f"""
✅ Forward Broadcast Complete

✅ Sent: {sent}
❌ Failed: {failed}
"""
    )

# ---------------- MAIN ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    ChatMemberHandler(
        bot_added,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        buttons
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        broadcast_text
    )
)

app.add_handler(
    MessageHandler(
        filters.FORWARDED,
        forward_post
    )
)

app.add_handler(
    MessageHandler(
        filters.ALL,
        auto_connect
    )
)

print("🚀 Bot Running...")

app.run_polling(drop_pending_updates=True)
