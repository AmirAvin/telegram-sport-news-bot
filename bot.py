import os
import json
import re
import asyncio
import feedparser
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SOURCES = [
    "https://www.khabarvarzeshi.com/rss",
]

FILE = "sent_news.json"


def load_sent():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(str(x) for x in data)
    except Exception:
        return set()


def save_sent(sent):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(sent), f, ensure_ascii=False, indent=2)


def get_news_id(link):
    match = re.search(r"/news/(\d+)", link)
    if match:
        return match.group(1)
    return link


def clean_text(text):
    return " ".join(text.split())


async def main():
    sent = load_sent()

    print("SENT IDS:", sorted(sent))
    print("CHECK 552592:", "552592" in sent)

    new_count = 0

    async with Bot(token=TOKEN) as bot:
        for source in SOURCES:
            feed = feedparser.parse(source)

            for item in feed.entries[:50]:
                title = clean_text(item.get("title", ""))
                link = item.get("link", "").strip()

                summary = clean_text(
                    item.get("summary", "")
                    or item.get("description", "")
                )

                if not title or not link:
                    continue

                news_id = get_news_id(link)

                if news_id in sent:
                    print("SKIPPED OLD NEWS:", news_id, title)
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

                sent.add(news_id)
                save_sent(sent)

                new_count += 1

                print("NEWS SENT:", news_id, title)

    if new_count == 0:
        print("NO NEW NEWS")
    else:
        print(f"TOTAL NEW NEWS SENT: {new_count}")


if __name__ == "__main__":
    asyncio.run(main())
