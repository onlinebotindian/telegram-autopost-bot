import json
import threading
import asyncio
from datetime import datetime

from flask import Flask

from telegram import (
Update,
ReplyKeyboardMarkup
)

from telegram.ext import (
ApplicationBuilder,
CommandHandler,
ContextTypes,
MessageHandler,
filters,
)

#---------------- BOT TOKEN ----------------

TOKEN = "YOUR_BOT_TOKEN"

#---------------- ADMINS ----------------

ADMINS = [
7638053663,
2116668482
]

#---------------- FILES ----------------

CHANNELS_FILE = "channels.json"
SCHEDULE_FILE = "schedule.json"

#---------------- DATA ----------------

broadcast_messages = []

waiting_broadcast = set()
waiting_forward = set()

#---------------- LOAD CHANNELS ----------------

# Load channels
try:
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
except:
    channels = []

# Load broadcast messages
try:
    with open(MESSAGES_FILE, "r") as f:
        sent_messages = json.load(f)
except:
    sent_messages = {}
channels = json.load(f)
except:
channels = []

#---------------- LOAD SCHEDULE ----------------

try:
with open(SCHEDULE_FILE, "r") as f:
scheduled_posts = json.load(f)
except:
scheduled_posts = []

#---------------- SAVE FUNCTIONS ----------------

def save_channels():
with open(CHANNELS_FILE, "w") as f:
json.dump(channels, f)

def save_schedule():
with open(SCHEDULE_FILE, "w") as f:
json.dump(scheduled_posts, f)

#---------------- FLASK KEEPALIVE ----------------

web = Flask(name)

@web.route("/")
def home():
return "Bot Running Successfully"

def run_web():
web.run(host="0.0.0.0", port=10000)

#---------------- KEYBOARD ----------------

keyboard = ReplyKeyboardMarkup(
[
["📢 Broadcast", "📨 Forward"],
["📊 Analytics", "📂 Channels"],
["🗑 Delete Last", "⏰ Schedule"]
],
resize_keyboard=True
)

#---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

if update.effective_user.id not in ADMINS:
    return

await update.message.reply_text(
    f"""

🚀 Advanced Broadcast Bot

📂 Connected Channels: {len(channels)}

Choose option below 👇
""",
reply_markup=keyboard
)

#---------------- AUTO CHANNEL DETECT ----------------

async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):

try:
    chat = update.my_chat_member.chat

    if chat.type == "channel":

        if chat.id not in channels:

            channels.append(chat.id)

            save_channels()

            for admin in ADMINS:

                try:
                    await context.bot.send_message(
                        admin,
                        f"""

✅ New Channel Connected

📢 {chat.title}
🆔 {chat.id}
"""
)

                except:
                    pass

except Exception as e:
    print(e)

#---------------- ANALYTICS ----------------

async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):

text = f"""

📊 BOT ANALYTICS

📂 Connected Channels: {len(channels)}
📨 Total Broadcasts: {len(broadcast_messages)}
⏰ Scheduled Posts: {len(scheduled_posts)}

🟢 Status: Online
"""

await update.message.reply_text(text)

#---------------- BUTTONS ----------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

if update.effective_user.id not in ADMINS:
    return

text = update.message.text
user_id = update.effective_user.id

# BROADCAST

if text == "📢 Broadcast":

    waiting_broadcast.add(user_id)

    await update.message.reply_text(
        "📨 Send message to broadcast."
    )

# FORWARD

elif text == "📨 Forward":

    waiting_forward.add(user_id)

    await update.message.reply_text(
        "📨 Forward any Telegram post."
    )

# ANALYTICS

elif text == "📊 Analytics":

    await analytics(update, context)

# CHANNELS

elif text == "📂 Channels":

    if not channels:

        await update.message.reply_text(
            "❌ No channels connected."
        )

        return

    txt = "📂 Connected Channels\n\n"

    for ch in channels:
        txt += f"{ch}\n"

    await update.message.reply_text(txt)

# DELETE LAST

elif text == "🗑 Delete Last":

    deleted = 0

    for data in broadcast_messages:

        for ch, msgid in data.items():

            try:

                await context.bot.delete_message(
                    chat_id=ch,
                    message_id=msgid
                )

                deleted += 1

            except:
                pass

    broadcast_messages.clear()

    await update.message.reply_text(
        f"🗑 Deleted {deleted} messages."
    )

