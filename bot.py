import os
import re
import json
import time
import requests

from pathlib import Path
from bs4 import BeautifulSoup


# ==========================================
# SETTINGS
# ==========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
DESTINATION = os.environ.get("CHANNEL", "@ligebartar24").strip()

SOURCE_CHANNEL = "F0_TB"
SOURCE_URL = f"https://t.me/s/{SOURCE_CHANNEL}"

STATE_FILE = Path("telegram_last_run.json")

HASHTAGS = "#فوتبال #گل"
SIGNATURE = "⚽️ @ligebartar24"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}

MAX_POSTS_PER_RUN = 20
MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096


# ==========================================
# STATE
# ==========================================

def load_last_post_id():
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            value = data.get(
                "last_post_id",
                data.get("last_id")
            )

            if value is not None:
                return int(value)

    except Exception as error:
        print("STATE READ ERROR:", repr(error))

    return None


def save_last_post_id(post_id):
    STATE_FILE.write_text(
        json.dumps(
            {"last_post_id": int(post_id)},
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# ==========================================
# READ SOURCE CHANNEL
# ==========================================

def get_source_posts():
    print("Reading source:", SOURCE_CHANNEL)

    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=40
    )

    print("SOURCE HTTP STATUS:", response.status_code)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    posts = []

    for message in soup.select(".tgme_widget_message"):
        reference = message.get("data-post", "")

        if not reference.startswith(SOURCE_CHANNEL + "/"):
            continue

        try:
            post_id = int(reference.rsplit("/", 1)[1])
        except (ValueError, IndexError):
            continue

        text_element = message.select_one(
            ".tgme_widget_message_text"
        )

        post_text = (
            text_element.get_text("\n", strip=True)
            if text_element
            else ""
        )

        # Find videos
        video_urls = []

        for video in message.select("video"):
            src = video.get("src")

            if src and src.startswith("http"):
                video_urls.append(src)

            for source in video.select("source"):
                src = source.get("src")

                if src and src.startswith("http"):
                    video_urls.append(src)

        video_urls = list(dict.fromkeys(video_urls))

        # Find photos
        photo_urls = []

        for photo in message.select(
            ".tgme_widget_message_photo_wrap"
        ):
            style = photo.get("style", "")

            match = re.search(
                r"""url\(['"]?(.*?)['"]?\)""",
                style
            )

            if match:
                photo_url = match.group(1).strip()

                if photo_url.startswith("http"):
                    photo_urls.append(photo_url)

        photo_urls = list(dict.fromkeys(photo_urls))

        posts.append({
            "id": post_id,
            "text": post_text,
            "video_urls": video_urls,
            "photo_urls": photo_urls,
        })

    posts.sort(key=lambda item: item["id"])

    print("POSTS FOUND:", len(posts))

    return posts


# ==========================================
# DOWNLOAD MEDIA
# ==========================================

def download_media(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=120
        )

        if response.status_code != 200:
            print("MEDIA DOWNLOAD FAILED:", response.status_code)
            return None

        if not response.content:
            print("MEDIA FILE EMPTY")
            return None

        return response.content

    except Exception as error:
        print("MEDIA DOWNLOAD ERROR:", repr(error))
        return None


# ==========================================
# CAPTIONS AND TEXT
# ==========================================

def build_caption(post_text):
    suffix = f"{HASHTAGS}\n\n{SIGNATURE}"
    text = (post_text or "").strip()

    available = MAX_CAPTION_LENGTH - len(suffix) - 2

    if len(text) > available:
        text = text[:available - 1].rstrip() + "…"

    if text:
        return f"{text}\n\n{suffix}"

    return suffix


def build_text(post_text):
    suffix = f"{HASHTAGS}\n\n{SIGNATURE}"
    text = (post_text or "").strip()

    available = MAX_MESSAGE_LENGTH - len(suffix) - 2

    if len(text) > available:
        text = text[:available - 1].rstrip() + "…"

    if text:
        return f"{text}\n\n{suffix}"

    return suffix


# ==========================================
# TELEGRAM API
# ==========================================

def telegram_request(method, data=None, files=None):
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is missing.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    try:
        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=180
        )

        try:
            result = response.json()
        except ValueError:
            print("INVALID TELEGRAM RESPONSE:", response.text[:300])
            return False

        if response.status_code == 200 and result.get("ok"):
            print("TELEGRAM SEND SUCCESS:", method)
            return True

        print(
            "TELEGRAM SEND FAILED:",
            json.dumps(result, ensure_ascii=False)
        )

    except Exception as error:
        print("TELEGRAM API ERROR:", repr(error))

    return False


def send_text(text):
    return telegram_request(
        "sendMessage",
        data={
            "chat_id": DESTINATION,
            "text": text,
        }
    )


def send_photo(photo_data, caption):
    return telegram_request(
        "sendPhoto",
        data={
            "chat_id": DESTINATION,
            "caption": caption,
        },
        files={
            "photo": (
                "football_photo.jpg",
                photo_data,
                "image/jpeg"
            )
        }
    )


def send_video(video_data, caption):
    return telegram_request(
        "sendVideo",
        data={
            "chat_id": DESTINATION,
            "caption": caption,
            "supports_streaming": "true",
        },
        files={
            "video": (
                "football_video.mp4",
                video_data,
                "video/mp4"
            )
        }
    )


# ==========================================
# PROCESS POSTS
# ==========================================

def main():
    print("=" * 40)
    print("FOOTBALL NEWS BOT STARTED")
    print("SOURCE:", SOURCE_CHANNEL)
    print("DESTINATION:", DESTINATION)
    print("=" * 40)

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is missing.")
        return

    try:
        posts = get_source_posts()
    except Exception as error:
        print("SOURCE ERROR:", repr(error))
        return

    if not posts:
        print("No posts found.")
        return

    last_post_id = load_last_post_id()

    # First run: save the latest post ID.
    # Do not send old posts.
    if last_post_id is None:
        newest_id = max(post["id"] for post in posts)
        save_last_post_id(newest_id)

        print("FIRST RUN: BASELINE SAVED")
        print("LAST POST ID:", newest_id)
        print("Old posts were not sent.")
        return

    new_posts = [
        post for post in posts
        if post["id"] > last_post_id
    ]

    if not new_posts:
        print("No new posts.")
        return

    new_posts = new_posts[:MAX_POSTS_PER_RUN]

    print("NEW POSTS:", len(new_posts))

    for post in new_posts:
        post_id = post["id"]

        print("-" * 40)
        print("PROCESSING POST:", post_id)

        caption = build_caption(post["text"])
        text = build_text(post["text"])

        success = False

        # Video post
        if post["video_urls"]:
            for video_url in post["video_urls"]:
                media = download_media(video_url)

                if media:
                    success = send_video(media, caption)
                    break

        # Photo post
        elif post["photo_urls"]:
            for photo_url in post["photo_urls"]:
                media = download_media(photo_url)

                if media:
                    success = send_photo(media, caption)
                    break

        # Text-only post
        elif post["text"].strip():
            success = send_text(text)

        else:
            print("SKIPPED: No readable text or supported media.")
            save_last_post_id(post_id)
            last_post_id = post_id
            continue

        # Do not mark a post as processed if sending failed.
        if not success:
            print("STOPPED: Post was not sent:", post_id)
            break

        save_last_post_id(post_id)
        last_post_id = post_id

        print("POST SENT SUCCESSFULLY:", post_id)

        time.sleep(2)

    print("=" * 40)
    print("BOT FINISHED")
    print("=" * 40)


if __name__ == "__main__":
    main()
