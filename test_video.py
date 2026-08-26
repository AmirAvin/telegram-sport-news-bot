import requests
import re

URL = "https://www.khabarvarzeshi.com/news/554650/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
}


def main():

    print("OPENING:", URL)

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("HTML LENGTH:", len(response.text))

    html = response.text

    print("\n=== VIDEO WORDS ===")

    for word in [
        ".mp4",
        ".m3u8",
        "video",
        "videoUrl",
        "video_url",
        "video-url",
        "player",
        "source",
        "iframe",
        "jwplayer",
        "aparat"
    ]:

        count = html.lower().count(word.lower())

        print(
            word,
            "=>",
            count
        )

    print("\n=== MEDIA URLS ===")

    patterns = [
        r'https?://[^"\']+\.mp4[^"\']*',
        r'https?://[^"\']+\.m3u8[^"\']*',
        r'https?://[^"\']+video[^"\']*',
        r'https?://[^"\']+player[^"\']*',
    ]

    found = set()

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.IGNORECASE
        )

        for url in matches:

            url = url.replace(
                "\\/",
                "/"
            )

            if url not in found:

                found.add(url)

                print(
                    url[:1000]
                )

    print("\n=== FINISHED ===")


if __name__ == "__main__":
    main()
