import os
import json
import re
import asyncio
import feedparser
import requests

from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from telegram import Bot


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

SENT_FILE = "sent_news.json"
MATCH_STATE_FILE = "match_state.json"

MAX_NEWS_PER_RUN = 10
REQUEST_TIMEOUT = 25

CUSTOM_EMOJI_ID = "5231262796364137694"

API_BASE = "https://v3.football.api-sports.io"

# ایران
API_TIMEZONE = "Asia/Tehran"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ============================================================
# FOOTBALL KEYWORDS
# ============================================================

FOOTBALL_KEYWORDS = [
    # ایران
    "فوتبال",
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "ذوب‌آهن",
    "گل گهر",
    "گل‌گهر",
    "نساجی",
    "ملوان",
    "فولاد",
    "هوادار",
    "آلومینیوم",
    "خیبر",
    "شمس آذر",
    "چادرملو",
    "پیکان",
    "مس رفسنجان",
    "استقلال خوزستان",

    # تیم ملی
    "تیم ملی فوتبال",
    "تیم ملی",
    "فدراسیون فوتبال",
    "فوتسال",
    "فوتبال ساحلی",

    # مسابقات
    "لیگ برتر",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان",
    "لیگ نخبگان",
    "لیگ اروپا",
    "لیگ کنفرانس",
    "لیگ ملت‌ها",
    "انتخابی جام جهانی",
    "دربی",
    "داربی",

    # بازیکنان ایرانی
    "طارمی",
    "آزمون",
    "جهانبخش",
    "قایدی",
    "قدوس",
    "عزت‌اللهی",
    "عزت اللهی",
    "محبی",
    "نوراللهی",
    "حاج‌صفی",
    "حاج صفی",
    "مهدی ترابی",
    "علیرضا بیرانوند",

    # اروپا
    "رئال مادرید",
    "بارسلونا",
    "اتلتیکو مادرید",
    "منچستریونایتد",
    "منچسترسیتی",
    "لیورپول",
    "چلسی",
    "آرسنال",
    "تاتنهام",
    "نیوکاسل",
    "بایرن مونیخ",
    "دورتموند",
    "اینتر",
    "میلان",
    "یوونتوس",
    "ناپولی",
    "رم",
    "لاتزیو",
    "پاری سن ژرمن",
    "پاری‌سن ژرمن",
    "مارسی",
    "موناکو",
    "آژاکس",
    "آیندهوون",

    # اصطلاحات فوتبال
    "گلزنی",
    "گل زد",
    "گلزنی کرد",
    "گل به خودی",
    "پنالتی",
    "داور",
    "مربی",
    "سرمربی",
    "بازیکن",
    "ترکیب",
    "تعویض",
    "کارت قرمز",
    "کارت زرد",
    "مصدوم",
    "مصدومیت",
    "انتقال",
    "قرارداد",
    "تمرین",
    "اردو",
    "بازی",
    "دیدار",
    "مسابقه",
    "برد",
    "باخت",
    "تساوی",
    "نتیجه",
    "سوت",
    "دربی",
]


# ============================================================
# HASHTAGS
# ============================================================

HASHTAG_KEYWORDS = [
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "ذوب‌آهن",
    "گل گهر",
    "گل‌گهر",
    "نساجی",
    "تیم ملی",
    "لیگ برتر",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان",
    "لیگ نخبگان",
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
    "پاری‌سن ژرمن",
    "فوتبال ایران",
    "فوتبال اروپا",
]


# ============================================================
# RSS SOURCES
# ============================================================

RSS_SOURCES = [
    "https://www.isna.ir/rss",
    "https://www.khabarvarzeshi.com/rss",
    "https://www.varzesh3.com/rss",
    "https://www.tasnimnews.com/fa/rss",
]


# ============================================================
# LOAD / SAVE SENT NEWS
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
                sent_news[-1500:],
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
# MATCH STATE
# ============================================================

