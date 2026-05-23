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

# =========================
# BOT TOKEN
# =========================

TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

# =========================
# MESSAGE
# =========================

MESSAGE = """🔥🔥 Stay active everyone! Must Join For Latest Movie/Series
https://t.me/+KL1eYgAdfM5iZmU1
https://t.me/+KL1eYgAdfM5iZmU1"""

# =========================
# GROUP IDS
# =========================

groups = {
    -1002678383754,
    -1003905629863,
    -1001406985843,
    -1003212251076,
    -1003354815437,
    -1002189482404
}

# =========================
# FLASK WEB SERVER
# =========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running Successfully!"

def run_web():
    web.run(host="0.0.0.0", port=10000)

# =========================
# AUTO DETECT NEW GROUPS
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
                    text="✅ Auto Post Bot Activated Successfully!"
                )

    except Exception as e:

        print(f"Track Error: {e}")

# =========================
# AUTO SEND LOOP
# =========================

async def auto_send(app):

    while True:

        try:

            for group_id in list(groups):

                try:

                    await app.bot.send_message(
                        chat_id=group_id,
                        text=MESSAGE,
                        disable_web_page_preview=True
                    )

                    print(f"Sent to {group_id}")

                except Exception as e:

                    print(f"Send Error: {e}")

            await asyncio.sleep(30)

        except Exception as e:

            print(f"Loop Crash: {e}")

            await asyncio.sleep(5)

# =========================
# STARTUP
# =========================

async def on_start(app):

    asyncio.create_task(auto_send(app))

    print("🔥 Auto Sender Started!")

# =========================
# MAIN
# =========================

def main():

    threading.Thread(target=run_web).start()

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(on_start)
        .build()
    )

    # Detect any activity/new groups
    app.add_handler(
        MessageHandler(
            filters.ALL,
            track_groups
        )
    )

    print("✅ Bot Running...")

    app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=2,
        timeout=30
    )

# =========================
# START
# =========================

if __name__ == "__main__":
    main()
