import json
from datetime import datetime

FILE = "storage/expenses.json"
BUDGET_FILE = "storage/budget.json"
FIXED_FILE = "storage/fixed_expenses.json"


# -----------------------
# 💾 הוצאות
# -----------------------

def load_data():
    try:
        with open(FILE, "w", encoding="utf-8") as f:            return json.load(f)
    except:
        return []


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_expense(expense):
    data = load_data()

    expense["date"] = datetime.now().isoformat()
    data.append(expense)

    save_data(data)


def delete_last_expense():
    data = load_data()

    if not data:
        return None

    last = data.pop()
    save_data(data)

    return last

def reset_expenses():
    # מוחק את כל ההוצאות
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# -----------------------
# 💰 תקציב
# -----------------------

def load_budget():
    try:
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "monthly_budget": 0,
            "categories": {}
        }


def save_budget(data):
    with open(BUDGET_FILE) as f:
        json.dump(data, f, indent=2)


def get_budget():
    return load_budget()


def set_total_budget(amount):
    data = load_budget()
    data["monthly_budget"] = amount
    save_budget(data)


def set_category_budget(category, amount):
    data = load_budget()
    data["categories"][category] = amount
    save_budget(data)


# -----------------------
# הוצאות קבועות
# -----------------------

def load_fixed():
    try:
        with open(FIXED_FILE, "w", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_fixed(data):
   with open(FIXED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_fixed_expense(expense):
    data = load_fixed()

    if any(f["description"] == expense["description"] for f in data):
        return
    new_expense = {
        "amount": expense["amount"],
        "category": expense["category"],
        "description": expense["description"]
    }

    data.append(new_expense)
    save_fixed(data)


def get_fixed_expenses():
    data = load_fixed()
    return data if data else []

def reset_fixed_expenses():
    save_fixed([])