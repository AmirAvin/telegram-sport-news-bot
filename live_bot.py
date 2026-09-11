import os
import requests

token = os.getenv("SPORTMONKS_TOKEN")

result = []

result.append("=== SPORTMONKS TEST ===")

if not token:
    result.append("TOKEN: NOT FOUND")
else:
    result.append("TOKEN: FOUND")

    try:
        response = requests.get(
            "https://api.sportmonks.com/v3/football/livescores",
            headers={
                "Authorization": token,
                "Accept": "application/json"
            },
            timeout=30
        )

        result.append(f"HTTP STATUS: {response.status_code}")
        result.append(f"RESPONSE LENGTH: {len(response.text)}")

        try:
            data = response.json()

            result.append(f"RESULTS: {data.get('results')}")
            result.append(f"ERRORS: {data.get('errors')}")
            result.append(f"MESSAGE: {data.get('message')}")

        except Exception:
            result.append("JSON ERROR")
            result.append(response.text[:1000])

    except Exception as e:
        result.append(f"REQUEST ERROR: {repr(e)}")

with open("sportmonks_test.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(result))

print("\n".join(result))
