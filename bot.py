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
    # 1. RSS enclosure
    for enclosure in item.get("enclosures", []):
        url = enclosure.get("href") or enclosure.get("url")

        if url:
            return url

    # 2. media_content
    for media in item.get("media_content", []):
        url = media.get("url")

        if url:
            return url

    # 3. media_thumbnail
    for media in item.get("media_thumbnail", []):
        url = media.get("url")

        if url:
            return url

    # 4. Search inside RSS HTML for an image
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


async def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing")
        return

    if not CHANNEL:
        print("ERROR: CHANNEL is missing")
        return

    sent = load_sent()

    print("SENT IDS:", sorted(sent))

    new_count = 0

    async with Bot(token=TOKEN) as bot:

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

                caption = (
                    f"⚽️ {safe_title}\n\n"
                    f"📝 {safe_summary}\n\n"
                    f'<a href="{html.escape(link, quote=True)}">'
                    f"🔗 لینک خبر"
                    f"</a>\n\n"
                    f"{FOOTER}"
                )

                media_url = get_media_url(item)

                print(
                    "TRYING TO SEND:",
                    news_id,
                    title
                )

                success = False

                # اگر RSS عکس داشت، ابتدا عکس را می‌فرستیم
                if media_url:
                    print(
                        "MEDIA FOUND:",
                        media_url
                    )

                    success = await send_photo(
                        bot,
                        media_url,
                        caption
                    )

                    if not success:
                        print(
                            "MEDIA SEND FAILED - "
                            "SENDING TEXT ONLY"
                        )

                # اگر عکس وجود نداشت یا ارسالش نشد
                if not success:
                    success = await send_text(
                        bot,
                        caption
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


if __name__ == "__main__":
    asyncio.run(main())
