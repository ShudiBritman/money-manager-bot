from storage.db import load_data, get_fixed_expenses
from datetime import datetime


# -----------------------
# 📅 גבולות חודש
# -----------------------

def get_month_range():
    now = datetime.now()

    start = datetime(now.year, now.month, 1)

    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)

    return start, end


# -----------------------
# 🔁 הוצאות קבועות
# -----------------------

def apply_fixed_expenses(data):
    fixed = get_fixed_expenses()
    start, end = get_month_range()

    for f in fixed:
        exists = any(
            e.get("description") == f["description"]
            and e.get("amount") == f["amount"]
            and e.get("category") == f["category"]
            and "date" in e
            and start <= datetime.fromisoformat(e["date"]) < end
            for e in data
        )
        if not exists:
            data.append({
                "amount": f["amount"],
                "category": f["category"],
                "description": f["description"],
                "date": start.isoformat()  # תמיד תחילת החודש
            })

    return data


# -----------------------
# 📊 סיכום חודשי
# -----------------------

def get_monthly_summary():
    data = load_data()
    data = apply_fixed_expenses(data)

    start, end = get_month_range()

    total = 0
    categories = {}

    for e in data:
        try:
            d = datetime.fromisoformat(e["date"])
        except:
            continue

        if start <= d < end:
            amount = float(e.get("amount", 0))
            category = e.get("category", "אחר")

            total += amount
            categories[category] = categories.get(category, 0) + amount

    return total, categories


# -----------------------
# 📂 סה״כ לפי קטגוריה
# -----------------------

def get_category_total(category):
    data = load_data()
    data = apply_fixed_expenses(data)

    start, end = get_month_range()

    total = 0

    for e in data:
        try:
            d = datetime.fromisoformat(e["date"])
        except:
            continue

        if (
            e.get("category") == category
            and start <= d < end
        ):
            total += float(e.get("amount", 0))

    return total

# -----------------------
# סיכום לפי חודש
# -----------------------

def get_month_range_by_name(month_name):
    months = {
        "ינואר": 1,
        "פברואר": 2,
        "מרץ": 3,
        "אפריל": 4,
        "מאי": 5,
        "יוני": 6,
        "יולי": 7,
        "אוגוסט": 8,
        "ספטמבר": 9,
        "אוקטובר": 10,
        "נובמבר": 11,
        "דצמבר": 12
    }

    month = months.get(month_name)

    if not month:
        return None, None

    now = datetime.now()
    start = datetime(now.year, month, 1)

    if month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, month + 1, 1)

    return start, end

def get_summary_by_month(month_name, category=None):
    data = load_data()
    data = apply_fixed_expenses(data)

    start, end = get_month_range_by_name(month_name)

    if not start:
        return None

    total = 0
    categories = {}

    for e in data:
        try:
            d = datetime.fromisoformat(e["date"])
        except:
            continue

        if start <= d < end:
            if category and e.get("category") != category:
                continue

            amount = float(e.get("amount", 0))
            cat = e.get("category", "אחר")

            total += amount
            categories[cat] = categories.get(cat, 0) + amount

    return total, categories


# -----------------------
# תאימות לאחור
# -----------------------

def get_category_summary(category):
    return get_category_total(category)