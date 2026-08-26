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

    emoji = "🏆"
    text = emoji + " تست دقیق Custom Emoji"

    # Telegram uses UTF-16 code units for entity offsets/lengths.
    offset = 0
    length = len(emoji.encode("utf-16-le")) // 2

    print("Emoji UTF-16 length:", length)

    entities = [
        MessageEntity(
            type=MessageEntityType.CUSTOM_EMOJI,
            offset=offset,
            length=length,
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
