from services.parser import parse_message
from storage.db import add_fixed_expense
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
    get_category_total
)


VALID_CATEGORIES = ["אוכל", "אוכל בחוץ", "תחבורה", "דיור", "בגדים", "חשבונות", "בלתי צפוי", "כללי"]


def handle(text):
    pending = get_pending()

    # 🔁 טיפול בהודעה המשך (בחירת קטגוריה)
    if pending:
        category = text.strip()

        if category not in VALID_CATEGORIES:
            return "קטגוריה לא תקינה, נסה שוב\n" + " | ".join(VALID_CATEGORIES)

        pending["category"] = category

        save_expense(pending)
        learn(pending["description"], category)

        clear_pending()

        return f"נשמר: {pending['amount']}₪ על {pending['description']} ({category})"

    # 🧠 parsing
    try:
        data = parse_message(text)
    except Exception:
        return "שגיאה, נסה שוב 🙏"

    action = data.get("action")

    # ➕ הוספת הוצאה
    if action == "add_expense":
        category, confidence = normalize_category(
            data.get("category", ""),
            data.get("description", "")
        )

        # ❗ לא בטוח
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

    # 📊 סיכום חודשי
    elif action == "get_summary":
        total, categories = get_monthly_summary()
        budget_data = get_budget()

        total_budget = budget_data.get("monthly_budget", 0)

        if total_budget == 0:
            result = f"סה״כ החודש: {total}₪\n\n"
        else:
            remaining = total_budget - total
            percent_used = int((total / total_budget) * 100) if total_budget > 0 else 0

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

    # 📂 סיכום לפי קטגוריה
    elif action == "get_category":
        category = data.get("category")

        # 🔥 נרמול גם כאן!
        category, _ = normalize_category(category)

        total = get_category_total(category)
        budget_data = get_budget()
        cat_budget = budget_data.get("categories", {}).get(category, 0)

        if cat_budget > 0:
            percent_used = int((total / cat_budget) * 100) if cat_budget > 0 else 0
            remaining = cat_budget - total

            return (
                f"{category}:\n"
                f"סה״כ: {total}₪\n"
                f"תקציב: {cat_budget}₪\n"
                f"נשאר: {remaining}₪ ({percent_used}% נוצל)"
            )

        return f"סה״כ על {category}: {total}₪"

    # 🔁 הוצאה קבועה
    elif action == "add_fixed_expense":
        add_fixed_expense(data)
        return f"הוצאה קבועה נוספה: {data['description']} {data['amount']}₪"

    # ❌ מחיקה
    elif action == "delete_last":
        deleted = delete_last_expense()

        if deleted:
            return f"נמחקה הוצאה: {deleted['amount']}₪ ({deleted['category']})"
        else:
            return "אין מה למחוק"

    # 💰 תקציב כולל
    elif action == "set_total_budget":
        set_total_budget(data["amount"])
        return f"התקציב הכולל הוגדר ל־{data['amount']}₪"

    # 📊 תקציב לפי קטגוריה
    elif action == "set_category_budget":
        category = data["category"]
        amount = data["amount"]

        set_category_budget(category, amount)
        return f"תקציב {category} הוגדר ל־{amount}₪"

    # 💰 כמה נשאר כולל
    elif action == "remaining_total":
        budget_data = get_budget()
        total_budget = budget_data.get("monthly_budget", 0)

        if total_budget == 0:
            return "לא הוגדר תקציב"

        total_spent, _ = get_monthly_summary()
        remaining = total_budget - total_spent
        percent_used = int((total_spent / total_budget) * 100) if total_budget > 0 else 0

        if remaining < 0:
            return f"חרגת מהתקציב הכולל ב־{abs(remaining)}₪ ⚠️ ({percent_used}% נוצל)"

        msg = f"נשאר לך {remaining}₪ מתוך {total_budget}₪ ({percent_used}% נוצל)"

        if percent_used >= 80:
            msg += "\n⚠️ אתה מתקרב לתקציב!"

        return msg

    # 📂 כמה נשאר בקטגוריה
    elif action == "remaining_category":
        category = data.get("category")
        category, _ = normalize_category(category)

        budget_data = get_budget()
        cat_budget = budget_data.get("categories", {}).get(category, 0)

        if cat_budget == 0:
            return f"לא הוגדר תקציב לקטגוריה {category}"

        spent = get_category_total(category)
        remaining = cat_budget - spent
        percent_used = int((spent / cat_budget) * 100) if cat_budget > 0 else 0

        if remaining < 0:
            return f"חרגת מ־{category} ב־{abs(remaining)}₪ ⚠️ ({percent_used}% נוצל)"

        msg = f"נשאר לך {remaining}₪ בקטגוריית {category} ({percent_used}% נוצל)"

        if percent_used >= 80:
            msg += "\n⚠️ אתה מתקרב לתקציב בקטגוריה!"

        return msg

    # 🤷 fallback
    elif action == "unknown":
        if "היי" in text or "שלום" in text:
            return "היי 👋 אני מנהל ההוצאות שלך\nנסה לכתוב: קפה 15"

        return (
            "לא הבנתי 🤔\n"
            "נסה:\n"
            "• קפה 15\n"
            "• דלק 200\n"
            "• סיכום\n"
            "• כמה הוצאתי על אוכל"
        )

    return "שגיאה לא צפויה 😅"



# ▶️ הרצה מקומית
if __name__ == "__main__":
    while True:
        text = input("You: ")
        print("Bot:", handle(text))