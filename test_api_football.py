import os
import requests

API_KEY = os.getenv("API_FOOTBALL_KEY")

URL = "https://v3.football.api-sports.io/status"

headers = {
    "x-apisports-key": API_KEY
}

print("=" * 50)
print("API-FOOTBALL CONNECTION TEST")
print("=" * 50)

if not API_KEY:
    print("❌ API_FOOTBALL_KEY پیدا نشد")
    raise SystemExit(1)

try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

    print("HTTP STATUS:", response.status_code)
    print("-" * 50)

    data = response.json()

    print("API RESPONSE:")
    print(data)

    print("-" * 50)

    if response.status_code == 200 and not data.get("errors"):
        print("✅ اتصال به API-FOOTBALL موفق بود")
        print("✅ API KEY معتبر است")
    else:
        print("❌ API پاسخ خطا داد")
        print("ERRORS:", data.get("errors"))

except Exception as error:
    print("❌ CONNECTION ERROR:")
    print(error)