def load_match_state():

    if not os.path.exists(MATCH_STATE_FILE):
        return {}

    try:

        with open(
            MATCH_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as error:

        print(
            "LOAD MATCH STATE ERROR:",
            error
        )

    return {}


def save_match_state(state):

    try:

        with open(
            MATCH_STATE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            "SAVE MATCH STATE ERROR:",
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
    max_length=650
):

    text = clean_text(text)

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    text = text[:max_length]

    last_space = text.rfind(" ")

    if last_space > 350:
        text = text[:last_space]

    return text + "..."


# ============================================================
# FOOTBALL FILTER
# ============================================================

def is_football_news(
    title,
    summary
):

    text = (
        f"{title} {summary}"
        .lower()
    )

    # --------------------------------------------------------
    # کلمات صریحاً غیرورزشی
    # --------------------------------------------------------

    non_sport_keywords = [
        "دولت",
        "استاندار",
        "وزیر",
        "مجلس",
        "نماینده مجلس",
        "انتخابات",
        "سیاسی",
        "سیاست",
        "اقتصاد",
        "اقتصادی",
        "بورس",
        "دلار",
        "طلا",
        "ارز",
        "بانک",
        "مسکن",
        "خودرو",
        "قطار",
        "هواپیما",
        "زلزله",
        "هواشناسی",
        "مدرسه",
        "دانشگاه",
        "آموزش و پرورش",
        "شهرداری",
        "استانداری",
        "تصادف",
        "حادثه",
        "بیمارستان",
        "درمان",
        "پزشکی",
    ]

    strong_football = [
        "فوتبال",
        "استقلال",
        "پرسپولیس",
        "سپاهان",
        "تراکتور",
        "ذوب آهن",
        "ذوب‌آهن",
        "گل گهر",
        "گل‌گهر",
        "نساجی",
        "ملوان",
        "فولاد",
        "لیگ برتر",
        "جام حذفی",
        "جام جهانی",
        "لیگ قهرمانان",
        "لیگ نخبگان",
        "لیگ اروپا",
        "تیم ملی فوتبال",
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
        "پاری‌سن ژرمن",
        "دربی",
        "داربی",
    ]

    for keyword in strong_football:

        if keyword.lower() in text:

            # خبرهای صریح فوتبال قبول شوند
            return True

    # اگر فقط کلمات عمومی مثل «بازی» یا «مربی» دارد
    # بدون نشانه واضح فوتبال، رد شود.

    general_football_words = [
        "گلزنی",
        "پنالتی",
        "ترکیب",
        "سرمربی",
        "بازیکن",
        "کارت قرمز",
        "کارت زرد",
        "تعویض",
        "مصدومیت",
    ]

    has_general = any(
        word.lower() in text
        for word in general_football_words
    )

    if has_general:

        for bad in non_sport_keywords:

            if bad.lower() in text:

                return False

        return True

    return False


# ============================================================
# HASHTAGS
# ============================================================

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
                + keyword
                .replace(" ", "_")
                .replace("‌", "")
            )

            if hashtag not in found:
                found.append(hashtag)

        if len(found) >= 5:
            break

    if "#فوتبال" not in found:
        found.append("#فوتبال")

    if "#اخبار_فوتبال" not in found:
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

        image = soup.find("img")

        if image:

            url = (
                image.get("src")
                or image.get("data-src")
            )

            if url:
                return url

    return None


# ============================================================
# VIDEO
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
        "mp4",
        "/video/",
        "/videos/",
        "video_url",
        "video-url",
        "videourl"
    ]

    for word in words:

        if word in url_lower:
            return True

    return False


# ============================================================
# APARAT HASH
# ============================================================

