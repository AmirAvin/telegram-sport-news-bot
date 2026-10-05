import os
import re
import json
import html
import time
import requests
import feedparser
import asyncio
import calendar
import hashlib
from urllib.parse import urlsplit, urlunsplit
from difflib import SequenceMatcher
from datetime import datetime, timezone
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

MAX_NEWS_PER_RUN = 10

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
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
# TEXT / URL HELPERS
# ============================================================
def normalize_title(text):
    if not text:
        return ""

    text = html.unescape(str(text))

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "\u200c": " ",
        "\u200d": " ",
        "\u200e": " ",
        "\u200f": " ",
        "\ufeff": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = re.sub(r"[^\w\sآ-ی]", " ", text)

    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(str(url).strip())

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path.rstrip("/"),
                "",
                "",
            )
        )

    except Exception:
        return str(url).strip().lower()


def make_news_fingerprint(title):
    normalized = normalize_title(title)

    if not normalized:
        return ""

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def make_news_key(news):
    return (
        f"title:{make_news_fingerprint(news.get('title', ''))}"
        f"|url:{normalize_url(news.get('link', ''))}"
    )


def title_similarity(title1, title2):
    a = normalize_title(title1)
    b = normalize_title(title2)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(None, a, b).ratio()


def truncate_to_sentence(text, max_length):
    if not text:
        return ""

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    candidate = text[:max_length].rstrip()

    positions = [
        candidate.rfind(x)
        for x in [
            "؟",
            "?",
            "!",
            "！",
            "。",
            ".",
            "؛",
            ";",
        ]
    ]

    positions = [x for x in positions if x >= 0]

    if positions:
        return candidate[:max(positions) + 1].strip()

    p = candidate.rfind("\n\n")

    if p > 0:
        return candidate[:p].strip()

    p = candidate.rfind(" ")

    return candidate[:p].strip() if p > 0 else candidate


def create_hashtags(title, article_text=""):
    normalized = normalize_title(
        f"{title} {article_text}"
    )

    found = []

    for key in sorted(
        HASHTAG_MAP,
        key=lambda x: len(normalize_title(x)),
        reverse=True,
    ):

        if normalize_title(key) in normalized:
            hashtag = HASHTAG_MAP[key]

            if hashtag not in found:
                found.append(hashtag)

        if len(found) >= 4:
            break

    if "#فوتبال" not in found:
        found.append("#فوتبال")

    return " ".join(found[:5])


def is_football_news(title, body=""):
    normalized = normalize_title(
        f"{title} {body}"
    )

    for bad in NON_FOOTBALL_KEYWORDS:
        if normalize_title(bad) in normalized:
            return False

    return any(
        normalize_title(k) in normalized
        for k in FOOTBALL_KEYWORDS
    )


