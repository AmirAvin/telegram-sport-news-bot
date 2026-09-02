import os
import re
import json
import html
import time
import requests
import feedparser

from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL", "@ligebartar24")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

SENT_FILE = "sent_news.json"

CUSTOM_EMOJI_ID = "5231262796364137694"


# =========================================================
# RSS SOURCES
# =========================================================

RSS_SOURCES = [

    # =========================
    # 🇮🇷 KHABAR VARZESHI - IRAN
    # =========================

    # لیگ برتر ایران
    "https://www.khabarvarzeshi.com/rss/tp/63",

    # لیگ انگلیس
    "https://www.khabarvarzeshi.com/rss/tp/64",

    # لالیگا
    "https://www.khabarvarzeshi.com/rss/tp/65",

    # بوندسلیگا
    "https://www.khabarvarzeshi.com/rss/tp/66",

    # سری آ
    "https://www.khabarvarzeshi.com/rss/tp/67",

    # لیگ فرانسه
    "https://www.khabarvarzeshi.com/rss/tp/68",

    # لیگ قهرمانان اروپا
    "https://www.khabarvarzeshi.com/rss/tp/75",

    # لیگ اروپا
    "https://www.khabarvarzeshi.com/rss/tp/76",

    # بازیکنان ایرانی خارج از کشور
    "https://www.khabarvarzeshi.com/rss/tp/111",

    # لیگ یک ایران
    "https://www.khabarvarzeshi.com/rss/tp/110",

    # جام حذفی ایران
    "https://www.khabarvarzeshi.com/rss/tp/103",

    # =========================
    # 🇮🇷 SARPOOSH - IRAN FOOTBALL
    # =========================

    "https://www.sarpoosh.com/rss/football.xml",

    "https://www.sarpoosh.com/rss/iran-pro-league.xml",

    "https://www.sarpoosh.com/rss/football-transfers/iran.xml",

    # =========================
    # 🌍 WORLD FOOTBALL
    # =========================

    "https://www.sarpoosh.com/rss/football-world.xml",

    "https://www.sarpoosh.com/rss/champions-league.xml",

    "https://www.sarpoosh.com/rss/football-transfers/world.xml",
]


# =========================================================
# FOOTBALL KEYWORDS
# =========================================================

FOOTBALL_KEYWORDS = [

    # 🇮🇷 ایران
    "استقلال",
    "پرسپولیس",
    "سپاهان",
    "تراکتور",
    "ذوب آهن",
    "ذوب‌آهن",
    "گل گهر",
    "گل‌گهر",
    "فولاد",
    "نساجی",
    "ملوان",
    "آلومینیوم",
    "هوادار",
    "شمس آذر",
    "خیبر",
    "چادرملو",
    "استقلال خوزستان",
    "پیکان",
    "مس رفسنجان",
    "مس کرمان",
    "فجر سپاسی",
    "شهر خودرو",

    # تیم ملی
    "تیم ملی",
    "تیم‌ملی",
    "ایران",
    "ملی پوش",
    "ملی‌پوش",
    "امیر قلعه نویی",
    "قلعه نویی",
    "قلعه‌نویی",

    # مسابقات ایران
    "لیگ برتر",
    "لیگ برتر ایران",
    "جام حذفی",
    "لیگ یک",
    "آزادگان",
    "فوتبال ایران",
    "فوتبال کشور",

    # نقل و انتقالات
    "نقل و انتقالات",
    "نقل‌وانتقالات",
    "انتقالات",
    "خرید",
    "فروش",
    "قرارداد",
    "تمدید قرارداد",

    # بازیکنان
    "بازیکن",
    "مربی",
    "سرمربی",
    "دروازه بان",
    "دروازه‌بان",
    "مهاجم",
    "مدافع",
    "هافبک",

    # مسابقه
    "گل",
    "گلزنی",
    "گلزن",
    "بازی",
    "دیدار",
    "مسابقه",
    "دربی",
    "داربی",
    "نتیجه",
    "ترکیب",
    "داور",
    "کارت قرمز",
    "کارت زرد",
    "اخراج",
    "VAR",
    "وی ای آر",
    "تعویض",

    # 🌍 اروپا
    "رئال مادرید",
    "بارسلونا",
    "اتلتیکو مادرید",
    "منچستریونایتد",
    "منچستر سیتی",
    "لیورپول",
    "آرسنال",
    "چلسی",
    "تاتنهام",
    "بایرن مونیخ",
    "دورتموند",
    "اینتر",
    "میلان",
    "یوونتوس",
    "ناپولی",
    "پاری سن ژرمن",
    "پاری‌سن‌ژرمن",

    # لیگ‌ها
    "لیگ قهرمانان اروپا",
    "لیگ اروپا",
    "پریمیرلیگ",
    "لیگ انگلیس",
    "لالیگا",
    "سری آ",
    "بوندسلیگا",
    "لیگ فرانسه",

    # بازیکنان معروف
    "رونالدو",
    "مسی",
    "امباپه",
    "هالند",
    "نیمار",
    "صلاح",
    "بلینگام",
    "وینیسیوس",
]


