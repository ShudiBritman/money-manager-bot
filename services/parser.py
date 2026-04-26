import json
import os
import logging
from .openai_service import ask_gpt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMORY_FILE = "storage/category_memory.json"

MONTHS = [
    "ינואר","פברואר","מרץ","אפריל","מאי","יוני",
    "יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"
]


# -----------------------
# 📚 טעינת זיכרון קטגוריות
# -----------------------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# -----------------------
# 🧠 למידה
# -----------------------
def learn_category(text, category):
    memory = load_memory()
    words = text.lower().split()

    for w in words:
        if len(w) < 3:
            continue
        memory[w] = category

    save_memory(memory)


# -----------------------
# 🔧 תיקון קטגוריה חכם
# -----------------------
def fix_category(text, category):
    text_lower = text.lower()
    memory = load_memory()

    # 1. זיכרון קודם
    for word, cat in memory.items():
        if word in text_lower:
            return cat

    # 2. חוקים קשיחים
    if any(w in text_lower for w in ["חולצה", "מכנס", "נעל", "בגד"]):
        return "בגדים"

    if any(w in text_lower for w in ["אוכל", "קפה", "מסעדה", "פיצה", "סופר"]):
        return "אוכל"

    if any(w in text_lower for w in ["דלק", "אוטובוס", "רכבת", "מונית"]):
        return "תחבורה"

    if any(w in text_lower for w in ["שכירות", "משכנתא"]):
        return "דיור"

    if any(w in text_lower for w in ["חשמל", "מים", "אינטרנט", "טלפון"]):
        return "חשבונות"

    return category


# -----------------------
# 📅 זיהוי חודש
# -----------------------
def detect_month(text):
    for m in MONTHS:
        if m in text:
            return m
    return None


# -----------------------
# 🧠 ניתוח הודעה
# -----------------------
def parse_message(text):
    messages = [
    {
        "role": "system",
        "content": """
אתה מערכת לניהול הוצאות.

תחזיר JSON בלבד.

אם אינך בטוח בקטגוריה → בחר "כללי".

פעולות:

1. add_expense
2. add_fixed_expense
3. get_summary
4. get_category
5. delete_last
6. set_total_budget
7. set_category_budget
8. remaining_total
9. remaining_category
10. reset
11. get_fixed_expenses
12. reset_fixed_expenses
13. get_month_summary

קטגוריות מותרות בלבד:
בגדים, אוכל, תחבורה, דיור, חשבונות, כללי, בלתי צפוי, אוכל בחוץ

חוקים:
- תמיד להחזיר JSON בלבד
- לא להחזיר טקסט נוסף
- לזהות סכומים מתוך משפט
"""
    },
    {"role": "user", "content": text}
]

    response = ask_gpt(messages)
    logger.info(f"RAW GPT RESPONSE: {response}")

    if not response:
        return {"action": "unknown"}

    response = response.strip()

    # ניקוי קוד בלוקים
    if response.startswith("```"):
        parts = response.split("```")
        if len(parts) > 1:
            response = parts[1]

    response = response.replace("json", "").strip()

    try:
        data = json.loads(response)
    except Exception as e:
        logger.error(f"PARSER ERROR: {e}")
        return {"action": "unknown"}

    if not data or "action" not in data:
        logger.error("INVALID RESPONSE STRUCTURE")
        return {"action": "unknown"}

    # -----------------------
    # 📅 חודש
    # -----------------------
    month = detect_month(text)
    if month and data.get("action") == "get_summary":
        return {
            "action": "get_month_summary",
            "month": month,
            "category": data.get("category")
        }

    # -----------------------
    # 🔧 תיקון ולמידה
    # -----------------------
    if data.get("action") in ["add_expense", "add_fixed_expense"]:
        original_category = data.get("category", "כללי")

        fixed = fix_category(text, original_category)
        data["category"] = fixed

        # למידה
        learn_category(text, fixed)

    return data