# ============================================================
# SENT DATABASE
# ============================================================
def load_sent_news():
    if not os.path.exists(SENT_FILE):
        return set()

    try:
        with open(
            SENT_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if isinstance(data, list):
            return {str(x) for x in data}

        if isinstance(data, dict):
            return {str(x) for x in data.keys()}

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
                sorted(sent),
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(
            "💾 SENT DATABASE SAVED:",
            len(sent)
        )

    except Exception as e:
        print(
            "SAVE SENT ERROR:",
            repr(e)
        )


def sent_contains_url(
    normalized_link,
    sent
):
    if not normalized_link:
        return False

    for item in sent:

        if isinstance(item, str):

            if (
                item.startswith("http://")
                or item.startswith("https://")
            ):

                if normalize_url(item) == normalized_link:
                    return True

    return False


def sent_contains_title_hash(
    title_hash,
    sent
):
    if not title_hash:
        return False

    if title_hash in sent:
        return True

    for item in sent:

        if (
            isinstance(item, str)
            and item.startswith("title:")
        ):

            if (
                item.split("|", 1)[0]
                .replace("title:", "", 1)
                == title_hash
            ):
                return True

    return False


def migrate_historical_news(
    news,
    sent
):
    clean_link = normalize_url(
        news.get("link", "")
    )

    title_hash = make_news_fingerprint(
        news.get("title", "")
    )

    if sent_contains_url(
        clean_link,
        sent
    ):

        if clean_link:
            sent.add(clean_link)

        if title_hash:
            sent.add(title_hash)

        sent.add(
            make_news_key(news)
        )

        return True

    return False


def is_already_sent(
    news,
    sent
):
    link = news.get("link", "")

    clean_link = normalize_url(link)

    title_hash = make_news_fingerprint(
        news.get("title", "")
    )

    return bool(
        (link and link in sent)
        or (
            clean_link
            and clean_link in sent
        )
        or sent_contains_url(
            clean_link,
            sent
        )
        or sent_contains_title_hash(
            title_hash,
            sent
        )
        or make_news_key(news) in sent
    )


def register_sent(
    news,
    sent
):
    link = news.get("link", "")

    clean_link = normalize_url(link)

    title_hash = make_news_fingerprint(
        news.get("title", "")
    )

    if link:
        sent.add(link)

    if clean_link:
        sent.add(clean_link)

    if title_hash:
        sent.add(title_hash)

    sent.add(
        make_news_key(news)
    )


# ============================================================
# STATE HELPERS
# ============================================================
def load_timestamp(path):
    if not os.path.exists(path):
        return None

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            value = json.load(f).get(
                "last_run"
            )

        return (
            float(value)
            if value
            else None
        )

    except Exception as e:
        print(
            "LOAD STATE ERROR:",
            path,
            repr(e)
        )

    return None


def save_timestamp(
    path,
    timestamp
):
    try:
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "last_run": timestamp
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(
            "💾 STATE SAVED:",
            path,
            timestamp
        )

    except Exception as e:
        print(
            "SAVE STATE ERROR:",
            path,
            repr(e)
        )


# ============================================================
# RSS
# ============================================================
def get_news(rss_url):
    try:

        response = requests.get(
            rss_url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=30,
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

            body = BeautifulSoup(
                summary,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            if (
                title
                and link
                and is_football_news(
                    title,
                    body
                )
            ):

                news.append(
                    {
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "entry": entry,
                        "source": "rss",
                    }
                )

        return news

    except Exception as e:

        print(
            "RSS ERROR:",
            repr(e)
        )

        return []


def get_news_timestamp(news):
    try:

        entry = news.get(
            "entry"
        )

        if not entry:
            return None

        parsed = (
            entry.get(
                "published_parsed"
            )
            or entry.get(
                "updated_parsed"
            )
        )

        return (
            float(calendar.timegm(parsed))
            if parsed
            else None
        )

    except Exception as e:

        print(
            "DATE ERROR:",
            repr(e)
        )

        return None


# ============================================================
# ARTICLE / IMAGE / APARAT
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
            timeout=30,
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

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "form",
                "aside",
            ]
        ):
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
            "main",
        ]

        container = None

        for selector in selectors:

            try:

                element = soup.select_one(
                    selector
                )

                if (
                    element
                    and len(
                        element.find_all("p")
                    ) >= 2
                ):

                    container = element
                    break

            except Exception:
                pass

        paragraphs = (
            container.find_all("p")
            if container
            else soup.find_all("p")
        )

        bad_phrases = [
            "عضویت در کانال",
            "اخبار مرتبط",
            "مطالب مرتبط",
            "تبلیغات",
            "کد خبر",
            "منبع:",
            "منبع خبر",
            "ارسال دیدگاه",
            "دیدگاه",
        ]

        texts = []
        seen = set()

        for p in paragraphs:

            text = re.sub(
                r"\s+",
                " ",
                p.get_text(
                    " ",
                    strip=True
                )
            ).strip()

            if len(text) < 25:
                continue

            if any(
                x in text
                for x in bad_phrases
            ):
                continue

            n = normalize_title(
                text
            )

            if n not in seen:

                seen.add(n)
                texts.append(text)

        result = "\n\n".join(
            texts
        ).strip()

        print(
            "ARTICLE TEXT:",
            len(result),
            "characters"
        )

        return result

    except Exception as e:

        print(
            "ARTICLE TEXT ERROR:",
            repr(e)
        )

        return ""


def extract_aparat_hash(text):

    if not text:
        return None

    try:

        text = html.unescape(
            str(text)
        )

        patterns = [
            r'aparat\.com/v/([A-Za-z0-9]+)',
            r'videohash[\/"\':=\s]+([A-Za-z0-9]+)',
            r'embed/videohash/([A-Za-z0-9]+)',
            r'videohash=([A-Za-z0-9]+)',
        ]

        for pattern in patterns:

            m = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if (
                m
                and m.group(1).strip()
            ):
                return m.group(1).strip()

    except Exception:
        pass

    return None


def find_aparat_hash_in_entry(
    entry
):
    if not entry:
        return None

    try:

        for key in entry.keys():

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
        pass

    return None