def extract_aparat_hash(
    article_url,
    html
):

    iframe_matches = re.findall(
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE
    )

    for iframe_url in iframe_matches:

        if "aparat.com" not in iframe_url.lower():
            continue

        print(
            "APARAT IFRAME:",
            iframe_url
        )

        match = re.search(
            r'videohash/([A-Za-z0-9_-]+)',
            iframe_url,
            flags=re.IGNORECASE
        )

        if match:

            video_hash = match.group(1)

            if video_hash.lower() != "video":

                print(
                    "APARAT VIDEO HASH FOUND:",
                    video_hash
                )

                return video_hash

        match = re.search(
            r'aparat\.com/(?:v|video)/([A-Za-z0-9_-]+)',
            iframe_url,
            flags=re.IGNORECASE
        )

        if match:

            video_hash = match.group(1)

            if video_hash.lower() != "video":

                print(
                    "APARAT VIDEO HASH FOUND:",
                    video_hash
                )

                return video_hash

    matches = re.findall(
        r'videohash[/"\':= ]+([A-Za-z0-9_-]+)',
        html,
        flags=re.IGNORECASE
    )

    for video_hash in matches:

        if video_hash.lower() == "video":
            continue

        if len(video_hash) < 4:
            continue

        print(
            "APARAT VIDEO HASH FOUND:",
            video_hash
        )

        return video_hash

    matches = re.findall(
        r'https?://(?:www\.)?aparat\.com/v/([A-Za-z0-9_-]+)',
        html,
        flags=re.IGNORECASE
    )

    for video_hash in matches:

        if video_hash.lower() == "video":
            continue

        print(
            "APARAT VIDEO HASH FOUND:",
            video_hash
        )

        return video_hash

    return None


# ============================================================
# APARAT API
# ============================================================

def get_aparat_video(video_hash):

    if not video_hash:
        return None

    api_url = (
        "https://www.aparat.com/"
        "api/fa/v1/video/video/show/"
        "videohash/"
        + video_hash
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

        if response.status_code != 200:
            return None

        data = response.json()

        attributes = (
            data
            .get("data", {})
            .get("attributes", {})
        )

        if not attributes:
            return None

        print(
            "APARAT TITLE:",
            attributes.get("title", "")
        )

        print(
            "APARAT DURATION:",
            attributes.get("duration", "")
        )

        file_link_all = attributes.get(
            "file_link_all",
            []
        )

        if file_link_all:

            profiles = sorted(
                file_link_all,
                key=lambda item: (
                    0
                    if item.get("profile") == "240p"
                    else 1
                )
            )

            for profile in profiles:

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
                    profile_name
                )

                for url in urls:

                    if url:

                        print(
                            "APARAT MP4 FOUND:",
                            profile_name
                        )

                        return url

        file_link = attributes.get(
            "file_link"
        )

        if file_link and is_video_url(
            file_link
        ):

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
# ARTICLE VIDEO
# ============================================================

def get_video_url(article_url):

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

        print(
            "ARTICLE CONTENT TYPE:",
            response.headers.get(
                "content-type",
                ""
            )
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
            .lower()
        )

        if content_type.startswith(
            "video/"
        ):

            return response.url

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        video_hash = extract_aparat_hash(
            article_url,
            html
        )

        if video_hash:

            aparat_url = get_aparat_video(
                video_hash
            )

            if aparat_url:

                print(
                    "✅ APARAT MP4 URL FOUND"
                )

                return aparat_url

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

                        return url

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
                candidates.append(data_src)

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

                    return url

        sources = soup.find_all(
            "source"
        )

        for source in sources:

            url = (
                source.get("src")
                or source.get("data-src")
            )

            if not url:
                continue

            url = urljoin(
                article_url,
                url
            )

            if is_video_url(url):

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
    seen_links = set()

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

                if link in seen_links:
                    continue

                if not is_football_news(
                    title,
                    summary
                ):
                    continue

                seen_links.add(link)

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
# CREATE MESSAGE
# ============================================================

def create_message(news):

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
# API-FOOTBALL REQUEST
# ============================================================

