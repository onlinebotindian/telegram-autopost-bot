import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

MESSAGE = """🔥🔥 Stay active everyone! Must Join For Latest Movie/Series
https://t.me/+KL1eYgAdfM5iZmU1
https://t.me/+KL1eYgAdfM5iZmU1"""

groups = {
    -1002678383754,
    -1003905629863,
    -1001406985843,
    -1003212251076,
    -1003354815437,
    -1002189482404
}

# =========================
# Flask Keep Alive
# =========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running!"

def run_web():
    web.run(host="0.0.0.0", port=10000)

# =========================
# Auto Detect Groups
# =========================

async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        chat = update.effective_chat

        if chat:

            group_id = chat.id

            if group_id not in groups:

                groups.add(group_id)

                print(f"Added Group: {group_id}")

                await context.bot.send_message(
                    chat_id=group_id,
                    text="✅ Auto Post Bot Activated!"
                )

    except Exception as e:
        print(e)

# =========================
# Auto Send Messages
# =========================

async def auto_send(app):

    while True:

        for group_id in list(groups):

            try:

                await app.bot.send_message(
                    chat_id=group_id,
                    text=MESSAGE,
                    disable_web_page_preview=True
                )

                print(f"Sent to {group_id}")

            except Exception as e:

                print(f"Error: {e}")

        await asyncio.sleep(300)

# =========================
# Main Bot
# =========================

async def start_bot():

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.ALL,
            track_groups
        )
    )

    await app.initialize()
    await app.start()

    asyncio.create_task(auto_send(app))

    print("✅ Bot Started!")

    await app.updater.start_polling()

    while True:
        await asyncio.sleep(999999)

# =========================
# Start Everything
# =========================

def main():

    threading.Thread(target=run_web).start()

    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
