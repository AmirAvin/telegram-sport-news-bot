import os
import re
import json
import html
import time
import hashlib
import requests
import feedparser
import asyncio

from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL", "@ligebartar24")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

SENT_FILE = "sent_news.json"
LAST_RUN_FILE = "last_run.json"
TELEGRAM_LAST_RUN_FILE = "telegram_last_run.json"

MAX_NEWS_PER_RUN = 10

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


# ============================================================
# TELEGRAM CHANNELS
# ============================================================

TELEGRAM_CHANNELS = [
    {
        "username": "ft360_ir",
        "name": "فوتبال ۳۶۰",
    }
]


# ============================================================
# RSS SOURCES
# ============================================================

RSS_SOURCES = [
    "https://www.khabarvarzeshi.com/rss/tp/63",
    "https://www.khabarvarzeshi.com/rss/tp/110",
    "https://www.khabarvarzeshi.com/rss/tp/111",
    "https://www.khabarvarzeshi.com/rss/tp/103",
    "https://www.khabarvarzeshi.com/rss/tp/64",
    "https://www.khabarvarzeshi.com/rss/tp/65",
    "https://www.khabarvarzeshi.com/rss/tp/66",
    "https://www.khabarvarzeshi.com/rss/tp/67",
    "https://www.khabarvarzeshi.com/rss/tp/68",
    "https://www.khabarvarzeshi.com/rss/tp/75",
    "https://www.khabarvarzeshi.com/rss/tp/76",

    "https://www.sarpoosh.com/rss/football.xml",
    "https://www.sarpoosh.com/rss/iran-pro-league.xml",
    "https://www.sarpoosh.com/rss/football-world.xml",
    "https://www.sarpoosh.com/rss/champions-league.xml",
    "https://www.sarpoosh.com/rss/football-transfers/iran.xml",
    "https://www.sarpoosh.com/rss/football-transfers/world.xml",
]


# ============================================================
# FOOTBALL KEYWORDS
# ============================================================

FOOTBALL_KEYWORDS = [
    "فوتبال",
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "ذوب‌آهن",
    "ملوان",
    "گل گهر",
    "گل‌گهر",
    "فولاد",
    "آلومینیوم",
    "مس رفسنجان",
    "مس کرمان",
    "شمس آذر",
    "خیبر",
    "هوادار",
    "چادرملو",
    "نساجی",
    "پیکان",
    "سایپا",
    "لیگ برتر",
    "لیگ یک",
    "لیگ آزادگان",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان",
    "لیگ اروپا",
    "لیگ کنفرانس",
    "تیم ملی",
    "تیم‌ملی",
    "مربی",
    "سرمربی",
    "بازیکن",
    "مهاجم",
    "مدافع",
    "دروازه بان",
    "دروازه‌بان",
    "گلزن",
    "گلزنی",
    "گل",
    "پنالتی",
    "کارت قرمز",
    "کارت زرد",
    "داوری",
    "داور",
    "VAR",
    "ویدیو",
    "ویدئو",
    "طارمی",
    "مهدی طارمی",
    "آزمون",
    "سردار آزمون",
    "قلی زاده",
    "قلی‌زاده",
    "محبی",
    "محمد محبی",
    "جهانبخش",
    "قدوس",
    "بیرانوند",
    "حسین حسینی",
    "قلعه نویی",
    "قلعه‌نویی",
    "مجیدی",
    "جباری",
    "پیروز قربانی",
    "نویدکیا",
    "تارتار",
    "سهرا بختیاری زاده",
    "رئال مادرید",
    "بارسلونا",
    "اتلتیکو",
    "منچستریونایتد",
    "منچسترسیتی",
    "لیورپول",
    "آرسنال",
    "چلسی",
    "تاتنهام",
    "بایرن",
    "دورتموند",
    "یوونتوس",
    "اینتر",
    "میلان",
    "پاری سن ژرمن",
    "پاری‌سن‌ژرمن",
    "ناپولی",
    "رم",
    "لاتزیو",
    "مسی",
    "رونالدو",
    "امباپه",
    "هالند",
    "نیمار",
    "صلاح",
    "وینیسیوس",
    "بلینگام",
    "آسیا",
    "اروپا",
    "قطر",
    "امارات",
    "عربستان",
]


