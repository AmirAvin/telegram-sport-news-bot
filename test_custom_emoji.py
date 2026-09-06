import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

CUSTOM_EMOJI_ID = "5791645007882495057"


async def main():
    print("START TEST")

    try:
        bot = Bot(token=BOT_TOKEN)

        me = await bot.get_me()
        print("BOT OK")
        print("Bot username:", me.username)

        text = (
            f'<tg-emoji emoji-id="{CUSTOM_EMOJI_ID}">⚽️</tg-emoji> '
            'تست ایموجی لیگ‌برتر @ligebartar24'
        )

        print("SENDING MESSAGE...")
        
        message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="HTML"
        )

        print("MESSAGE SENT")
        print("MESSAGE ID:", message.message_id)

        await bot.close()

    except Exception as e:
        print("===== ERROR DETAILS =====")
        print(type(e).__name__)
        print(str(e))
        print("=========================")
        raise


if __name__ == "__main__":
    asyncio.run(main())
