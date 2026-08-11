import os
import json
import re
import asyncio
import html
import feedparser

from telegram import Bot
from telegram.error import TimedOut, NetworkError, TelegramError

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SOURCES = [
    "https://www.khabarvarzeshi.com/rss",
]

FILE = "sent_news.json"
FOOTER = "@ligebartar24"

CHECK_INTERVAL = 600  # هر 10 دقیقه


def load_sent():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return set(str(x) for x in data)

        return set()

    except Exception as e:
        print("Could not load sent_news.json:", e)
        return set()


def save_sent(sent):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            sorted(sent),
            f,
            ensure_ascii=False,
            indent=2
        )


def get_news_id(link):
    match = re.search(r"/news/(\d+)", link)

    if match:
        return match.group(1)

    return link


def clean_text(text):
    if not text:
        return ""

    return " ".join(str(text).split())


def get_media_url(item):
    for enclosure in item.get("enclosures", []):
        url = enclosure.get("href") or enclosure.get("url")

        if url:
            return url

    for media in item.get("media_content", []):
        url = media.get("url")

        if url:
            return url

    for media in item.get("media_thumbnail", []):
        url = media.get("url")

        if url:
            return url

    raw = (
        item.get("summary", "")
        or item.get("description", "")
        or ""
    )

    match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        raw,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


async def send_text(bot, message):
    for attempt in range(3):
        try:
            await bot.send_message(
                chat_id=CHANNEL,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )

            return True

        except (TimedOut, NetworkError) as e:
            print(
                f"Telegram connection error "
                f"(attempt {attempt + 1}/3): {e}"
            )

            if attempt < 2:
                await asyncio.sleep(5)

        except TelegramError as e:
            print("Telegram error:", e)
            return False

        except Exception as e:
            print("Unexpected error:", e)
            return False

    return False


async def send_photo(bot, photo_url, caption):
    for attempt in range(3):
        try:
            await bot.send_photo(
                chat_id=CHANNEL,
                photo=photo_url,
                caption=caption,
                parse_mode="HTML",
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )

            return True

        except (TimedOut, NetworkError) as e:
            print(
                f"Photo connection error "
                f"(attempt {attempt + 1}/3): {e}"
            )

            if attempt < 2:
                await asyncio.sleep(5)

        except TelegramError as e:
            print("Photo Telegram error:", e)
            return False

        except Exception as e:
            print("Photo error:", e)
            return False

    return False


async def check_news(bot):
    sent = load_sent()

    print("Checking for new news...")

    new_count = 0

    for source in SOURCES:

        try:
            feed = feedparser.parse(source)

        except Exception as e:
            print("RSS error:", e)
            continue

        for item in feed.entries[:50]:

            title = clean_text(
                item.get("title", "")
            )

            link = item.get(
                "link",
                ""
            ).strip()

            summary = clean_text(
                item.get("summary", "")
                or item.get("description", "")
            )

            if not title or not link:
                continue

            news_id = get_news_id(link)

            if news_id in sent:
                print(
                    "SKIPPED OLD NEWS:",
                    news_id,
                    title
                )
                continue

            if not summary:
                summary = (
                    "جزئیات بیشتر این خبر را "
                    "می‌توانید از لینک منبع مشاهده کنید."
                )

            if len(summary) > 500:
                summary = summary[:500] + "..."

            safe_title = html.escape(title)
            safe_summary = html.escape(summary)
            safe_link = html.escape(link, quote=True)

            message = (
                f"⚽️ {safe_title}\n\n"
                f"📝 {safe_summary}\n\n"
                f'<a href="{safe_link}">🔗 لینک خبر</a>\n\n'
                f"{FOOTER}"
            )

            print(
                "TRYING TO SEND:",
                news_id,
                title
            )

            media_url = get_media_url(item)

            success = False

            if media_url:
                print(
                    "MEDIA FOUND:",
                    media_url
                )

                success = await send_photo(
                    bot,
                    media_url,
                    message
                )

            if not success:
                success = await send_text(
                    bot,
                    message
                )

            if success:
                sent.add(news_id)
                save_sent(sent)

                new_count += 1

                print(
                    "NEWS SENT:",
                    news_id,
                    title
                )

            else:
                print(
                    "NEWS NOT SENT:",
                    news_id,
                    title
                )

    if new_count == 0:
        print("NO NEW NEWS")

    else:
        print(
            f"TOTAL NEW NEWS SENT: {new_count}"
        )


async def main():

    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    if not CHANNEL:
        print("ERROR: CHANNEL is missing")
        return

    print("Football Bot started.")
    print("Checking news every 10 minutes.")

    async with Bot(token=TOKEN) as bot:

        while True:

            try:
                await check_news(bot)

            except Exception as e:
                print(
                    "ERROR DURING NEWS CHECK:",
                    e
                )

            print(
                "Next check in 10 minutes..."
            )

            await asyncio.sleep(
                CHECK_INTERVAL
            )


if __name__ == "__main__":
    asyncio.run(main())
