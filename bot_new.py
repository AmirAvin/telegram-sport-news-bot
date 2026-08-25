import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def main():
    bot = Bot(BOT_TOKEN)

    updates = await bot.get_updates()

    print("=== UPDATES ===")

    for update in updates:
        print(update)

    await bot.shutdown()

asyncio.run(main())
