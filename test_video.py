import requests
import json

VIDEO_HASH = "mxh0449"

URLS = [
    f"https://www.aparat.com/api/video/v1/video/show/videohash/{VIDEO_HASH}",
    f"https://www.aparat.com/api/fa/v1/video/video/show/videohash/{VIDEO_HASH}",
    f"https://www.aparat.com/api/video/v1/video/show/{VIDEO_HASH}",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": f"https://www.aparat.com/v/{VIDEO_HASH}",
}


def main():

    print("=== APARAT API TEST ===")
    print("VIDEO HASH:", VIDEO_HASH)

    for url in URLS:

        print("\n--------------------------------")
        print("REQUEST:")
        print(url)

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            print("STATUS:", response.status_code)
            print(
                "CONTENT TYPE:",
                response.headers.get("content-type")
            )

            print(
                "RESPONSE LENGTH:",
                len(response.text)
            )

            print("\nRESPONSE:")

            try:

                data = response.json()

                print(
                    json.dumps(
                        data,
                        ensure_ascii=False,
                        indent=2
                    )[:10000]
                )

            except Exception:

                print(
                    response.text[:5000]
                )

        except Exception as e:

            print(
                "ERROR:",
                e
            )

    print("\n=== FINISHED ===")


if __name__ == "__main__":
    main()