def get_aparat_video(
    url,
    news_entry=None
):

    print(
        "🎥 CHECKING APARAT VIDEO:",
        url
    )

    try:

        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language":
                "fa-IR,fa;q=0.9,en;q=0.8",
            "Referer":
                "https://www.aparat.com/",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            return None

        video_hash = extract_aparat_hash(
            response.text
        )

        if (
            not video_hash
            and news_entry
        ):

            video_hash = (
                find_aparat_hash_in_entry(
                    news_entry.get(
                        "entry"
                    )
                )
            )

        if (
            not video_hash
            and news_entry
        ):

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
            "https://www.aparat.com/"
            "api/fa/v1/video/video/show/"
            f"videohash/{video_hash}"
        )

        api_response = requests.get(
            api_url,
            headers=headers,
            timeout=30,
        )

        if api_response.status_code != 200:
            return None

        data = (
            api_response.json()
            .get("data", {})
            .get("attributes", {})
        )

        links = data.get(
            "file_link_all",
            []
        )

        choices = []

        for item in links:

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
                    and ".mp4"
                    in media_url.lower()
                ):

                    choices.append(
                        (
                            profile,
                            media_url
                        )
                    )

        for quality in [
            "360p",
            "240p",
            "144p",
        ]:

            for profile, media_url in choices:

                if profile == quality:
                    return media_url

        return (
            choices[0][1]
            if choices
            else None
        )

    except Exception as e:

        print(
            "APARAT VIDEO ERROR:",
            repr(e)
        )

        return None


def get_entry_image(news):

    if news.get("image_url"):
        return news.get(
            "image_url"
        )

    try:

        entry = news.get(
            "entry"
        )

        if entry:

            for group in [
                entry.get(
                    "media_content",
                    []
                ),
                entry.get(
                    "media_thumbnail",
                    []
                ),
                entry.get(
                    "enclosures",
                    []
                ),
            ]:

                for media in group:

                    if isinstance(
                        media,
                        dict
                    ):

                        url = (
                            media.get("url")
                            or media.get("href")
                        )

                        if url:
                            return url

            summary = news.get(
                "summary",
                ""
            )

            soup = BeautifulSoup(
                summary,
                "html.parser"
            )

            img = soup.find("img")

            if img:

                return (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-original")
                )

    except Exception as e:

        print(
            "IMAGE ERROR:",
            repr(e)
        )

    return None


# ============================================================
# CAPTIONS
# ============================================================
def build_media_caption(
    title,
    article_text,
    hashtags
):

    footer = (
        f"\n\n{html.escape(hashtags)}"
        f"\n\n@ligebartar24"
    )

    fixed = (
        f"<b>{html.escape(title)}</b>"
        "\n\n"
    )

    available = max(
        50,
        1024
        - len(fixed)
        - len(footer)
        - 5
    )

    body = truncate_to_sentence(
        article_text,
        available
    )

    return (
        fixed
        + html.escape(body)
        + footer
    )


def build_text_message(
    title,
    article_text,
    hashtags
):

    footer = (
        f"\n\n{html.escape(hashtags)}"
        f"\n\n@ligebartar24"
    )

    fixed = (
        f"<b>{html.escape(title)}</b>"
        "\n\n"
    )

    available = max(
        100,
        4096
        - len(fixed)
        - len(footer)
        - 5
    )

    body = truncate_to_sentence(
        article_text,
        available
    )

    return (
        fixed
        + html.escape(body)
        + footer
    )


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(
        coro
    )


