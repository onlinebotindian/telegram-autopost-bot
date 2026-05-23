from flask import Flask
from threading import Thread
from telegram import Update, Bot
from telegram.ext import (
    Application,
    ChatMemberHandler,
    ContextTypes,
)
import asyncio
import json
import os
import nest_asyncio

# Fix asyncio issue on Render
nest_asyncio.apply()

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

GROUPS_FILE = "groups.json"

MESSAGES = [
    "🔥 🔥 Stay active everyone!Must Join For Latest Movie/Series",
    "📢 https://t.me/+KL1eYgAdfM5iZmU1",
    "🚀 https://t.me/+KL1eYgAdfM5iZmU1"
]

# ---------------- WEB SERVER ---------------- #

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Running Successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# ---------------- GROUP STORAGE ---------------- #

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return []

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f)

groups = load_groups()

# ---------------- DETECT GROUPS ---------------- #

async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat:

        chat_id = chat.id

        if chat_id not in groups:

            groups.append(chat_id)

            save_groups(groups)

            print(f"Added New Group: {chat_id}")

# ---------------- AUTO MESSAGE LOOP ---------------- #

async def auto_send(app):

    bot: Bot = app.bot

    count = 0

    while True:

        msg = MESSAGES[count % len(MESSAGES)]

        for group_id in groups:

            try:

                await bot.send_message(
                    chat_id=group_id,
                    text=msg
                )

                print(f"Message sent to {group_id}")

            except Exception as e:

                print(f"Failed {group_id}: {e}")

        count += 1

        await asyncio.sleep(30)  # 9 minutes

# ---------------- START BOT ---------------- #

async def on_start(app):

    asyncio.create_task(auto_send(app))

# ---------------- MAIN ---------------- #

def main():

    # Start Flask Web Server
    Thread(target=run_web).start()

    # Create Event Loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Telegram App
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(on_start)
        .build()
    )

    # Detect when bot added to groups
    app.add_handler(
        ChatMemberHandler(
            track_groups,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    print("Bot Running...")

    # Start Bot
    app.run_polling()

if __name__ == "__main__":
    main()
