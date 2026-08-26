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

REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


# =========================
# کلمات فوتبال
# =========================

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


# =========================
# کلمات هشتگ
# =========================

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


# =========================
# منابع RSS
# =========================

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

        with open(
            SENT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except Exception:

        return []


def save_sent_news(sent_news):

    with open(
        SENT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

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

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    text = soup.get_text(
        " ",
        strip=True
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================
# کوتاه کردن متن
# =========================

def shorten_text(
    text,
    max_length=700
):

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

def is_football_news(
    title,
    summary
):

    text = (
        f"{title} {summary}"
    ).lower()

    for keyword in FOOTBALL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================
# ساخت هشتگ
# =========================

def create_hashtags(
    title,
    summary
):

    text = (
        f"{title} {summary}"
    )

    found = []

    sorted_keywords = sorted(
        HASHTAG_KEYWORDS,
        key=len,
        reverse=True
    )

    for keyword in sorted_keywords:

        if keyword.lower() in text.lower():

            hashtag = (
                "#" +
                keyword.replace(
                    " ",
                    "_"
                )
            )

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

    return " ".join(
        found[:5]
    )


# =========================
# پیدا کردن رسانه در RSS
# =========================

def get_media_url(entry):

    # media_content
    media_content = entry.get(
        "media_content",
        []
    )

    if media_content:

        for media in media_content:

            url = media.get("url")

            if url:
                return url

    # media_thumbnail
    media_thumbnail = entry.get(
        "media_thumbnail",
        []
    )

    if media_thumbnail:

        for media in media_thumbnail:

            url = media.get("url")

            if url:
                return url

    # enclosures
    enclosures = entry.get(
        "enclosures",
        []
    )

    if enclosures:

        for enclosure in enclosures:

            url = (
                enclosure.get("href")
                or enclosure.get("url")
            )

            if url:
                return url

    # summary HTML
    html = entry.get(
        "summary",
        ""
    )

    if html:

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # img
        image = soup.find("img")

        if image:

            src = (
                image.get("src")
                or image.get("data-src")
            )

            if src:
                return src

    return None


# =========================
# پیدا کردن ویدیو از صفحه خبر
# =========================

def get_video_url(
    article_url
):

    if not article_url:
        return None

    try:

        response = requests.get(
            article_url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            allow_redirects=True
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()

        # اگر خود URL مستقیماً ویدیو بود
        if content_type.startswith("video/"):
            return response.url

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # =========================
        # og:video
        # =========================

        og_video_names = [
            "og:video",
            "og:video:url",
            "og:video:secure_url"
        ]

        for name in og_video_names:

            tag = soup.find(
                "meta",
                attrs={
                    "property": name
                }
            )

            if not tag:

                tag = soup.find(
                    "meta",
                    attrs={
                        "name": name
                    }
                )

            if tag:

                url = tag.get("content")

                if url and is_probable_video_url(url):
                    return make_absolute_url(
                        article_url,
                        url
                    )

        # =========================
        # video tag
        # =========================

        videos = soup.find_all(
            "video"
        )

        for video in videos:

            candidates = []

            src = video.get("src")

            if src:
                candidates.append(src)

            data_src = video.get(
                "data-src"
            )

            if data_src:
                candidates.append(
                    data_src
                )

            for source in video.find_all(
                "source"
            ):

                src = (
                    source.get("src")
                    or source.get("data-src")
                )

                if src:
                    candidates.append(src)

            for url in candidates:

                if is_probable_video_url(url):

                    return make_absolute_url(
                        article_url,
                        url
                    )

        # =========================
        # source tag
        # =========================

        sources = soup.find_all(
            "source"
        )

        for source in sources:

            url = (
                source.get("src")
                or source.get("data-src")
            )

            if url and is_probable_video_url(url):

                return make_absolute_url(
                    article_url,
                    url
                )

        # =========================
        # لینک مستقیم ویدیو
        # =========================

        for link in soup.find_all(
            "a",
            href=True
        ):

            url = link.get("href")

            if url and is_probable_video_url(url):

                return make_absolute_url(
                    article_url,
                    url
                )

    except Exception as e:

        print(
            "VIDEO PAGE ERROR:",
            e
        )

    return None


# =========================
# تشخیص URL ویدیو
# =========================

def is_probable_video_url(
    url
):

    if not url:
        return False

    url_lower = url.lower()

    video_extensions = [
        ".mp4",
        ".m4v",
        ".mov",
        ".webm",
        ".avi",
        ".mkv"
    ]

    for extension in video_extensions:

        if extension in url_lower:
            return True

    # بعضی CDNها پسوند ندارند
    video_words = [
        "/video/",
        "/videos/",
        "video_url",
        "video-url",
        "videourl",
        "mp4"
    ]

    for word in video_words:

        if word in url_lower:
            return True

    return False


# =========================
# تبدیل URL نسبی به کامل
# =========================

def make_absolute_url(
    base_url,
    url
):

    if not url:
        return None

    if url.startswith(
        "//"
    ):

        return "https:" + url

    if url.startswith(
        "http://"
    ) or url.startswith(
        "https://"
    ):

        return url

    from urllib.parse import urljoin

    return urljoin(
        base_url,
        url
    )


# =========================
# دریافت خبرها
# =========================

def get_news():

    all_news = []

    for rss_url in RSS_SOURCES:

        try:

            print(
                "READING RSS:",
                rss_url
            )

            response = requests.get(
                rss_url,
                timeout=15,
                headers=HEADERS
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            for entry in feed.entries:

                title = clean_text(
                    entry.get(
                        "title",
                        ""
                    )
                )

                summary = clean_text(
                    entry.get(
                        "summary",
                        ""
                    )
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
                "RSS ERROR:",
                rss_url
            )

            print(e)

    return all_news


# =========================
# ساخت متن خبر
# =========================

def create_message(
    news
):

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
# دانلود و ارسال رسانه
# =========================

async def send_media(
    bot,
    media_url,
    caption
):

    if not media_url:
        return False

    try:

        print(
            "MEDIA URL:",
            media_url
        )

        response = requests.get(
            media_url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()

        print(
            "MEDIA CONTENT TYPE:",
            content_type
        )

        # =========================
        # عکس
        # =========================

        if content_type.startswith(
            "image/"
        ):

            await bot.send_photo(
                chat_id=CHANNEL,
                photo=response.content,
                caption=caption,
                parse_mode="HTML"
            )

            print(
                "PHOTO SENT"
            )

            return True

        # =========================
        # ویدیو
        # =========================

        if content_type.startswith(
            "video/"
        ):

            await bot.send_video(
                chat_id=CHANNEL,
                video=response.content,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True
            )

            print(
                "VIDEO SENT"
            )

            return True

        # =========================
        # اگر Content-Type درست نبود
        # ولی URL شبیه ویدیو بود
        # =========================

        if is_probable_video_url(
            media_url
        ):

            await bot.send_video(
                chat_id=CHANNEL,
                video=response.content,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True
            )

            print(
                "VIDEO SENT BY URL"
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
        "تعداد اخبار ارسال شده قبلی:",
        len(sent_news)
    )

    news_list = get_news()

    print(
        "تعداد اخبار فوتبالی پیدا شده:",
        len(news_list)
    )

    bot = Bot(
        token=BOT_TOKEN
    )

    sent_count = 0

    for news in news_list:

        if sent_count >= MAX_NEWS_PER_RUN:
            break

        link = news["link"]

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

            # =========================
            # اول تلاش برای پیدا کردن ویدیو
            # =========================

            print(
                "CHECKING VIDEO:",
                news["title"]
            )

            video_url = get_video_url(
                link
            )

            media_sent = False

            # =========================
            # اگر ویدیو پیدا شد
            # =========================

            if video_url:

                print(
                    "VIDEO FOUND:",
                    video_url
                )

                media_sent = await send_media(
                    bot,
                    video_url,
                    message
                )

                if media_sent:

                    print(
                        "VIDEO NEWS SENT"
                    )

            # =========================
            # اگر ویدیو ارسال نشد
            # از رسانه RSS استفاده کن
            # =========================

            if not media_sent:

                rss_media = news.get(
                    "media_url"
                )

                if rss_media:

                    print(
                        "USING RSS MEDIA"
                    )

                    media_sent = await send_media(
                        bot,
                        rss_media,
                        message
                    )

            # =========================
            # اگر هیچ رسانه‌ای نبود
            # فقط متن
            # =========================

            if not media_sent:

                print(
                    "NO MEDIA - SENDING TEXT"
                )

                await bot.send_message(
                    chat_id=CHANNEL,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

            # =========================
            # ذخیره خبر
            # =========================

            sent_news.append(
                link
            )

            save_sent_news(
                sent_news
            )

            sent_count += 1

            print(
                "NEWS SENT:",
                news["title"]
            )

            await asyncio.sleep(
                2
            )

        except Exception as e:

            print(
                "SEND ERROR:"
            )

            print(e)

    print(
        "✅ اجرای ربات تمام شد.",
        sent_count,
        "خبر ارسال شد."
    )


# =========================
# شروع
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
