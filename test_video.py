import requests
import re
import json

URL = "https://www.aparat.com/v/mxh0449"

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

    print("OPENING APARAT:")
    print(URL)

    try:

        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("HTML LENGTH:", len(response.text))

        html = response.text

        print("\n=== SEARCH VIDEO DATA ===")

        keywords = [
            "video",
            "stream",
            "cdn",
            "file",
            "url",
            "quality",
            "video_id",
            "videoId",
            "videoHash",
            "hash"
        ]

        for keyword in keywords:

            print(
                keyword,
                "=>",
                html.lower().count(
                    keyword.lower()
                )
            )

        print("\n=== JSON-LIKE DATA ===")

        patterns = [
            r'"video[^"]*"\s*:\s*"[^"]+"',
            r'"stream[^"]*"\s*:\s*"[^"]+"',
            r'"cdn[^"]*"\s*:\s*"[^"]+"',
            r'"file[^"]*"\s*:\s*"[^"]+"',
            r'"url"\s*:\s*"[^"]+"',
            r'"src"\s*:\s*"[^"]+"',
        ]

        found = set()

        for pattern in patterns:

            matches = re.findall(
                pattern,
                html,
                re.IGNORECASE
            )

            for item in matches:

                item = item.replace(
                    "\\/",
                    "/"
                )

                if item not in found:

                    found.add(item)

                    print(
                        item[:2000]
                    )

        print("\n=== APARAT CDN LINKS ===")

        urls = re.findall(
            r'https?://[^"\']+',
            html
        )

        for url in urls:

            url = url.replace(
                "\\/",
                "/"
            )

            if any(
                word in url.lower()
                for word in [
                    "cdn",
                    "video",
                    "stream",
                    "aparat"
                ]
            ):

                print(
                    url[:2000]
                )

        print("\n=== FINISHED ===")

    except Exception as e:

        print(
            "ERROR:",
            e
        )


if __name__ == "__main__":
    main()
