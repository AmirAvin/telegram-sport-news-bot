import os
import json
import re
import asyncio
import feedparser
import requests

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from telegram import Bot


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

SENT_FILE = "sent_news.json"

MAX_NEWS_PER_RUN = 10
REQUEST_TIMEOUT = 30

CUSTOM_EMOJI_ID = "5231262796364137694"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
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


# =========================================================
# SENT NEWS
# =========================================================

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
        print("LOAD SENT ERROR:", error)

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
        print("SAVE SENT ERROR:", error)


# =========================================================
# TEXT
# =========================================================

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


# =========================================================
# FOOTBALL FILTER
# =========================================================

def is_football_news(
    title,
    summary
):

    text = (
        f"{title} {summary}"
        .lower()
    )

    for keyword in FOOTBALL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================================================
# HASHTAGS
# =========================================================

def create_hashtags(
    title,
    summary
):

    text = (
        f"{title} {summary}"
        .lower()
    )

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


# =========================================================
# RSS MEDIA
# =========================================================

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

        image = soup.find("img")

        if image:

            url = (
                image.get("src")
                or image.get("data-src")
            )

            if url:
                return url

    return None


# =========================================================
# VIDEO URL CHECK
# =========================================================

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


# =========================================================
# APARAT VIDEO HASH
# =========================================================

