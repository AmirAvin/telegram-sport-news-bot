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

# حداکثر تعداد خبر در هر اجرا
MAX_NEWS_PER_RUN = 10

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
    "استقلال", "پرسپولیس", "سپاهان", "تراکتور",
    "ذوب آهن", "ذوب‌آهن", "ملوان", "گل گهر", "گل‌گهر",
    "فولاد", "آلومینیوم", "مس رفسنجان", "مس کرمان",
    "شمس آذر", "خیبر", "هوادار", "چادرملو",
    "نساجی", "پیکان", "سایپا",

    "لیگ برتر", "لیگ یک", "لیگ آزادگان",
    "جام حذفی", "جام جهانی", "لیگ قهرمانان",
    "لیگ اروپا", "لیگ کنفرانس",

    "تیم ملی", "تیم‌ملی", "مربی", "سرمربی",
    "بازیکن", "مهاجم", "مدافع", "دروازه بان",
    "دروازه‌بان", "گلزن", "گلزنی", "گل",
    "پنالتی", "کارت قرمز", "کارت زرد",
    "داوری", "داور", "VAR", "ویدیو", "ویدئو",

    "طارمی", "مهدی طارمی", "آزمون", "سردار آزمون",
    "قلی زاده", "قلی‌زاده", "محبی", "محمد محبی",
    "جهانبخش", "قدوس", "بیرانوند", "حسین حسینی",
    "قلعه نویی", "قلعه‌نویی", "مجیدی", "جباری",
    "پیروز قربانی", "نویدکیا", "تارتار",
    "سهراب بختیاری زاده", "سهراب بختیاری‌زاده",

    "رئال مادرید", "بارسلونا", "اتلتیکو",
    "منچستریونایتد", "منچسترسیتی", "لیورپول",
    "آرسنال", "چلسی", "تاتنهام", "بایرن",
    "دورتموند", "یوونتوس", "اینتر", "میلان",
    "پاری سن ژرمن", "پاری‌سن‌ژرمن",
    "ناپولی", "رم", "لاتزیو",

    "مسی", "رونالدو", "امباپه", "هالند",
    "نیمار", "صلاح", "وینیسیوس", "بلینگام",

    "آسیا", "اروپا", "قطر", "امارات",
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
# NORMALIZE TEXT
# ============================================================

def normalize_title(text):

    if not text:
        return ""

    text = html.unescape(str(text))

    text = text.replace("ي", "ی")
    text = text.replace("ى", "ی")
    text = text.replace("ك", "ک")
    text = text.replace("\u200c", " ")

    # حذف علائم و فاصله‌های اضافی
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = re.sub(r"[^\w\sآ-ی]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()


# ============================================================
# NORMALIZE URL
# ============================================================

def normalize_url(url):

    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())

        # حذف query و fragment
        clean = urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            "",
            ""
        ))

        return clean

    except Exception:
        return url.strip().lower()


# ============================================================
# NEWS FINGERPRINT
# ============================================================

def make_news_fingerprint(title):

    normalized = normalize_title(title)

    if not normalized:
        return ""

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def make_news_key(news):

    title = news.get("title", "")
    link = news.get("link", "")

    title_hash = make_news_fingerprint(title)
    clean_link = normalize_url(link)

    return f"title:{title_hash}|url:{clean_link}"


# ============================================================
# SMART TEXT TRUNCATE
# ============================================================

def truncate_to_sentence(text, max_length):

    if not text:
        return ""

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    candidate = text[:max_length].rstrip()

    sentence_endings = [
        "؟", "?", "!", "！", "。",
        ".", "؛", ";"
    ]

    positions = []

    for ending in sentence_endings:

        position = candidate.rfind(ending)

        if position >= 0:
            positions.append(position)

    if positions:

        last_position = max(positions)

        result = candidate[
            :last_position + 1
        ].strip()

        if result:
            return result

    paragraph_position = candidate.rfind("\n\n")

    if paragraph_position > 0:

        result = candidate[
            :paragraph_position
        ].strip()

        if result:
            return result

    space_position = candidate.rfind(" ")

    if space_position > 0:
        return candidate[:space_position].strip()

    return candidate.strip()


# ============================================================
# SMART HASHTAGS
# ============================================================

