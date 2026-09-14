import os
import requests

SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

LEAGUE_ID = 902

BASE_URL = "https://api.sportmonks.com/v3/football"


def get_live_matches():
    url = f"{BASE_URL}/livescores"

    params = {
        "api_token": SPORTMONKS_TOKEN,
        "include": "participants;league;events",
        "filters": f"leagueIds:{LEAGUE_ID}",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text[:5000])

    if response.status_code != 200:
        return []

    data = response.json()

    return data.get("data", [])


def main():

    print("=" * 50)
    print("🇮🇷 IRAN LIVE FOOTBALL BOT")
    print("=" * 50)

    if not SPORTMONKS_TOKEN:
        print("❌ SPORTMONKS_TOKEN NOT FOUND")
        return

    if not CHANNEL_ID:
        print("❌ CHANNEL_ID NOT FOUND")
        return

    print("✅ SPORTMONKS TOKEN FOUND")
    print("✅ CHANNEL ID FOUND")
    print("🏆 LEAGUE ID:", LEAGUE_ID)

    try:

        matches = get_live_matches()

        print()
        print("LIVE MATCHES FOUND:", len(matches))

        if not matches:
            print("ℹ️ NO LIVE MATCHES RIGHT NOW")
            return

        for match in matches:

            print()
            print("-" * 50)

            print(
                "MATCH ID:",
                match.get("id")
            )

            print(
                "NAME:",
                match.get("name")
            )

            print(
                "MINUTE:",
                match.get("minute")
            )

            print(
                "STATE:",
                match.get("state")
            )

            participants = match.get(
                "participants",
                []
            )

            for team in participants:

                print(
                    "TEAM:",
                    team.get("name")
                )

            events = match.get(
                "events",
                []
            )

            print(
                "EVENTS:",
                len(events)
            )

            for event in events:

                print(
                    "EVENT:",
                    event
                )

    except Exception as e:

        print(
            "❌ ERROR:",
            repr(e)
        )


if __name__ == "__main__":
    main()