# =========================================================
# NON FOOTBALL KEYWORDS
# =========================================================

NON_FOOTBALL_KEYWORDS = [

    "والیبال",
    "بسکتبال",
    "کشتی",
    "تنیس",
    "فوتسال",
    "بوکس",
    "دوومیدانی",
    "شنا",
    "وزنه برداری",
    "وزنه‌برداری",
    "فرمول یک",
    "موتورسواری",
]


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_title(text):

    if not text:
        return ""

    text = html.unescape(str(text))

    text = BeautifulSoup(text, "html.parser").get_text(" ")

    text = text.replace("‌", " ")

    text = text.replace("ي", "ی")
    text = text.replace("ى", "ی")
    text = text.replace("ك", "ک")

    text = text.lower()

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# SENT DATABASE
# =========================================================

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

    except Exception as e:

        print("SENT FILE ERROR:", e)

    return []


def save_sent_news(sent_news):

    try:

        with open(
            SENT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                sent_news[-2000:],
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("SAVE SENT ERROR:", e)


# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate_news(title, link, sent_news):

    normalized = normalize_title(title)

    title_key = "title:" + normalized

    for item in sent_news:

        if item == link:
            return True

        if item == title_key:
            return True

        if isinstance(item, dict):

            old_link = item.get("link", "")
            old_title = item.get("title", "")

            if old_link and old_link == link:
                return True

            if old_title:
                if normalize_title(old_title) == normalized:
                    return True

    return False


def register_sent_news(
    sent_news,
    title,
    link
):

    normalized = normalize_title(title)

    if link and link not in sent_news:
        sent_news.append(link)

    title_key = "title:" + normalized

    if title_key not in sent_news:
        sent_news.append(title_key)

    save_sent_news(sent_news)


# =========================================================
# FOOTBALL FILTER
# =========================================================

def is_football_news(title, summary=""):

    text = normalize_title(
        f"{title} {summary}"
    )

    # اگر صراحتاً مربوط به ورزش دیگری بود
    for bad in NON_FOOTBALL_KEYWORDS:

        if normalize_title(bad) in text:

            # اگر همزمان کلمه فوتبال ایران/فوتبال داشت
            if (
                "فوتبال" not in text
                and "استقلال" not in text
                and "پرسپولیس" not in text
                and "تیم ملی" not in text
            ):
                return False

    # خبرهای فوتبال ایران
    iran_words = [
        "استقلال",
        "پرسپولیس",
        "سپاهان",
        "تراکتور",
        "ذوب آهن",
        "ذوب‌آهن",
        "گل گهر",
        "گل‌گهر",
        "فولاد",
        "نساجی",
        "ملوان",
        "آلومینیوم",
        "هوادار",
        "شمس آذر",
        "خیبر",
        "چادرملو",
        "تیم ملی",
        "لیگ برتر",
        "جام حذفی",
        "لیگ یک",
        "آزادگان",
        "فوتبال ایران",
    ]

    for word in iran_words:

        if normalize_title(word) in text:
            return True

    # خبرهای فوتبال اروپا
    for word in FOOTBALL_KEYWORDS:

        if normalize_title(word) in text:
            return True

    # خود کلمه فوتبال
    if "فوتبال" in text:
        return True

    return False


# =========================================================
# GET RSS NEWS
# =========================================================

def get_news():

    all_news = []

    seen_urls = set()
    seen_titles = set()

    for rss_url in RSS_SOURCES:

        print("\nRSS:", rss_url)

        try:

            response = requests.get(
                rss_url,
                timeout=20,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                }
            )

            print(
                "RSS STATUS:",
                response.status_code
            )

            if response.status_code != 200:
                continue

            feed = feedparser.parse(
                response.content
            )

            for entry in feed.entries[:20]:

                title = (
                    entry.get("title")
                    or ""
                ).strip()

                link = (
                    entry.get("link")
                    or ""
                ).strip()

                summary = (
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                )

                if not title or not link:
                    continue

                normalized = normalize_title(
                    title
                )

                # تکراری داخل همین اجرا
                if link in seen_urls:
                    continue

                if normalized in seen_titles:
                    continue

                # فقط فوتبال
                if not is_football_news(
                    title,
                    summary
                ):
                    print(
                        "NOT FOOTBALL:",
                        title[:100]
                    )
                    continue

                seen_urls.add(link)
                seen_titles.add(normalized)

                all_news.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "source": rss_url,
                    "entry": entry,
                })

        except Exception as e:

            print(
                "RSS ERROR:",
                rss_url,
                e
            )

    print(
        "\nTOTAL UNIQUE FOOTBALL NEWS:",
        len(all_news)
    )

    return all_news


