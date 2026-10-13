import requests
from bs4 import BeautifulSoup

CHANNEL = "F0_TB"
POST_ID = "141223"

URL = f"https://t.me/s/{CHANNEL}/{POST_ID}"

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
            URL,
            headers=HEADERS,
            timeout=30,
        )

        print("PAGE STATUS:", response.status_code)

        if response.status_code != 200:
            print("RESULT: PAGE FAILED")
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

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

            try:
                video_response = requests.get(
                    video_url,
                    headers=HEADERS,
                    stream=True,
                    timeout=30,
                    headers_extra=None,
                )
            except TypeError:
                video_response = requests.get(
                    video_url,
                    headers=HEADERS,
                    stream=True,
                    timeout=30,
                )

            print("VIDEO HTTP STATUS:", video_response.status_code)
            print(
                "CONTENT TYPE:",
                video_response.headers.get("Content-Type", "unknown")
            )
            print(
                "CONTENT LENGTH:",
                video_response.headers.get("Content-Length", "unknown")
            )

            video_response.close()

            if (
                video_response.status_code == 200
                and "video" in video_response.headers.get(
                    "Content-Type", ""
                ).lower()
            ):
                print("RESULT: VIDEO DOWNLOAD ACCESS CONFIRMED")
                return

        print("RESULT: VIDEO DOWNLOAD NOT CONFIRMED")

    except Exception as error:
        print("ERROR:", repr(error))


if __name__ == "__main__":
    main()
