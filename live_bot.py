import os
import requests

TOKEN = os.getenv("SPORTMONKS_TOKEN")

print("===== LIVE FOOTBALL BOT =====")

if not TOKEN:
    print("ERROR: SPORTMONKS_TOKEN NOT FOUND")
    raise SystemExit(1)

print("TOKEN: FOUND")

url = "https://api.sportmonks.com/v3/football/livescores"

headers = {
    "Authorization": TOKEN,
    "Accept": "application/json",
}

try:
    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print("HTTP STATUS:", response.status_code)
    print("RESPONSE LENGTH:", len(response.text))
    print("RESPONSE:")
    print(response.text[:5000])

except Exception as e:
    print("REQUEST ERROR:", repr(e))
    raise
