import os
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

MAX_CAPTION_LENGTH = 1024
MAX_POSTS_PER_RUN = 20


# ==========================================
# STATE MANAGEMENT
# ==========================================

def load_last_post_id():
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))

        if isinstance(data, dict):
            value = data.get(
                "last_post_id",
                data.get("last_id")
            )
        else:
            value = None

        if value is not None:
            return int(value)

    except Exception as error:
        print("STATE READ ERROR:", repr(error))

    return None


def save_last_post_id(post_id):
    data = {
        "last_post_id": int(post_id)
    }

    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# ==========================================
# TELEGRAM SOURCE
# ==========================================

def get_source_posts():
    print("Reading source channel:", SOURCE_CHANNEL)

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

        video_urls = []

        for video in message.select("video"):
            src = video.get("src")

            if src and src.startswith("http"):
                video_urls.append(src)

            for source in video.select("source"):
                src = source.get("src")

                if src and src.startswith("http"):
                    video_urls.append(src)

        # Remove duplicate video URLs while preserving order.
        video_urls = list(dict.fromkeys(video_urls))

        posts.append({
            "id": post_id,
            "text": post_text,
            "video_urls": video_urls,
        })

    posts.sort(key=lambda item: item["id"])

    print("POSTS FOUND:", len(posts))

    return posts


# ==========================================
# VIDEO DOWNLOAD
# ==========================================

def download_video(video_url):
    print("Downloading video...")

    response = requests.get(
        video_url,
        headers=HEADERS,
        timeout=120,
        stream=True
    )

    if response.status_code != 200:
        print("VIDEO DOWNLOAD FAILED:", response.status_code)
        response.close()
        return None

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if "video" not in content_type and ".mp4" not in video_url.lower():
        print("NOT A VIDEO:", content_type)
        response.close()
        return None

    video_data = bytearray()

    try:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                video_data.extend(chunk)

    except Exception as error:
        print("VIDEO DOWNLOAD ERROR:", repr(error))
        response.close()
        return None

    finally:
        response.close()

    if not video_data:
        print("VIDEO FILE IS EMPTY")
        return None

    print("VIDEO DOWNLOADED:", len(video_data), "bytes")

    return bytes(video_data)


# ==========================================
# CAPTION
# ==========================================

def build_caption(post_text):
    suffix = f"{HASHTAGS}\n\n{SIGNATURE}"

    if not post_text:
        return suffix

    available_length = (
        MAX_CAPTION_LENGTH - len(suffix) - 2
    )

    text = post_text.strip()

    if len(text) > available_length:
        text = text[:available_length - 1].rstrip() + "…"

    return f"{text}\n\n{suffix}"


# ==========================================
# SEND VIDEO TO DESTINATION
# ==========================================

def send_video(video_data, caption):
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing from GitHub Secrets."
        )

    api_url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    )

    print("Sending video to:", DESTINATION)

    response = requests.post(
        api_url,
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
        },
        timeout=180
    )

    try:
        result = response.json()
    except ValueError:
        print("TELEGRAM RESPONSE:", response.text[:500])
        return False

    if response.status_code == 200 and result.get("ok"):
        print("VIDEO SENT SUCCESSFULLY")
        return True

    print("TELEGRAM SEND FAILED:")
    print(json.dumps(result, ensure_ascii=False))

    return False


# ==========================================
# MAIN PROCESS
# ==========================================

def main():
    print("=" * 45)
    print("FOOTBALL VIDEO BOT STARTED")
    print("SOURCE:", SOURCE_CHANNEL)
    print("DESTINATION:", DESTINATION)
    print("=" * 45)

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

    # First run: save the newest post ID without forwarding
    # old posts. This prevents a flood of historical videos.
    if last_post_id is None:
        newest_id = max(post["id"] for post in posts)

        save_last_post_id(newest_id)

        print("FIRST RUN: BASELINE SAVED")
        print("LAST POST ID:", newest_id)
        print("No old posts were forwarded.")
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

        video_urls = post["video_urls"]

        # Skip posts without video.
        if not video_urls:
            print("SKIPPED: No video in this post.")

            save_last_post_id(post_id)
            last_post_id = post_id
            continue

        video_data = None

        # Try each video URL until one downloads successfully.
        for video_url in video_urls:
            video_data = download_video(video_url)

            if video_data:
                break

        # If a video exists but cannot be downloaded,
        # stop here so this post can be retried next run.
        if not video_data:
            print("STOPPED: Video could not be downloaded.")
            break

        caption = build_caption(post["text"])

        success = send_video(video_data, caption)

        if not success:
            print("STOPPED: Telegram did not accept the video.")
            break

        # Save progress after each processed post.
        save_last_post_id(post_id)
        last_post_id = post_id

        print("POST COMPLETED:", post_id)

        time.sleep(2)

    print("=" * 45)
    print("BOT FINISHED")
    print("=" * 45)


if __name__ == "__main__":
    main()
