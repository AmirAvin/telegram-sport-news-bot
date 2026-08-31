import os
import json
import re
import asyncio
import feedparser
import requests

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

MAX_NEWS_PER_RUN = 10
REQUEST_TIMEOUT = 25

CUSTOM_EMOJI_ID = "5231262796364137694"

API_BASE = "https://v3.football.api-sports.io"

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
    "فوتبال",
    "football",
    "soccer",
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
    "شمس آذر",
    "تیم ملی",
    "لیگ برتر",
    "جام حذفی",
    "جام جهانی",
    "لیگ قهرمانان",
    "لیگ اروپا",
    "کنفرانس لیگ",
    "لژیونر",
    "طارمی",
    "آزمون",
    "جهانبخش",
    "قایدی",
    "رونالدو",
    "مسی",
    "نیمار",
    "امباپه",
    "لامین یامال",
    "رئال مادرید",
    "بارسلونا",
    "منچستریونایتد",
    "منچسترسیتی",
    "لیورپول",
    "چلسی",
    "آرسنال",
    "تاتنهام",
    "بایرن مونیخ",
    "اینتر",
    "میلان",
    "یوونتوس",
    "ناپولی",
    "رم",
    "لاتزیو",
    "پاری سن ژرمن",
    "پاری‌سن ژرمن",
    "مارسی",
    "اتلتیکو مادرید",
    "سویا",
    "والنسیا",
    "دربی",
    "داربی",
    "گلزنی",
    "گل",
    "پنالتی",
    "کارت قرمز",
    "کارت زرد",
    "ترکیب",
    "مصدومیت",
    "انتقال",
    "نقل و انتقالات",
    "سرمربی",
    "بازیکن",
    "دروازه بان",
    "دروازه‌بان",
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
    "ملوان",
    "فولاد",
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
# API REQUEST
# ============================================================

def api_request(endpoint, params=None):

    if not API_FOOTBALL_KEY:
        print("❌ API_FOOTBALL_KEY پیدا نشد")
        return None

    url = API_BASE + endpoint

    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=REQUEST_TIMEOUT
        )

        print(
            "API REQUEST:",
            endpoint,
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
                "API RESPONSE ERRORS:",
                data.get("errors")
            )

        return data

    except Exception as error:

        print(
            "API REQUEST ERROR:",
            error
        )

        return None


# ============================================================
# API STATUS
# ============================================================

def check_api_status():

    print(
        "================================"
    )

    print(
        "CHECKING API-FOOTBALL"
    )

    data = api_request(
        "/status"
    )

    if not data:
        return False

    response = data.get(
        "response",
        {}
    )

    subscription = response.get(
        "subscription",
        {}
    )

    requests_info = response.get(
        "requests",
        {}
    )

    print(
        "API PLAN:",
        subscription.get("plan")
    )

    print(
        "API REQUESTS TODAY:",
        requests_info.get("current"),
        "/",
        requests_info.get("limit_day")
    )

    print(
        "================================"
    )

    return True


# ============================================================
# LOAD SENT NEWS
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


# ============================================================
# SAVE SENT NEWS
# ============================================================