# =========================================================
# ARTICLE CONTENT
# =========================================================

def get_article_content(url):

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        print(
            "ARTICLE STATUS:",
            response.status_code
        )

        print(
            "ARTICLE CONTENT TYPE:",
            response.headers.get(
                "content-type"
            )
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript"
            ]
        ):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        return text

    except Exception as e:

        print(
            "ARTICLE ERROR:",
            e
        )

        return ""


# =========================================================
# APARAT VIDEO
# =========================================================

def get_aparat_video(url):

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        iframe = soup.find(
            "iframe",
            src=re.compile(
                r"aparat\.com"
            )
        )

        if not iframe:
            return None

        iframe_url = iframe.get(
            "src",
            ""
        )

        print(
            "APARAT IFRAME:",
            iframe_url
        )

        match = re.search(
            r"/videohash/([^/]+)",
            iframe_url
        )

        if not match:
            return None

        video_hash = match.group(1)

        print(
            "APARAT VIDEO HASH FOUND:",
            video_hash
        )

        api_url = (
            "https://www.aparat.com/"
            "api/fa/v1/video/video/show/"
            f"videohash/{video_hash}"
        )

        api_response = requests.get(
            api_url,
            timeout=20,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        print(
            "APARAT API STATUS:",
            api_response.status_code
        )

        if api_response.status_code != 200:
            return None

        data = api_response.json()

        # جستجوی لینک mp4
        def find_mp4(obj):

            if isinstance(obj, dict):

                for key, value in obj.items():

                    if isinstance(
                        value,
                        str
                    ):

                        if (
                            ".mp4" in value
                        ):
                            return value

                    result = find_mp4(
                        value
                    )

                    if result:
                        return result

            elif isinstance(
                obj,
                list
            ):

                for value in obj:

                    result = find_mp4(
                        value
                    )

                    if result:
                        return result

            return None

        mp4 = find_mp4(data)

        if mp4:

            print(
                "APARAT MP4 FOUND"
            )

            return mp4

    except Exception as e:

        print(
            "APARAT ERROR:",
            e
        )

    return None


# =========================================================
# IMAGE FROM RSS
# =========================================================

def get_entry_image(entry):

    try:

        media_content = entry.get(
            "media_content"
        )

        if media_content:

            for media in media_content:

                url = media.get(
                    "url"
                )

                if url:
                    return url

        media_thumbnail = entry.get(
            "media_thumbnail"
        )

        if media_thumbnail:

            for media in media_thumbnail:

                url = media.get(
                    "url"
                )

                if url:
                    return url

        enclosures = entry.get(
            "enclosures"
        )

        if enclosures:

            for enclosure in enclosures:

                url = enclosure.get(
                    "href"
                ) or enclosure.get(
                    "url"
                )

                if url:
                    return url

    except Exception as e:

        print(
            "IMAGE ERROR:",
            e
        )

    return None


# =========================================================
# TELEGRAM SEND
# =========================================================

def send_news(
    bot,
    news
):

    title = news["title"]
    link = news["link"]

    entry = news["entry"]

    print(
        "\nPROCESSING:",
        title
    )

    # -----------------------------------------------------
    # APARAT VIDEO
    # -----------------------------------------------------

    video_url = None

    try:

        video_url = get_aparat_video(
            link
        )

    except Exception as e:

        print(
            "VIDEO CHECK ERROR:",
            e
        )

    if video_url:

        try:

            media_response = requests.get(
                video_url,
                timeout=60,
                stream=True,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                }
            )

            print(
                "MEDIA STATUS:",
                media_response.status_code
            )

            print(
                "MEDIA CONTENT TYPE:",
                media_response.headers.get(
                    "content-type"
                )
            )

            if (
                media_response.status_code == 200
                and "video" in
                media_response.headers.get(
                    "content-type",
                    ""
                )
            ):

                temp_file = (
                    "temp_video.mp4"
                )

                with open(
                    temp_file,
                    "wb"
                ) as f:

                    for chunk in media_response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            f.write(chunk)

                print(
                    "✅ VIDEO DOWNLOADED"
                )

                caption = (
                    f"⚽️ <b>{html.escape(title)}</b>\n\n"
                    f"🔗 {html.escape(link)}\n\n"
                    f"@ligebartar24"
                )

                with open(
                    temp_file,
                    "rb"
                ) as video_file:

                    await_send_video(
                        bot,
                        video_file,
                        caption
                    )

                try:
                    os.remove(
                        temp_file
                    )
                except:
                    pass

                print(
                    "✅ VIDEO NEWS SENT:",
                    title
                )

                return True

        except Exception as e:

            print(
                "VIDEO SEND ERROR:",
                e
            )

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image_url = get_entry_image(
        entry
    )

    caption = (
        f"⚽️ <b>{html.escape(title)}</b>\n\n"
        f"🔗 {html.escape(link)}\n\n"
        f"@ligebartar24"
    )

    try:

        if image_url:

            await_send_photo(
                bot,
                image_url,
                caption
            )

            print(
                "✅ PHOTO SENT"
            )

        else:

            await_send_message(
                bot,
                caption
            )

            print(
                "✅ TEXT NEWS SENT"
            )

        print(
            "NEWS SENT:",
            title
        )

        return True

    except Exception as e:

        print(
            "TELEGRAM SEND ERROR:",
            e
        )

        return False