# ============================================================
# NON FOOTBALL KEYWORDS
# ============================================================

NON_FOOTBALL_KEYWORDS = [
    "والیبال",
    "بسکتبال",
    "کشتی",
    "تکواندو",
    "جودو",
    "بوکس",
    "وزنه برداری",
    "وزنه‌برداری",
    "فوتسال",
    "هندبال",
    "تنیس",
    "پینگ پنگ",
    "دوومیدانی",
    "دو و میدانی",
    "شنا",
    "اتومبیلرانی",
    "فرمول یک",
    "فرمول‌یک",
    "دوچرخه سواری",
    "دوچرخه‌سواری",
    "موتورسواری",
    "اسکی",
]


# ============================================================
# HASHTAGS
# ============================================================

HASHTAG_MAP = {
    "استقلال": "#استقلال",
    "پرسپولیس": "#پرسپولیس",
    "سپاهان": "#سپاهان",
    "تراکتور": "#تراکتور",
    "ذوب آهن": "#ذوب_آهن",
    "ذوب‌آهن": "#ذوب_آهن",
    "ملوان": "#ملوان",
    "گل گهر": "#گل_گهر",
    "گل‌گهر": "#گل_گهر",
    "فولاد": "#فولاد",
    "لیگ برتر": "#لیگ_برتر",
    "لیگ یک": "#لیگ_یک",
    "جام حذفی": "#جام_حذفی",
    "تیم ملی": "#تیم_ملی",
    "تیم‌ملی": "#تیم_ملی",
    "رئال مادرید": "#رئال_مادرید",
    "بارسلونا": "#بارسلونا",
    "منچستریونایتد": "#منچستریونایتد",
    "منچسترسیتی": "#منچسترسیتی",
    "لیورپول": "#لیورپول",
    "آرسنال": "#آرسنال",
    "چلسی": "#چلسی",
    "بایرن": "#بایرن",
    "دورتموند": "#دورتموند",
    "یوونتوس": "#یوونتوس",
    "اینتر": "#اینتر",
    "میلان": "#میلان",
    "پاری سن ژرمن": "#پاری_سن_ژرمن",
    "پاری‌سن‌ژرمن": "#پاری_سن_ژرمن",
    "طارمی": "#طارمی",
    "آزمون": "#آزمون",
    "قلی زاده": "#قلی_زاده",
    "قلی‌زاده": "#قلی_زاده",
    "محبی": "#محبی",
    "جهانبخش": "#جهانبخش",
    "قدوس": "#قدوس",
    "بیرانوند": "#بیرانوند",
    "رونالدو": "#رونالدو",
    "مسی": "#مسی",
    "امباپه": "#امباپه",
    "هالند": "#هالند",
    "نیمار": "#نیمار",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_title(text):
    if not text:
        return ""

    text = html.unescape(str(text))
    text = text.replace("\u200c", " ")
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def clean_text(text):
    if not text:
        return ""

    soup = BeautifulSoup(str(text), "html.parser")
    text = soup.get_text(" ", strip=True)

    text = html.unescape(text)
    text = text.replace("\u200c", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def truncate(text, limit):
    text = text or ""

    if len(text) <= limit:
        return text

    return text[:limit - 3].rstrip() + "..."


def clean_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(url)

        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            "",
            ""
        ))

    except Exception:
        return url


def fingerprint(text):
    normalized = normalize_title(text)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def similarity(a, b):
    a = normalize_title(a)
    b = normalize_title(b)

    if not a or not b:
        return 0

    return SequenceMatcher(None, a, b).ratio()


# ============================================================
# FOOTBALL FILTER
# ============================================================

def is_football_news(title, summary=""):
    text = normalize_title(
        f"{title} {summary}"
    )

    for bad in NON_FOOTBALL_KEYWORDS:
        if normalize_title(bad) in text:
            return False

    for keyword in FOOTBALL_KEYWORDS:
        if normalize_title(keyword) in text:
            return True

    return False


def is_telegram_football_post(text):
    """
    ft360_ir is a football channel.
    We reject obvious non-football posts but don't require
    a football keyword in every short post/video caption.
    """

    normalized = normalize_title(text)

    for bad in NON_FOOTBALL_KEYWORDS:
        if normalize_title(bad) in normalized:
            return False

    return True