def create_hashtags(title, article_text=""):

    # فقط عنوان + متن واقعی خبر
    full_text = f"{title} {article_text}"
    normalized = normalize_title(full_text)

    found = []

    sorted_keys = sorted(
        HASHTAG_MAP.keys(),
        key=lambda x: len(normalize_title(x)),
        reverse=True
    )

    for key in sorted_keys:

        key_normalized = normalize_title(key)

        if key_normalized in normalized:

            tag = HASHTAG_MAP[key]

            if tag not in found:
                found.append(tag)

        if len(found) >= 4:
            break

    if "#فوتبال" not in found:
        found.append("#فوتبال")

    return " ".join(found[:5])


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

        result = set()

        if isinstance(data, list):

            for item in data:

                if isinstance(item, str):
                    result.add(item)

        elif isinstance(data, dict):

            for key in data.keys():

                result.add(str(key))

        return result

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
                sorted(list(sent)),
                f,
                ensure_ascii=False,
                indent=2
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


def is_already_sent(news, sent):

    link = news.get("link", "")
    title = news.get("title", "")

    normalized_link = normalize_url(link)
    title_hash = make_news_fingerprint(title)

    # لینک اصلی
    if link in sent:
        return True

    # لینک نرمال‌شده
    if normalized_link in sent:
        return True

    # هش عنوان
    if title_hash in sent:
        return True

    # کلید ترکیبی
    key = make_news_key(news)

    if key in sent:
        return True

    # بررسی دیتابیس‌های قدیمی
    for old_item in sent:

        if not isinstance(old_item, str):
            continue

        if old_item == title_hash:
            return True

        if old_item.startswith("title:"):

            if title_hash in old_item:
                return True

    return False


def register_sent(news, sent):

    link = news.get("link", "")
    title = news.get("title", "")

    clean_link = normalize_url(link)
    title_hash = make_news_fingerprint(title)
    key = make_news_key(news)

    if clean_link:
        sent.add(clean_link)

    if title_hash:
        sent.add(title_hash)

    sent.add(key)

    save_sent_news(sent)


# ============================================================
# LAST RUN
# ============================================================

