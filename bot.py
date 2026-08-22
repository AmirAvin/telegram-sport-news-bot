import os
import json
import re
import asyncio
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# =========================
# تنظیمات
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SENT_FILE = "sent_news.json"

MAX_NEWS_PER_RUN = 10

LOGO_FILE = "ligebartar_sticker.webp"

FOOTBALL_KEYWORDS = [
    "فوتبال",
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "گل گهر",
    "نساجی",
    "تیم ملی",
    "لیگ برتر",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان",
    "لیگ اروپا",
    "لژیونر",
    "طارمی",
    "آزمون",
    "جهانبخش",
    "قایدی",
    "رونالدو",
    "مسی",
    "رئال مادرید",
    "بارسلونا",
    "منچستریونایتد",
    "منچسترسیتی",
    "لیورپول",
    "چلسی",
    "آرسنال",
    "بایرن مونیخ",
    "اینتر",
    "میلان",
    "یوونتوس",
    "پاری سن ژرمن",
]

HASHTAG_KEYWORDS = [
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "گل گهر",
    "نساجی",
    "تیم ملی",
    "لیگ برتر",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان اروپا",
    "لیگ قهرمانان",
    "لیگ اروپا",
    "لژیونر",
    "مهدی طارمی",
    "طارمی",
    "سردار آزمون",
    "آزمون",
    "علیرضا جهانبخش",
    "جهانبخش",
    "مهدی قایدی",
    "قایدی",
    "رئال مادرید",
    "بارسلونا",
    "منچستریونایتد",
    "منچسترسیتی",
    "لیورپول",
    "چلسی",
    "آرسنال",
    "بایرن مونیخ",
    "اینتر",
    "میلان",
    "یوونتوس",
    "پاری سن ژرمن",
    "فوتبال ایران",
    "فوتبال اروپا",
]

RSS_SOURCES = [
    "https://www.isna.ir/rss",
    "https://www.khabarvarzeshi.com/rss",
    "https://www.varzesh3.com/rss",
    "https://www.tasnimnews.com/fa/rss",
]


# =========================
# اخبار ارسال شده
# =========================

def load_sent_news():
    if not os.path.exists(SENT_FILE):
        return []

    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_sent_news(sent_news):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            sent_news[-1000:],
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# تمیز کردن متن
# =========================

def clean_text(text):
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")

    text = soup.get_text(" ", strip=True)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================
# کوتاه کردن متن
# =========================

def shorten_text(text, max_length=700):

    text = clean_text(text)

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    shortened = text[:max_length]

    last_space = shortened.rfind(" ")

    if last_space > 400:
        shortened = shortened[:last_space]

    return shortened + "..."


# =========================
# تشخیص خبر فوتبالی
# =========================

def is_football_news(title, summary):

    text = f"{title} {summary}".lower()

    for keyword in FOOTBALL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================
# ساخت هشتگ
# =========================

def create_hashtags(title, summary):

    text = f"{title} {summary}"

    found = []

    sorted_keywords = sorted(
        HASHTAG_KEYWORDS,
        key=len,
        reverse=True
    )

    for keyword in sorted_keywords:

        if keyword.lower() in text.lower():

            hashtag = "#" + keyword.replace(" ", "_")

            if hashtag not in found:
                found.append(hashtag)

        if len(found) >= 5:
            break

    if len(found) < 3:
        if "#فوتبال" not in found:
            found.append("#فوتبال")

    if len(found) < 3:
        if "#اخبار_فوتبال" not in found:
            found.append("#اخبار_فوتبال")

    return " ".join(found[:5])


# =========================
# پیدا کردن رسانه خبر
# =========================

def get_media_url(entry):

    # 1 - media_content
    media_content = entry.get("media_content", [])

    if media_content:

        for media in media_content:

            url = media.get("url")

            if url:
                return url

    # 2 - media_thumbnail
    media_thumbnail = entry.get("media_thumbnail", [])

    if media_thumbnail:

        for media in media_thumbnail:

            url = media.get("url")

            if url:
                return url

    # 3 - enclosure
    enclosures = entry.get("enclosures", [])

    if enclosures:

        for enclosure in enclosures:

            url = enclosure.get("href") or enclosure.get("url")

            if url:
                return url

    # 4 - لینک عکس داخل summary
    html = entry.get("summary", "")

    if html:

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        image = soup.find("img")

        if image:

            src = image.get("src")

            if src:
                return src

    return None


# =========================
# دریافت خبرها
# =========================

