import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

CUSTOM_EMOJI_ID = "5791645007882495057"


async def main():
    print("START TEST")
    print("Connecting to Telegram...")

    bot = Bot(token=BOT_TOKEN)

    me = await bot.get_me()
    print("BOT OK")
    print("Bot username:", me.username)

    text = (
        f'<tg-emoji emoji-id="{CUSTOM_EMOJI_ID}">⚽️</tg-emoji> '
        'تست ایموجی لیگ‌برتر @ligebartar24'
    )

    print("Sending message...")

    message = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode="HTML"
    )

    print("MESSAGE SENT")
    print("Message ID:", message.message_id)

    await bot.close()
    print("TEST FINISHED")


if __name__ == "__main__":
    asyncio.run(main())
