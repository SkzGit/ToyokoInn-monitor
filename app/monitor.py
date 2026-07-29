from datetime import datetime, timedelta
from app.notify import notify
import json
import time
from pathlib import Path

from app.parser import check_room_status

BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS_FILE = BASE_DIR / "config" / "settings.json"
HOTELS_FILE = BASE_DIR / "data" / "hotels.json"
STATE_FILE = BASE_DIR / "data" / "state.json"
LOG_FILE = BASE_DIR / "data" / "monitor.log"
HISTORY_FILE = BASE_DIR / "data" / "history.json"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def is_monitor_enabled(settings):
    return settings.get("monitor_enabled", True)

def is_monitor_enabled(settings):
    return settings.get("monitor_enabled", True)

def load_state():

    if not STATE_FILE.exists():
        return {}

    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=4,
        )

def cleanup_state(state, settings):

    valid_keys = set()

    for stay in settings["dates"]:

        for candidate in stay["candidates"]:

            valid_keys.add(
                "|".join([
                    stay["date"],
                    str(stay["nights"]),
                    candidate["hotelId"],
                    candidate["roomSearch"],
                    "禁煙",
                    str(stay["people"]),
                    str(stay["rooms"]),
                ])
            )

            valid_keys.add(
                "|".join([
                    stay["date"],
                    str(stay["nights"]),
                    candidate["hotelId"],
                    candidate["roomSearch"],
                    "喫煙",
                    str(stay["people"]),
                    str(stay["rooms"]),
                ])
            )

    return {
        key: value
        for key, value in state.items()
        if key in valid_keys
    }

def write_log(message):

    now = datetime.now().strftime("%H:%M:%S")

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as f:

        f.write(f"[{now}] {message}\n")

def load_history():

    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_history(history):

    history = history[:100]

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=4,
        )

def main():

    settings = load_json(SETTINGS_FILE)

    if not is_monitor_enabled(settings):
        print("monitor_enabled=false のため監視を終了します。")
        return

    if not is_monitor_enabled(settings):
        print("monitor_enabled=false のため監視を終了します。")
        return

    hotels = load_json(HOTELS_FILE)

    state = load_state()
    history = load_history()

    state = cleanup_state(
        state,
        settings,
    )

    hotel_map = {
        hotel["id"]: hotel
        for hotel in hotels
    }

    print("=" * 50)
    print("東横INN 空室チェック開始")
    print("=" * 50)

    write_log("空室チェック開始")

    for stay in settings["dates"]:

        print()
        print(f"宿泊日 : {stay['date']}")
        print(f"人数   : {stay['people']}")
        print(f"部屋数 : {stay['rooms']}")

        for candidate in stay["candidates"]:

            hotel_id = candidate["hotelId"]

            if hotel_id not in hotel_map:

                print(f"ホテルID {hotel_id} が見つかりません。")
                continue

            hotel = hotel_map[hotel_id]

            hotel_name = hotel["name"]

            room_display = candidate["roomSearch"]

            for room in hotel["rooms"]:
                if room["search"] == candidate["roomSearch"]:
                    room_display = room["display"]
                    break

            hotel_url = (
                f"https://www.toyoko-inn.com/search/detail/{hotel_id}"
            )

            print()
            print("-" * 40)
            print(hotel_name)
            print(room_display)

            results = check_room_status(
                url=hotel_url,
                stay=stay,
                candidate=candidate,
            )

            if not results:
                print("空室なし")
                write_log(f"{hotel_name}｜{room_display}｜空室なし")

            for result in results:

                key = "|".join([
                    stay["date"],
                    str(stay["nights"]),
                    candidate["hotelId"],
                    result["room_name"],
                    result["smoking"],
                    str(stay["people"]),
                    str(stay["rooms"]),
                ])

                previous = key in state

                message = build_message(
                    hotel_name,
                    room_display,
                    candidate,
                    stay,
                    result,
                )

                if not previous:
                    print(
                        f"★ 新しく空室が出ました！（{result['smoking']}）"
                    )

                    write_log(
                        f"{hotel_name}｜{room_display}｜"
                        f"{result['smoking']}｜"
                        f"残り{result['remaining']}室｜"
                        f"{result['price']}円｜新規"
                    )

                    notify(message)

                    history.insert(
                        0,
                        {
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "hotel": hotel_name,
                            "room": room_display,
                            "smoking": result["smoking"],
                            "price": result["price"],
                            "remaining": result["remaining"],
                        },
                    )                    

                else:
                    print(
                        f"空室あり（継続）（{result['smoking']}）"
                    )

                    write_log(
                        f"{hotel_name}｜{room_display}｜"
                        f"{result['smoking']}｜"
                        f"残り{result['remaining']}室｜"
                        f"{result['price']}円｜継続"
                    )

                state[key] = {
                    "remaining": result["remaining"],
                    "price": result["price"],
                    "last_checked": datetime.now().isoformat(
                        timespec="seconds"
                    ),
                }

            time.sleep(1)

    save_state(state)
    save_history(history)

    print()
    print("=" * 50)
    print("空室チェック終了")
    print("=" * 50)

    write_log("空室チェック終了")

def build_message(
    hotel_name,
    room_display,
    candidate,
    stay,
    result,
):

    checkin = datetime.strptime(
        stay["date"],
        "%Y-%m-%d",
    )

    checkout = checkin + timedelta(
        days=stay["nights"],
    )

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    checkin_text = (
        f"{checkin.strftime('%Y-%m-%d')}"
        f"({weekdays[checkin.weekday()]})"
    )

    checkout_text = (
        f"{checkout.strftime('%Y-%m-%d')}"
        f"({weekdays[checkout.weekday()]})"
    )

    notify_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if result["smoking"] == "禁煙":
        smoking_icon = "🚭"
    elif result["smoking"] == "喫煙":
        smoking_icon = "🚬"
    else:
        smoking_icon = "❓"

    message = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🚨 **東横INN 空室通知** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕒【通知日時】{notify_time}\n\n"
        f"🏨【ホテル】{hotel_name}\n"
        f"📅【宿泊】"
        f"{checkin_text} ～ "
        f"{checkout_text}"
        f"（{stay['nights']}泊）\n"
        f"👥【人数】{stay['people']}名\n"
        f"🛏️【部屋】{room_display}\n"
        f"{smoking_icon}【部屋種別】{result['smoking']}\n"
    )

    if result["price"] is not None:
        message += (
            f"💰【料金】{result['price']}円\n"
        )

    if result["remaining"] is not None:
        message += (
            f"🟢【残室数】{result['remaining']}室\n"
        )

    message += (
        f"\n🔗 **予約ページ**\n"
        f"https://www.toyoko-inn.com/search/detail/{candidate['hotelId']}"
        "\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    return message

def run():

    while True:

        settings = load_json(SETTINGS_FILE)

        interval_hours = settings.get("intervalHours", 0)
        interval_minutes = settings.get("intervalMinutes", 30)

        interval_seconds = interval_hours * 3600 + interval_minutes * 60

        main()

        print()

        if interval_hours > 0 and interval_minutes > 0:
            print(f"{interval_hours}時間{interval_minutes}分後に再チェックします。")
        elif interval_hours > 0:
            print(f"{interval_hours}時間後に再チェックします。")
        else:
            print(f"{interval_minutes}分後に再チェックします。")

        print()

        time.sleep(interval_seconds)

if __name__ == "__main__":
    run()