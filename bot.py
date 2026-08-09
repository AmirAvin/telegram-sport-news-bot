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


def clean_text(text):
    return " ".join(text.split())


async def main():
    sent = load_sent()
    new_count = 0

    async with Bot(token=TOKEN) as bot:
        for source in SOURCES:
            feed = feedparser.parse(source)

            for item in feed.entries[:20]:
                title = clean_text(item.get("title", ""))
                link = item.get("link", "").strip()
                summary = clean_text(item.get("summary", ""))

                if not title or not link:
                    continue

                if link in sent:
                    continue

                if not summary:
                    summary = "جزئیات بیشتر این خبر را می‌توانید از لینک منبع مشاهده کنید."

                if len(summary) > 500:
                    summary = summary[:500] + "..."

                message = (
                    f"⚽️ {title}\n\n"
                    f"📝 {summary}\n\n"
                    f"🔗 منبع: {link}"
                )

                await bot.send_message(
                    chat_id=CHANNEL,
                    text=message
                )

                sent.add(link)
                save_sent(sent)
                new_count += 1

                print("NEWS SENT:", title)

    if new_count == 0:
        print("NO NEW NEWS")
    else:
        print(f"TOTAL NEW NEWS SENT: {new_count}")


if __name__ == "__main__":
    asyncio.run(main())
