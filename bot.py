from flask import Flask
from threading import Thread
import asyncio
import os
import json
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
    filters
)

# ---------------- FLASK KEEP ALIVE ---------------- #

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot Running"

def run():
    app_web.run(host='0.0.0.0', port=10000)

Thread(target=run).start()

# ---------------- ASYNC FIX ---------------- #

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ---------------- ADMINS ---------------- #

ADMINS = [
    7638053663,
    2116668482
]

# ---------------- TOKEN ---------------- #

TOKEN = os.getenv("BOT_TOKEN")

# ---------------- STORAGE ---------------- #

CHANNELS_FILE = "channels.json"
HISTORY_FILE = "history.json"

try:
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
except:
    channels = {}

try:
    with open(HISTORY_FILE, "r") as f:
        broadcast_history = json.load(f)
except:
    broadcast_history = {}

# ---------------- SAVE ---------------- #

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(broadcast_history, f)

# ---------------- VARIABLES ---------------- #

stats = {
    "sent": 0,
    "failed": 0
}

broadcast_data = {
    "button_text": "",
    "button_url": ""
}

last_forward = {}

broadcast_number = 0

# ---------------- ADMIN CHECK ---------------- #

def admin_only(user_id):
    return user_id in ADMINS

# ---------------- MENU ---------------- #

menu_keyboard = ReplyKeyboardMarkup(
    [
        ["📤 Broadcast", "🔁 Forward"],
        ["📊 Stats", "📢 Channels"],
        ["🗑 Delete", "⏰ Schedule"]
    ],
    resize_keyboard=True
)

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = """
🚀 ADVANCED BROADCAST BOT

Features:
✅ Forward Broadcast
✅ Schedule Posts
✅ Analytics
✅ Auto Detect Channels
✅ Delete Broadcast
✅ Progress Bar
✅ Channel Names
✅ Error Logs
"""

    await update.message.reply_text(
        text,
        reply_markup=menu_keyboard
    )

# ---------------- AUTO DETECT ---------------- #

async def detect_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type in ["channel", "supergroup"]:

        channels[str(chat.id)] = chat.title

        save_channels()

# ---------------- BOT ADDED ---------------- #

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type not in ["channel", "supergroup"]:
        return

    channels[str(chat.id)] = chat.title

    save_channels()

    try:

        count = await context.bot.get_chat_member_count(chat.id)

    except:
        count = "Unknown"

    text = f"""
✅ Connected Successfully

📢 {chat.title}

🆔 {chat.id}

👥 Members: {count}
"""

    for admin in ADMINS:

        try:

            await context.bot.send_message(
                chat_id=admin,
                text=text
            )

        except:
            pass

# ---------------- BUTTON ---------------- #

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    data = " ".join(context.args)

    if "|" not in data:

        await update.message.reply_text(
            "Use:\n/button TEXT | URL"
        )

        return

    text, url = data.split("|")

    broadcast_data["button_text"] = text.strip()
    broadcast_data["button_url"] = url.strip()

    await update.message.reply_text(
        "✅ Button Saved"
    )

# ---------------- BROADCAST ---------------- #

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global broadcast_number

    if not admin_only(update.effective_user.id):
        return

    text = update.message.text.replace("/broadcast", "").strip()

    if not text:

        await update.message.reply_text(
            "❌ Send message"
        )

        return

    progress = await update.message.reply_text(
        "🚀 Broadcasting Started..."
    )

    keyboard = None

    if broadcast_data["button_text"]:

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    broadcast_data["button_text"],
                    url=broadcast_data["button_url"]
                )
            ]
        ])

    sent = 0
    failed = 0

    broadcast_number += 1

    broadcast_history[str(broadcast_number)] = {}

    total = len(channels)

    for i, channel_id in enumerate(channels):

        try:

            msg = await context.bot.send_message(
                chat_id=int(channel_id),
                text=text,
                reply_markup=keyboard
            )

            broadcast_history[str(broadcast_number)][channel_id] = msg.message_id

            sent += 1
            stats["sent"] += 1

        except Exception as e:

            failed += 1
            stats["failed"] += 1

            for admin in ADMINS:

                try:

                    await context.bot.send_message(
                        admin,
                        f"❌ Failed in {channels[channel_id]}\n\n{e}"
                    )

                except:
                    pass

        if i % 5 == 0:

            await progress.edit_text(
                f"🚀 Broadcasting...\n\n{i+1}/{total}"
            )

    save_history()

    await progress.edit_text(
        f"✅ Broadcast Completed\n\nSent: {sent}\nFailed: {failed}"
    )

# ---------------- FORWARD BROADCAST ---------------- #

async def save_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    if update.message.forward_origin:

        last_forward[update.effective_user.id] = update.message

        await update.message.reply_text(
            "✅ Forward Saved\n\nNow send /forwardbroadcast"
        )