def get_news():

    all_news = []

    for rss_url in RSS_SOURCES:

        try:

            response = requests.get(
                rss_url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            for entry in feed.entries:

                title = clean_text(
                    entry.get("title", "")
                )

                summary = clean_text(
                    entry.get("summary", "")
                )

                link = entry.get(
                    "link",
                    ""
                ).strip()

                if not title or not link:
                    continue

                if not is_football_news(
                    title,
                    summary
                ):
                    continue

                media_url = get_media_url(
                    entry
                )

                all_news.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "media_url": media_url
                })

        except Exception as e:

            print(
                f"RSS ERROR: {rss_url}"
            )

            print(e)

    return all_news


# =========================
# ساخت متن خبر
# =========================

def create_message(news):

    title = news["title"]

    summary = shorten_text(
        news["summary"]
    )

    hashtags = create_hashtags(
        title,
        summary
    )

    message = (
        f"⚽️ <b>{title}</b>\n\n"
    )

    if summary:
        message += (
            f"{summary}\n\n"
        )

    message += (
        f"{hashtags}\n\n"
        f"📢 @ligebartar24"
    )

    return message


# =========================
# ارسال لوگو
# =========================

async def send_logo(bot):

    if not os.path.exists(LOGO_FILE):

        print(
            "⚠️ فایل لوگو پیدا نشد:",
            LOGO_FILE
        )

        return

    try:

        with open(
            LOGO_FILE,
            "rb"
        ) as logo:

            await bot.send_sticker(
                chat_id=CHANNEL,
                sticker=logo
            )

        print("✅ LOGO SENT")

    except Exception as e:

        print(
            "⚠️ Sticker ارسال نشد:",
            e
        )

        # اگر فایل WEBP استیکر معتبر تلگرام نبود،
        # به عنوان فایل ارسال می‌شود.
        try:

            with open(
                LOGO_FILE,
                "rb"
            ) as logo:

                await bot.send_document(
                    chat_id=CHANNEL,
                    document=logo
                )

            print(
                "✅ LOGO SENT AS DOCUMENT"
            )

        except Exception as e2:

            print(
                "❌ LOGO ERROR:",
                e2
            )


# =========================
# ارسال رسانه
# =========================

async def send_media(
    bot,
    media_url,
    caption
):

    if not media_url:
        return False

    try:

        response = requests.get(
            media_url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()

        # تصویر
        if (
            content_type.startswith(
                "image/"
            )
        ):

            await bot.send_photo(
                chat_id=CHANNEL,
                photo=response.content,
                caption=caption,
                parse_mode="HTML"
            )

            return True

        # ویدئو
        if (
            content_type.startswith(
                "video/"
            )
        ):

            await bot.send_video(
                chat_id=CHANNEL,
                video=response.content,
                caption=caption,
                parse_mode="HTML"
            )

            return True

    except Exception as e:

        print(
            "MEDIA ERROR:",
            e
        )

    return False


# =========================
# اجرای اصلی
# =========================

async def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN پیدا نشد"
        )

        return

    if not CHANNEL:

        print(
            "❌ CHANNEL پیدا نشد"
        )

        return

    sent_news = load_sent_news()

    print(
        f"تعداد اخبار ارسال شده قبلی: "
        f"{len(sent_news)}"
    )

    news_list = get_news()

    print(
        f"تعداد اخبار فوتبالی پیدا شده: "
        f"{len(news_list)}"
    )

    bot = Bot(
        token=BOT_TOKEN
    )

    sent_count = 0

    for news in news_list:

        if sent_count >= MAX_NEWS_PER_RUN:
            break

        link = news["link"]

        # جلوگیری از تکراری
        if link in sent_news:

            print(
                "SKIPPED DUPLICATE:",
                news["title"]
            )

            continue

        message = create_message(
            news
        )

        try:

            # -------------------------
            # ارسال خبر
            # -------------------------

            media_sent = await send_media(
                bot,
                news.get("media_url"),
                message
            )

            if not media_sent:

                await bot.send_message(
                    chat_id=CHANNEL,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

            # -------------------------
            # ارسال لوگو
            # -------------------------

            await send_logo(bot)

            # ذخیره خبر
            sent_news.append(link)

            save_sent_news(
                sent_news
            )

            sent_count += 1

            print(
                "NEWS SENT:",
                news["title"]
            )

            await asyncio.sleep(2)

        except Exception as e:

            print(
                "SEND ERROR:"
            )

            print(e)

    print(
        f"✅ اجرای ربات تمام شد. "
        f"{sent_count} خبر ارسال شد."
    )


# =========================
# شروع
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
