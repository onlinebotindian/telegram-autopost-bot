import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    ContextTypes,
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
# SAVE GROUPS
# =========================
groups = set()

# =========================
# FLASK SERVER
# =========================
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running!"

def run_web():
    web.run(host="0.0.0.0", port=10000)

# =========================
# WHEN BOT BECOMES ADMIN
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

            if groups:

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

            # 30 seconds
            await asyncio.sleep(30)

        except Exception as e:

            print(f"Loop Crash: {e}")

            await asyncio.sleep(5)

# =========================
# STARTUP
# =========================
async def on_start(app):

    asyncio.create_task(auto_send(app))

    print("Auto Sender Started!")

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

    app.add_handler(
        ChatMemberHandler(
            track_groups,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    print("Bot Running...")

    app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=2,
        timeout=30
    )

if __name__ == "__main__":
    main()