# SCHEDULE

elif text == "⏰ Schedule":

    await update.message.reply_text(
        """

Use:

/schedule 2026-05-20 10:30 | Hello Everyone
"""
)

#---------------- LIVE BROADCAST ----------------

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

if user_id not in waiting_broadcast:
    return

waiting_broadcast.remove(user_id)

sent = 0
failed = 0

saved = {}

total = len(channels)

progress = await update.message.reply_text(
    "📡 Broadcast Started..."
)

for index, ch in enumerate(channels):

    try:

        msg = await context.bot.send_message(
            chat_id=ch,
            text=update.message.text
        )

        saved[ch] = msg.message_id

        sent += 1

    except Exception as e:

        failed += 1

        print(e)

    try:

        percent = int((index + 1) / total * 100)

        await progress.edit_text(
            f"""

📡 Broadcasting...

✅ Sent: {sent}
❌ Failed: {failed}

📊 Progress: {percent}%
"""
)

    except:
        pass

broadcast_messages.append(saved)

await progress.edit_text(
    f"""

✅ Broadcast Completed

✅ Sent: {sent}
❌ Failed: {failed}
"""
)

#---------------- FORWARD ----------------

async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

if user_id not in waiting_forward:
    return

if not update.message.forward_origin:
    return

waiting_forward.remove(user_id)

sent = 0
failed = 0

total = len(channels)

progress = await update.message.reply_text(
    "📨 Forward Started..."
)

for index, ch in enumerate(channels):

    try:

        await context.bot.forward_message(
            chat_id=ch,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )

        sent += 1

    except Exception as e:

        failed += 1

        print(e)

    try:

        percent = int((index + 1) / total * 100)

        await progress.edit_text(
            f"""

📨 Forwarding...

✅ Sent: {sent}
❌ Failed: {failed}

📊 Progress: {percent}%
"""
)

    except:
        pass

await progress.edit_text(
    f"""

✅ Forward Completed

✅ Sent: {sent}
❌ Failed: {failed}
"""
)

#---------------- SCHEDULE COMMAND ----------------

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):

if update.effective_user.id not in ADMINS:
    return

try:

    data = update.message.text.replace("/schedule ", "")

    split = data.split(" | ")

    time = split[0]
    text = split[1]

    scheduled_posts.append({
        "time": time,
        "text": text
    })

    save_schedule()

    await update.message.reply_text(
        f"""

✅ Scheduled Successfully

⏰ {time}

📝 {text}
"""
)

except:

    await update.message.reply_text(
        """

❌ Wrong Format

Use:

/schedule 2026-05-20 10:30 | Hello Everyone
"""
)

#---------------- CHECK SCHEDULE ----------------

async def check_schedule(app):

while True:

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    remove_posts = []

    for post in scheduled_posts:

        if post["time"] == now:

            for ch in channels:

                try:

                    await app.bot.send_message(
                        ch,
                        post["text"]
                    )

                except:
                    pass

            for admin in ADMINS:

                try:

                    await app.bot.send_message(
                        admin,
                        f"""

⏰ Scheduled Post Sent

📝 {post['text']}
"""
)

                except:
                    pass

            remove_posts.append(post)

    for p in remove_posts:
        scheduled_posts.remove(p)

    save_schedule()

    await asyncio.sleep(60)

#---------------- RESTART NOTIFY ----------------

async def notify_restart(app):

for admin in ADMINS:

    try:

        await app.bot.send_message(
            admin,
            "♻️ Bot Restarted Successfully."
        )

    except:
        pass

#---------------- MAIN ----------------

def main():

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CommandHandler("schedule", schedule))

app.add_handler(
    MessageHandler(
        filters.StatusUpdate.MY_CHAT_MEMBER,
        bot_added
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        buttons
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        broadcast
    )
)

app.add_handler(
    MessageHandler(
        filters.ALL,
        forward_post
    )
)

async def startup(app):

    await notify_restart(app)

    asyncio.create_task(
        check_schedule(app)
    )

app.post_init = startup

print("🚀 Bot Running...")

asyncio.set_event_loop(asyncio.new_event_loop())

while True:

    try:

        app.run_polling(
            drop_pending_updates=True
        )

    except Exception as e:

        print("CRASH:", e)

        print("♻️ Restarting...")

#---------------- START ----------------

threading.Thread(target=run_web).start()

main()
