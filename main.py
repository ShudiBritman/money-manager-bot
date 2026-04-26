from services.parser import parse_message
from storage.db import (
    add_fixed_expense,
    reset_expenses,
    get_fixed_expenses,
    reset_fixed_expenses
)
from services.pending import set_pending, get_pending, clear_pending
from services.learning import learn
from services.normalizer import normalize_category
from storage.db import (
    set_total_budget,
    set_category_budget,
    get_budget,
    save_expense,
    delete_last_expense,
)
from logic.summary import (
    get_monthly_summary,
    get_category_total,
    get_summary_by_month
)


VALID_CATEGORIES = ["אוכל", "אוכל בחוץ", "תחבורה", "דיור", "בגדים", "חשבונות", "בלתי צפוי", "כללי"]


def handle(text):
    pending = get_pending()
    cleaned = text.strip().lower()

    YES = ["כן", "yes", "y", "ok", "אוקיי"]
    NO = ["לא", "no", "n"]

    # =========================
    # 🔥 CONFIRM RESET (הכי ראשון)
    # =========================
    if pending and pending.get("action") == "confirm_reset":

        

        if any(word in cleaned for word in YES):
            reset_expenses()  # או reset_all אם בא לך למחוק גם תקציב
            clear_pending()
            return "נמחק הכל 🗑️"

        if any(word in cleaned for word in NO):
            clear_pending()
            return "בוטל"

        return "לא הבנתי 🤔 כתוב כן או לא"
    
    if pending and pending.get("action") == "confirm_reset_fixed":
        if any(word in cleaned for word in YES):
            reset_fixed_expenses()
            clear_pending()
            return "כל ההוצאות הקבועות נמחקו 🗑️"

        else:
            clear_pending()
            return "בוטל"

    # =========================
    # 🔥 אם המשתמש שלח הוצאה חדשה → בטל pending
    # =========================
    if pending and any(char.isdigit() for char in text):
        clear_pending()
        pending = None

    # =========================
    # 🔁 טיפול ב-pending רגיל
    # =========================
    if pending and len(text.split()) <= 3:
        category_input = text.strip()

        category, confidence = normalize_category(category_input, category_input)

        if not category:
            clear_pending()
            return (
                "לא הצלחתי להבין את הקטגוריה 🤔\n"
                "נסה לבחור:\n" + " | ".join(VALID_CATEGORIES)
            )

        pending["category"] = category

        save_expense(pending)
        learn(pending["description"], category)

        clear_pending()

        return f"נשמר: {pending['amount']}₪ על {pending['description']} ({category})"

    # =========================
    # 🧠 parsing
    # =========================
    try:
        data = parse_message(text)
    except Exception:
        return "שגיאה, נסה שוב 🙏"

    action = data.get("action")

    # =========================
    # ➕ הוספת הוצאה
    # =========================
    if action == "add_expense":
        category, confidence = normalize_category(
            data.get("category", ""),
            data.get("description", "")
        )

        if not category:
            set_pending(data)
            return (
                f"לא בטוח לאיזה קטגוריה לשייך 🤔\n"
                f"הוצאה: {data['description']} {data['amount']}₪\n\n"
                "בחר קטגוריה:\n" +
                " | ".join(VALID_CATEGORIES)
            )

        data["category"] = category

        save_expense(data)
        learn(data["description"], category)

        return f"נשמר: {data['amount']}₪ על {data['description']} ({category}, {int(confidence*100)}%)"

    # =========================
    # 📊 סיכום חודשי
    # =========================
    elif action == "get_summary":
        total, categories = get_monthly_summary()
        budget_data = get_budget()

        total_budget = budget_data.get("monthly_budget", 0)

        if total_budget == 0:
            result = f"סה״כ החודש: {total}₪\n\n"
        else:
            remaining = total_budget - total
            percent_used = int((total / total_budget) * 100)

            result = f"סה״כ החודש: {total}₪\n"
            result += f"תקציב: {total_budget}₪\n"

            if remaining < 0:
                result += f"חריגה: {abs(remaining)}₪ ⚠️ ({percent_used}% נוצל)\n"
            else:
                result += f"נשאר: {remaining}₪ ({percent_used}% נוצל)\n"

            if percent_used >= 80:
                result += "⚠️ אתה מתקרב לתקציב!\n"

            result += "\n"

        for k, v in categories.items():
            result += f"{k}: {v}₪\n"

        return result

    # =========================
    # 📂 לפי קטגוריה
    # =========================
    elif action == "get_category":
        category_input = data.get("category", "")
        category, _ = normalize_category(category_input, category_input)

        if not category:
            return "לא הצלחתי להבין את הקטגוריה"

        total = get_category_total(category)
        return f"סה״כ על {category}: {total}₪"

    # =========================
    # 🔁 קבוע
    # =========================
    elif action == "add_fixed_expense":
        add_fixed_expense(data)
        return f"הוצאה קבועה נוספה: {data['description']} {data['amount']}₪"
    
    elif action == "reset_fixed_expenses":
        set_pending({"action": "confirm_reset_fixed"})
        return "למחוק את כל ההוצאות הקבועות? כתוב כן"

    # =========================
    # ❌ מחיקה
    # =========================
    elif action == "delete_last":
        deleted = delete_last_expense()

        if deleted:
            return f"נמחקה הוצאה: {deleted['amount']}₪ ({deleted['category']})"
        return "אין מה למחוק"

    # =========================
    # 💰 תקציב
    # =========================
    elif action == "set_total_budget":
        set_total_budget(data["amount"])
        return f"התקציב הכולל הוגדר ל־{data['amount']}₪"

    elif action == "set_category_budget":
        set_category_budget(data["category"], data["amount"])
        return f"תקציב {data['category']} הוגדר ל־{data['amount']}₪"

    elif action == "remaining_total":
        budget_data = get_budget()
        total_budget = budget_data.get("monthly_budget", 0)

        if total_budget == 0:
            return "לא הוגדר תקציב"

        total_spent, _ = get_monthly_summary()
        remaining = total_budget - total_spent
        percent_used = int((total_spent / total_budget) * 100)

        if remaining < 0:
            return f"חרגת מהתקציב ב־{abs(remaining)}₪ ⚠️ ({percent_used}%)"

        return f"נשאר {remaining}₪ ({percent_used}%)"

    # =========================
    # 🔥 RESET
    # =========================
    elif action == "reset":
        set_pending({"action": "confirm_reset"})
        return "אתה בטוח שברצונך למחוק הכל? כתוב כן או לא"
    
    elif action == "get_fixed_expenses":
        fixed = get_fixed_expenses()

        if not fixed:
            return "אין הוצאות קבועות עדיין"

        result = "📌 הוצאות קבועות:\n\n"

        for f in fixed:
            result += f"- {f['description']}: {f['amount']}₪ ({f['category']})\n"

        total = sum(f["amount"] for f in fixed)
        result += f"\nסה״כ חודשי קבוע: {total}₪"

        return result
    

    elif action == "get_month_summary":
        month = data.get("month")
        category = data.get("category")

        result = get_summary_by_month(month, category)

        if not result:
            return "לא זיהיתי את החודש 🤔"

        total, categories = result

        if total == 0:
            return f"📅 {month}:\nאין הוצאות בחודש הזה"

        msg = f"📅 סיכום {month}:\n"
        msg += f"סה״כ: {total}₪\n\n"

        for k, v in categories.items():
            msg += f"{k}: {v}₪\n"

        return msg

    # =========================
    # 🤷 fallback
    # =========================
    return "לא הבנתי 🤔"



# ▶️ הרצה מקומית
if __name__ == "__main__":
    while True:
        text = input("You: ")
        print("Bot:", handle(text))