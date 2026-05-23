import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from flask import Flask
from threading import Thread
from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import json
import os

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

MESSAGES = [
    "🔥🔥 Stay active everyone! Must Join For Latest Movie/Series",
    "📢 https://t.me/+KL1eYgAdfM5iZmU1",
    "🚀 https://t.me/+KL1eYgAdfM5iZmU1"
]

GROUPS_FILE = "groups.json"

# ---------------- WEB ---------------- #

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Running Successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# ---------------- STORAGE ---------------- #

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return []

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f)

groups = load_groups()

# ---------------- AUTO DETECT GROUPS ---------------- #

async def detect_group(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat:

        chat_id = chat.id

        if str(chat.type) in ["group", "supergroup", "channel"]:

            if chat_id not in groups:

                groups.append(chat_id)

                save_groups(groups)

                print(f"Added New Group: {chat_id}")

# ---------------- AUTO SEND ---------------- #

async def auto_send(app):

    bot: Bot = app.bot

    count = 0

    while True:

        if groups:

            msg = MESSAGES[count % len(MESSAGES)]

            for group_id in groups:

                try:

                    await bot.send_message(
                        chat_id=group_id,
                        text=msg
                    )

                    print(f"Sent to {group_id}")

                except Exception as e:

                    print(f"Error {group_id}: {e}")

            count += 1

        await asyncio.sleep(40)

# ---------------- START ---------------- #

async def on_start(app):

    asyncio.create_task(auto_send(app))

# ---------------- MAIN ---------------- #

def main():

    Thread(target=run_web).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.post_init = on_start

    # Detect every message/group automatically
    app.add_handler(
        MessageHandler(
            filters.ALL,
            detect_group
        )
    )

    print("Bot Running...")

    app.run_polling()

if __name__ == "__main__":
    main()
