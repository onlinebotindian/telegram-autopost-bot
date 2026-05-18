from telegram import Bot
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

async def send_messages():
    while True:
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text="🚀 Auto message from Render"
            )
            print("Message Sent")

        except Exception as e:
            print(e)

        await asyncio.sleep(60)

asyncio.run(send_messages())
