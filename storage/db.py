import psycopg2
import os
from datetime import datetime

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))


def query(sql, params=None, fetch=False):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        if fetch:
            return cur.fetchall()
        conn.commit()


# -----------------------
# 💾 הוצאות
# -----------------------

def load_data():
    rows = query(
        "SELECT amount, category, description, date FROM expenses ORDER BY date ASC",
        fetch=True
    )

    return [
        {
            "amount": r[0],
            "category": r[1],
            "description": r[2],
            "date": r[3].isoformat()
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
            expense["amount"],
            expense["category"],
            expense["description"],
            datetime.now()
        )
    )


def delete_last_expense():
    row = query(
        """
        SELECT id, amount, category FROM expenses
        ORDER BY date DESC LIMIT 1
        """,
        fetch=True
    )

    if not row:
        return None

    expense_id, amount, category = row[0]

    query("DELETE FROM expenses WHERE id = %s", (expense_id,))

    return {
        "amount": amount,
        "category": category
    }


def reset_expenses():
    query("DELETE FROM expenses")


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
        "monthly_budget": row[0][0],
        "categories": {c[0]: c[1] for c in categories}
    }


def set_total_budget(amount):
    query("DELETE FROM budget")
    query(
        "INSERT INTO budget (monthly_budget) VALUES (%s)",
        (amount,)
    )


def set_category_budget(category, amount):
    query(
        """
        INSERT INTO category_budget (category, amount)
        VALUES (%s, %s)
        ON CONFLICT (category)
        DO UPDATE SET amount = EXCLUDED.amount
        """,
        (category, amount)
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
            "amount": r[0],
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
            expense["amount"],
            expense["category"],
            expense["description"]
        )
    )


def get_fixed_expenses():
    return load_fixed()


def reset_fixed_expenses():
    query("DELETE FROM fixed_expenses")