def football_api(
    endpoint,
    params=None
):

    if not API_FOOTBALL_KEY:

        print(
            "❌ API_FOOTBALL_KEY پیدا نشد"
        )

        return None

    url = (
        API_BASE
        + "/"
        + endpoint
    )

    headers = {
        "x-apisports-key":
            API_FOOTBALL_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=20
        )

        print(
            "API-FOOTBALL:",
            endpoint
        )

        print(
            "API STATUS:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "API ERROR:",
                response.text[:500]
            )

            return None

        data = response.json()

        if data.get("errors"):

            print(
                "API ERRORS:",
                data.get("errors")
            )

            return None

        return data

    except Exception as error:

        print(
            "API-FOOTBALL ERROR:",
            error
        )

        return None


# ============================================================
# API FOOTBALL - TODAY'S FIXTURES
# ============================================================

def get_today_fixtures():

    today = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d"
    )

    print(
        "API FOOTBALL DATE:",
        today
    )

    data = football_api(
        "fixtures",
        {
            "date": today,
            "timezone": API_TIMEZONE
        }
    )

    if not data:
        return []

    fixtures = data.get(
        "response",
        []
    )

    print(
        "API FOOTBALL FIXTURES:",
        len(fixtures)
    )

    return fixtures


# ============================================================
# TEAM NAMES
# ============================================================

def team_name(team):

    if not team:
        return "نامشخص"

    return team.get(
        "name",
        "نامشخص"
    )


# ============================================================
# MATCH STATUS
# ============================================================

LIVE_STATUSES = {
    "1H",
    "HT",
    "2H",
    "ET",
    "BT",
    "P"
}

FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN"
}


# ============================================================
# FORMAT MINUTE
# ============================================================

def format_minute(
    event
):

    time_data = event.get(
        "time",
        {}
    )

    minute = time_data.get(
        "elapsed"
    )

    extra = time_data.get(
        "extra"
    )

    if minute is None:
        return ""

    if extra:
        return f"{minute}+{extra}"

    return str(minute)


# ============================================================
# MATCH MESSAGE
# ============================================================

def match_logo():

    return (
        '<tg-emoji emoji-id="'
        + CUSTOM_EMOJI_ID
        + '">🏆</tg-emoji>'
    )


def create_match_header(
    fixture
):

    league = fixture.get(
        "league",
        {}
    )

    teams = fixture.get(
        "teams",
        {}
    )

    goals = fixture.get(
        "goals",
        {}
    )

    home = team_name(
        teams.get("home")
    )

    away = team_name(
        teams.get("away")
    )

    home_goals = goals.get(
        "home"
    )

    away_goals = goals.get(
        "away"
    )

    status = (
        fixture
        .get("fixture", {})
        .get("status", {})
    )

    short_status = status.get(
        "short",
        ""
    )

    elapsed = status.get(
        "elapsed"
    )

    league_name = league.get(
        "name",
        "فوتبال"
    )

    if home_goals is None:
        score = "🆚"
    else:
        score = (
            f"{home_goals} - {away_goals}"
        )

    if short_status in LIVE_STATUSES:

        if elapsed:

            status_text = (
                f"🔴 زنده | دقیقه {elapsed}"
            )

        else:

            status_text = "🔴 زنده"

    elif short_status in FINISHED_STATUSES:

        status_text = "🏁 پایان بازی"

    elif short_status == "HT":

        status_text = "⏸ بین دو نیمه"

    else:

        status_text = "⏰ پیش از بازی"

    message = (
        match_logo()
        + " <b>"
        + league_name
        + "</b>\n\n"
        + "⚽️ <b>"
        + home
        + "</b>  "
        + score
        + "  <b>"
        + away
        + "</b>\n\n"
        + status_text
        + "\n\n"
        + "📢 @ligebartar24"
    )

    return message


# ============================================================
# EVENTS
# ============================================================

