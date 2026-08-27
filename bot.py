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

# پشتیبانی از هر دو نام
CHANNEL = (
    os.getenv("CHANNEL_ID")
    or os.getenv("CHANNEL")
)

SENT_FILE = "sent_news.json"

MAX_NEWS_PER_RUN = 10

REQUEST_TIMEOUT = 30

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
# هشتگ‌ها
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

    media_content = entry.get(
        "media_content",
        []
    )

    if media_content:

        for media in media_content:

            url = media.get("url")

            if url:
                return url

    media_thumbnail = entry.get(
        "media_thumbnail",
        []
    )

    if media_thumbnail:

        for media in media_thumbnail:

            url = media.get("url")

            if url:
                return url

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

    html = entry.get(
        "summary",
        ""
    )

    if html:

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

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
# تشخیص URL ویدیو
# =========================

def is_probable_video_url(url):

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

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("http://"):
        return url

    if url.startswith("https://"):
        return url

    from urllib.parse import urljoin

    return urljoin(
        base_url,
        url
    )


# ==========================================================
# پیدا کردن Video Hash آپارات از صفحه خبر
# ==========================================================

def find_aparat_hash_from_html(
    html
):

    if not html:
        return None

    # روش اول: videohash
    patterns = [
        r"videohash/([A-Za-z0-9_-]+)",
        r"videohash%2F([A-Za-z0-9_-]+)",
        r"/v/([A-Za-z0-9_-]+)",
        r"aparat\.com/v/([A-Za-z0-9_-]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if match:

            video_hash = match.group(1)

            if video_hash:

                print(
                    "APARAT HASH FOUND:",
                    video_hash
                )

                return video_hash

    # روش دوم: بررسی iframe
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for iframe in soup.find_all(
        "iframe"
    ):

        src = (
            iframe.get("src")
            or iframe.get("data-src")
            or ""
        )

        if "aparat.com" in src.lower():

            print(
                "APARAT IFRAME:",
                src
            )

            for pattern in patterns:

                match = re.search(
                    pattern,
                    src,
                    re.IGNORECASE
                )

                if match:

                    video_hash = match.group(1)

                    if video_hash:

                        print(
                            "APARAT HASH FOUND FROM IFRAME:",
                            video_hash
                        )

                        return video_hash

    return None


# ==========================================================
# دریافت لینک MP4 از API آپارات
# ==========================================================

def get_aparat_video_url(
    video_hash
):

    if not video_hash:
        return None

    api_url = (
        "https://www.aparat.com/"
        "api/fa/v1/video/video/show/"
        f"videohash/{video_hash}"
    )

    print(
        "APARAT API:",
        api_url
    )

    try:

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

        # =========================
        # روش اول: file_link_all
        # =========================

        file_links = attributes.get(
            "file_link_all",
            []
        )

        best_url = None

        best_quality = 0

        for item in file_links:

            profile = str(
                item.get(
                    "profile",
                    ""
                )
            ).lower()

            urls = item.get(
                "urls",
                []
            )

            if not urls:
                continue

            url = urls[0]

            # کیفیت را از profile استخراج می‌کنیم
            quality_match = re.search(
                r"(\d+)",
                profile
            )

            if quality_match:

                quality = int(
                    quality_match.group(1)
                )

            else:

                quality = 0

            print(
                "APARAT FILE:",
                profile,
                url
            )

            # کیفیت ترجیحی:
            # 240p یا بالاتر
            if quality > best_quality:

                best_quality = quality
                best_url = url

        if best_url:

            print(
                "APARAT MP4 SELECTED:",
                best_url
            )

            return best_url

        # =========================
        # روش دوم: file_link
        # =========================

        file_link = attributes.get(
            "file_link"
        )

        if file_link:

            print(
                "APARAT FILE LINK:",
                file_link
            )

            return file_link

    except Exception as e:

        print(
            "APARAT API ERROR:",
            e
        )

    print(
        "APARAT VIDEO URL NOT FOUND"
    )

    return None


# ==========================================================
# پیدا کردن ویدیو آپارات از صفحه خبر
# ==========================================================

def get_aparat_video_from_article(
    article_url
):

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

        html = response.text

        video_hash = find_aparat_hash_from_html(
            html
        )

        if not video_hash:

            print(
                "APARAT HASH NOT FOUND"
            )

            return None

        video_url = get_aparat_video_url(
            video_hash
        )

        return video_url

    except Exception as e:

        print(
            "APARAT ARTICLE ERROR:",
            e
        )

        return None


# =========================
# پیدا کردن ویدیو عمومی
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

        # اگر خود URL ویدیو بود
        if content_type.startswith(
            "video/"
        ):

            return response.url

        html = response.text

        # ==================================================
        # اول آپارات
        # ==================================================

        if "aparat.com" in html.lower():

            aparat_video = (
                get_aparat_video_from_html(
                    html
                )
            )

            if aparat_video:

                return aparat_video

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # =========================
        # OG VIDEO
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

                url = tag.get(
                    "content"
                )

                if url:

                    url = make_absolute_url(
                        article_url,
                        url
                    )

                    if is_probable_video_url(
                        url
                    ):

                        print(
                            "VIDEO FOUND IN OG:",
                            url
                        )

                        return url

        # =========================
        # VIDEO TAG
        # =========================

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

                url = make_absolute_url(
                    article_url,
                    url
                )

                if is_probable_video_url(
                    url
                ):

                    print(
                        "VIDEO FOUND IN VIDEO TAG:",
                        url
                    )

                    return url

        # =========================
        # SOURCE TAG
        # =========================

        sources = soup.find_all(
            "source"
        )

        for source in sources:

            url = (
                source.get("src")
                or source.get("data-src")
            )

            if url:

                url = make_absolute_url(
                    article_url,
                    url
                )

                if is_probable_video_url(
                    url
                ):

                    print(
                        "VIDEO FOUND IN SOURCE:",
                        url
                    )

                    return url

        # =========================
        # لینک‌های مستقیم
        # =========================

        for link in soup.find_all(
            "a",
            href=True
        ):

            url = link.get(
                "href"
            )

            if url:

                url = make_absolute_url(
                    article_url,
                    url
                )

                if is_probable_video_url(
                    url
                ):

                    print(
                        "VIDEO FOUND IN LINK:",
                        url
                    )

                    return url

    except Exception as e:

        print(
            "VIDEO PAGE ERROR:",
            e
        )

    print(
        "VIDEO NOT FOUND"
    )

    return None


# ==========================================================
# استخراج ویدیو آپارات از HTML
# ==========================================================

def get_aparat_video_from_html(
    html
):

    video_hash = find_aparat_hash_from_html(
        html
    )

    if not video_hash:
        return None

    return get_aparat_video_url(
        video_hash
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

        content_length = len(
            response.content
        )

        print(
            "MEDIA CONTENT TYPE:",
            content_type
        )

        print(
            "MEDIA SIZE:",
            content_length,
            "bytes"
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

        if (
            content_type.startswith("video/")
            or
            ".mp4" in media_url.lower()
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
            "❌ CHANNEL_ID یا CHANNEL پیدا نشد"
        )

        return

    print(
        "CHANNEL:",
        CHANNEL
    )

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

            print(
                "CHECKING VIDEO:",
                news["title"]
            )

            print(
                "ARTICLE URL:",
                link
            )

            # ==================================================
            # پیدا کردن ویدیو
            # ==================================================

            video_url = get_video_url(
                link
            )

            media_sent = False

            # ==================================================
            # ارسال ویدیو
            # ==================================================

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
                        "🎥 VIDEO NEWS SENT"
                    )

            # ==================================================
            # اگر ویدیو ارسال نشد، عکس RSS
            # ==================================================

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

            # ==================================================
            # اگر هیچ رسانه‌ای نبود
            # ==================================================

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

            # ==================================================
            # ذخیره خبر
            # ==================================================

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
