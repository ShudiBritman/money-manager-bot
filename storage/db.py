import psycopg2
import os
from datetime import datetime


# -----------------------
# 🔌 DB Connection
# -----------------------

def get_conn():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require",
        connect_timeout=5
    )


def query(sql, params=None, fetch=False):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if fetch:
                    return cur.fetchall()
    except Exception as e:
        print("❌ DB ERROR:", e)
        return [] if fetch else None
    finally:
        conn.close()


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
    ) or []

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
            float(expense.get("amount", 0)),
            expense.get("category"),
            expense.get("description", ""),
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

    categories = query(
        "SELECT category, amount FROM category_budget",
        fetch=True
    ) or []

    return {
        "monthly_budget": float(row[0][0]) if row else 0,
        "categories": {c[0]: float(c[1]) for c in categories}
    }


def set_total_budget(amount):
    query("DELETE FROM budget")
    query(
        "INSERT INTO budget (monthly_budget) VALUES (%s)",
        (float(amount),)
    )


def set_category_budget(category, amount):
    if not category:
        return

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
# 📌 הוצאות קבועות (עם ID!)
# -----------------------

def load_fixed():
    rows = query(
        """
        SELECT id, amount, category, description
        FROM fixed_expenses
        ORDER BY id ASC
        """,
        fetch=True
    ) or []

    return [
        {
            "id": r[0],
            "amount": float(r[1]),
            "category": r[2],
            "description": r[3]
        }
        for r in rows
    ]


def add_fixed_expense(expense):
    query(
        """
        INSERT INTO fixed_expenses (amount, category, description)
        VALUES (%s, %s, %s)
        """,
        (
            float(expense.get("amount", 0)),
            expense.get("category"),
            expense.get("description", "")
        )
    )


def delete_fixed_expense(expense_id):
    row = query(
        """
        SELECT id, amount, category, description
        FROM fixed_expenses
        WHERE id = %s
        """,
        (expense_id,),
        fetch=True
    )

    if not row:
        return None

    query("DELETE FROM fixed_expenses WHERE id = %s", (expense_id,))

    r = row[0]
    return {
        "id": r[0],
        "amount": float(r[1]),
        "category": r[2],
        "description": r[3]
    }


def get_fixed_expenses():
    return load_fixed()


def reset_fixed_expenses():
    query("DELETE FROM fixed_expenses")


# -----------------------
# 📂 קטגוריות מותאמות אישית
# -----------------------

def add_category(name):
    if not name:
        return

    query(
        """
        INSERT INTO categories (name)
        VALUES (%s)
        ON CONFLICT (name) DO NOTHING
        """,
        (name,)
    )


def get_categories():
    rows = query(
        "SELECT name FROM categories",
        fetch=True
    ) or []

    return [r[0] for r in rows]


# -----------------------
# 📊 סיכום
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

    rows = rows or []

    total = sum(float(r[1]) for r in rows)
    categories = {r[0]: float(r[1]) for r in rows}

    # ➕ קבועות
    for f in get_fixed_expenses():
        if category and f["category"] != category:
            continue

        total += float(f["amount"])
        categories[f["category"]] = categories.get(f["category"], 0) + float(f["amount"])

    return total, categories


# -----------------------
# 🧠 LEARNING
# -----------------------

def learn_words(words, category):
    if not words or not category:
        return

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                for word in set(words):

                    if len(word) < 3 or word.isdigit():
                        continue

                    cur.execute(
                        """
                        INSERT INTO learning (word, category, count, updated_at)
                        VALUES (%s, %s, 1, NOW())
                        ON CONFLICT (word, category)
                        DO UPDATE SET
                            count = learning.count + 1,
                            updated_at = NOW()
                        """,
                        (word, category)
                    )
    finally:
        conn.close()



def get_learning_scores(words):
    if not words:
        return {}

    rows = query(
        """
        SELECT category, SUM(count)
        FROM learning
        WHERE word = ANY(%s)
        GROUP BY category
        """,
        (list(set(words)),),
        fetch=True
    ) or []

    return {r[0]: float(r[1]) for r in rows}



def load_fixed():
    rows = query(
        "SELECT id, amount, category, description FROM fixed_expenses",
        fetch=True
    ) or []

    return [
        {
            "id": r[0],
            "amount": float(r[1]),
            "category": r[2],
            "description": r[3]
        }
        for r in rows
    ]


def delete_fixed_expense_by_id(expense_id):
    row = query(
        "SELECT id, amount, category, description FROM fixed_expenses WHERE id = %s",
        (expense_id,),
        fetch=True
    )

    if not row:
        return None

    query("DELETE FROM fixed_expenses WHERE id = %s", (expense_id,))

    r = row[0]
    return {
        "id": r[0],
        "amount": float(r[1]),
        "category": r[2],
        "description": r[3]
    }