# ---------------- FORWARD SEND ---------------- #

async def forwardbroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global broadcast_number

    if not admin_only(update.effective_user.id):
        return

    if update.effective_user.id not in last_forward:

        await update.message.reply_text(
            "❌ Forward a message first"
        )

        return

    progress = await update.message.reply_text(
        "🚀 Forward Broadcasting..."
    )

    message = last_forward[update.effective_user.id]

    broadcast_number += 1

    broadcast_history[str(broadcast_number)] = {}

    total = len(channels)

    for i, channel_id in enumerate(channels):

        try:

            msg = await context.bot.forward_message(
                chat_id=int(channel_id),
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            broadcast_history[str(broadcast_number)][channel_id] = msg.message_id

        except Exception as e:

            for admin in ADMINS:

                try:

                    await context.bot.send_message(
                        admin,
                        f"❌ Failed in {channels[channel_id]}\n\n{e}"
                    )

                except:
                    pass

        if i % 5 == 0:

            await progress.edit_text(
                f"🚀 Forwarding...\n\n{i+1}/{total}"
            )

    save_history()

    await progress.edit_text(
        "✅ Forward Broadcast Completed"
    )

# ---------------- DELETE ---------------- #

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    if not context.args:

        await update.message.reply_text(
            "Use:\n/delete NUMBER"
        )

        return

    num = context.args[0]

    if num not in broadcast_history:

        await update.message.reply_text(
            "❌ Broadcast not found"
        )

        return

    deleted = 0

    for channel_id, msg_id in broadcast_history[num].items():

        try:

            await context.bot.delete_message(
                chat_id=int(channel_id),
                message_id=msg_id
            )

            deleted += 1

        except:
            pass

    await update.message.reply_text(
        f"🗑 Deleted from {deleted} chats"
    )

# ---------------- DELETE ALL ---------------- #

async def deleteall(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    deleted = 0

    for b in broadcast_history.values():

        for channel_id, msg_id in b.items():

            try:

                await context.bot.delete_message(
                    chat_id=int(channel_id),
                    message_id=msg_id
                )

                deleted += 1

            except:
                pass

    await update.message.reply_text(
        f"🗑 Deleted {deleted} messages"
    )

# ---------------- CHANNELS ---------------- #

async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    text = ""

    for cid, name in channels.items():

        text += f"📢 {name}\n🆔 {cid}\n\n"

    if not text:
        text = "No channels connected"

    await update.message.reply_text(text)

# ---------------- STATS ---------------- #

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    total_subs = 0

    for cid in channels:

        try:

            count = await context.bot.get_chat_member_count(int(cid))

            total_subs += count

        except:
            pass

    text = f"""
📊 Analytics

📢 Channels: {len(channels)}

👥 Total Subs: {total_subs}

✅ Sent: {stats['sent']}

❌ Failed: {stats['failed']}
"""

    await update.message.reply_text(text)

# ---------------- SCHEDULE ---------------- #

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_only(update.effective_user.id):
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "Use:\n/schedule MINUTES message"
        )

        return

    minutes = int(context.args[0])

    text = " ".join(context.args[1:])

    await update.message.reply_text(
        f"⏰ Scheduled in {minutes} mins"
    )

    await asyncio.sleep(minutes * 60)

    for channel_id in channels:

        try:

            await context.bot.send_message(
                int(channel_id),
                text
            )

        except:
            pass

# ---------------- BUTTON MENU ---------------- #

async def button_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📊 Stats":
        await stats_cmd(update, context)

    elif text == "📢 Channels":
        await channels_cmd(update, context)

    elif text == "🗑 Delete":

        await update.message.reply_text(
            "Use:\n/delete NUMBER"
        )

    elif text == "📤 Broadcast":

        await update.message.reply_text(
            "Use:\n/broadcast YOUR MESSAGE"
        )

    elif text == "🔁 Forward":

        await update.message.reply_text(
            "Forward a message then send:\n/forwardbroadcast"
        )

    elif text == "⏰ Schedule":

        await update.message.reply_text(
            "Use:\n/schedule MINUTES MESSAGE"
        )

# ---------------- APP ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

# COMMANDS
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("forwardbroadcast", forwardbroadcast))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("deleteall", deleteall))
app.add_handler(CommandHandler("channels", channels_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("schedule", schedule))

# AUTO DETECT
app.add_handler(MessageHandler(filters.ALL, detect_channels))

# BUTTON MENU
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_menu))

# SAVE FORWARD
app.add_handler(MessageHandler(filters.FORWARDED, save_forward))

# BOT ADDED
app.add_handler(
    ChatMemberHandler(
        bot_added,
        ChatMemberHandler.MY_CHAT_MEMBER
    )
)

print("🚀 Advanced Bot Running...")

app.run_polling()
