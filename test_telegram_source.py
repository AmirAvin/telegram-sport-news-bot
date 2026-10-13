import requests
from bs4 import BeautifulSoup

CHANNEL = "F0_TB"
POST_ID = "141223"

POST_URL = f"https://t.me/s/{CHANNEL}/{POST_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


def main():
    print("CHECKING SPECIFIC TELEGRAM POST")
    print("POST:", f"https://t.me/{CHANNEL}/{POST_ID}")

    try:
        response = requests.get(
            POST_URL,
            headers=HEADERS,
            timeout=30
        )

        print("PAGE STATUS:", response.status_code)

        if response.status_code != 200:
            print("RESULT: PAGE FAILED")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        target = None

        for message in soup.select(".tgme_widget_message"):
            post_ref = message.get("data-post", "")

            if post_ref == f"{CHANNEL}/{POST_ID}":
                target = message
                break

        if target is None:
            print("RESULT: TARGET POST NOT FOUND IN PAGE")
            print("The post may not be included in this preview.")
            return

        text_element = target.select_one(
            ".tgme_widget_message_text"
        )

        post_text = (
            text_element.get_text(" ", strip=True)
            if text_element
            else ""
        )

        print("POST TEXT FOUND:", bool(post_text))
        print("TEXT LENGTH:", len(post_text))

        video_urls = set()

        for video in target.select("video"):
            src = video.get("src")

            if src and src.startswith("http"):
                video_urls.add(src)

            for source in video.select("source"):
                src = source.get("src")

                if src and src.startswith("http"):
                    video_urls.add(src)

        print("VIDEO URLS FOUND:", len(video_urls))

        if not video_urls:
            print("RESULT: NO DIRECT VIDEO URL FOR THIS POST")
            return

        for index, video_url in enumerate(video_urls, 1):
            print(f"TESTING VIDEO {index}")

            video_response = requests.get(
                video_url,
                headers=HEADERS,
                stream=True,
                timeout=30
            )

            status = video_response.status_code
            content_type = video_response.headers.get(
                "Content-Type",
                "unknown"
            )
            content_length = video_response.headers.get(
                "Content-Length",
                "unknown"
            )

            print("VIDEO HTTP STATUS:", status)
            print("CONTENT TYPE:", content_type)
            print("CONTENT LENGTH:", content_length)

            video_response.close()

            if status == 200 and (
                "video" in content_type.lower()
                or ".mp4" in video_url.lower()
            ):
                print("RESULT: VIDEO DOWNLOAD ACCESS CONFIRMED")
                return

        print("RESULT: VIDEO DOWNLOAD NOT CONFIRMED")

    except Exception as error:
        print("ERROR:", repr(error))


if __name__ == "__main__":
    main()
