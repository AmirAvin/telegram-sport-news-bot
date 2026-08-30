import os
import json
import re
import asyncio
import feedparser
import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup
from telegram import Bot


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SENT_FILE = "sent_news.json"

MAX_NEWS_PER_RUN = 10
REQUEST_TIMEOUT = 30

CUSTOM_EMOJI_ID = "5231262796364137694"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


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
    "پاری سن ژرمن"
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
    "لیگ قهرمانان",
    "لیگ اروپا",
    "لژیونر",
    "طارمی",
    "آزمون",
    "جهانبخش",
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
    "فوتبال اروپا"
]


RSS_SOURCES = [
    "https://www.isna.ir/rss",
    "https://www.khabarvarzeshi.com/rss",
    "https://www.varzesh3.com/rss",
    "https://www.tasnimnews.com/fa/rss"
]


# ============================================================
# SENT NEWS
# ============================================================

def load_sent_news():

    if not os.path.exists(SENT_FILE):
        return []

    try:

        with open(
            SENT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception as error:

        print(
            "LOAD SENT ERROR:",
            error
        )

    return []


def save_sent_news(sent_news):

    try:

        with open(
            SENT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sent_news[-1000:],
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            "SAVE SENT ERROR:",
            error
        )


# ============================================================
# TEXT
# ============================================================

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


def shorten_text(
    text,
    max_length=700
):

    text = clean_text(text)

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    text = text[:max_length]

    last_space = text.rfind(" ")

    if last_space > 400:
        text = text[:last_space]

    return text + "..."


# ============================================================
# FOOTBALL FILTER
# ============================================================

def is_football_news(
    title,
    summary
):

    text = f"{title} {summary}".lower()

    for keyword in FOOTBALL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# ============================================================
# HASHTAGS
# ============================================================

def create_hashtags(
    title,
    summary
):

    text = f"{title} {summary}".lower()

    found = []

    keywords = sorted(
        HASHTAG_KEYWORDS,
        key=len,
        reverse=True
    )

    for keyword in keywords:

        if keyword.lower() in text:

            hashtag = (
                "#"
                + keyword.replace(
                    " ",
                    "_"
                )
            )

            if hashtag not in found:
                found.append(hashtag)

        if len(found) >= 5:
            break

    if (
        len(found) < 3
        and "#فوتبال" not in found
    ):
        found.append("#فوتبال")

    if (
        len(found) < 3
        and "#اخبار_فوتبال" not in found
    ):
        found.append("#اخبار_فوتبال")

    return " ".join(
        found[:5]
    )


# ============================================================
# RSS MEDIA
# ============================================================

def get_media_url(entry):

    media_content = entry.get(
        "media_content",
        []
    )

    for media in media_content:

        url = media.get("url")

        if url:
            return url

    media_thumbnail = entry.get(
        "media_thumbnail",
        []
    )

    for media in media_thumbnail:

        url = media.get("url")

        if url:
            return url

    enclosures = entry.get(
        "enclosures",
        []
    )

    for enclosure in enclosures:

        url = (
            enclosure.get("href")
            or enclosure.get("url")
        )

        if url:
            return url

    summary = entry.get(
        "summary",
        ""
    )

    if summary:

        soup = BeautifulSoup(
            summary,
            "html.parser"
        )

        image = soup.find(
            "img"
        )

        if image:

            url = (
                image.get("src")
                or image.get("data-src")
            )

            if url:
                return url

    return None


# ============================================================
# VIDEO URL CHECK
# ============================================================

def is_video_url(url):

    if not url:
        return False

    url_lower = url.lower()

    extensions = [
        ".mp4",
        ".m4v",
        ".mov",
        ".webm",
        ".avi",
        ".mkv"
    ]

    for extension in extensions:

        if extension in url_lower:
            return True

    words = [
        "/video/",
        "/videos/",
        "video_url",
        "video-url",
        "videourl",
        "mp4"
    ]

    for word in words:

        if word in url_lower:
            return True

    return False


# ============================================================
# APARAT VIDEO HASH
# ============================================================

def extract_aparat_hash(
    url
):

    if not url:
        return None

    patterns = [

        r"videohash/([A-Za-z0-9_-]{5,20})",

        r"aparat\.com/v/([A-Za-z0-9_-]{5,20})",

        r"aparat\.com/video/([A-Za-z0-9_-]{5,20})",

        r"aparat\.com/video/video/([A-Za-z0-9_-]{5,20})"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url,
            re.IGNORECASE
        )

        if match:

            video_hash = match.group(1)

            print(
                "APARAT HASH FOUND:",
                video_hash
            )

            return video_hash

    return None


# ============================================================
# APARAT API
# ============================================================

def get_aparat_mp4(
    video_hash
):

    if not video_hash:
        return None

    api_url = (
        "https://www.aparat.com/api/fa/v1/"
        "video/video/show/videohash/"
        + video_hash
    )

    print(
        "APARAT API:",
        api_url
    )

    try:

        response = requests.get(
            api_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        print(
            "APARAT API STATUS:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        attributes = (
            data
            .get("data", {})
            .get("attributes", {})
        )

        title = attributes.get(
            "title"
        )

        if title:

            print(
                "APARAT TITLE:",
                title
            )

        duration = attributes.get(
            "duration"
        )

        if duration:

            print(
                "APARAT DURATION:",
                duration
            )

        content_type = attributes.get(
            "content_type"
        )

        print(
            "APARAT CONTENT TYPE:",
            content_type
        )

        # ----------------------------------------------------
        # file_link_all
        # ----------------------------------------------------

        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        for profile in file_link_all:

            profile_name = profile.get(
                "profile",
                ""
            )

            urls = profile.get(
                "urls",
                []
            )

            print(
                "APARAT PROFILE:",
                profile_name,
                "URLS:",
                len(urls)
            )

            for mp4_url in urls:

                if mp4_url:

                    print(
                        "APARAT MP4 FOUND:",
                        profile_name
                    )

                    return mp4_url

        # ----------------------------------------------------
        # Fallback file_link
        # ----------------------------------------------------

        file_link = attributes.get(
            "file_link"
        )

        if file_link:

            print(
                "APARAT FILE LINK FOUND"
            )

            return file_link

    except Exception as error:

        print(
            "APARAT API ERROR:",
            error
        )

    print(
        "APARAT MP4 NOT FOUND"
    )

    return None


# ============================================================
# GET VIDEO FROM ARTICLE
# ============================================================

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

        print(
            "ARTICLE STATUS:",
            response.status_code
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()

        print(
            "ARTICLE CONTENT TYPE:",
            content_type
        )

        # ----------------------------------------------------
        # Direct video
        # ----------------------------------------------------

        if content_type.startswith(
            "video/"
        ):
            return response.url

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ----------------------------------------------------
        # 1. APARAT IFRAMES
        # ----------------------------------------------------

        for iframe in soup.find_all(
            "iframe"
        ):

            iframe_url = (
                iframe.get("src")
                or iframe.get("data-src")
                or iframe.get("data-url")
            )

            if not iframe_url:
                continue

            iframe_url = urljoin(
                article_url,
                iframe_url
            )

            print(
                "IFRAME FOUND:",
                iframe_url
            )

            video_hash = extract_aparat_hash(
                iframe_url
            )

            if video_hash:

                mp4_url = get_aparat_mp4(
                    video_hash
                )

                if mp4_url:

                    print(
                        "✅ APARAT VIDEO FOUND"
                    )

                    return mp4_url

        # ----------------------------------------------------
        # 2. Search whole HTML for Aparat
        # ----------------------------------------------------

        aparat_patterns = [

            r'https?://(?:www\.)?aparat\.com/video/video/embed/videohash/([A-Za-z0-9_-]{5,20})',

            r'https?://(?:www\.)?aparat\.com/v/([A-Za-z0-9_-]{5,20})',

            r'videohash[/\\]+([A-Za-z0-9_-]{5,20})'

        ]

        for pattern in aparat_patterns:

            matches = re.findall(
                pattern,
                html,
                re.IGNORECASE
            )

            for video_hash in matches:

                print(
                    "APARAT HASH IN HTML:",
                    video_hash
                )

                mp4_url = get_aparat_mp4(
                    video_hash
                )

                if mp4_url:

                    print(
                        "✅ APARAT VIDEO FOUND FROM HTML"
                    )

                    return mp4_url

        # ----------------------------------------------------
        # 3. OG VIDEO
        # ----------------------------------------------------

        og_names = [
            "og:video",
            "og:video:url",
            "og:video:secure_url"
        ]

        for name in og_names:

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

                url = tag.get(
                    "content"
                )

                if url:

                    url = urljoin(
                        article_url,
                        url
                    )

                    if is_video_url(
                        url
                    ):

                        print(
                            "VIDEO FOUND OG:",
                            url
                        )

                        return url

        # ----------------------------------------------------
        # 4. VIDEO TAG
        # ----------------------------------------------------

        videos = soup.find_all(
            "video"
        )

        for video in videos:

            candidates = []

            src = video.get(
                "src"
            )

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
                    candidates.append(
                        src
                    )

            for url in candidates:

                url = urljoin(
                    article_url,
                    url
                )

                if is_video_url(
                    url
                ):

                    print(
                        "VIDEO FOUND TAG:",
                        url
                    )

                    return url

        # ----------------------------------------------------
        # 5. SOURCE TAG
        # ----------------------------------------------------

        sources = soup.find_all(
            "source"
        )

        for source in sources:

            url = (
                source.get("src")
                or source.get("data-src")
            )

            if url:

                url = urljoin(
                    article_url,
                    url
                )

                if is_video_url(
                    url
                ):

                    print(
                        "VIDEO FOUND SOURCE:",
                        url
                    )

                    return url

    except Exception as error:

        print(
            "VIDEO PAGE ERROR:",
            error
        )

    print(
        "VIDEO NOT FOUND"
    )

    return None


# ============================================================
# RSS NEWS
# ============================================================

def get_news():

    all_news = []

    for rss_url in RSS_SOURCES:

        try:

            print(
                "================================"
            )

            print(
                "READING RSS:",
                rss_url
            )

            response = requests.get(
                rss_url,
                timeout=20,
                headers=HEADERS
            )

            print(
                "RSS STATUS:",
                response.status_code
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

                all_news.append({

                    "title": title,

                    "summary": summary,

                    "link": link,

                    "media_url": get_media_url(
                        entry
                    )

                })

        except Exception as error:

            print(
                "RSS ERROR:",
                rss_url
            )

            print(
                error
            )

    return all_news


# ============================================================
# MESSAGE
# ============================================================

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

    logo = (
        '<tg-emoji emoji-id="'
        + CUSTOM_EMOJI_ID
        + '">🏆</tg-emoji>'
    )

    message = (
        logo
        + " <b>"
        + title
        + "</b>\n\n"
    )

    if summary:

        message += (
            summary
            + "\n\n"
        )

    message += (
        hashtags
        + "\n\n"
        + "📢 @ligebartar24"
    )

    return message


# ============================================================
# SEND MEDIA
# ============================================================

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

        print(
            "MEDIA STATUS:",
            response.status_code
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

        content_length = len(
            response.content
        )

        print(
            "MEDIA SIZE:",
            content_length,
            "bytes"
        )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

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
                "✅ PHOTO SENT"
            )

            return True

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        if (
            content_type.startswith(
                "video/"
            )
            or is_video_url(
                media_url
            )
        ):

            await bot.send_video(

                chat_id=CHANNEL,

                video=response.content,

                caption=caption,

                parse_mode="HTML",

                supports_streaming=True
            )

            print(
                "✅ VIDEO SENT"
            )

            return True

    except Exception as error:

        print(
            "MEDIA ERROR:",
            error
        )

    return False


# ============================================================
# MAIN
# ============================================================

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
        "SENT NEWS COUNT:",
        len(sent_news)
    )

    news_list = get_news()

    print(
        "FOOTBALL NEWS FOUND:",
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
                "SKIPPED OLD NEWS:",
                news["title"]
            )

            continue

        print(
            "\n"
            + "=" * 70
        )

        print(
            "PROCESSING:",
            news["title"]
        )

        message = create_message(
            news
        )

        try:

            media_sent = False

            # ------------------------------------------------
            # اول: پیدا کردن ویدئو
            # ------------------------------------------------

            video_url = get_video_url(
                link
            )

            if video_url:

                print(
                    "🎥 VIDEO URL FOUND"
                )

                media_sent = await send_media(

                    bot,

                    video_url,

                    message
                )

                if media_sent:

                    print(
                        "✅ VIDEO NEWS SENT"
                    )

            # ------------------------------------------------
            # دوم: اگر ویدئو نبود، عکس RSS
            # ------------------------------------------------

            if not media_sent:

                rss_media = news.get(
                    "media_url"
                )

                if rss_media:

                    print(
                        "TRY RSS MEDIA:",
                        rss_media
                    )

                    media_sent = await send_media(

                        bot,

                        rss_media,

                        message
                    )

            # ------------------------------------------------
            # سوم: اگر هیچ رسانه‌ای نبود، متن
            # ------------------------------------------------

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

                print(
                    "✅ TEXT SENT"
                )

            # ------------------------------------------------
            # ذخیره خبر ارسال‌شده
            # ------------------------------------------------

            sent_news.append(
                link
            )

            save_sent_news(
                sent_news
            )

            sent_count += 1

            print(
                "✅ NEWS SENT:",
                news["title"]
            )

            await asyncio.sleep(
                2
            )

        except Exception as error:

            print(
                "❌ SEND ERROR:",
                error
            )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "✅ اجرای ربات تمام شد."
    )

    print(
        f"تعداد خبرهای ارسال‌شده: {sent_count}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
