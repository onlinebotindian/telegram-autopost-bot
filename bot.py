from telegram import Bot
import time
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

while True:
    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text="🚀 Hello from Render Auto Bot"
        )
        print("Message Sent")

    except Exception as e:
        print(e)

    time.sleep(60)