# =========================================================
# ASYNC HELPERS
# =========================================================

import asyncio


def await_send_message(
    bot,
    text
):

    asyncio.get_event_loop().run_until_complete(
        bot.send_message(
            chat_id=CHANNEL,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False
        )
    )


def await_send_photo(
    bot,
    photo,
    caption
):

    asyncio.get_event_loop().run_until_complete(
        bot.send_photo(
            chat_id=CHANNEL,
            photo=photo,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    )


def await_send_video(
    bot,
    video,
    caption
):

    asyncio.get_event_loop().run_until_complete(
        bot.send_video(
            chat_id=CHANNEL,
            video=video,
            caption=caption,
            parse_mode=ParseMode.HTML,
            supports_streaming=True
        )
    )


# =========================================================
# PROCESS RSS
# =========================================================

def process_rss_news():

    sent_news = load_sent_news()

    print(
        "\nSENT DATABASE COUNT:",
        len(sent_news)
    )

    news_list = get_news()

    sent_count = 0

    for news in news_list:

        title = news["title"]
        link = news["link"]

        # ---------------------------------------------
        # DUPLICATE
        # ---------------------------------------------

        if is_duplicate_news(
            title,
            link,
            sent_news
        ):

            print(
                "🚫 DUPLICATE SKIPPED:",
                title
            )

            continue

        print(
            "\nNEW NEWS:",
            title
        )

        bot = Bot(
            token=BOT_TOKEN
        )

        try:

            success = send_news(
                bot,
                news
            )

            if success:

                register_sent_news(
                    sent_news,
                    title,
                    link
                )

                sent_count += 1

                print(
                    "✅ SAVED TO DATABASE"
                )

                # جلوگیری از ارسال سریع تعداد زیاد
                time.sleep(2)

        except Exception as e:

            print(
                "PROCESS ERROR:",
                e
            )

    print(
        "\nRSS SENT COUNT:",
        sent_count
    )

    return sent_count


# =========================================================
# API FOOTBALL STATUS
# =========================================================

def check_api_status():

    if not API_FOOTBALL_KEY:

        print(
            "⚠️ API FOOTBALL KEY NOT FOUND"
        )

        return False

    url = (
        "https://v3.football.api-sports.io/status"
    )

    headers = {
        "x-apisports-key":
        API_FOOTBALL_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print(
            "API REQUEST: /status",
            response.status_code
        )

        data = response.json()

        print(
            "API RESPONSE:",
            data
        )

        if data.get("errors"):

            print(
                "⚠️ API ERROR:",
                data["errors"]
            )

            print(
                "RSS NEWS WILL CONTINUE"
            )

            return False

        result = data.get(
            "response"
        )

        if not isinstance(
            result,
            dict
        ):

            print(
                "⚠️ UNEXPECTED API RESPONSE"
            )

            return False

        return True

    except Exception as e:

        print(
            "API STATUS ERROR:",
            e
        )

        return False


# =========================================================
# MAIN
# =========================================================

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

    api_ok = check_api_status()

    if not api_ok:

        print(
            "⚠️ API FOOTBALL UNAVAILABLE"
        )

        print(
            "➡️ RSS NEWS WILL STILL RUN"
        )

    # ---------------------------------------------
    # RSS
    # ---------------------------------------------

    sent = process_rss_news()

    print(
        "\n================================"
    )

    print(
        f"✅ اجرای ربات تمام شد. "
        f"{sent} خبر جدید ارسال شد"
    )

    print(
        "================================"
    )


if __name__ == "__main__":

    main()