def save_sent_news(sent_news):

    try:

        with open(
            SENT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sent_news[-2000:],
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
# CLEAN TEXT
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


# ============================================================
# SHORTEN
# ============================================================

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

    text = (
        f"{title} {summary}"
        .lower()
    )

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

    if len(found) < 3:
        found.append("#فوتبال")

    if len(found) < 3:
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
            r"videohash/([A-Za-z0-9_-]+)",
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
            r"aparat\.com/(?:v|video)/([A-Za-z0-9_-]+)",
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
        r"https?://(?:www\.)?aparat\.com/v/([A-Za-z0-9_-]+)",
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

def get_aparat_video(
    video_hash
):

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

        print(
            "ARTICLE CONTENT TYPE:",
            response.headers.get(
                "content-type",
                ""
            )
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

        if content_type.startswith("video/"):

            print(
                "DIRECT VIDEO FOUND"
            )

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

                        print(
                            "VIDEO FOUND OG:",
                            url
                        )

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

            print(
                error
            )

    return all_news


# ============================================================
# API FOOTBALL — LIVE MATCHES
# ============================================================

def get_live_matches():

    print(
        "================================"
    )

    print(
        "CHECKING LIVE FOOTBALL MATCHES"
    )

    data = api_request(
        "/fixtures",
        {
            "live": "all"
        }
    )

    if not data:
        return []

    fixtures = data.get(
        "response",
        []
    )

    print(
        "LIVE MATCHES:",
        len(fixtures)
    )

    return fixtures


# ============================================================
# API FOOTBALL — TODAY MATCHES
# ============================================================

def get_today_matches():

    from datetime import datetime, timezone

    today = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    data = api_request(
        "/fixtures",
        {
            "date": today
        }
    )

    if not data:
        return []

    fixtures = data.get(
        "response",
        []
    )

    print(
        "TODAY MATCHES:",
        len(fixtures)
    )

    return fixtures


# ============================================================
# LIVE EVENT TEXT
# ============================================================

def translate_event_type(
    event
):

    event_type = event.get(
        "type",
        ""
    )

    detail = event.get(
        "detail",
        ""
    )

    player = (
        event
        .get("player", {})
        .get("name", "")
    )

    assist = (
        event
        .get("assist", {})
        .get("name", "")
    )

    team = (
        event
        .get("team", {})
        .get("name", "")
    )

    minute = event.get(
        "time",
        {}
    ).get(
        "elapsed",
        ""
    )

    if event_type == "Goal":

        text = (
            f"⚽ گل در دقیقه {minute}!\n"
            f"👤 {player}\n"
            f"🏟 {team}"
        )

        if assist:
            text += f"\n🎯 پاس گل: {assist}"

        return text

    if event_type == "Card":

        if "Red" in detail:

            return (
                f"🟥 کارت قرمز در دقیقه "
                f"{minute}\n"
                f"👤 {player}\n"
                f"🏟 {team}"
            )

        return (
            f"🟨 کارت زرد در دقیقه "
            f"{minute}\n"
            f"👤 {player}\n"
            f"🏟 {team}"
        )

    if event_type == "subst":

        player_out = (
            event
            .get("player", {})
            .get("name", "")
        )

        player_in = (
            event
            .get("assist", {})
            .get("name", "")
        )

        return (
            f"🔄 تعویض در دقیقه {minute}\n"
            f"⬅️ {player_out}\n"
            f"➡️ {player_in}"
        )

    return None


# ============================================================
# LIVE MATCH MESSAGE
# ============================================================

def create_live_match_message(
    fixture,
    event
):

    teams = fixture.get(
        "teams",
        {}
    )

    home = teams.get(
        "home",
        {}
    ).get(
        "name",
        "تیم میزبان"
    )

    away = teams.get(
        "away",
        {}
    ).get(
        "name",
        "تیم مهمان"
    )

    goals = fixture.get(
        "goals",
        {}
    )

    home_goals = goals.get(
        "home",
        0
    )

    away_goals = goals.get(
        "away",
        0
    )

    event_text = translate_event_type(
        event
    )

    if not event_text:
        return None

    logo = (
        '<tg-emoji emoji-id="'
        + CUSTOM_EMOJI_ID
        + '">🏆</tg-emoji>'
    )

    return (
        logo
        + " <b>⚽ اتفاق مهم در بازی</b>\n\n"
        + f"🏠 {home}  {home_goals}\n"
        + f"✈️ {away}  {away_goals}\n\n"
        + event_text
        + "\n\n"
        + "#فوتبال #نتیجه_زنده\n\n"
        + "📢 @ligebartar24"
    )


# ============================================================
# SEND TEXT
# ============================================================

async def send_text(
    bot,
    text
):

    try:

        await bot.send_message(
            chat_id=CHANNEL,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        return True

    except Exception as error:

        print(
            "SEND TEXT ERROR:",
            error
        )

        return False


# ============================================================
# CREATE NEWS MESSAGE
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

        print(
            "MEDIA CONTENT TYPE:",
            content_type
        )

        print(
            "MEDIA CONTENT LENGTH:",
            len(response.content)
        )

        if content_type.startswith("image/"):

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

        if content_type.startswith("video/"):

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

        if is_video_url(media_url):

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
# PROCESS RSS NEWS
# ============================================================

async def process_rss_news(
    bot,
    sent_news
):

    news_list = get_news()

    print(
        "FOOTBALL NEWS FOUND:",
        len(news_list)
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

        if not media_sent:

            await send_text(
                bot,
                message
            )

            print(
                "✅ TEXT SENT"
            )

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

    return sent_count


# ============================================================
# PROCESS LIVE MATCHES
# ============================================================

async def process_live_matches(
    bot,
    sent_news
):

    fixtures = get_live_matches()

    event_sent = 0

    for fixture in fixtures:

        fixture_id = fixture.get(
            "fixture",
            {}
        ).get(
            "id"
        )

        if not fixture_id:
            continue

        home = (
            fixture
            .get("teams", {})
            .get("home", {})
            .get("name", "")
        )

        away = (
            fixture
            .get("teams", {})
            .get("away", {})
            .get("name", "")
        )

        # فقط بازی‌های مهم فوتبال
        match_text = (
            f"{home} {away}"
        ).lower()

        if not is_football_news(
            match_text,
            ""
        ):
            continue

        data = api_request(
            "/fixtures/events",
            {
                "fixture": fixture_id
            }
        )

        if not data:
            continue

        events = data.get(
            "response",
            []
        )

        for event in events:

            event_id = (
                f"event_{fixture_id}_"
                f"{event.get('time', {}).get('elapsed', '')}_"
                f"{event.get('type', '')}_"
                f"{event.get('player', {}).get('id', '')}"
            )

            if event_id in sent_news:
                continue

            message = create_live_match_message(
                fixture,
                event
            )

            if not message:
                continue

            if await send_text(
                bot,
                message
            ):

                sent_news.append(
                    event_id
                )

                save_sent_news(
                    sent_news
                )

                event_sent += 1

                print(
                    "✅ LIVE EVENT SENT:",
                    event_id
                )

    return event_sent


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

    if not API_FOOTBALL_KEY:

        print(
            "❌ API_FOOTBALL_KEY پیدا نشد"
        )

        return

    sent_news = load_sent_news()

    print(
        "SENT NEWS COUNT:",
        len(sent_news)
    )

    # --------------------------------------------------------
    # API STATUS
    # --------------------------------------------------------

    check_api_status()

    bot = Bot(
        token=BOT_TOKEN
    )

    # --------------------------------------------------------
    # LIVE
    # --------------------------------------------------------

    live_sent = await process_live_matches(
        bot,
        sent_news
    )

    print(
        "LIVE EVENTS SENT:",
        live_sent
    )

    # --------------------------------------------------------
    # RSS
    # --------------------------------------------------------

    news_sent = await process_rss_news(
        bot,
        sent_news
    )

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------

    print(
        "================================"
    )

    print(
        f"✅ اجرای ربات تمام شد. "
        f"{news_sent} خبر + "
        f"{live_sent} اتفاق زنده ارسال شد."
    )

    print(
        "================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