# ============================================================
# HASHTAGS
# ============================================================

def create_hashtags(title, summary=""):
    text = f"{title} {summary}"

    result = []

    for keyword, hashtag in HASHTAG_MAP.items():
        if normalize_title(keyword) in normalize_title(text):
            if hashtag not in result:
                result.append(hashtag)

    if "فوتبال" in normalize_title(text):
        if "#فوتبال" not in result:
            result.insert(0, "#فوتبال")

    return " ".join(result[:6])


# ============================================================
# SENT DATABASE
# ============================================================

def load_sent():
    if not os.path.exists(SENT_FILE):
        return {
            "urls": [],
            "titles": [],
            "keys": []
        }

    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError()

        data.setdefault("urls", [])
        data.setdefault("titles", [])
        data.setdefault("keys", [])

        return data

    except Exception:
        return {
            "urls": [],
            "titles": [],
            "keys": []
        }


def save_sent(data):
    try:
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )
    except Exception as e:
        print("SAVE SENT ERROR:", e)


def make_news_key(news):
    title = normalize_title(news.get("title", ""))
    url = clean_url(news.get("link", ""))

    return hashlib.sha256(
        f"{title}|{url}".encode("utf-8")
    ).hexdigest()


def is_already_sent(news, sent):
    url = clean_url(news.get("link", ""))
    title_hash = fingerprint(news.get("title", ""))
    key = make_news_key(news)

    if url and url in sent["urls"]:
        return True

    if title_hash and title_hash in sent["titles"]:
        return True

    if key in sent["keys"]:
        return True

    return False


def register_sent(news, sent):
    url = clean_url(news.get("link", ""))
    title_hash = fingerprint(news.get("title", ""))
    key = make_news_key(news)

    if url and url not in sent["urls"]:
        sent["urls"].append(url)

    if title_hash and title_hash not in sent["titles"]:
        sent["titles"].append(title_hash)

    if key not in sent["keys"]:
        sent["keys"].append(key)

    # Prevent unlimited growth
    sent["urls"] = sent["urls"][-5000:]
    sent["titles"] = sent["titles"][-5000:]
    sent["keys"] = sent["keys"][-5000:]


# ============================================================
# LAST RUN
# ============================================================

def load_timestamp(filename):
    if not os.path.exists(filename):
        return None

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        return float(data.get("timestamp"))

    except Exception:
        return None


def save_timestamp(filename, timestamp):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": float(timestamp)},
                f
            )
    except Exception as e:
        print("SAVE TIMESTAMP ERROR:", e)


# ============================================================
# RSS
# ============================================================

def get_entry_image(entry):
    try:
        media_content = entry.get("media_content", [])

        if media_content:
            for media in media_content:
                url = media.get("url")

                if url:
                    return url

        media_thumbnail = entry.get("media_thumbnail", [])

        if media_thumbnail:
            for media in media_thumbnail:
                url = media.get("url")

                if url:
                    return url

        enclosures = entry.get("enclosures", [])

        for enclosure in enclosures:
            url = enclosure.get("href") or enclosure.get("url")

            if url:
                media_type = enclosure.get("type", "")

                if media_type.startswith("image/"):
                    return url

        summary = entry.get("summary", "")

        soup = BeautifulSoup(
            summary,
            "html.parser"
        )

        image = soup.find("img")

        if image and image.get("src"):
            return image["src"]

    except Exception:
        pass

    return None


def get_news_timestamp(entry):
    try:
        if entry.get("published_parsed"):
            return calendar.timegm(
                entry.published_parsed
            )
    except Exception:
        pass

    try:
        if entry.get("updated_parsed"):
            return calendar.timegm(
                entry.updated_parsed
            )
    except Exception:
        pass

    return time.time()


