import os
import json
import asyncio
import feedparser
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SOURCES = [
    "https://www.khabarvarzeshi.com/rss",
    "https://www.khabarvarzeshi.com/rss/tp/1",
    "https://www.khabarvarzeshi.com/rss/tp/119",
    "https://www.khabarvarzeshi.com/rss/tp/63",
    "https://www.khabarvarzeshi.com/rss/tp/145",
    "https://www.khabarvarzeshi.com/rss/tp/157",
]

FILE = "sent_news.json"


def load_sent():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_sent(sent):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent), f, ensure_ascii=False, indent=2)


async def main():
    sent = load_sent()

    async with Bot(token=TOKEN) as bot:
        for source in SOURCES:
            feed = feedparser.parse(source)

            for item in feed.entries[:10]:
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()

                if not title or not link:
                    continue

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
                return

    print("NO NEW NEWS")


if __name__ == "__main__":
    asyncio.run(main())
