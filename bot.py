import asyncio

# Fix Python 3.14 asyncio issue
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)
import json
import os

# ---------------- BOT TOKEN ---------------- #

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

# ---------------- AUTO MESSAGE ---------------- #

MESSAGES = [
    "🔥🔥 Stay active everyone! Must Join For Latest Movie/Series\nhttps://t.me/+KL1eYgAdfM5iZmU1\nhttps://t.me/+KL1eYgAdfM5iZmU1"
]

GROUPS_FILE = "groups.json"

# ---------------- WEB SERVER ---------------- #

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

# ---------------- DETECT GROUP ---------------- #

async def detect_group(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        chat = update.effective_chat

        if not chat:
            return

        if chat.type not in ["group", "supergroup", "channel"]:
            return

        chat_id = chat.id

        if chat_id not in groups:

            groups.append(chat_id)

            save_groups(groups)

            print(f"Added Group: {chat_id}")

            # Instant message when added
            try:

                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Bot is now active in this group!\n🔥 Auto posting started."
                )

            except Exception as e:

                print(e)

    except Exception as e:

        print(e)

# ---------------- AUTO SEND LOOP ---------------- #

async def auto_send(app):

    count = 0

    while True:

        try:

            if groups:

                msg = MESSAGES[count % len(MESSAGES)]

                for group_id in groups:

                    try:

                        await app.bot.send_message(
    chat_id=group_id,
    text=msg,
    disable_web_page_preview=True
                        )

                        print(f"Sent to {group_id}")

                    except Exception as e:

                        print(f"Group Error: {e}")

                count += 1

            await asyncio.sleep(30)

        except Exception as e:

            print(f"Loop Error: {e}")

            await asyncio.sleep(10)

# ---------------- MAIN ---------------- #

def main():

    Thread(target=run_web).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Detect groups automatically
    app.add_handler(
        MessageHandler(
            filters.ALL,
            detect_group
        )
    )

    async def startup(app):

        print("Starting Auto Send Loop...")

        asyncio.create_task(auto_send(app))

    app.post_init = startup

    print("Bot Running...")

    app.run_polling(
        drop_pending_updates=True
    )

# ---------------- START ---------------- #

if __name__ == "__main__":
    main()
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

# ---------------- DETECT GROUP ---------------- #

async def detect_group(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in ["group", "supergroup", "channel"]:
        return

    chat_id = chat.id

    if chat_id not in groups:

        groups.append(chat_id)

        save_groups(groups)

        print(f"Added Group: {chat_id}")

        # Instant live message
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ Bot is now active in this group!\n🔥 Auto posting started."
            )
        except:
            pass

# ---------------- AUTO SEND ---------------- #

async def auto_send(app):

    count = 0

    while True:

        if groups:

            msg = MESSAGES[count % len(MESSAGES)]

            for group_id in groups:

                try:

                    await app.bot.send_message(
                        chat_id=group_id,
                        text=msg
                    )

                    print(f"Sent to {group_id}")

                except Exception as e:

                    print(f"Error: {e}")

            count += 1

        await asyncio.sleep(30)

# ---------------- START ---------------- #

async def post_init(app):

    asyncio.create_task(auto_send(app))

# ---------------- MAIN ---------------- #

def main():

    Thread(target=run_web).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

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