def extract_goals(
    fixture
):

    events = fixture.get(
        "events",
        []
    )

    goals = []

    for event in events:

        event_type = event.get(
            "type",
            ""
        )

        detail = event.get(
            "detail",
            ""
        )

        if event_type != "Goal":
            continue

        player = event.get(
            "player",
            {}
        )

        assist = event.get(
            "assist",
            {}
        )

        team = event.get(
            "team",
            {}
        )

        goals.append({
            "id": event.get(
                "time",
                {}
            ).get("elapsed"),
            "minute": format_minute(
                event
            ),
            "player": player.get(
                "name",
                "بازیکن"
            ),
            "assist": assist.get(
                "name"
            ),
            "team": team.get(
                "name",
                ""
            ),
            "detail": detail,
        })

    return goals


# ============================================================
# CREATE GOAL MESSAGE
# ============================================================

def create_goal_message(
    fixture,
    event
):

    teams = fixture.get(
        "teams",
        {}
    )

    home = team_name(
        teams.get("home")
    )

    away = team_name(
        teams.get("away")
    )

    goals = fixture.get(
        "goals",
        {}
    )

    home_score = goals.get(
        "home",
        0
    )

    away_score = goals.get(
        "away",
        0
    )

    detail = event.get(
        "detail",
        ""
    )

    if detail == "Own Goal":
        goal_type = "گل به خودی"
    elif detail == "Penalty":
        goal_type = "پنالتی"
    elif detail == "Missed Penalty":
        goal_type = "پنالتی از دست رفت"
    else:
        goal_type = "گل"

    player = event.get(
        "player",
        "بازیکن"
    )

    minute = event.get(
        "minute",
        ""
    )

    team = event.get(
        "team",
        ""
    )

    message = (
        "⚽️ <b>گــــــــل!</b>\n\n"
        + "🔥 "
        + "<b>"
        + str(team)
        + "</b>\n"
        + "⚽️ "
        + str(player)
        + " — "
        + goal_type
        + "\n"
        + "⏱ دقیقه "
        + str(minute)
        + "\n\n"
        + "🏟 "
        + home
        + "  "
        + str(home_score)
        + " - "
        + str(away_score)
        + "  "
        + away
        + "\n\n"
        + "📢 @ligebartar24"
    )

    return message


# ============================================================
# LINEUPS
# ============================================================

def create_lineup_message(
    fixture
):

    lineups = fixture.get(
        "lineups",
        []
    )

    if not lineups:
        return None

    teams = fixture.get(
        "teams",
        {}
    )

    home = team_name(
        teams.get("home")
    )

    away = team_name(
        teams.get("away")
    )

    text = (
        match_logo()
        + " <b>ترکیب رسمی</b>\n\n"
        + "⚽️ "
        + home
        + " 🆚 "
        + away
        + "\n\n"
    )

    for lineup in lineups:

        team = lineup.get(
            "team",
            {}
        )

        team_name_value = team.get(
            "name",
            "تیم"
        )

        formation = lineup.get(
            "formation",
            ""
        )

        text += (
            "🔵 <b>"
            + team_name_value
            + "</b>"
        )

        if formation:

            text += (
                " | سیستم "
                + formation
            )

        text += "\n"

        starters = lineup.get(
            "startXI",
            []
        )

        names = []

        for item in starters:

            player = item.get(
                "player",
                {}
            )

            name = player.get(
                "name"
            )

            if name:
                names.append(
                    name
                )

        if names:

            text += (
                "\n".join(
                    "• " + name
                    for name in names
                )
            )

        text += "\n\n"

    text += (
        "📢 @ligebartar24"
    )

    return text


# ============================================================
# MATCH STATE KEY
# ============================================================

def get_match_key(
    fixture
):

    fixture_data = fixture.get(
        "fixture",
        {}
    )

    fixture_id = fixture_data.get(
        "id"
    )

    return str(
        fixture_id
    )


# ============================================================
# PROCESS FOOTBALL FIXTURES
# ============================================================

