import os
import json
import time
import requests

# ============================================================
# SETTINGS
# ============================================================

SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Persian Gulf Pro League
LEAGUE_ID = 902

BASE_URL = "https://api.sportmonks.com/v3/football"

STATE_FILE = "live_state.json"

REQUEST_TIMEOUT = 30


# ============================================================
# STATE
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "matches": {},
            "events": {}
        }

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        return data

    except Exception as e:
        print("STATE LOAD ERROR:", repr(e))

        return {
            "matches": {},
            "events": {}
        }


def save_state(state):

    try:
        with open(
            STATE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2
            )

        print("STATE SAVED")

    except Exception as e:
        print("STATE SAVE ERROR:", repr(e))


# ============================================================
# SPORTMONKS REQUEST
# ============================================================

def sportmonks_get(endpoint, params=None):

    if params is None:
        params = {}

    params["api_token"] = SPORTMONKS_TOKEN

    url = f"{BASE_URL}/{endpoint}"

    try:

        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        print()
        print("SPORTMONKS REQUEST:")
        print(url)
        print("STATUS:", response.status_code)

        if response.status_code != 200:

            print(
                "SPORTMONKS ERROR:",
                response.text[:3000]
            )

            return None

        data = response.json()

        return data

    except Exception as e:

        print(
            "SPORTMONKS REQUEST ERROR:",
            repr(e)
        )

        return None


# ============================================================
# GET INPLAY MATCHES
# ============================================================

def get_live_matches():

    data = sportmonks_get(
        "livescores/inplay",
        {
            "include":
                "participants;league;state;scores;events"
        }
    )

    if not data:
        return []

    matches = data.get(
        "data",
        []
    )

    if isinstance(matches, dict):
        matches = [matches]

    iran_matches = []

    for match in matches:

        league_id = match.get(
            "league_id"
        )

        if str(league_id) == str(LEAGUE_ID):

            iran_matches.append(match)

    return iran_matches


# ============================================================
# TEAM NAMES
# ============================================================

def get_team_names(match):

    home = "تیم میزبان"
    away = "تیم مهمان"

    participants = match.get(
        "participants",
        []
    )

    for participant in participants:

        name = participant.get(
            "name",
            "Unknown"
        )

        meta = participant.get(
            "meta",
            {}
        )

        location = meta.get(
            "location"
        )

        if location == "home":
            home = name

        elif location == "away":
            away = name

    return home, away


# ============================================================
# SCORE
# ============================================================

def get_score(match):

    home_score = 0
    away_score = 0

    scores = match.get(
        "scores",
        []
    )

    for score in scores:

        description = str(
            score.get(
                "description",
                ""
            )
        ).upper()

        score_value = score.get(
            "score",
            {}
        )

        goals = score_value.get(
            "goals"
        )

        if goals is None:
            continue

        if description in [
            "CURRENT",
            "2ND_HALF",
            "1ST_HALF"
        ]:

            participant = score.get(
                "participant_id"
            )

            participants = match.get(
                "participants",
                []
            )

            for team in participants:

                if team.get("id") == participant:

                    location = (
                        team.get(
                            "meta",
                            {}
                        ).get("location")
                    )

                    if location == "home":
                        home_score = goals

                    elif location == "away":
                        away_score = goals

    return home_score, away_score


# ============================================================
# EVENT TEXT
# ============================================================

def event_text(
    match,
    event
):

    home, away = get_team_names(
        match
    )

    event_type = event.get(
        "type_id"
    )

    minute = event.get(
        "minute"
    )

    extra_minute = event.get(
        "extra_minute"
    )

    player_name = event.get(
        "player_name"
    )

    result = event.get(
        "result"
    )

    info = event.get(
        "info"
    )

    addition = event.get(
        "addition"
    )

    minute_text = ""

    if minute is not None:

        minute_text = f"⏱ دقیقه {minute}"

        if extra_minute:
            minute_text += f"+{extra_minute}"

    # ========================================================
    # GOAL
    # ========================================================

    if event_type == 14:

        text = "⚽ گل!"

        if player_name:
            text += f"\n👤 {player_name}"

        if minute_text:
            text += f"\n{minute_text}"

        if result:
            text += f"\n📊 نتیجه: {result}"

        return text

    # ========================================================
    # CARD
    # ========================================================

    if event_type == 17:

        card = str(
            result or info or addition or ""
        ).lower()

        if "red" in card or "قرمز" in card:
            icon = "🟥"
            title = "کارت قرمز"

        else:
            icon = "🟨"
            title = "کارت زرد"

        text = f"{icon} {title}"

        if player_name:
            text += f"\n👤 {player_name}"

        if minute_text:
            text += f"\n{minute_text}"

        return text

    # ========================================================
    # SUBSTITUTION
    # ========================================================

    if event_type == 18:

        text = "🔄 تعویض"

        if player_name:
            text += f"\n⬅️ {player_name}"

        if addition:
            text += f"\n➡️ {addition}"

        if minute_text:
            text += f"\n{minute_text}"

        return text

    # ========================================================
    # VAR
    # ========================================================

    if event_type == 10:

        text = "🖥️ VAR"

        if info:
            text += f"\n📌 {info}"

        if addition:
            text += f"\n📌 {addition}"

        if minute_text:
            text += f"\n{minute_text}"

        return text

    # ========================================================
    # PENALTY
    # ========================================================

    if event_type == 16:

        text = "⚽ پنالتی"

        if player_name:
            text += f"\n👤 {player_name}"

        if minute_text:
            text += f"\n{minute_text}"

        return text

    return None


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(text):

    if not BOT_TOKEN:
        print("BOT_TOKEN NOT FOUND")
        return False

    if not CHANNEL_ID:
        print("CHANNEL_ID NOT FOUND")
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHANNEL_ID,
        "text": text
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        print(
            "TELEGRAM STATUS:",
            response.status_code
        )

        print(
            "TELEGRAM RESPONSE:",
            response.text[:2000]
        )

        return response.status_code == 200

    except Exception as e:

        print(
            "TELEGRAM ERROR:",
            repr(e)
        )

        return False