def fetch_rss(source):
    try:
        response = requests.get(
            source,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=30
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        results = []

        for entry in feed.entries:
            title = clean_text(
                entry.get("title", "")
            )

            summary = clean_text(
                entry.get("summary", "")
            )

            link = entry.get("link", "")

            if not title or not link:
                continue

            if not is_football_news(
                title,
                summary
            ):
                continue

            results.append({
                "title": title,
                "summary": summary,
                "link": link,
                "timestamp": get_news_timestamp(entry),
                "image_url": get_entry_image(entry),
                "source": "rss",
            })

        return results

    except Exception as e:
        print(
            "RSS ERROR:",
            source,
            e
        )

        return []


def get_article_text(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside"
        ]):
            tag.decompose()

        candidates = soup.find_all([
            "article",
            "main"
        ])

        if candidates:
            text = candidates[0].get_text(
                "\n",
                strip=True
            )
        else:
            text = soup.get_text(
                "\n",
                strip=True
            )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        return truncate(
            text,
            2500
        )

    except Exception:
        return ""


# ============================================================
# TELEGRAM PUBLIC CHANNEL
# ============================================================

def parse_telegram_datetime(value):
    if not value:
        return None

    try:
        value = value.strip()

        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.timestamp()

    except Exception:
        return None


def extract_css_url(style):
    if not style:
        return None

    match = re.search(
        r"url\(\s*['\"]?(.*?)['\"]?\s*\)",
        style,
        re.IGNORECASE
    )

    if match:
        return html.unescape(
            match.group(1)
        )

    return None