async def process_football_matches(
    bot,
    state
):

    if not API_FOOTBALL_KEY:

        print(
            "⚠️ API_FOOTBALL_KEY موجود نیست"
        )

        return state

    fixtures = get_today_fixtures()

    if not fixtures:

        print(
            "هیچ بازی امروز از API دریافت نشد."
        )

        return state

    for fixture in fixtures:

        try:

            fixture_data = fixture.get(
                "fixture",
                {}
            )

            fixture_id = fixture_data.get(
                "id"
            )

            if not fixture_id:
                continue

            status = fixture_data.get(
                "status",
                {}
            )

            status_short = status.get(
                "short",
                ""
            )

            teams = fixture.get(
                "teams",
                {}
            )

            home = team_name(
                teams.get("home")
            )

            away = team_name(
                teams.get("away")
            )

            key = get_match_key(
                fixture
            )

            old = state.get(
                key,
                {}
            )

            # ------------------------------------------------
            # CURRENT SCORE
            # ------------------------------------------------

            goals = fixture.get(
                "goals",
                {}
            )

            current_home = goals.get(
                "home"
            )

            current_away = goals.get(
                "away"
            )

            previous_home = old.get(
                "home"
            )

            previous_away = old.get(
                "away"
            )

            print(
                "MATCH:",
                home,
                "vs",
                away,
                "|",
                status_short,
                "|",
                current_home,
                "-",
                current_away
            )

            # ------------------------------------------------
            # FIRST TIME WE SEE MATCH
            # ------------------------------------------------

            if key not in state:

                state[key] = {
                    "home": current_home,
                    "away": current_away,
                    "status": status_short,
                    "lineup_sent": False,
                    "goals_sent": []
                }

                # اگر بازی زنده است، وضعیت فعلی را بفرست
                if status_short in LIVE_STATUSES:

                    message = create_match_header(
                        fixture
                    )

                    await bot.send_message(
                        chat_id=CHANNEL,
                        text=message,
                        parse_mode="HTML"
                    )

                    print(
                        "✅ LIVE MATCH SENT"
                    )

            # ------------------------------------------------
            # GOALS
            # ------------------------------------------------

            if (
                previous_home is not None
                and previous_away is not None
                and (
                    current_home != previous_home
                    or current_away != previous_away
                )
            ):

                goals_events = extract_goals(
                    fixture
                )

                sent_goal_keys = set(
                    old.get(
                        "goals_sent",
                        []
                    )
                )

                for event in goals_events:

                    goal_key = (
                        str(event.get("minute"))
                        + "|"
                        + str(event.get("player"))
                        + "|"
                        + str(event.get("team"))
                    )

                    if goal_key in sent_goal_keys:
                        continue

                    message = create_goal_message(
                        fixture,
                        event
                    )

                    await bot.send_message(
                        chat_id=CHANNEL,
                        text=message,
                        parse_mode="HTML"
                    )

                    print(
                        "⚽️ GOAL SENT:",
                        event
                    )

                    sent_goal_keys.add(
                        goal_key
                    )

                    old["goals_sent"] = list(
                        sent_goal_keys
                    )

                    await asyncio.sleep(1)

            # ------------------------------------------------
            # LINEUPS
            # ------------------------------------------------

            if not old.get(
                "lineup_sent",
                False
            ):

                lineup_message = create_lineup_message(
                    fixture
                )

                if lineup_message:

                    # فقط در بازه نزدیک شروع بازی
                    # یا زمانی که ترکیب واقعاً آمده باشد

                    await bot.send_message(
                        chat_id=CHANNEL,
                        text=lineup_message,
                        parse_mode="HTML"
                    )

                    old["lineup_sent"] = True

                    print(
                        "✅ LINEUPS SENT:",
                        home,
                        "vs",
                        away
                    )

            # ------------------------------------------------
            # FINISHED
            # ------------------------------------------------

            if (
                status_short in FINISHED_STATUSES
                and old.get(
                    "finished_sent",
                    False
                ) is not True
            ):

                message = (
                    "🏁 <b>پایان بازی</b>\n\n"
                    + "⚽️ <b>"
                    + home
                    + "</b>  "
                    + str(current_home)
                    + " - "
                    + str(current_away)
                    + "  <b>"
                    + away
                    + "</b>\n\n"
                    + "📢 @ligebartar24"
                )

                await bot.send_message(
                    chat_id=CHANNEL,
                    text=message,
                    parse_mode="HTML"
                )

                old["finished_sent"] = True

                print(
                    "🏁 FULL TIME SENT"
                )

            # ------------------------------------------------
            # SAVE STATE
            # ------------------------------------------------

            old["home"] = current_home
            old["away"] = current_away
            old["status"] = status_short

            state[key] = old

            await asyncio.sleep(0.3)

        except Exception as error:

            print(
                "MATCH PROCESS ERROR:",
                error
            )

    return state


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

        try:

            head = requests.head(
                media_url,
                timeout=REQUEST_TIMEOUT,
                headers=HEADERS,
                allow_redirects=True
            )

            print(
                "MEDIA HEAD STATUS:",
                head.status_code
            )

            print(
                "MEDIA HEAD TYPE:",
                head.headers.get(
                    "content-type",
                    ""
                )
            )

        except Exception as head_error:

            print(
                "MEDIA HEAD ERROR:",
                head_error
            )

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
            response.headers.get(
                "content-type",
                ""
            )
            .lower()
        )

        print(
            "MEDIA CONTENT TYPE:",
            content_type
        )

        print(
            "MEDIA CONTENT LENGTH:",
            len(response.content)
        )

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
                "✅ VIDEO SENT"
            )

            return True

        if is_video_url(
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
                "✅ VIDEO SENT BY URL"
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

    print(
        "================================"
    )

    print(
        "TELEGRAM SPORTS NEWS BOT"
    )

    print(
        "API-FOOTBALL ENABLED"
    )

    print(
        "================================"
    )

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

    if API_FOOTBALL_KEY:

        print(
            "✅ API_FOOTBALL_KEY FOUND"
        )

    else:

        print(
            "⚠️ API_FOOTBALL_KEY NOT FOUND"
        )

    # --------------------------------------------------------
    # SENT NEWS
    # --------------------------------------------------------

    sent_news = load_sent_news()

    print(
        "SENT NEWS COUNT:",
        len(sent_news)
    )

    # --------------------------------------------------------
    # MATCH STATE
    # --------------------------------------------------------

    match_state = load_match_state()

    # --------------------------------------------------------
    # BOT
    # --------------------------------------------------------

    bot = Bot(
        token=BOT_TOKEN
    )

    # --------------------------------------------------------
    # FOOTBALL API
    # --------------------------------------------------------

    try:

        match_state = await process_football_matches(
            bot,
            match_state
        )

        save_match_state(
            match_state
        )

    except Exception as error:

        print(
            "FOOTBALL API PROCESS ERROR:",
            error
        )

    # --------------------------------------------------------
    # RSS NEWS
    # --------------------------------------------------------

    news_list = get_news()

    print(
        "FOOTBALL NEWS FOUND:",
        len(news_list)
    )

    sent_count = 0

    # --------------------------------------------------------
    # PROCESS NEWS
    # --------------------------------------------------------

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
            "================================"
        )

        print(
            "PROCESSING:",
            news["title"]
        )

        message = create_message(
            news
        )

        media_sent = False

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        video_url = get_video_url(
            link
        )

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
                    "✅ VIDEO NEWS SENT"
                )

        # ----------------------------------------------------
        # RSS IMAGE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

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

        await asyncio.sleep(2)

    print(
        "================================"
    )

    print(
        f"✅ اجرای ربات تمام شد. "
        f"{sent_count} خبر ارسال شد."
    )

    print(
        "================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
