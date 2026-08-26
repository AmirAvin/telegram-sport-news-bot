import requests
import re

URL = "https://www.aparat.com/v/mxh0449"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
}


def main():

    print("OPENING APARAT VIDEO:")
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

        print("\n=== MP4 SEARCH ===")

        found = set()

        patterns = [
            r'https?://[^"\']+\.mp4[^"\']*',
            r'https?:\\?/\\?/[^"\']+\.mp4[^"\']*',
            r'"url"\s*:\s*"([^"]+)"',
            r'"src"\s*:\s*"([^"]+)"',
            r'"file"\s*:\s*"([^"]+)"',
        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                html,
                re.IGNORECASE
            )

            for match in matches:

                if isinstance(match, tuple):
                    match = match[0]

                url = match.replace(
                    "\\/",
                    "/"
                )

                if (
                    "mp4" in url.lower()
                    or "video" in url.lower()
                    or "cdn" in url.lower()
                ):

                    if url not in found:

                        found.add(url)

                        print(
                            "FOUND:",
                            url[:2000]
                        )

        print("\n=== IMPORTANT WORDS ===")

        for keyword in [
            "video",
            "file",
            "src",
            "url",
            "cdn",
            "stream",
            "quality",
            "360",
            "480",
            "720",
            "1080",
            "m3u8",
            "mp4"
        ]:

            print(
                keyword,
                "=>",
                html.lower().count(
                    keyword.lower()
                )
            )

        print("\n=== HTML PREVIEW ===")

        print(
            html[:3000]
        )

        print("\n=== FINISHED ===")

    except Exception as e:

        print(
            "ERROR:",
            e
        )


if __name__ == "__main__":
    main()