def clean_telegram_text(text):
    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    text = soup.get_text(
        "\n",
        strip=True
    )

    text = html.unescape(text)

    # Remove URLs from copied Telegram text
    text = re.sub(
        r"https?://\S+",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"www\.\S+",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"(?<!\w)t\.me/\S+",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove source channel handle
    text = re.sub(
        r"@ft360_ir\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def split_telegram_title(text):
    text = text.strip()

    if not text:
        return (
            "خبر فوتبال",
            ""
        )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return (
            "خبر فوتبال",
            ""
        )

    title = lines[0]

    if len(title) > 180:
        title = truncate(
            title,
            180
        )

    body = text

    if body.startswith(lines[0]):
        body = body[len(lines[0]):].strip()

    return title, body


def get_telegram_channel_news(username):
    url = f"https://t.me/s/{username}"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        messages = soup.select(
            "div.tgme_widget_message"
        )

        results = []

        for message in messages:
            date_element = message.select_one(
                "a.tgme_widget_message_date"
            )

            time_element = message.select_one(
                "a.tgme_widget_message_date time"
            )

            if not date_element:
                continue

            post_url = date_element.get(
                "href",
                ""
            )

            timestamp = None

            if time_element:
                timestamp = parse_telegram_datetime(
                    time_element.get(
                        "datetime",
                        ""
                    )
                )

            if not timestamp:
                continue

            text_element = message.select_one(
                "div.tgme_widget_message_text"
            )

            raw_text = ""

            if text_element:
                raw_text = str(
                    text_element
                )

            text = clean_telegram_text(
                raw_text
            )

            photo_element = message.select_one(
                "a.tgme_widget_message_photo_wrap"
            )

            video_element = message.select_one(
                "a.tgme_widget_message_video_player"
            )

            image_url = None
            media_type = "none"

            if photo_element:
                image_url = extract_css_url(
                    photo_element.get(
                        "style",
                        ""
                    )
                )

                if image_url:
                    media_type = "photo"

            elif video_element:
                # Telegram public preview does not give us
                # a reliable direct MP4 file.
                # Therefore we DO NOT send the video thumbnail
                # as if it were the video.
                media_type = "video"

            if not text and media_type == "none":
                continue

            if not is_telegram_football_post(text):
                continue

            title, body = split_telegram_title(
                text
            )

            if media_type == "video" and not text:
                title = "ویدئوی فوتبال ۳۶۰"
                body = ""

            results.append({
                "title": title,
                "summary": body,
                "full_text": text,
                "link": post_url,
                "timestamp": timestamp,
                "image_url": image_url,
                "media_type": media_type,
                "source": "telegram",
                "source_channel": username,
            })

        return results

    except Exception as e:
        print(
            "TELEGRAM CHANNEL ERROR:",
            username,
            e
        )

        return []


# ============================================================
# TELEGRAM MESSAGE BUILDERS
# ============================================================

def build_caption(news):
    title = clean_text(
        news.get("title", "")
    )

    summary = clean_text(
        news.get("summary", "")
    )

    hashtags = create_hashtags(
        title,
        summary
    )

    parts = []

    if title:
        parts.append(
            f"<b>{html.escape(title)}</b>"
        )

    if summary:
        parts.append(
            html.escape(
                truncate(summary, 750)
            )
        )

    if hashtags:
        parts.append(
            hashtags
        )

    parts.append(
        "@ligebartar24"
    )

    caption = "\n\n".join(
        parts
    )

    return truncate(
        caption,
        1024
    )


def build_text_message(news):
    title = clean_text(
        news.get("title", "")
    )

    summary = clean_text(
        news.get("summary", "")
    )

    hashtags = create_hashtags(
        title,
        summary
    )

    parts = []

    if title:
        parts.append(
            f"<b>{html.escape(title)}</b>"
        )

    if summary:
        parts.append(
            html.escape(
                truncate(summary, 3000)
            )
        )

    if hashtags:
        parts.append(
            hashtags
        )

    parts.append(
        "@ligebartar24"
    )

    return "\n\n".join(parts)


# ============================================================
# APARAT VIDEO
# ============================================================

def get_aparat_video(url, news):
    """
    Try to find an Aparat video.
    If unavailable, return None.
    """

    try:
        text = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=20
        ).text

        patterns = [
            r'https?://www\.aparat\.com/v/[^"\']+',
            r'https?://aparat\.com/v/[^"\']+',
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:
                return match.group(0)

    except Exception:
        pass

    return None


# ============================================================
# DOWNLOAD MEDIA
# ============================================================

def download_file(url, filename):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=30,
            stream=True
        )

        response.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in response.iter_content(
                chunk_size=8192
            ):
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        print(
            "DOWNLOAD ERROR:",
            e
        )

        return False


# ============================================================
# SEND NEWS
# ============================================================

def run_async(coro):
    try:
        return asyncio.run(coro)

    except RuntimeError:
        loop = asyncio.new_event_loop()

        try:
            return loop.run_until_complete(
                coro
            )
        finally:
            loop.close()


def send_news(bot, news, sent):
    try:
        caption = build_caption(
            news
        )

        text_message = build_text_message(
            news
        )

        # ----------------------------------------------------
        # TELEGRAM SOURCE
        # ----------------------------------------------------

        if news.get("source") == "telegram":

            image_url = news.get(
                "image_url"
            )

            media_type = news.get(
                "media_type"
            )

            if (
                image_url
                and media_type == "photo"
            ):
                filename = "telegram_photo.jpg"

                if download_file(
                    image_url,
                    filename
                ):
                    with open(
                        filename,
                        "rb"
                    ) as photo:

                        run_async(
                            bot.send_photo(
                                chat_id=CHANNEL,
                                photo=photo,
                                caption=caption,
                                parse_mode=ParseMode.HTML
                            )
                        )

                    try:
                        os.remove(filename)
                    except Exception:
                        pass

                else:
                    run_async(
                        bot.send_message(
                            chat_id=CHANNEL,
                            text=text_message,
                            parse_mode=ParseMode.HTML
                        )
                    )

            else:
                # Important:
                # A Telegram preview video is NOT treated as a photo.
                # Until we have a real MP4 URL, send text only.

                run_async(
                    bot.send_message(
                        chat_id=CHANNEL,
                        text=text_message,
                        parse_mode=ParseMode.HTML
                    )
                )

            register_sent(
                news,
                sent
            )

            return True

        # ----------------------------------------------------
        # RSS SOURCE
        # ----------------------------------------------------

        article_text = get_article_text(
            news.get("link", "")
        )

        if article_text:
            news_for_caption = dict(news)

            news_for_caption["summary"] = (
                article_text
            )

            caption = build_caption(
                news_for_caption
            )

            text_message = build_text_message(
                news_for_caption
            )

        # Try Aparat video only for RSS pages
        video_url = get_aparat_video(
            news.get("link", ""),
            news
        )

        if video_url:
            # We only send it if it is an actual downloadable
            # video file. Otherwise don't pretend it is a video.

            if video_url.endswith(
                (".mp4", ".m4v", ".webm")
            ):
                filename = "temp_video.mp4"

                if download_file(
                    video_url,
                    filename
                ):
                    with open(
                        filename,
                        "rb"
                    ) as video:

                        run_async(
                            bot.send_video(
                                chat_id=CHANNEL,
                                video=video,
                                caption=caption,
                                parse_mode=ParseMode.HTML
                            )
                        )

                    try:
                        os.remove(filename)
                    except Exception:
                        pass

                    register_sent(
                        news,
                        sent
                    )

                    return True

        # Photo
        image_url = news.get(
            "image_url"
        )

        if image_url:
            filename = "temp_photo.jpg"

            if download_file(
                image_url,
                filename
            ):
                with open(
                    filename,
                    "rb"
                ) as photo:

                    run_async(
                        bot.send_photo(
                            chat_id=CHANNEL,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    )

                try:
                    os.remove(filename)
                except Exception:
                    pass

                register_sent(
                    news,
                    sent
                )

                return True

        # Text
        run_async(
            bot.send_message(
                chat_id=CHANNEL,
                text=text_message,
                parse_mode=ParseMode.HTML
            )
        )

        register_sent(
            news,
            sent
        )

        return True

    except Exception as e:
        print(
            "SEND NEWS ERROR:",
            e
        )

        return False


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_news(news_list):
    result = []

    for news in sorted(
        news_list,
        key=lambda x: x.get(
            "timestamp",
            0
        )
    ):
        duplicate = False

        for existing in result:

            if clean_url(
                news.get("link", "")
            ) == clean_url(
                existing.get("link", "")
            ):
                duplicate = True
                break

            if similarity(
                news.get("title", ""),
                existing.get("title", "")
            ) >= 0.88:
                duplicate = True
                break

        if not duplicate:
            result.append(news)

    return result


# ============================================================
# RSS PROCESS
# ============================================================

def process_rss_news(bot, sent):
    print("")
    print("=" * 40)
    print("STARTING RSS")
    print("=" * 40)

    last_run = load_timestamp(
        LAST_RUN_FILE
    )

    now = time.time()

    all_news = []

    for source in RSS_SOURCES:
        print(
            "RSS:",
            source
        )

        news = fetch_rss(
            source
        )

        all_news.extend(
            news
        )

    print(
        "RSS FOOTBALL NEWS:",
        len(all_news)
    )

    # First run:
    # establish baseline and don't publish old news.
    if last_run is None:
        if all_news:
            newest = max(
                n.get("timestamp", now)
                for n in all_news
            )

            save_timestamp(
                LAST_RUN_FILE,
                max(now, newest)
            )
        else:
            save_timestamp(
                LAST_RUN_FILE,
                now
            )

        print(
            "RSS BASELINE CREATED"
        )

        return

    new_news = []

    for news in all_news:

        timestamp = news.get(
            "timestamp",
            0
        )

        if timestamp <= last_run:
            continue

        if is_already_sent(
            news,
            sent
        ):
            continue

        new_news.append(
            news
        )

    new_news = deduplicate_news(
        new_news
    )

    print(
        "NEW RSS NEWS:",
        len(new_news)
    )

    if not new_news:
        save_timestamp(
            LAST_RUN_FILE,
            now
        )

        return

    sent_count = 0
    last_success_timestamp = last_run

    for news in new_news[:MAX_NEWS_PER_RUN]:

        print(
            "SENDING RSS:",
            news.get("title")
        )

        success = send_news(
            bot,
            news,
            sent
        )

        if success:
            sent_count += 1

            last_success_timestamp = max(
                last_success_timestamp,
                news.get(
                    "timestamp",
                    last_success_timestamp
                )
            )

            save_sent(
                sent
            )

            time.sleep(1)

        else:
            print(
                "RSS SEND FAILED"
            )

    if sent_count > 0:
        save_timestamp(
            LAST_RUN_FILE,
            last_success_timestamp
        )

    save_sent(
        sent
    )

    print(
        "RSS SENT:",
        sent_count
    )


# ============================================================
# TELEGRAM CHANNEL PROCESS
# ============================================================

def process_telegram_news(bot, sent):
    print("")
    print("=" * 40)
    print("STARTING TELEGRAM CHANNELS")
    print("=" * 40)

    last_run = load_timestamp(
        TELEGRAM_LAST_RUN_FILE
    )

    now = time.time()

    all_news = []

    for channel in TELEGRAM_CHANNELS:

        username = channel["username"]

        print(
            "TELEGRAM CHANNEL:",
            username
        )

        news = get_telegram_channel_news(
            username
        )

        all_news.extend(
            news
        )

        print(
            "FOUND:",
            len(news)
        )

    # First Telegram run:
    # DO NOT publish old posts.
    if last_run is None:

        if all_news:
            newest = max(
                n.get(
                    "timestamp",
                    now
                )
                for n in all_news
            )

            save_timestamp(
                TELEGRAM_LAST_RUN_FILE,
                max(now, newest)
            )

        else:
            save_timestamp(
                TELEGRAM_LAST_RUN_FILE,
                now
            )

        print(
            "TELEGRAM BASELINE CREATED"
        )

        return

    new_news = []

    for news in all_news:

        timestamp = news.get(
            "timestamp",
            0
        )

        if timestamp <= last_run:
            continue

        if is_already_sent(
            news,
            sent
        ):
            continue

        new_news.append(
            news
        )

    new_news = deduplicate_news(
        new_news
    )

    print(
        "NEW TELEGRAM NEWS:",
        len(new_news)
    )

    if not new_news:
        save_timestamp(
            TELEGRAM_LAST_RUN_FILE,
            now
        )

        return

    sent_count = 0

    last_success_timestamp = last_run

    for news in new_news[:MAX_NEWS_PER_RUN]:

        print(
            "SENDING TELEGRAM:",
            news.get("title")
        )

        success = send_news(
            bot,
            news,
            sent
        )

        if success:
            sent_count += 1

            last_success_timestamp = max(
                last_success_timestamp,
                news.get(
                    "timestamp",
                    last_success_timestamp
                )
            )

            save_sent(
                sent
            )

            time.sleep(1)

        else:
            print(
                "TELEGRAM SEND FAILED"
            )

    # Only move Telegram timestamp after successful sends.
    if sent_count > 0:
        save_timestamp(
            TELEGRAM_LAST_RUN_FILE,
            last_success_timestamp
        )

    save_sent(
        sent
    )

    print(
        "TELEGRAM SENT:",
        sent_count
    )


# ============================================================
# API FOOTBALL STATUS
# ============================================================

def check_api_football():
    if not API_FOOTBALL_KEY:
        print(
            "API FOOTBALL KEY NOT SET - RSS MODE"
        )

        return False

    try:
        response = requests.get(
            "https://v3.football.api-sports.io/status",
            headers={
                "x-apisports-key":
                    API_FOOTBALL_KEY
            },
            timeout=20
        )

        print(
            "API REQUEST:",
            response.status_code
        )

        data = response.json()

        print(
            "API RESPONSE:",
            data
        )

        errors = data.get(
            "errors",
            {}
        )

        if errors:
            print(
                "API FOOTBALL UNAVAILABLE"
            )

            return False

        return True

    except Exception as e:
        print(
            "API FOOTBALL ERROR:",
            e
        )

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 50)
    print("TELEGRAM SPORTS NEWS BOT")
    print("=" * 50)
    print("FOOTBALL ONLY")
    print("RSS + TELEGRAM PUBLIC CHANNEL")
    print("=" * 50)

    if not BOT_TOKEN:
        print(
            "ERROR: BOT_TOKEN IS NOT SET"
        )

        return

    # API is optional.
    # Even if suspended, RSS and Telegram continue.
    check_api_football()

    try:
        bot = Bot(
            token=BOT_TOKEN
        )

        # Verify Telegram bot token
        me = run_async(
            bot.get_me()
        )

        print(
            "BOT:",
            me.username
        )

    except Exception as e:
        print(
            "BOT CONNECTION ERROR:",
            e
        )

        return

    sent = load_sent()

    # RSS
    process_rss_news(
        bot,
        sent
    )

    # Telegram public channels
    process_telegram_news(
        bot,
        sent
    )

    save_sent(
        sent
    )

    print("")
    print("=" * 50)
    print("BOT FINISHED")
    print("=" * 50)


if __name__ == "__main__":
    main()
