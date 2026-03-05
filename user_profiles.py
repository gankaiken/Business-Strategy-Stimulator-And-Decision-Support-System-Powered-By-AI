import json
import os

USER_JSON = "data/users.json"


def _ensure_user_json():
    folder = os.path.dirname(USER_JSON)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    if not os.path.exists(USER_JSON):
        with open(USER_JSON, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)


def load_users():
    _ensure_user_json()
    with open(USER_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(USER_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def select_user():
    users = load_users()

    user_id = input("Enter user ID: ").strip()
    if not user_id:
        raise SystemExit("User ID cannot be empty.")

    if user_id not in users:
        print(f"👤 New user '{user_id}' created.")
        users[user_id] = {"businesses": {}}
        save_users(users)

    return user_id


def select_business(user_id):
    users = load_users()
    businesses = users[user_id]["businesses"]

    if businesses:
        print("\nYour businesses:")
        for idx, bid in enumerate(businesses.keys(), start=1):
            print(f"{idx}. {bid}")
        print(f"{len(businesses) + 1}. Create new business")

        choice = input("Select option: ").strip()

        try:
            choice = int(choice)
            if 1 <= choice <= len(businesses):
                return list(businesses.keys())[choice - 1]
        except ValueError:
            pass

    business_id = input("Enter new business ID (name): ").strip()
    if not business_id:
        raise SystemExit("Business ID cannot be empty.")

    users[user_id]["businesses"][business_id] = {"years": []}
    save_users(users)
    print(f"Business '{business_id}' created.")

    return business_id


def select_year(user_id, business_id):
    users = load_users()
    years = users[user_id]["businesses"][business_id]["years"]

    if years:
        print("\nAvailable years:")
        for y in years:
            print(f"- {y}")
        print("Or enter a new year.")

    try:
        year = int(input("Enter year: ").strip())
    except ValueError:
        raise SystemExit("Year must be a number.")

    if year not in years:
        years.append(year)
        users[user_id]["businesses"][business_id]["years"] = sorted(years)
        save_users(users)
        print(f"Year {year} added for business '{business_id}'.")

    return year


# For GUI
def ensure_user_exists(user_id: str):
    if not user_id:
        raise ValueError("User ID cannot be empty.")

    users = load_users()
    if user_id not in users:
        users[user_id] = {"businesses": {}}
        save_users(users)


def ensure_business_exists(user_id: str, business_id: str):
    user_id = user_id.strip().lower()
    business_id = business_id.strip().lower()

    if not business_id:
        raise ValueError("Business ID cannot be empty.")

    users = load_users()
    ensure_user_exists(user_id)

    businesses = users[user_id]["businesses"]
    if business_id not in businesses:
        businesses[business_id] = {"years": []}
        save_users(users)


def ensure_year_exists(user_id: str, business_id: str, year: int):
    if not isinstance(year, int):
        raise ValueError("Year must be an integer.")

    users = load_users()
    ensure_business_exists(user_id, business_id)

    years = users[user_id]["businesses"][business_id]["years"]
    if year not in years:
        years.append(year)
        users[user_id]["businesses"][business_id]["years"] = sorted(years)
        save_users(users)


def list_businesses(user_id: str):
    users = load_users()
    return list(users.get(user_id, {}).get("businesses", {}).keys())


def list_years(user_id: str, business_id: str):
    users = load_users()
    return (
        users.get(user_id, {})
        .get("businesses", {})
        .get(business_id, {})
        .get("years", [])
    )
