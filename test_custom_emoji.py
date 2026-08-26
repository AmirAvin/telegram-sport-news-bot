import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

CUSTOM_EMOJI_ID = "5791832221211959289"


async def main():
    bot = Bot(token=BOT_TOKEN)

    text = (
        f'<tg-emoji emoji-id="{CUSTOM_EMOJI_ID}">🏆</tg-emoji> '
        'تست بررسی Custom Emoji'
    )

    message = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode="HTML"
    )

    print("MESSAGE SENT")
    print("Message ID:", message.message_id)
    print("Message entities:", message.entities)

    await bot.shutdown()


asyncio.run(main())
