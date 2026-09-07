import os
import re
import json
import html
import time
import requests
import feedparser
import asyncio
import calendar

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

CUSTOM_EMOJI_ID = "5231262796364137694"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
)


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
    "مس شهر بابک",
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
    "خداداد",
    "قلعه نویی",
    "قلعه‌نویی",
    "مجیدی",
    "جباری",
    "پیروز قربانی",
    "نویدکیا",
    "تارتار",
    "سهراب بختیاری زاده",
    "سهراب بختیاری‌زاده",

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

    "آسیا",
    "اروپا",
    "قطر",
    "امارات",
    "عربستان",
    "کرواسی",
    "روسیه",
]


NON_FOOTBALL_KEYWORDS = [
    "والیبال",
    "بسکتبال",
    "کشتی",
    "تنیس",
    "بوکس",
    "فرمول یک",
    "اتومبیلرانی",
    "اسب",
]


# ============================================================
# HASHTAGS
# ============================================================

HASHTAG_MAP = {
    "استقلال": "#استقلال",
    "پرسپولیس": "#پرسپولیس",
    "سپاهان": "#سپاهان",
    "تراکتور": "#تراکتور",
    "ذوب آهن": "#ذوب‌آهن",
    "ذوب‌آهن": "#ذوب‌آهن",
    "فولاد": "#فولاد",
    "ملوان": "#ملوان",
    "گل گهر": "#گل‌گهر",
    "گل‌گهر": "#گل‌گهر",
    "آلومینیوم": "#آلومینیوم",
    "طارمی": "#طارمی",
    "آزمون": "#آزمون",
    "بیرانوند": "#بیرانوند",
    "حسینی": "#حسینی",
    "قلعه نویی": "#قلعه‌نویی",
    "قلعه‌نویی": "#قلعه‌نویی",
    "پیروز قربانی": "#پیروزقربانی",
    "نویدکیا": "#نویدکیا",
    "تارتار": "#تارتار",
    "جباری": "#جباری",
    "جام حذفی": "#جام_حذفی",
    "لیگ برتر": "#لیگ_برتر",
    "لیگ قهرمانان": "#لیگ_قهرمانان",
    "لیگ اروپا": "#لیگ_اروپا",
    "تیم ملی": "#تیم_ملی",

    "رئال مادرید": "#رئال_مادرید",
    "بارسلونا": "#بارسلونا",
    "اتلتیکو": "#اتلتیکو",
    "منچستریونایتد": "#منچستریونایتد",
    "منچسترسیتی": "#منچسترسیتی",
    "لیورپول": "#لیورپول",
    "آرسنال": "#آرسنال",
    "چلسی": "#چلسی",
    "تاتنهام": "#تاتنهام",
    "بایرن": "#بایرن",
    "دورتموند": "#دورتموند",
    "یوونتوس": "#یوونتوس",
    "اینتر": "#اینتر",
    "میلان": "#میلان",
    "پاری سن ژرمن": "#پاری‌سن‌ژرمن",
    "پاری‌سن‌ژرمن": "#پاری‌سن‌ژرمن",

    "فوتبال": "#فوتبال",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_title(text):

    if not text:
        return ""

    text = html.unescape(str(text))

    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")

    text = text.replace("\u200c", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


# ============================================================
# HASHTAGS
# ============================================================

def create_hashtags(title):

    normalized = normalize_title(title)

    found = []

    sorted_keys = sorted(
        HASHTAG_MAP.keys(),
        key=len,
        reverse=True
    )

    for key in sorted_keys:

        if normalize_title(key) in normalized:

            tag = HASHTAG_MAP[key]

            if tag not in found:
                found.append(tag)

        if len(found) >= 4:
            break

    if "#فوتبال" not in found:
        found.append("#فوتبال")

    return " ".join(
        found[:5]
    )


# ============================================================
# SENT DATABASE
# ============================================================

def load_sent_news():

    if not os.path.exists(
        SENT_FILE
    ):
        return set()

    try:

        with open(
            SENT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(
            data,
            list
        ):
            return set(data)

        if isinstance(
            data,
            dict
        ):
            return set(data.keys())

    except Exception as e:

        print(
            "LOAD SENT ERROR:",
            repr(e)
        )

    return set()


def save_sent_news(sent):

    try:

        with open(
            SENT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                list(sent),
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            "SAVE SENT ERROR:",
            repr(e)
        )


def register_sent(
    link,
    sent
):

    sent.add(link)

    save_sent_news(
        sent
    )


# ============================================================
# LAST RUN
# ============================================================

def load_last_run():

    if not os.path.exists(
        LAST_RUN_FILE
    ):
        return None

    try:

        with open(
            LAST_RUN_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        value = data.get(
            "last_run"
        )

        if value:
            return float(value)

    except Exception as e:

        print(
            "LOAD LAST RUN ERROR:",
            repr(e)
        )

    return None


def save_last_run(
    timestamp
):

    try:

        with open(
            LAST_RUN_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "last_run": timestamp
                },
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            "SAVE LAST RUN ERROR:",
            repr(e)
        )


# ============================================================
# FOOTBALL FILTER
# ============================================================

def is_football_news(title):

    normalized = normalize_title(
        title
    )

    for bad in NON_FOOTBALL_KEYWORDS:

        if normalize_title(
            bad
        ) in normalized:

            return False

    for keyword in FOOTBALL_KEYWORDS:

        if normalize_title(
            keyword
        ) in normalized:

            return True

    return False


# ============================================================
# RSS
# ============================================================

def get_news(
    rss_url
):

    try:

        headers = {
            "User-Agent": USER_AGENT
        }

        response = requests.get(
            rss_url,
            headers=headers,
            timeout=30
        )

        print(
            "RSS STATUS:",
            response.status_code
        )

        if response.status_code != 200:
            return []

        feed = feedparser.parse(
            response.content
        )

        news = []

        for entry in feed.entries:

            title = html.unescape(
                entry.get(
                    "title",
                    ""
                )
            ).strip()

            link = entry.get(
                "link",
                ""
            ).strip()

            summary = entry.get(
                "summary",
                entry.get(
                    "description",
                    ""
                )
            )

            if not title or not link:
                continue

            if not is_football_news(
                title
            ):

                print(
                    "NOT FOOTBALL:",
                    title
                )

                continue

            news.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "entry": entry,
                }
            )

        return news

    except Exception as e:

        print(
            "RSS ERROR:",
            repr(e)
        )

        return []


# ============================================================
# NEWS TIMESTAMP
# ============================================================

def get_news_timestamp(
    news
):

    try:

        entry = news.get(
            "entry"
        )

        if not entry:
            return None

        published_parsed = entry.get(
            "published_parsed"
        )

        if published_parsed:

            return float(
                calendar.timegm(
                    published_parsed
                )
            )

        updated_parsed = entry.get(
            "updated_parsed"
        )

        if updated_parsed:

            return float(
                calendar.timegm(
                    updated_parsed
                )
            )

    except Exception as e:

        print(
            "NEWS TIMESTAMP ERROR:",
            repr(e)
        )

    return None


# ============================================================
# ARTICLE CONTENT
# ============================================================

def get_article_content(
    url
):

    try:

        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return ""

        return response.text

    except Exception as e:

        print(
            "ARTICLE ERROR:",
            repr(e)
        )

        return ""


# ============================================================
# APARAT HASH FINDER
# ============================================================

def extract_aparat_hash(
    text
):

    if not text:
        return None

    try:

        text = html.unescape(
            str(text)
        )

        patterns = [

            r'aparat\.com/v/([A-Za-z0-9]+)',

            r'aparat\.com\/v\/([A-Za-z0-9]+)',

            r'videohash[\/"\':=\s]+([A-Za-z0-9]+)',

            r'/video/video/embed/videohash/([A-Za-z0-9]+)',

            r'embed/videohash/([A-Za-z0-9]+)',

            r'["\']\/v\/([A-Za-z0-9]+)["\']',

            r'data-videohash\s*=\s*["\']([^"\']+)["\']',

            r'videoHash\s*[:=]\s*["\']([^"\']+)["\']',

            r'video_hash\s*[:=]\s*["\']([^"\']+)["\']',

            r'["\']uid["\']\s*[:=]\s*["\']([A-Za-z0-9]+)["\']',

            r'videohash=([A-Za-z0-9]+)',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(
                    1
                ).strip()

                if value:
                    return value

    except Exception as e:

        print(
            "HASH EXTRACTION ERROR:",
            repr(e)
        )

    return None


def find_aparat_hash_in_entry(
    entry
):

    if not entry:
        return None

    try:

        if hasattr(
            entry,
            "keys"
        ):

            for key in entry.keys():

                try:

                    value = entry.get(
                        key
                    )

                    if isinstance(
                        value,
                        (str, bytes)
                    ):

                        if isinstance(
                            value,
                            bytes
                        ):

                            value = value.decode(
                                "utf-8",
                                errors="ignore"
                            )

                        found = extract_aparat_hash(
                            value
                        )

                        if found:

                            print(
                                "✅ APARAT HASH FOUND FROM RSS FIELD:",
                                key,
                                found
                            )

                            return found

                except Exception:
                    continue

    except Exception as e:

        print(
            "RSS ENTRY HASH ERROR:",
            repr(e)
        )

    return None


# ============================================================
# APARAT VIDEO
# ============================================================

def get_aparat_video(
    url,
    news_entry=None
):

    print()
    print(
        "🎥 CHECKING APARAT VIDEO:",
        url
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
        "Referer": "https://www.aparat.com/",
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            "APARAT PAGE STATUS:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        page_html = response.text

        video_hash = None

        # ----------------------------------------------------
        # 1. HTML
        # ----------------------------------------------------

        video_hash = extract_aparat_hash(
            page_html
        )

        if video_hash:

            print(
                "✅ VIDEO HASH FOUND FROM HTML:",
                video_hash
            )

        # ----------------------------------------------------
        # 2. iframe
        # ----------------------------------------------------

        if not video_hash:

            try:

                soup = BeautifulSoup(
                    page_html,
                    "html.parser"
                )

                for iframe in soup.find_all(
                    "iframe"
                ):

                    src = iframe.get(
                        "src",
                        ""
                    )

                    if src:

                        found = extract_aparat_hash(
                            src
                        )

                        if found:

                            video_hash = found

                            print(
                                "✅ VIDEO HASH FOUND FROM IFRAME:",
                                video_hash
                            )

                            break

            except Exception as e:

                print(
                    "IFRAME SEARCH ERROR:",
                    repr(e)
                )

        # ----------------------------------------------------
        # 3. Script
        # ----------------------------------------------------

        if not video_hash:

            try:

                soup = BeautifulSoup(
                    page_html,
                    "html.parser"
                )

                for script in soup.find_all(
                    "script"
                ):

                    script_text = script.get_text(
                        " ",
                        strip=False
                    )

                    if not script_text:
                        continue

                    found = extract_aparat_hash(
                        script_text
                    )

                    if found:

                        video_hash = found

                        print(
                            "✅ VIDEO HASH FOUND FROM SCRIPT:",
                            video_hash
                        )

                        break

            except Exception as e:

                print(
                    "SCRIPT SEARCH ERROR:",
                    repr(e)
                )

        # ----------------------------------------------------
        # 4. RSS entry
        # ----------------------------------------------------

        if not video_hash and news_entry:

            video_hash = find_aparat_hash_in_entry(
                news_entry.get(
                    "entry"
                )
            )

        # ----------------------------------------------------
        # 5. RSS summary
        # ----------------------------------------------------

        if not video_hash and news_entry:

            summary = news_entry.get(
                "summary",
                ""
            )

            video_hash = extract_aparat_hash(
                summary
            )

            if video_hash:

                print(
                    "✅ VIDEO HASH FOUND FROM RSS SUMMARY:",
                    video_hash
                )

        # ----------------------------------------------------
        # No hash
        # ----------------------------------------------------

        if not video_hash:

            print(
                "❌ APARAT VIDEO HASH NOT FOUND"
            )

            return None

        # ----------------------------------------------------
        # Aparat API
        # ----------------------------------------------------

        api_url = (
            "https://www.aparat.com/api/fa/v1/video/video/show/"
            f"videohash/{video_hash}"
        )

        print(
            "APARAT API URL:",
            api_url
        )

        api_response = requests.get(
            api_url,
            headers=headers,
            timeout=30
        )

        print(
            "APARAT API STATUS:",
            api_response.status_code
        )

        if api_response.status_code != 200:
            return None

        try:

            data = api_response.json()

        except Exception as e:

            print(
                "APARAT JSON ERROR:",
                repr(e)
            )

            return None

        root = data.get(
            "data",
            {}
        )

        if isinstance(
            root,
            dict
        ):

            attributes = root.get(
                "attributes",
                {}
            )

        else:

            attributes = {}

        if not isinstance(
            attributes,
            dict
        ):

            attributes = {}

        print(
            "VIDEO TITLE:",
            attributes.get(
                "title"
            )
        )

        print(
            "VIDEO DURATION:",
            attributes.get(
                "duration"
            )
        )

        print(
            "VIDEO PROCESS:",
            attributes.get(
                "process"
            )
        )

        print(
            "VIDEO CONTENT TYPE:",
            attributes.get(
                "content_type"
            )
        )

        print(
            "VIDEO CAN DOWNLOAD:",
            attributes.get(
                "can_download"
            )
        )

        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        if not file_link_all:

            print(
                "❌ NO FILE_LINK_ALL"
            )

            return None

        mp4_list = []

        # ----------------------------------------------------
        # MP4 extraction
        # ----------------------------------------------------

        for item in file_link_all:

            if not isinstance(
                item,
                dict
            ):
                continue

            profile = item.get(
                "profile",
                ""
            )

            urls = item.get(
                "urls",
                []
            )

            if isinstance(
                urls,
                str
            ):

                urls = [urls]

            if not isinstance(
                urls,
                list
            ):

                continue

            for media_url in urls:

                if not isinstance(
                    media_url,
                    str
                ):
                    continue

                clean_url = media_url.strip()

                if ".mp4" in clean_url.lower():

                    print(
                        "✅ MP4 FOUND:",
                        profile
                    )

                    mp4_list.append(
                        {
                            "profile": profile,
                            "url": clean_url
                        }
                    )

        # ----------------------------------------------------
        # Recursive fallback
        # ----------------------------------------------------

        if not mp4_list:

            def recursive_find(obj):

                found = []

                if isinstance(
                    obj,
                    dict
                ):

                    for value in obj.values():

                        found.extend(
                            recursive_find(
                                value
                            )
                        )

                elif isinstance(
                    obj,
                    list
                ):

                    for value in obj:

                        found.extend(
                            recursive_find(
                                value
                            )
                        )

                elif isinstance(
                    obj,
                    str
                ):

                    if ".mp4" in obj.lower():

                        found.append(
                            obj
                        )

                return found

            recursive_urls = recursive_find(
                file_link_all
            )

            for media_url in recursive_urls:

                mp4_list.append(
                    {
                        "profile": "",
                        "url": media_url
                    }
                )

        # ----------------------------------------------------
        # Unique URLs
        # ----------------------------------------------------

        unique = []

        seen_urls = set()

        for item in mp4_list:

            media_url = item["url"]

            if media_url in seen_urls:
                continue

            seen_urls.add(
                media_url
            )

            unique.append(
                item
            )

        mp4_list = unique

        print(
            "🎬 ALL MP4 VIDEOS FOUND:",
            len(mp4_list)
        )

        if not mp4_list:

            print(
                "❌ NO MP4 URL FOUND"
            )

            return None

        # ----------------------------------------------------
        # Select quality
        # ----------------------------------------------------

        preferred_profiles = [
            "360p",
            "240p",
            "144p",
        ]

        selected = None

        for preferred in preferred_profiles:

            for item in mp4_list:

                if item["profile"] == preferred:

                    selected = item

                    break

            if selected:
                break

        if selected is None:

            selected = mp4_list[0]

        print(
            "🎬 SELECTED APARAT VIDEO:",
            selected["profile"]
        )

        return selected["url"]

    except Exception as e:

        print(
            "APARAT VIDEO ERROR:",
            repr(e)
        )

        return None


# ============================================================
# IMAGE
# ============================================================

def get_entry_image(
    news
):

    try:

        entry = news.get(
            "entry"
        )

        if not entry:
            return None

        media_content = entry.get(
            "media_content",
            []
        )

        if media_content:

            for media in media_content:

                if isinstance(
                    media,
                    dict
                ):

                    url = media.get(
                        "url"
                    )

                    if url:
                        return url

        media_thumbnail = entry.get(
            "media_thumbnail",
            []
        )

        if media_thumbnail:

            for media in media_thumbnail:

                if isinstance(
                    media,
                    dict
                ):

                    url = media.get(
                        "url"
                    )

                    if url:
                        return url

        enclosures = entry.get(
            "enclosures",
            []
        )

        if enclosures:

            for media in enclosures:

                if isinstance(
                    media,
                    dict
                ):

                    url = media.get(
                        "href",
                        media.get(
                            "url"
                        )
                    )

                    if url:
                        return url

    except Exception as e:

        print(
            "IMAGE ERROR:",
            repr(e)
        )

    return None


# ============================================================
# SEND NEWS
# ============================================================

def send_news(
    bot,
    news,
    sent
):

    title = news["title"]
    link = news["link"]

    print()
    print(
        "PROCESSING:",
        title
    )

    hashtags = create_hashtags(
        title
    )

    print(
        "HASHTAGS:",
        hashtags
    )

    caption = (
        f"{html.escape(title)}\n\n"
        f"{hashtags}\n\n"
        f"@ligebartar24"
    )

    # ========================================================
    # VIDEO
    # ========================================================

    video_url = get_aparat_video(
        link,
        news
    )

    if video_url:

        print()
        print(
            "🎬 DOWNLOADING VIDEO..."
        )

        temp_file = "temp_video.mp4"

        try:

            media_response = requests.get(
                video_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Referer": "https://www.aparat.com/",
                    "Origin": "https://www.aparat.com",
                },
                stream=True,
                timeout=120
            )

            print(
                "MEDIA STATUS:",
                media_response.status_code
            )

            print(
                "MEDIA CONTENT TYPE:",
                media_response.headers.get(
                    "Content-Type"
                )
            )

            print(
                "MEDIA CONTENT LENGTH:",
                media_response.headers.get(
                    "Content-Length"
                )
            )

            if media_response.status_code == 200:

                content_type = (
                    media_response.headers.get(
                        "Content-Type",
                        ""
                    ).lower()
                )

                if (
                    "video" in content_type
                    or ".mp4" in video_url.lower()
                ):

                    with open(
                        temp_file,
                        "wb"
                    ) as f:

                        for chunk in media_response.iter_content(
                            chunk_size=1024 * 256
                        ):

                            if chunk:
                                f.write(chunk)

                    file_size = os.path.getsize(
                        temp_file
                    )

                    print(
                        "✅ VIDEO DOWNLOADED:",
                        file_size,
                        "bytes"
                    )

                    try:

                        with open(
                            temp_file,
                            "rb"
                        ) as video_file:

                            awaitable = bot.send_video(
                                chat_id=CHANNEL,
                                video=video_file,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                supports_streaming=True
                            )

                            asyncio.get_event_loop().run_until_complete(
                                awaitable
                            )

                        print(
                            "✅ VIDEO NEWS SENT:",
                            title
                        )

                        register_sent(
                            link,
                            sent
                        )

                        if os.path.exists(
                            temp_file
                        ):

                            os.remove(
                                temp_file
                            )

                        return True

                    except Exception as e:

                        print(
                            "VIDEO TELEGRAM SEND ERROR:",
                            repr(e)
                        )

            else:

                print(
                    "❌ VIDEO DOWNLOAD FAILED"
                )

        except Exception as e:

            print(
                "VIDEO DOWNLOAD ERROR:",
                repr(e)
            )

        finally:

            if os.path.exists(
                temp_file
            ):

                try:
                    os.remove(
                        temp_file
                    )
                except Exception:
                    pass

    # ========================================================
    # IMAGE
    # ========================================================

    image_url = get_entry_image(
        news
    )

    if image_url:

        print(
            "🖼 SENDING IMAGE..."
        )

        temp_image = "temp_news.jpg"

        try:

            image_response = requests.get(
                image_url,
                headers={
                    "User-Agent": USER_AGENT
                },
                timeout=30
            )

            print(
                "IMAGE STATUS:",
                image_response.status_code
            )

            if image_response.status_code == 200:

                with open(
                    temp_image,
                    "wb"
                ) as f:

                    f.write(
                        image_response.content
                    )

                with open(
                    temp_image,
                    "rb"
                ) as photo:

                    awaitable = bot.send_photo(
                        chat_id=CHANNEL,
                        photo=photo,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )

                    asyncio.get_event_loop().run_until_complete(
                        awaitable
                    )

                print(
                    "✅ IMAGE NEWS SENT:",
                    title
                )

                register_sent(
                    link,
                    sent
                )

                if os.path.exists(
                    temp_image
                ):

                    os.remove(
                        temp_image
                    )

                return True

        except Exception as e:

            print(
                "IMAGE SEND ERROR:",
                repr(e)
            )

        finally:

            if os.path.exists(
                temp_image
            ):

                try:
                    os.remove(
                        temp_image
                    )
                except Exception:
                    pass

    # ========================================================
    # TEXT
    # ========================================================

    try:

        print(
            "📝 SENDING TEXT NEWS..."
        )

        awaitable = bot.send_message(
            chat_id=CHANNEL,
            text=caption,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        asyncio.get_event_loop().run_until_complete(
            awaitable
        )

        print(
            "✅ TEXT NEWS SENT:",
            title
        )

        register_sent(
            link,
            sent
        )

        return True

    except Exception as e:

        print(
            "TELEGRAM SEND ERROR:",
            repr(e)
        )

        return False


# ============================================================
# RSS PROCESS
# ============================================================

def process_rss_news(
    bot,
    sent
):

    print()
    print(
        "========================================"
    )

    print(
        "📰 CHECKING FOR NEW FOOTBALL NEWS"
    )

    print(
        "========================================"
    )

    current_time = time.time()

    last_run = load_last_run()

    # ========================================================
    # FIRST RUN
    # ========================================================

    if last_run is None:

        print()
        print(
            "⚠️ FIRST RUN"
        )

        print(
            "➡️ OLD RSS NEWS WILL NOT BE SENT"
        )

        print(
            "➡️ CREATING BASELINE..."
        )

        save_last_run(
            current_time
        )

        print(
            "✅ BASELINE CREATED"
        )

        return

    # ========================================================
    # COLLECT NEW NEWS
    # ========================================================

    all_new_news = []

    for rss_url in RSS_SOURCES:

        print()
        print(
            "RSS:",
            rss_url
        )

        news_list = get_news(
            rss_url
        )

        for news in news_list:

            link = news["link"]
            title = news["title"]

            if link in sent:

                print(
                    "🚫 DUPLICATE SKIPPED:",
                    title
                )

                continue

            news_timestamp = get_news_timestamp(
                news
            )

            if news_timestamp is None:

                print(
                    "⚠️ NO DATE - SKIPPED:",
                    title
                )

                continue

            if news_timestamp <= last_run:

                print(
                    "⏭️ OLD NEWS SKIPPED:",
                    title
                )

                continue

            print()
            print(
                "🆕 NEW NEWS FOUND:",
                title
            )

            all_new_news.append(
                news
            )

    # ========================================================
    # REMOVE DUPLICATES IN SAME RUN
    # ========================================================

    unique_news = []

    seen_links = set()

    for news in all_new_news:

        link = news["link"]

        if link in seen_links:
            continue

        seen_links.add(
            link
        )

        unique_news.append(
            news
        )

    all_new_news = unique_news

    # ========================================================
    # SORT BY DATE
    # ========================================================

    all_new_news.sort(
        key=lambda item: (
            get_news_timestamp(
                item
            ) or 0
        )
    )

    print()
    print(
        "========================================"
    )

    print(
        "🆕 TOTAL NEW NEWS:",
        len(all_new_news)
    )

    print(
        "========================================"
    )

    # ========================================================
    # SEND ALL NEW NEWS
    # ========================================================

    for news in all_new_news:

        title = news["title"]

        print()
        print(
            "📤 PROCESSING NEW NEWS:",
            title
        )

        success = send_news(
            bot,
            news,
            sent
        )

        if success:

            print(
                "✅ NEWS COMPLETED:",
                title
            )

        else:

            print(
                "❌ NEWS FAILED:",
                title
            )

        time.sleep(1)

    # ========================================================
    # SAVE LAST RUN
    # ========================================================

    save_last_run(
        current_time
    )

    print()
    print(
        "========================================"
    )

    print(
        "✅ RSS CHECK COMPLETED"
    )

    print(
        "NEW NEWS SENT:",
        len(all_new_news)
    )

    print(
        "========================================"
    )


# ============================================================
# API FOOTBALL
# ============================================================

def check_api_status():

    if not API_FOOTBALL_KEY:

        print(
            "⚠️ API FOOTBALL KEY NOT FOUND"
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
            response.request.path_url,
            response.status_code
        )

        try:

            data = response.json()

        except Exception:

            print(
                "API RESPONSE:",
                response.text
            )

            return False

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
                "⚠️ API ERROR:",
                errors
            )

            return False

        return True

    except Exception as e:

        print(
            "API STATUS ERROR:",
            repr(e)
        )

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "TELEGRAM SPORTS NEWS BOT"
    )

    print(
        "================================"
    )

    print(
        "🇮🇷 IRAN + 🌍 EUROPE FOOTBALL"
    )

    print(
        "================================"
    )

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN NOT FOUND"
        )

        return

    bot = Bot(
        token=BOT_TOKEN
    )

    api_ok = check_api_status()

    if not api_ok:

        print(
            "⚠️ API FOOTBALL UNAVAILABLE"
        )

        print(
            "➡️ RSS NEWS WILL STILL RUN"
        )

    sent = load_sent_news()

    print()
    print(
        "SENT DATABASE COUNT:",
        len(sent)
    )

    process_rss_news(
        bot,
        sent
    )

    print()
    print(
        "================================"
    )

    print(
        "BOT RUN FINISHED"
    )

    print(
        "================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
