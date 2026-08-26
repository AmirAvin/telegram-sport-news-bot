import os
import asyncio
from telegram import Bot
from telegram.constants import MessageEntityType
from telegram import MessageEntity


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

CUSTOM_EMOJI_ID = "5791832221211959289"


async def main():
    bot = Bot(token=BOT_TOKEN)

    text = "🏆 تست Custom Emoji با Entity"

    entities = [
        MessageEntity(
            type=MessageEntityType.CUSTOM_EMOJI,
            offset=0,
            length=2,
            custom_emoji_id=CUSTOM_EMOJI_ID,
        )
    ]

    message = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        entities=entities,
    )

    print("MESSAGE SENT")
    print("Message ID:", message.message_id)
    print("Message entities:", message.entities)

    await bot.shutdown()


asyncio.run(main())
