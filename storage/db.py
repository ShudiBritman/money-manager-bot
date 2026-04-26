import psycopg2
import os
from datetime import datetime


# -----------------------
# 🔌 DB Connection
# -----------------------

def get_conn():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )


def query(sql, params=None, fetch=False):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if fetch:
                    return cur.fetchall()
    finally:
        conn.close()  # ✅ חשוב מאוד


# -----------------------
# 💾 הוצאות
# -----------------------

def load_data():
    rows = query(
        """
        SELECT amount, category, description, date
        FROM expenses
        ORDER BY date ASC
        """,
        fetch=True
    )

    return [
        {
            "amount": float(r[0]),
            "category": r[1],
            "description": r[2],
            "date": r[3].isoformat() if r[3] else None
        }
        for r in rows
    ]


def save_expense(expense):
    query(
        """
        INSERT INTO expenses (amount, category, description, date)
        VALUES (%s, %s, %s, %s)
        """,
        (
            float(expense["amount"]),
            expense["category"],
            expense["description"],
            datetime.now()
        )
    )


def delete_last_expense():
    row = query(
        """
        SELECT id, amount, category, description
        FROM expenses
        ORDER BY date DESC
        LIMIT 1
        """,
        fetch=True
    )

    if not row:
        return None

    expense_id, amount, category, description = row[0]

    query("DELETE FROM expenses WHERE id = %s", (expense_id,))

    return {
        "amount": float(amount),
        "category": category,
        "description": description
    }


def reset_expenses():
    query("TRUNCATE TABLE expenses RESTART IDENTITY")


# -----------------------
# 💰 תקציב
# -----------------------

def get_budget():
    row = query(
        "SELECT monthly_budget FROM budget LIMIT 1",
        fetch=True
    )

    if not row:
        return {
            "monthly_budget": 0,
            "categories": {}
        }

    categories = query(
        "SELECT category, amount FROM category_budget",
        fetch=True
    )

    return {
        "monthly_budget": float(row[0][0]),
        "categories": {c[0]: float(c[1]) for c in categories}
    }


def set_total_budget(amount):
    query("DELETE FROM budget")
    query(
        "INSERT INTO budget (monthly_budget) VALUES (%s)",
        (float(amount),)
    )


def set_category_budget(category, amount):
    query(
        """
        INSERT INTO category_budget (category, amount)
        VALUES (%s, %s)
        ON CONFLICT (category)
        DO UPDATE SET amount = EXCLUDED.amount
        """,
        (category, float(amount))
    )


# -----------------------
# 📌 הוצאות קבועות
# -----------------------

def load_fixed():
    rows = query(
        "SELECT amount, category, description FROM fixed_expenses",
        fetch=True
    )

    return [
        {
            "amount": float(r[0]),
            "category": r[1],
            "description": r[2]
        }
        for r in rows
    ]


def add_fixed_expense(expense):
    query(
        """
        INSERT INTO fixed_expenses (amount, category, description)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (
            float(expense["amount"]),
            expense["category"],
            expense["description"]
        )
    )


def get_fixed_expenses():
    return load_fixed()


def reset_fixed_expenses():
    query("DELETE FROM fixed_expenses")


# -----------------------
# 📊 סיכום לפי חודש (DB)
# -----------------------

def get_summary_by_month_db(year, month, category=None):
    if category:
        rows = query(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE EXTRACT(YEAR FROM date) = %s
              AND EXTRACT(MONTH FROM date) = %s
              AND category = %s
            GROUP BY category
            """,
            (year, month, category),
            fetch=True
        )
    else:
        rows = query(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE EXTRACT(YEAR FROM date) = %s
              AND EXTRACT(MONTH FROM date) = %s
            GROUP BY category
            """,
            (year, month),
            fetch=True
        )

    total = sum(float(r[1]) for r in rows) if rows else 0
    categories = {r[0]: float(r[1]) for r in rows} if rows else {}

    # -----------------------
    # ➕ הוספת הוצאות קבועות
    # -----------------------
    fixed = get_fixed_expenses()

    for f in fixed:
        if category and f["category"] != category:
            continue

        total += float(f["amount"])
        categories[f["category"]] = categories.get(f["category"], 0) + float(f["amount"])

    return total, categories


def get_monthly_summary_db(start, end):
    rows = query(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date >= %s AND date < %s
        GROUP BY category
        """,
        (start, end),
        fetch=True
    )

    total = sum(float(r[1]) for r in rows) if rows else 0
    categories = {r[0]: float(r[1]) for r in rows} if rows else {}

    # ➕ הוצאות קבועות
    fixed = get_fixed_expenses()

    for f in fixed:
        total += float(f["amount"])
        categories[f["category"]] = categories.get(f["category"], 0) + float(f["amount"])

    return total, categories