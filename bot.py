import os
import asyncio
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")


async def main():
    async with Bot(token=TOKEN) as bot:
        await bot.send_message(
            chat_id=CHANNEL,
            text="⚽️ تست ربات فوتبال — اتصال موفق شد!"
        )

    print("TEST MESSAGE SENT")


if __name__ == "__main__":
    asyncio.run(main())
