import os
import requests

token = os.getenv("SPORTMONKS_TOKEN")

print("=== LIVE BOT TEST ===")

if not token:
    print("TOKEN NOT FOUND")
    raise SystemExit(1)

print("TOKEN FOUND")

url = "https://api.sportmonks.com/v3/football/livescores"

response = requests.get(
    url,
    headers={"Authorization": token},
    timeout=30
)

print("STATUS:", response.status_code)

try:
    data = response.json()
    print("RESULTS:", data.get("results"))
    print("MESSAGE:", data.get("message"))
    print("ERRORS:", data.get("errors"))
except Exception:
    print("RAW:", response.text[:1000])