def extract_aparat_hash(url):

    if not url:
        return None

    patterns = [
        r"aparat\.com/v/([A-Za-z0-9]+)",
        r"aparat\.com/video/([A-Za-z0-9]+)",
        r"videohash/([A-Za-z0-9]+)",
        r"/v/([A-Za-z0-9]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


# =========================================================
# APARAT API
# =========================================================

def get_aparat_video_url(
    article_url
):

    if not article_url:
        return None

    try:

        parsed = urlparse(
            article_url
        )

        hostname = (
            parsed.hostname
            or ""
        ).lower()

        # فقط برای لینک‌های آپارات
        if (
            "aparat.com" not in hostname
            and "aparat.ir" not in hostname
        ):
            return None

        video_hash = extract_aparat_hash(
            article_url
        )

        if not video_hash:

            print(
                "APARAT HASH NOT FOUND:",
                article_url
            )

            return None

        api_url = (
            "https://www.aparat.com/"
            "api/fa/v1/video/video/show/"
            "videohash/"
            + video_hash
        )

        print(
            "APARAT HASH:",
            video_hash
        )

        print(
            "APARAT API:",
            api_url
        )

        response = requests.get(
            api_url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS
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
            "title",
            ""
        )

        duration = attributes.get(
            "duration",
            ""
        )

        print(
            "APARAT TITLE:",
            title
        )

        print(
            "APARAT DURATION:",
            duration
        )

        if attributes.get(
            "process"
        ) != "done":

            print(
                "APARAT VIDEO NOT READY"
            )

            return None

        # اولویت با MP4
        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        best_url = None

        best_quality = 0

        for item in file_link_all:

            profile = item.get(
                "profile",
                ""
            )

            urls = item.get(
                "urls",
                []
            )

            if not urls:
                continue

            match = re.search(
                r"(\d+)p",
                profile
            )

            quality = (
                int(match.group(1))
                if match
                else 0
            )

            if quality > best_quality:

                best_quality = quality
                best_url = urls[0]

        if best_url:

            print(
                "APARAT MP4 FOUND:",
                best_quality,
                "p"
            )

            return best_url

        # fallback
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

    return None


# =========================================================
# ARTICLE VIDEO DETECTION
# =========================================================

def get_video_url(
    article_url
):

    if not article_url:
        return None

    # -----------------------------------------
    # 1. اگر خود لینک آپارات باشد
    # -----------------------------------------

    aparat_video = get_aparat_video_url(
        article_url
    )

    if aparat_video:
        return aparat_video

    # -----------------------------------------
    # 2. باز کردن صفحه خبر
    # -----------------------------------------

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

        content_type = (
            response.headers
            .get(
                "content-type",
                ""
            )
            .lower()
        )

        print(
            "ARTICLE CONTENT TYPE:",
            content_type
        )

        if content_type.startswith(
            "video/"
        ):
            return response.url

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # -----------------------------------------
        # 3. آپارات داخل صفحه
        # -----------------------------------------

        html_text = response.text

        aparat_patterns = [
            r"aparat\.com/v/([A-Za-z0-9]+)",
            r"aparat\.com/video/([A-Za-z0-9]+)",
            r"videohash/([A-Za-z0-9]+)"
        ]

        for pattern in aparat_patterns:

            match = re.search(
                pattern,
                html_text,
                re.IGNORECASE
            )

            if match:

                video_hash = match.group(1)

                print(
                    "APARAT VIDEO HASH FOUND:",
                    video_hash
                )

                api_url = (
                    "https://www.aparat.com/"
                    "api/fa/v1/video/video/show/"
                    "videohash/"
                    + video_hash
                )

                try:

                    api_response = requests.get(
                        api_url,
                        timeout=REQUEST_TIMEOUT,
                        headers=HEADERS
                    )

                    print(
                        "APARAT EMBED API STATUS:",
                        api_response.status_code
                    )

                    if api_response.status_code == 200:

                        data = api_response.json()

                        attributes = (
                            data
                            .get("data", {})
                            .get("attributes", {})
                        )

                        file_links = (
                            attributes.get(
                                "file_link_all",
                                []
                            )
                        )

                        best_url = None
                        best_quality = 0

                        for item in file_links:

                            profile = item.get(
                                "profile",
                                ""
                            )

                            urls = item.get(
                                "urls",
                                []
                            )

                            if not urls:
                                continue

                            quality_match = re.search(
                                r"(\d+)p",
                                profile
                            )

                            quality = (
                                int(
                                    quality_match.group(1)
                                )
                                if quality_match
                                else 0
                            )

                            if quality > best_quality:

                                best_quality = quality
                                best_url = urls[0]

                        if best_url:

                            print(
                                "APARAT MP4 FROM ARTICLE:",
                                best_quality,
                                "p"
                            )

                            return best_url

                except Exception as error:

                    print(
                        "APARAT EMBED ERROR:",
                        error
                    )

                break

        # -----------------------------------------
        # 4. OpenGraph video
        # -----------------------------------------

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

                    if is_video_url(url):

                        print(
                            "VIDEO FOUND OG:",
                            url
                        )

                        return url

        # -----------------------------------------
        # 5. Video tag
        # -----------------------------------------

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
                    candidates.append(src)

            for url in candidates:

                url = urljoin(
                    article_url,
                    url
                )

                if is_video_url(url):

                    print(
                        "VIDEO FOUND TAG:",
                        url
                    )

                    return url

        # -----------------------------------------
        # 6. Source tag
        # -----------------------------------------

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

                if is_video_url(url):

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


# =========================================================
# NEWS
# =========================================================

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
                timeout=15,
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

            print(error)

    return all_news


# =========================================================
# MESSAGE
# =========================================================

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


# =========================================================
# SEND MEDIA
# =========================================================

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

        # -----------------------------------------
        # HEAD
        # -----------------------------------------

        try:

            head_response = requests.head(
                media_url,
                timeout=REQUEST_TIMEOUT,
                headers=HEADERS,
                allow_redirects=True
            )

            print(
                "MEDIA HEAD STATUS:",
                head_response.status_code
            )

            head_content_type = (
                head_response.headers
                .get(
                    "content-type",
                    ""
                )
                .lower()
            )

            print(
                "MEDIA HEAD TYPE:",
                head_content_type
            )

        except Exception as error:

            print(
                "HEAD ERROR:",
                error
            )

        # -----------------------------------------
        # GET
        # -----------------------------------------

        response = requests.get(
            media_url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            allow_redirects=True
        )

        print(
            "MEDIA STATUS:",
            response.status_code
        )

        response.raise_for_status()

        content_type = (
            response.headers
            .get(
                "content-type",
                ""
            )
            .lower()
        )

        content_length = len(
            response.content
        )

        print(
            "MEDIA CONTENT TYPE:",
            content_type
        )

        print(
            "MEDIA CONTENT LENGTH:",
            content_length
        )

        # -----------------------------------------
        # VIDEO
        # -----------------------------------------

        if (
            content_type.startswith(
                "video/"
            )
            or is_video_url(
                media_url
            )
        ):

            try:

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
                    "VIDEO SEND ERROR:",
                    error
                )

        # -----------------------------------------
        # IMAGE
        # -----------------------------------------

        if content_type.startswith(
            "image/"
        ):

            try:

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

            except Exception as error:

                print(
                    "PHOTO SEND ERROR:",
                    error
                )

        # -----------------------------------------
        # fallback by URL
        # -----------------------------------------

        if is_video_url(
            media_url
        ):

            try:

                await bot.send_video(
                    chat_id=CHANNEL,
                    video=response.content,
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True
                )

                print(
                    "✅ VIDEO SENT BY URL"
                )

                return True

            except Exception as error:

                print(
                    "VIDEO URL SEND ERROR:",
                    error
                )

    except Exception as error:

        print(
            "MEDIA ERROR:",
            error
        )

    return False


# =========================================================
# MAIN
# =========================================================

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

        message = create_message(
            news
        )

        try:

            print(
                "================================"
            )

            print(
                "PROCESSING:",
                news["title"]
            )

            # -----------------------------------------
            # 1. VIDEO
            # -----------------------------------------

            video_url = get_video_url(
                link
            )

            media_sent = False

            if video_url:

                print(
                    "VIDEO FOUND:"
                )

                print(
                    video_url
                )

                media_sent = await send_media(
                    bot,
                    video_url,
                    message
                )

            # -----------------------------------------
            # 2. RSS IMAGE
            # -----------------------------------------

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

            # -----------------------------------------
            # 3. TEXT
            # -----------------------------------------

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
                    "TEXT SENT"
                )

            # -----------------------------------------
            # SAVE
            # -----------------------------------------

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

        except Exception as error:

            print(
                "SEND ERROR:",
                error
            )

    print(
        "================================"
    )

    print(
        f"✅ اجرای ربات تمام شد. "
        f"{sent_count} خبر ارسال شد."
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
``
