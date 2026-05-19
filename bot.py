from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import json

# ---------------- BOT TOKEN ----------------

TOKEN = "YOUR_BOT_TOKEN"

# ---------------- ADMINS ----------------

ADMINS = [2116668482]

# ---------------- FILES ----------------

CHANNELS_FILE = "channels.json"
SCHEDULE_FILE = "schedule.json"

# ---------------- VARIABLES ----------------

broadcast_messages = []

waiting_broadcast = set()
waiting_forward = set()

# ---------------- LOAD CHANNELS ----------------

try:
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
except:
    channels = []

# ---------------- LOAD SCHEDULE ----------------

try:
    with open(SCHEDULE_FILE, "r") as f:
        scheduled_posts = json.load(f)
except:
    scheduled_posts = []

# ---------------- SAVE FUNCTIONS ----------------

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

def save_schedule():
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(scheduled_posts, f)

# ---------------- FLASK ----------------

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running Successfully!"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        ["📢 Broadcast", "📨 Forward"],
        ["📡 Channels", "📊 Analytics"],
        ["🗑 Delete Broadcasts", "ℹ️ Help"]
    ]

    keyboard = ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🚀 Auto Post Bot Online!",
        reply_markup=keyboard
    )

# ---------------- BOT ADDED ----------------

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat.type in ["channel", "supergroup"]:

        if chat.id not in channels:
            channels.append(chat.id)
            save_channels()

        for admin in ADMINS:
            try:
                await context.bot.send_message(
                    admin,
                    f"✅ Connected Successfully\n\n📛 {chat.title}\n🆔 `{chat.id}`",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(e)

# ---------------- BUTTONS ----------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    # BROADCAST

    if text == "📢 Broadcast":
        waiting_broadcast.add(user_id)

        await update.message.reply_text(
            "📢 Send message to broadcast."
        )

    # FORWARD

    elif text == "📨 Forward":
        waiting_forward.add(user_id)

        await update.message.reply_text(
            "📨 Forward any message now."
        )

    # CHANNELS

    elif text == "📡 Channels":

        if not channels:
            msg = "❌ No channels connected."
        else:
            msg = "📡 Connected Channels\n\n"

            for ch in channels:
                msg += f"`{ch}`\n"

        await update.message.reply_text(
            msg,
            parse_mode="Markdown"
        )

    # ANALYTICS

    elif text == "📊 Analytics":

        await update.message.reply_text(
            f"📊 Bot Analytics\n\n📡 Total Channels: {len(channels)}"
        )

    # DELETE

    elif text == "🗑 Delete Broadcasts":

        broadcast_messages.clear()

        await update.message.reply_text(
            "🗑 All broadcast history deleted."
        )

    # HELP

    elif text == "ℹ️ Help":

        await update.message.reply_text(
            "Use buttons below to manage broadcasts."
        )

# ---------------- BROADCAST ----------------

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    # NORMAL BROADCAST

    if user_id in waiting_broadcast:

        waiting_broadcast.remove(user_id)

        sent = 0
        failed = 0

        progress = await update.message.reply_text(
            "📡 Broadcasting Started..."
        )

        for chat_id in channels:

            try:
                msg = await context.bot.send_message(
                    chat_id,
                    update.message.text
                )

                broadcast_messages.append(
                    (chat_id, msg.message_id)
                )

                sent += 1

            except:
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

    # FORWARD MODE

    elif user_id in waiting_forward:

        waiting_forward.remove(user_id)

        sent = 0
        failed = 0

        progress = await update.message.reply_text(
            "📨 Forwarding Started..."
        )

        for chat_id in channels:

            try:

                msg = await update.message.copy(chat_id)

                broadcast_messages.append(
                    (chat_id, msg.message_id)
                )

                sent += 1

            except:
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

# ---------------- MAIN ----------------

def main():

    Thread(target=run_web).start()

    telegram_app = Application.builder().token(TOKEN).build()

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.StatusUpdate.MY_CHAT_MEMBER,
            bot_added
        )
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )

    telegram_app.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            handle_broadcast
        )
    )

    print("🚀 Bot Running...")

    telegram_app.run_polling()

# ---------------- RUN ----------------

if __name__ == "__main__":
    main()
