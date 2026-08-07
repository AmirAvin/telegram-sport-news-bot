import os
import feedparser
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

bot = Bot(token=TOKEN)

RSS_URL = "https://feeds.bbci.co.uk/sport/football/rss.xml"

def get_news():
    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        return feed.entries[0].title + "\n\n" + feed.entries[0].link
    return None

def send_news():
    news = get_news()
    if news:
        bot.send_message(
            chat_id=CHANNEL,
            text="⚽️ خبر فوتبال\n\n" + news
        )

if __name__ == "__main__":
    send_news()
