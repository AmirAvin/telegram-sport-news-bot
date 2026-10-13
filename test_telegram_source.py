import requests
from bs4 import BeautifulSoup

POST_URL = "https://t.me/s/F0_TB/141223"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


def main():
    print("Checking public Telegram post...")
    print("Post:", POST_URL)

    try:
        response = requests.get(
            POST_URL,
            headers=HEADERS,
            timeout=30,
        )

        print("HTTP STATUS:", response.status_code)

        if response.status_code != 200:
            print("RESULT: Public post could not be loaded.")
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        messages = soup.select(
            ".tgme_widget_message"
        )

        print("MESSAGES FOUND:", len(messages))

        video_elements = soup.select(
            ".tgme_widget_message_video"
        )

        print("VIDEO ELEMENTS:", len(video_elements))

        video_sources = soup.select("video source")
        videos = soup.select("video")

        print("VIDEO TAGS:", len(videos))
        print("VIDEO SOURCES:", len(video_sources))

        direct_urls = set()

        for element in video_sources:
            src = element.get("src")
            if src and src.startswith("http"):
                direct_urls.add(src)

        for element in videos:
            src = element.get("src")
            if src and src.startswith("http"):
                direct_urls.add(src)

        print("DIRECT VIDEO URLS:", len(direct_urls))

        for url in direct_urls:
            print("VIDEO URL:", url[:200])

        if direct_urls:
            print("RESULT: A possible direct video URL was found.")
        elif video_elements:
            print(
                "RESULT: Video is indicated in the page, "
                "but no direct video URL was found."
            )
        else:
            print(
                "RESULT: No accessible video element was found."
            )

    except Exception as error:
        print("ERROR:", repr(error))


if __name__ == "__main__":
    main()
