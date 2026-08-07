import os
import feedparser
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

RSS_URL = "https://feeds.bbci.co.uk/sport/football/rss.xml"


async def send_news():
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("No news found")
        return

    news = feed.entries[0]

    title = news.get("title", "خبر فوتبال")
    link = news.get("link", "")

    text = f"⚽️ {title}\n\n🔗 {link}"

    async with Bot(token=TOKEN) as bot:
        await bot.send_message(
            chat_id=CHANNEL,
            text=text
        )

    print("News sent successfully")


if __name__ == "__main__":
    asyncio.run(send_news())