# ============================================================
# PROCESS MATCH
# ============================================================

def process_match(
    match,
    state
):

    fixture_id = str(
        match.get("id")
    )

    home, away = get_team_names(
        match
    )

    home_score, away_score = get_score(
        match
    )

    print()
    print("=" * 60)
    print(
        f"{home} {home_score} - "
        f"{away_score} {away}"
    )

    print(
        "FIXTURE:",
        fixture_id
    )

    print(
        "STATE:",
        match.get("state")
    )

    print(
        "EVENT COUNT:",
        len(
            match.get(
                "events",
                []
            )
        )
    )

    # ========================================================
    # MATCH STATE
    # ========================================================

    previous = state["matches"].get(
        fixture_id
    )

    current_state_id = match.get(
        "state_id"
    )

    if previous is None:

        state["matches"][fixture_id] = {
            "state_id": current_state_id,
            "home_score": home_score,
            "away_score": away_score
        }

    else:

        old_state_id = previous.get(
            "state_id"
        )

        if old_state_id != current_state_id:

            print(
                "STATE CHANGED:",
                old_state_id,
                "->",
                current_state_id
            )

            state["matches"][fixture_id][
                "state_id"
            ] = current_state_id

        if (
            previous.get("home_score")
            != home_score
            or
            previous.get("away_score")
            != away_score
        ):

            print(
                "SCORE CHANGED:",
                previous.get("home_score"),
                previous.get("away_score"),
                "->",
                home_score,
                away_score
            )

            state["matches"][fixture_id][
                "home_score"
            ] = home_score

            state["matches"][fixture_id][
                "away_score"
            ] = away_score

    # ========================================================
    # EVENTS
    # ========================================================

    events = match.get(
        "events",
        []
    )

    for event in events:

        event_id = event.get(
            "id"
        )

        if event_id is None:
            continue

        event_key = str(event_id)

        if event_key in state["events"]:

            continue

        text = event_text(
            match,
            event
        )

        if not text:

            state["events"][event_key] = True
            continue

        message = (
            f"🇮🇷 لیگ برتر ایران\n\n"
            f"⚽ {home} "
            f"{home_score} - "
            f"{away_score} "
            f"{away}\n\n"
            f"{text}\n\n"
            f"@ligebartar24"
        )

        print()
        print(
            "NEW EVENT:",
            message
        )

        if send_telegram(message):

            state["events"][event_key] = True

            save_state(
                state
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("🇮🇷 IRAN LIVE FOOTBALL BOT")
    print("=" * 60)

    if not SPORTMONKS_TOKEN:

        print(
            "❌ SPORTMONKS_TOKEN NOT FOUND"
        )

        return

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN NOT FOUND"
        )

        return

    if not CHANNEL_ID:

        print(
            "❌ CHANNEL_ID NOT FOUND"
        )

        return

    print("✅ SPORTMONKS TOKEN FOUND")
    print("✅ BOT TOKEN FOUND")
    print("✅ CHANNEL ID FOUND")
    print("🏆 LEAGUE:", LEAGUE_ID)

    state = load_state()

    matches = get_live_matches()

    print()
    print(
        "🇮🇷 IRAN LIVE MATCHES:",
        len(matches)
    )

    if not matches:

        print(
            "ℹ️ No Iranian live matches right now."
        )

        save_state(
            state
        )

        return

    for match in matches:

        try:

            process_match(
                match,
                state
            )

        except Exception as e:

            print(
                "MATCH ERROR:",
                repr(e)
            )

    save_state(
        state
    )

    print()
    print("=" * 60)
    print("✅ LIVE BOT FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
