import requests
import re

URL = "https://www.aparat.com/video/video/embed/videohash/mxh0449/vt/frame?recom=self"

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
        print("FINAL URL:", response.url)
        print(
            "CONTENT TYPE:",
            response.headers.get("content-type")
        )
        print(
            "HTML LENGTH:",
            len(response.text)
        )

        html = response.text

        print("\n=== VIDEO URL SEARCH ===")

        patterns = [
            r'https?://[^"\']+\.mp4[^"\']*',
            r'https?://[^"\']+\.m3u8[^"\']*',
            r'https?://[^"\']+\.webm[^"\']*',
            r'https?://[^"\']+\.m4v[^"\']*',
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
                        "VIDEO URL:",
                        url[:1500]
                    )

        print("\n=== APARAT DATA ===")

        for keyword in [
            "file",
            "video",
            "videoUrl",
            "360",
            "480",
            "720",
            "1080",
            "src",
            "cdn"
        ]:

            count = html.lower().count(
                keyword.lower()
            )

            print(
                keyword,
                "=>",
                count
            )

        print("\n=== FINISHED ===")

    except Exception as e:

        print(
            "ERROR:",
            e
        )


if __name__ == "__main__":
    main()
