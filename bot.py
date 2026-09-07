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
# NON FOOTBALL
# ============================================================

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
# HASHTAG MAP
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
    "مس رفسنجان": "#مس_رفسنجان",
    "مس کرمان": "#مس_کرمان",
    "شمس آذر": "#شمس‌آذر",
    "خیبر": "#خیبر",
    "هوادار": "#هوادار",
    "چادرملو": "#چادرملو",
    "نساجی": "#نساجی",
    "پیکان": "#پیکان",
    "سایپا": "#سایپا",

    "لیگ برتر": "#لیگ_برتر",
    "لیگ یک": "#لیگ_یک",
    "لیگ آزادگان": "#لیگ_آزادگان",
    "جام حذفی": "#جام_حذفی",
    "جام جهانی": "#جام_جهانی",
    "لیگ قهرمانان": "#لیگ_قهرمانان",
    "لیگ اروپا": "#لیگ_اروپا",
    "لیگ کنفرانس": "#لیگ_کنفرانس",
    "سوپر جام": "#سوپرجام",

    "تیم ملی": "#تیم_ملی",
    "تیم‌ملی": "#تیم_ملی",
    "ایران": "#ایران",

    "مهدی طارمی": "#طارمی",
    "طارمی": "#طارمی",
    "سردار آزمون": "#آزمون",
    "آزمون": "#آزمون",
    "علیرضا جهانبخش": "#جهانبخش",
    "جهانبخش": "#جهانبخش",
    "محمد محبی": "#محمدمحبی",
    "محبی": "#محبی",
    "قلی زاده": "#قلی‌زاده",
    "قلی‌زاده": "#قلی‌زاده",
    "بیرانوند": "#بیرانوند",
    "حسین حسینی": "#حسین‌حسینی",
    "حسینی": "#حسینی",
    "پیروز قربانی": "#پیروزقربانی",
    "سهراب بختیاری زاده": "#بختیاری‌زاده",
    "سهراب بختیاری‌زاده": "#بختیاری‌زاده",
    "قلعه نویی": "#قلعه‌نویی",
    "قلعه‌نویی": "#قلعه‌نویی",
    "جباری": "#جباری",
    "نویدکیا": "#نویدکیا",
    "تارتار": "#تارتار",
    "علی دایی": "#علی_دایی",
    "کریم باقری": "#کریم_باقری",

    "رئال مادرید": "#رئال_مادرید",
    "بارسلونا": "#بارسلونا",
    "اتلتیکو مادرید": "#اتلتیکو_مادرید",
    "اتلتیکو": "#اتلتیکو",
    "منچستریونایتد": "#منچستریونایتد",
    "منچسترسیتی": "#منچسترسیتی",
    "لیورپول": "#لیورپول",
    "آرسنال": "#آرسنال",
    "چلسی": "#چلسی",
    "تاتنهام": "#تاتنهام",
    "بایرن مونیخ": "#بایرن_مونیخ",
    "بایرن": "#بایرن",
    "دورتموند": "#دورتموند",
    "یوونتوس": "#یوونتوس",
    "اینتر میلان": "#اینتر_میلان",
    "اینتر": "#اینتر",
    "آث میلان": "#میلان",
    "میلان": "#میلان",
    "پاری سن ژرمن": "#پاری‌سن‌ژرمن",
    "پاری‌سن‌ژرمن": "#پاری‌سن‌ژرمن",
    "ناپولی": "#ناپولی",
    "رم": "#رم",
    "لاتزیو": "#لاتزیو",

    "لیونل مسی": "#مسی",
    "مسی": "#مسی",
    "کریستیانو رونالدو": "#رونالدو",
    "رونالدو": "#رونالدو",
    "امباپه": "#امباپه",
    "هالند": "#هالند",
    "نیمار": "#نیمار",
    "صلاح": "#صلاح",
    "وینیسیوس": "#وینیسیوس",
    "بلینگام": "#بلینگام",

    "فوتبال": "#فوتبال",
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize_title(text):

    if not text:
        return ""

    text = html.unescape(
        str(text)
    )

    text = text.replace(
        "ي",
        "ی"
    )

    text = text.replace(
        "ك",
        "ک"
    )

    text = text.replace(
        "\u200c",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


# ============================================================
# SMART HASHTAGS
# ============================================================

def create_hashtags(
    title,
    article_text=""
):

    full_text = (
        f"{title} {article_text}"
    )

    normalized = normalize_title(
        full_text
    )

    found = []

    sorted_keys = sorted(
        HASHTAG_MAP.keys(),
        key=lambda x: len(
            normalize_title(x)
        ),
        reverse=True
    )

    for key in sorted_keys:

        key_normalized = normalize_title(
            key
        )

        if key_normalized in normalized:

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

    save_sent_news(sent)


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


def save_last_run(timestamp):

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
# GET RSS NEWS
# ============================================================

def get_news(rss_url):

    try:

        response = requests.get(
            rss_url,
            headers={
                "User-Agent": USER_AGENT
            },
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
                continue

            news.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "entry": entry
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
# NEWS DATE
# ============================================================

def get_news_timestamp(news):

    try:

        entry = news.get(
            "entry"
        )

        if not entry:
            return None

        published = entry.get(
            "published_parsed"
        )

        if published:

            return float(
                calendar.timegm(
                    published
                )
            )

        updated = entry.get(
            "updated_parsed"
        )

        if updated:

            return float(
                calendar.timegm(
                    updated
                )
            )

    except Exception as e:

        print(
            "DATE ERROR:",
            repr(e)
        )

    return None


# ============================================================
# REAL ARTICLE TEXT
# ============================================================

def get_article_text(url):

    print(
        "📄 GETTING ARTICLE TEXT:",
        url
    )

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language":
                    "fa-IR,fa;q=0.9,en;q=0.8",
            },
            timeout=30
        )

        print(
            "ARTICLE STATUS:",
            response.status_code
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        # حذف عناصر غیرخبری
        for tag in soup([
            "script",
            "style",
            "noscript",
            "header",
            "footer",
            "nav",
            "form",
            "aside"
        ]):

            tag.decompose()

        selectors = [
            "article",
            "[class*='article-content']",
            "[class*='article_content']",
            "[class*='news-content']",
            "[class*='news_content']",
            "[class*='post-content']",
            "[class*='post_content']",
            "[class*='content-detail']",
            "[class*='content_detail']",
            "[class*='news-text']",
            "[class*='news_text']",
            "[class*='article-body']",
            "[class*='article_body']",
            "main"
        ]

        container = None

        for selector in selectors:

            try:

                element = soup.select_one(
                    selector
                )

                if element:

                    paragraphs = element.find_all(
                        "p"
                    )

                    if len(paragraphs) >= 2:

                        container = element
                        break

            except Exception:
                continue

        if container:

            paragraphs = container.find_all(
                "p"
            )

        else:

            paragraphs = soup.find_all(
                "p"
            )

        texts = []

        for p in paragraphs:

            text = p.get_text(
                " ",
                strip=True
            )

            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            if not text:
                continue

            if len(text) < 25:
                continue

            bad_phrases = [
                "عضویت در کانال",
                "اخبار مرتبط",
                "مطالب مرتبط",
                "تبلیغات",
                "کد خبر",
                "منبع:",
                "منبع خبر",
                "ارسال دیدگاه",
                "دیدگاه"
            ]

            if any(
                phrase in text
                for phrase in bad_phrases
            ):
                continue

            texts.append(text)

        if not texts:

            print(
                "⚠️ ARTICLE TEXT NOT FOUND"
            )

            return ""

        unique_texts = []
        seen = set()

        for text in texts:

            normalized = normalize_title(
                text
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            unique_texts.append(
                text
            )

        article_text = "\n\n".join(
            unique_texts
        )

        article_text = re.sub(
            r"\n{3,}",
            "\n\n",
            article_text
        ).strip()

        print(
            "✅ ARTICLE TEXT FOUND:",
            len(article_text),
            "characters"
        )

        return article_text

    except Exception as e:

        print(
            "ARTICLE TEXT ERROR:",
            repr(e)
        )

        return ""


# ============================================================
# APARAT HASH
# ============================================================

def extract_aparat_hash(text):

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
            "HASH ERROR:",
            repr(e)
        )

    return None


def find_aparat_hash_in_entry(entry):

    if not entry:
        return None

    try:

        for key in entry.keys():

            try:

                value = entry.get(
                    key
                )

                if isinstance(
                    value,
                    bytes
                ):

                    value = value.decode(
                        "utf-8",
                        errors="ignore"
                    )

                if isinstance(
                    value,
                    str
                ):

                    found = extract_aparat_hash(
                        value
                    )

                    if found:
                        return found

            except Exception:
                continue

    except Exception:
        pass

    return None


# ============================================================
# GET APARAT VIDEO
# ============================================================

def get_aparat_video(
    url,
    news_entry=None
):

    print(
        "🎥 CHECKING APARAT VIDEO:",
        url
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language":
            "fa-IR,fa;q=0.9,en;q=0.8",
        "Referer":
            "https://www.aparat.com/",
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

        video_hash = extract_aparat_hash(
            page_html
        )

        if video_hash:

            print(
                "✅ VIDEO HASH FOUND:",
                video_hash
            )

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
                    "IFRAME ERROR:",
                    repr(e)
                )

        if not video_hash:

            try:

                soup = BeautifulSoup(
                    page_html,
                    "html.parser"
                )

                for script in soup.find_all(
                    "script"
                ):

                    text = script.get_text(
                        " ",
                        strip=False
                    )

                    found = extract_aparat_hash(
                        text
                    )

                    if found:

                        video_hash = found

                        print(
                            "✅ VIDEO HASH FOUND FROM SCRIPT:",
                            video_hash
                        )

                        break

            except Exception:
                pass

        if not video_hash and news_entry:

            video_hash = find_aparat_hash_in_entry(
                news_entry.get(
                    "entry"
                )
            )

        if not video_hash and news_entry:

            video_hash = extract_aparat_hash(
                news_entry.get(
                    "summary",
                    ""
                )
            )

        if not video_hash:

            print(
                "❌ APARAT VIDEO HASH NOT FOUND"
            )

            return None

        api_url = (
            "https://www.aparat.com/api/fa/v1/video/video/show/"
            f"videohash/{video_hash}"
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

        except Exception:

            return None

        root = data.get(
            "data",
            {}
        )

        attributes = root.get(
            "attributes",
            {}
        )

        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        if not file_link_all:

            print(
                "❌ NO VIDEO FILE"
            )

            return None

        mp4_list = []

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

            for media_url in urls:

                if (
                    isinstance(
                        media_url,
                        str
                    )
                    and ".mp4" in media_url.lower()
                ):

                    mp4_list.append(
                        {
                            "profile": profile,
                            "url": media_url
                        }
                    )

        if not mp4_list:

            print(
                "❌ NO MP4 FOUND"
            )

            return None

        unique = []
        seen = set()

        for item in mp4_list:

            if item["url"] in seen:
                continue

            seen.add(
                item["url"]
            )

            unique.append(
                item
            )

        mp4_list = unique

        for quality in [
            "360p",
            "240p",
            "144p"
        ]:

            for item in mp4_list:

                if item["profile"] == quality:

                    print(
                        "🎬 SELECTED:",
                        quality
                    )

                    return item["url"]

        print(
            "🎬 SELECTED FIRST MP4"
        )

        return mp4_list[0]["url"]

    except Exception as e:

        print(
            "APARAT VIDEO ERROR:",
            repr(e)
        )

        return None


# ============================================================
# IMAGE
# ============================================================

def get_entry_image(news):

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

        summary = news.get(
            "summary",
            ""
        )

        if summary:

            soup = BeautifulSoup(
                summary,
                "html.parser"
            )

            for img in soup.find_all(
                "img"
            ):

                for attr in [
                    "src",
                    "data-src",
                    "data-original",
                    "data-lazy-src"
                ]:

                    image_url = img.get(
                        attr
                    )

                    if image_url:
                        return image_url

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

    # --------------------------------------------------------
    # متن واقعی خبر
    # --------------------------------------------------------

    article_text = get_article_text(
        link
    )

    # اگر متن واقعی پیدا نشد
    if not article_text:

        article_text = BeautifulSoup(
            news.get(
                "summary",
                ""
            ),
            "html.parser"
        ).get_text(
            " ",
            strip=True
        )

        article_text = re.sub(
            r"\s+",
            " ",
            article_text
        ).strip()

    print(
        "ARTICLE TEXT LENGTH:",
        len(article_text)
    )

    # --------------------------------------------------------
    # هشتگ‌ها از تیتر + متن واقعی
    # --------------------------------------------------------

    hashtags = create_hashtags(
        title,
        article_text
    )

    print(
        "HASHTAGS:",
        hashtags
    )

    safe_title = html.escape(
        title
    )

    # --------------------------------------------------------
    # متن کوتاه برای عکس و ویدئو
    # --------------------------------------------------------

    media_text = article_text[:650]

    if len(article_text) > 650:
        media_text += "..."

    media_text = html.escape(
        media_text
    )

    # --------------------------------------------------------
    # متن کامل‌تر برای پیام متنی
    # --------------------------------------------------------

    text_message = article_text[:3000]

    if len(article_text) > 3000:
        text_message += "..."

    text_message = html.escape(
        text_message
    )

    # --------------------------------------------------------
    # CAPTION
    # --------------------------------------------------------

    caption = (
        f"<b>{safe_title}</b>\n\n"
        f"{media_text}\n\n"
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

        print(
            "🎬 DOWNLOADING VIDEO..."
        )

        temp_file = "temp_video.mp4"

        try:

            media_response = requests.get(
                video_url,
                headers={
                    "User-Agent":
                        USER_AGENT,
                    "Referer":
                        "https://www.aparat.com/",
                    "Origin":
                        "https://www.aparat.com"
                },
                stream=True,
                timeout=120
            )

            print(
                "MEDIA STATUS:",
                media_response.status_code
            )

            if media_response.status_code == 200:

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
                    "VIDEO SIZE:",
                    file_size
                )

                try:

                    with open(
                        temp_file,
                        "rb"
                    ) as video_file:

                        asyncio.get_event_loop().run_until_complete(
                            bot.send_video(
                                chat_id=CHANNEL,
                                video=video_file,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                supports_streaming=True
                            )
                        )

                    print(
                        "✅ VIDEO NEWS SENT"
                    )

                    register_sent(
                        link,
                        sent
                    )

                    return True

                except Exception as e:

                    print(
                        "VIDEO TELEGRAM ERROR:",
                        repr(e)
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
            "🖼 SENDING IMAGE:",
            image_url
        )

        temp_image = "temp_news.jpg"

        try:

            image_response = requests.get(
                image_url,
                headers={
                    "User-Agent":
                        USER_AGENT
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

                    asyncio.get_event_loop().run_until_complete(
                        bot.send_photo(
                            chat_id=CHANNEL,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    )

                print(
                    "✅ IMAGE NEWS SENT"
                )

                register_sent(
                    link,
                    sent
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

        text_caption = (
            f"<b>{safe_title}</b>\n\n"
            f"{text_message}\n\n"
            f"{hashtags}\n\n"
            f"@ligebartar24"
        )

        text_caption = text_caption[:4090]

        asyncio.get_event_loop().run_until_complete(
            bot.send_message(
                chat_id=CHANNEL,
                text=text_caption,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        )

        print(
            "✅ TEXT NEWS SENT"
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
# PROCESS RSS
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

    if last_run is None:

        print()
        print(
            "⚠️ FIRST RUN"
        )

        print(
            "➡️ OLD RSS NEWS WILL NOT BE SENT"
        )

        save_last_run(
            current_time
        )

        print(
            "✅ BASELINE CREATED"
        )

        return

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
                    "🚫 DUPLICATE:",
                    title
                )

                continue

            news_timestamp = get_news_timestamp(
                news
            )

            if news_timestamp is None:

                print(
                    "⚠️ NO DATE:",
                    title
                )

                continue

            if news_timestamp <= last_run:

                print(
                    "⏭️ OLD:",
                    title
                )

                continue

            print(
                "🆕 NEW:",
                title
            )

            all_new_news.append(
                news
            )

    # --------------------------------------------------------
    # حذف تکراری‌های RSS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # مرتب‌سازی
    # --------------------------------------------------------

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

    # بدون محدودیت تعداد
    for news in all_new_news:

        send_news(
            bot,
            news,
            sent
        )

        time.sleep(1)

    # ثبت زمان اجرای فعلی
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
