from storage.db import get_fixed_expenses, query
from datetime import datetime


# -----------------------
# 📥 טעינת נתונים לפי טווח
# -----------------------
def load_data_by_range(start, end):
    rows = query(
        """
        SELECT amount, category, description, date
        FROM expenses
        WHERE date >= %s AND date < %s
        ORDER BY date ASC
        """,
        (start, end),
        fetch=True
    )

    return [
        {
            "amount": float(r[0]) if r[0] else 0,
            "category": r[1],
            "description": r[2],
            "date": r[3].isoformat() if r[3] else None
        }
        for r in rows
    ]


# -----------------------
# 📅 גבולות חודש נוכחי
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
def apply_fixed_expenses(data, start, end):
    fixed = get_fixed_expenses()

    for f in fixed:
        exists = any(
            e.get("description") == f["description"]
            and abs(float(e.get("amount", 0)) - float(f["amount"])) < 0.01
            and e.get("category") == f["category"]
            and e.get("date")
            and start <= datetime.fromisoformat(e["date"]) < end
            for e in data
        )

        if not exists:
            data.append({
                "amount": float(f["amount"]),
                "category": f["category"],
                "description": f["description"],
                "date": start.isoformat()
            })

    return data


# -----------------------
# 📊 סיכום חודשי
# -----------------------
def get_monthly_summary(category=None):
    start, end = get_month_range()

    data = load_data_by_range(start, end)
    data = apply_fixed_expenses(data, start, end)

    total = 0.0
    categories = {}

    for e in data:
        try:
            if not e.get("date"):
                continue

            d = datetime.fromisoformat(e["date"])
        except:
            continue

        # הגנה נוספת
        if not (start <= d < end):
            continue

        if category and e.get("category") != category:
            continue

        amount = float(e.get("amount", 0))
        cat = e.get("category", "אחר")

        total += amount
        categories[cat] = categories.get(cat, 0) + amount

    return total, categories


# -----------------------
# 📂 סה״כ לפי קטגוריה
# -----------------------
def get_category_total(category):
    total, categories = get_monthly_summary()
    return categories.get(category, 0)


# -----------------------
# 📅 טווח לפי שם חודש
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


# -----------------------
# 📊 סיכום לפי חודש
# -----------------------
def get_summary_by_month(month_name, category=None):
    start, end = get_month_range_by_name(month_name)

    if not start:
        return None

    data = load_data_by_range(start, end)
    data = apply_fixed_expenses(data, start, end)

    total = 0.0
    categories = {}

    for e in data:
        try:
            if not e.get("date"):
                continue

            d = datetime.fromisoformat(e["date"])
        except:
            continue

        if not (start <= d < end):
            continue

        if category and e.get("category") != category:
            continue

        amount = float(e.get("amount", 0))
        cat = e.get("category", "אחר")

        total += amount
        categories[cat] = categories.get(cat, 0) + amount

    return total, categories


# -----------------------
# 🔢 חודש לשם מספר
# -----------------------
def month_name_to_number(name):
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
    return months.get(name)


# -----------------------
# 🔁 תאימות לאחור
# -----------------------
def get_category_summary(category):
    return get_category_total(category)