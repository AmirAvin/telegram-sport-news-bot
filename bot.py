import os
import json
import asyncio
import feedparser
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SOURCES = [
    "https://www.varzesh3.com/rss",
]

FILE = "sent_news.json"


def load_sent():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception:
        return set()


def save_sent(sent):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent), f, ensure_ascii=False, indent=2)


async def main():
    sent = load_sent()

    bot = Bot(token=TOKEN)

    try:
        for source in SOURCES:
            feed = feedparser.parse(source)

            for item in feed.entries[:10]:
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()

                if not title or not link:
                    continue

                # جلوگیری از ارسال خبر تکراری
                if link in sent:
                    continue

                message = (
                    f"⚽️ {title}\n\n"
                    f"🔗 {link}"
                )

                await bot.send_message(
                    chat_id=CHANNEL,
                    text=message
                )

                sent.add(link)
                save_sent(sent)

                print("NEWS SENT:", title)

                # فقط یک خبر جدید در هر اجرا
                return

        print("NO NEW NEWS")

    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
