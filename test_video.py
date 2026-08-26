import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.khabarvarzeshi.com/news/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def main():

    print("OPENING:", URL)

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    print("STATUS:", response.status_code)
    print("CONTENT TYPE:", response.headers.get("content-type"))

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    print("\n=== VIDEO TAGS ===")

    videos = soup.find_all("video")

    for video in videos:

        print("VIDEO:", video)

        for source in video.find_all("source"):

            print(
                "SOURCE:",
                source.get("src")
                or source.get("data-src")
            )

    print("\n=== OG VIDEO ===")

    for tag in soup.find_all("meta"):

        prop = tag.get("property", "")

        if "video" in prop.lower():

            print(
                prop,
                ":",
                tag.get("content")
            )

    print("\n=== MP4 LINKS ===")

    found = set()

    for match in re.findall(
        r'https?://[^"\']+?\.mp4[^"\']*',
        response.text,
        re.IGNORECASE
    ):

        if match not in found:

            found.add(match)

            print(match)

    print("\n=== FINISHED ===")


if __name__ == "__main__":
    main()
