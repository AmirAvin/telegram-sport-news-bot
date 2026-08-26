import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def main():
    bot = Bot(token=BOT_TOKEN)

    try:
        chat = await bot.get_chat("@ligebartar24")

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
