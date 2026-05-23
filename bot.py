from telegram import Bot
import asyncio

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"
GROUP_ID = -1001234567890

MESSAGES = [
    "🔥 Stay active everyone! Join Below For More Latest Movies/Series",
    "📢 https://t.me/+KL1eYgAdfM5iZmU1",
    "🚀 https://t.me/+KL1eYgAdfM5iZmU1"
]

bot = Bot(token=BOT_TOKEN)

async def auto_send():
    count = 0

    while True:
        msg = MESSAGES[count % len(MESSAGES)]

        try:
            await bot.send_message(
                chat_id=GROUP_ID,
                text=msg
            )

            print("Message Sent:", msg)

        except Exception as e:
            print(e)

        count += 1

        await asyncio.sleep(540)  # 9 minutes

asyncio.run(auto_send())