# ============================================================
# SEND NEWS
# ============================================================
def send_news(
    bot,
    news,
    sent
):

    title = news["title"]

    print(
        "\nPROCESSING:",
        title
    )

    article_text = get_article_text(
        news["link"]
    )

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

    hashtags = create_hashtags(
        title,
        article_text
    )

    caption = build_media_caption(
        title,
        article_text,
        hashtags
    )

    print(
        "HASHTAGS:",
        hashtags
    )

    # ========================================================
    # APARAT VIDEO
    # ========================================================
    video_url = get_aparat_video(
        news["link"],
        news
    )

    if video_url:

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
                        "https://www.aparat.com",
                },
                stream=True,
                timeout=120,
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

                with open(
                    temp_file,
                    "rb"
                ) as video_file:

                    run_async(
                        bot.send_video(
                            chat_id=CHANNEL,
                            video=video_file,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            supports_streaming=True,
                        )
                    )

                print(
                    "✅ VIDEO NEWS SENT"
                )

                register_sent(
                    news,
                    sent
                )

                return True

        except Exception as e:

            print(
                "VIDEO ERROR:",
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

        temp_image = "temp_news.jpg"

        try:

            image_response = requests.get(
                image_url,
                headers={
                    "User-Agent":
                        USER_AGENT
                },
                timeout=30,
            )

            if (
                image_response.status_code == 200
                and image_response.content
            ):

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

                    run_async(
                        bot.send_photo(
                            chat_id=CHANNEL,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    )

                print(
                    "✅ IMAGE NEWS SENT"
                )

                register_sent(
                    news,
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

        run_async(
            bot.send_message(
                chat_id=CHANNEL,
                text=build_text_message(
                    title,
                    article_text,
                    hashtags
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        )

        print(
            "✅ TEXT NEWS SENT"
        )

        register_sent(
            news,
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
# RSS PROCESSOR
# ============================================================
def process_rss_news(
    bot,
    sent
):

    print(
        "\n========================================"
    )

    print(
        "📰 CHECKING RSS FOOTBALL NEWS"
    )

    print(
        "========================================"
    )

    current_time = time.time()

    last_run = load_timestamp(
        LAST_RUN_FILE
    )

    if last_run is None:

        print(
            "⚠️ RSS FIRST RUN - BASELINE ONLY"
        )

        save_timestamp(
            LAST_RUN_FILE,
            current_time
        )

        return

    all_new = []

    for rss_url in RSS_SOURCES:

        print(
            "\nRSS:",
            rss_url
        )

        for news in get_news(
            rss_url
        ):

            if (
                migrate_historical_news(
                    news,
                    sent
                )
                or is_already_sent(
                    news,
                    sent
                )
            ):
                continue

            ts = get_news_timestamp(
                news
            )

            if (
                ts is None
                or ts <= last_run
            ):
                continue

            all_new.append(
                news
            )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================
    unique = []

    seen_titles = set()
    seen_urls = set()

    for news in all_new:

        th = make_news_fingerprint(
            news["title"]
        )

        u = normalize_url(
            news["link"]
        )

        if (
            th in seen_titles
            or (
                u
                and u in seen_urls
            )
        ):
            continue

        seen_titles.add(
            th
        )

        if u:
            seen_urls.add(
                u
            )

        unique.append(
            news
        )

    unique.sort(
        key=lambda x:
        get_news_timestamp(x) or 0
    )

    sent_count = 0
    last_success = None

    # ========================================================
    # SEND MAX 10 NEWS
    # ========================================================
    for news in unique[
        :MAX_NEWS_PER_RUN
    ]:

        if send_news(
            bot,
            news,
            sent
        ):

            sent_count += 1

            last_success = (
                get_news_timestamp(
                    news
                )
            )

            save_sent_news(
                sent
            )

        time.sleep(1)

    # ========================================================
    # UPDATE LAST RUN
    # ========================================================
    if last_success is not None:

        save_timestamp(
            LAST_RUN_FILE,
            last_success
        )

    elif not unique:

        save_timestamp(
            LAST_RUN_FILE,
            current_time
        )

    save_sent_news(
        sent
    )

    print(
        "RSS NEWS SENT:",
        sent_count
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
            timeout=20,
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

        return not bool(
            data.get(
                "errors",
                {}
            )
        )

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
        "=" * 50
    )

    print(
        "TELEGRAM SPORTS NEWS BOT"
    )

    print(
        "=" * 50
    )

    print(
        "FOOTBALL ONLY"
    )

    print(
        "RSS ONLY"
    )

    print(
        "OUTPUT CHANNEL:",
        CHANNEL
    )

    print(
        "=" * 50
    )

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN NOT FOUND"
        )

        return

    bot = Bot(
        token=BOT_TOKEN
    )

    if not check_api_status():

        print(
            "⚠️ API FOOTBALL UNAVAILABLE"
        )

        print(
            "➡️ RSS NEWS WILL STILL RUN"
        )

    sent = load_sent_news()

    print(
        "SENT DATABASE COUNT:",
        len(sent)
    )

    # ========================================================
    # فقط RSS
    # ========================================================
    process_rss_news(
        bot,
        sent
    )

    print(
        "\n================================"
    )

    print(
        "BOT RUN FINISHED"
    )

    print(
        "================================"
    )


if __name__ == "__main__":
    main()
