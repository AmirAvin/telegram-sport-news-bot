import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

CUSTOM_EMOJI_ID = "5791832221211959289"


async def main():
    bot = Bot(token=BOT_TOKEN)

    print("CHANNEL_ID starts with -100:", CHANNEL_ID.startswith("-100"))
    print("CHANNEL_ID length:", len(CHANNEL_ID))

    try:
        chat = await bot.get_chat(chat_id=CHANNEL_ID)

        print("CHAT FOUND")
        print("Chat ID:", chat.id)
        print("Chat type:", chat.type)
        print("Chat username:", chat.username)

    except Exception as e:
        print("GET CHAT FAILED")
        print(type(e).__name__)
        print(str(e))

    await bot.shutdown()


asyncio.run(main())