def load_last_run():

    if not os.path.exists(LAST_RUN_FILE):
        return None

    try:

        with open(
            LAST_RUN_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        value = data.get("last_run")

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

        print(
            "💾 LAST RUN SAVED:",
            timestamp
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

    normalized = normalize_title(title)

    for bad in NON_FOOTBALL_KEYWORDS:

        if normalize_title(bad) in normalized:
            return False

    for keyword in FOOTBALL_KEYWORDS:

        if normalize_title(keyword) in normalized:
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
                entry.get("title", "")
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

            if not is_football_news(title):
                continue

            news.append({
                "title": title,
                "link": link,
                "summary": summary,
                "entry": entry
            })

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

        entry = news.get("entry")

        if not entry:
            return None

        published = entry.get(
            "published_parsed"
        )

        if published:

            return float(
                calendar.timegm(published)
            )

        updated = entry.get(
            "updated_parsed"
        )

        if updated:

            return float(
                calendar.timegm(updated)
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

                element = soup.select_one(selector)

                if element:

                    paragraphs = element.find_all("p")

                    if len(paragraphs) >= 2:

                        container = element
                        break

            except Exception:
                continue

        if container:
            paragraphs = container.find_all("p")
        else:
            paragraphs = soup.find_all("p")

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

            normalized = normalize_title(text)

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_texts.append(text)

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
# APARAT
# ============================================================

def extract_aparat_hash(text):

    if not text:
        return None

    try:

        text = html.unescape(str(text))

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

                value = match.group(1).strip()

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

                value = entry.get(key)

                if isinstance(value, bytes):

                    value = value.decode(
                        "utf-8",
                        errors="ignore"
                    )

                if isinstance(value, str):

                    found = extract_aparat_hash(value)

                    if found:
                        return found

            except Exception:
                continue

    except Exception:
        pass

    return None


def get_aparat_video(url, news_entry=None):

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

        if not video_hash:

            try:

                soup = BeautifulSoup(
                    page_html,
                    "html.parser"
                )

                for iframe in soup.find_all("iframe"):

                    src = iframe.get("src", "")

                    found = extract_aparat_hash(src)

                    if found:

                        video_hash = found

                        print(
                            "✅ VIDEO HASH FROM IFRAME:",
                            video_hash
                        )

                        break

            except Exception:
                pass

        if not video_hash:

            try:

                soup = BeautifulSoup(
                    page_html,
                    "html.parser"
                )

                for script in soup.find_all("script"):

                    text = script.get_text(
                        " ",
                        strip=False
                    )

                    found = extract_aparat_hash(text)

                    if found:

                        video_hash = found
                        break

            except Exception:
                pass

        if not video_hash and news_entry:

            video_hash = find_aparat_hash_in_entry(
                news_entry.get("entry")
            )

        if not video_hash and news_entry:

            video_hash = extract_aparat_hash(
                news_entry.get("summary", "")
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

        root = data.get("data", {})
        attributes = root.get("attributes", {})

        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        if not file_link_all:
            return None

        mp4_list = []

        for item in file_link_all:

            if not isinstance(item, dict):
                continue

            profile = item.get("profile", "")
            urls = item.get("urls", [])

            if isinstance(urls, str):
                urls = [urls]

            for media_url in urls:

                if (
                    isinstance(media_url, str)
                    and ".mp4" in media_url.lower()
                ):

                    mp4_list.append({
                        "profile": profile,
                        "url": media_url
                    })

        if not mp4_list:
            return None

        unique = []
        seen = set()

        for item in mp4_list:

            if item["url"] in seen:
                continue

            seen.add(item["url"])
            unique.append(item)

        for quality in ["360p", "240p", "144p"]:

            for item in unique:

                if item["profile"] == quality:
                    return item["url"]

        return unique[0]["url"]

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

        entry = news.get("entry")

        if not entry:
            return None

        media_content = entry.get(
            "media_content",
            []
        )

        for media in media_content:

            if isinstance(media, dict):

                url = media.get("url")

                if url:
                    return url

        media_thumbnail = entry.get(
            "media_thumbnail",
            []
        )

        for media in media_thumbnail:

            if isinstance(media, dict):

                url = media.get("url")

                if url:
                    return url

        enclosures = entry.get(
            "enclosures",
            []
        )

        for media in enclosures:

            if isinstance(media, dict):

                url = media.get(
                    "href",
                    media.get("url")
                )

                if url:
                    return url

        summary = news.get("summary", "")

        if summary:

            soup = BeautifulSoup(
                summary,
                "html.parser"
            )

            for img in soup.find_all("img"):

                for attr in [
                    "src",
                    "data-src",
                    "data-original",
                    "data-lazy-src"
                ]:

                    image_url = img.get(attr)

                    if image_url:
                        return image_url

    except Exception as e:

        print(
            "IMAGE ERROR:",
            repr(e)
        )

    return None


# ============================================================
# BUILD CAPTION
# ============================================================

def build_media_caption(
    title,
    article_text,
    hashtags
):

    safe_title = html.escape(title)
    safe_hashtags = html.escape(hashtags)

    footer = (
        f"\n\n{safe_hashtags}"
        f"\n\n@ligebartar24"
    )

    TELEGRAM_CAPTION_LIMIT = 1024

    fixed_part = (
        f"<b>{safe_title}</b>\n\n"
    )

    available = (
        TELEGRAM_CAPTION_LIMIT
        - len(fixed_part)
        - len(footer)
        - 5
    )

    if available < 50:
        available = 50

    media_text = truncate_to_sentence(
        article_text,
        available
    )

    caption = (
        fixed_part
        + html.escape(media_text)
        + footer
    )

    if len(caption) > TELEGRAM_CAPTION_LIMIT:

        available -= (
            len(caption)
            - TELEGRAM_CAPTION_LIMIT
        )

        media_text = truncate_to_sentence(
            article_text,
            max(50, available)
        )

        caption = (
            fixed_part
            + html.escape(media_text)
            + footer
        )

    return caption


# ============================================================
# BUILD TEXT MESSAGE
# ============================================================

def build_text_message(
    title,
    article_text,
    hashtags
):

    safe_title = html.escape(title)
    safe_hashtags = html.escape(hashtags)

    footer = (
        f"\n\n{safe_hashtags}"
        f"\n\n@ligebartar24"
    )

    TELEGRAM_TEXT_LIMIT = 4096

    fixed_part = (
        f"<b>{safe_title}</b>\n\n"
    )

    available = (
        TELEGRAM_TEXT_LIMIT
        - len(fixed_part)
        - len(footer)
        - 5
    )

    if available < 100:
        available = 100

    text_message = truncate_to_sentence(
        article_text,
        available
    )

    return (
        fixed_part
        + html.escape(text_message)
        + footer
    )


# ============================================================
# SEND NEWS
# ============================================================

def send_news(bot, news, sent):

    title = news["title"]

    print()
    print(
        "PROCESSING:",
        title
    )

    article_text = get_article_text(
        news["link"]
    )

    if not article_text:

        article_text = BeautifulSoup(
            news.get("summary", ""),
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

    print(
        "HASHTAGS:",
        hashtags
    )

    caption = build_media_caption(
        title,
        article_text,
        hashtags
    )

    # ========================================================
    # VIDEO
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
                    "User-Agent": USER_AGENT,
                    "Referer":
                        "https://www.aparat.com/",
                    "Origin":
                        "https://www.aparat.com"
                },
                stream=True,
                timeout=120
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

            if os.path.exists(temp_file):

                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    # ========================================================
    # IMAGE
    # ========================================================

    image_url = get_entry_image(news)

    if image_url:

        temp_image = "temp_news.jpg"

        try:

            image_response = requests.get(
                image_url,
                headers={
                    "User-Agent": USER_AGENT
                },
                timeout=30
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

            if os.path.exists(temp_image):

                try:
                    os.remove(temp_image)
                except Exception:
                    pass

    # ========================================================
    # TEXT
    # ========================================================

    try:

        text_message = build_text_message(
            title,
            article_text,
            hashtags
        )

        asyncio.get_event_loop().run_until_complete(
            bot.send_message(
                chat_id=CHANNEL,
                text=text_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
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
# PROCESS RSS
# ============================================================

def process_rss_news(bot, sent):

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

        print(
            "⚠️ FIRST RUN"
        )

        save_last_run(current_time)

        print(
            "✅ BASELINE CREATED"
        )

        return

    all_new_news = []

    # ========================================================
    # دریافت اخبار
    # ========================================================

    for rss_url in RSS_SOURCES:

        print()
        print(
            "RSS:",
            rss_url
        )

        news_list = get_news(rss_url)

        for news in news_list:

            title = news["title"]

            # --------------------------------------------
            # بررسی دیتابیس
            # --------------------------------------------

            if is_already_sent(news, sent):

                print(
                    "🚫 ALREADY SENT:",
                    title
                )

                continue

            # --------------------------------------------
            # بررسی تاریخ
            # --------------------------------------------

            news_timestamp = get_news_timestamp(news)

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

            all_new_news.append(news)

    # ========================================================
    # حذف تکراری با عنوان
    # ========================================================

    unique_news = []

    seen_titles = set()
    seen_urls = set()

    for news in all_new_news:

        title_hash = make_news_fingerprint(
            news["title"]
        )

        clean_url = normalize_url(
            news["link"]
        )

        if title_hash in seen_titles:

            print(
                "🚫 DUPLICATE TITLE:",
                news["title"]
            )

            continue

        if clean_url in seen_urls:

            print(
                "🚫 DUPLICATE URL:",
                news["title"]
            )

            continue

        seen_titles.add(title_hash)
        seen_urls.add(clean_url)

        unique_news.append(news)

    all_new_news = unique_news

    # ========================================================
    # مرتب‌سازی قدیمی به جدید
    # ========================================================

    all_new_news.sort(
        key=lambda item: (
            get_news_timestamp(item) or 0
        )
    )

    print()
    print(
        "========================================"
    )

    print(
        "TOTAL NEW UNIQUE NEWS:",
        len(all_new_news)
    )

    print(
        "MAX NEWS PER RUN:",
        MAX_NEWS_PER_RUN
    )

    print(
        "========================================"
    )

    # ========================================================
    # محدودیت تعداد
    # ========================================================

    news_to_send = all_new_news[
        :MAX_NEWS_PER_RUN
    ]

    skipped_count = (
        len(all_new_news)
        - len(news_to_send)
    )

    if skipped_count > 0:

        print(
            "⏸️ NEWS LEFT FOR NEXT RUN:",
            skipped_count
        )

    # ========================================================
    # ارسال
    # ========================================================

    sent_count = 0

    for news in news_to_send:

        success = send_news(
            bot,
            news,
            sent
        )

        if success:
            sent_count += 1

        time.sleep(1)

    # ========================================================
    # ذخیره زمان
    # ========================================================

    save_last_run(current_time)

    print()
    print(
        "========================================"
    )

    print(
        "✅ RSS CHECK COMPLETED"
    )

    print(
        "NEWS SENT:",
        sent_count
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
