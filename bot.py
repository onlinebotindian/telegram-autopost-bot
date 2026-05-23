from telegram import Update, Bot
from telegram.ext import (
    Application,
    ChatMemberHandler,
    ContextTypes,
)
import asyncio
import json
import os

BOT_TOKEN = "8999369476:AAGRgPLOlAd2m_PRljWVtHFU9H8Qe6kbK_s"

GROUPS_FILE = "groups.json"

MESSAGES = [
    "🔥 Stay active everyone! Join For Latest Movies/Series",
    "📢 https://t.me/+KL1eYgAdfM5iZmU1",
    "🚀 https://t.me/+KL1eYgAdfM5iZmU1"
]

# Load groups
def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return []

# Save groups
def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f)

groups = load_groups()

# Detect bot added as admin
async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if chat:
        chat_id = chat.id

        if chat_id not in groups:
            groups.append(chat_id)
            save_groups(groups)

            print(f"Added new group: {chat_id}")

# Auto sender loop
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

                print(f"Sent to {group_id}")

            except Exception as e:
                print(e)

        count += 1

        await asyncio.sleep(540)  # 9 minutes

async def on_start(app):

    asyncio.create_task(auto_send(app))

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
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

    app.run_polling()

if __name__ == "__main__":
    main()
