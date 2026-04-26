import json
import os
import logging
import re
from .openai_service import ask_gpt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMORY_FILE = "storage/category_memory.json"

MONTHS = [
    "ינואר","פברואר","מרץ","אפריל","מאי","יוני",
    "יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"
]

STOPWORDS = {
    "על", "עם", "של", "את", "זה", "זו",
    "קניתי", "קונה", "שילמתי", "הוצאתי",
    "שקל", "שח", "₪",
    "לי", "שלי", "פה", "שם"
}


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
# 🧠 ניקוי מילים
# -----------------------
def tokenize(text):
    words = re.findall(r'\w+', text.lower())

    filtered = []
    for w in words:
        if w.isdigit():
            continue
        if len(w) < 3:
            continue
        if w in STOPWORDS:
            continue

        filtered.append(w)

    return filtered


# -----------------------
# 🧠 למידה
# -----------------------
def learn_category(text, category):
    if not category:
        return

    memory = load_memory()
    words = tokenize(text)

    for w in words:
        memory[w] = category

    save_memory(memory)


# -----------------------
# 🔧 תיקון קטגוריה חכם
# -----------------------
def fix_category(text, category):
    text_lower = text.lower()
    memory = load_memory()

    # 1. זיכרון קודם (הכי חזק)
    for word, cat in memory.items():
        if word in text_lower:
            return cat

    # 2. חוקים קשיחים
    if any(w in text_lower for w in ["חולצה", "מכנס", "נעל", "בגד", "כיפה"]):
        return "בגדים"

    if any(w in text_lower for w in ["אוכל", "קפה", "מסעדה", "פיצה", "סופר"]):
        return "אוכל"

    if any(w in text_lower for w in ["דלק", "אוטובוס", "רכבת", "מונית"]):
        return "תחבורה"

    if any(w in text_lower for w in ["שכירות", "משכנתא"]):
        return "דיור"

    if any(w in text_lower for w in ["חשמל", "מים", "אינטרנט", "טלפון"]):
        return "חשבונות"

    # ❗ אין התאמה → לא מנחשים
    return None


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

פעולות:
add_expense, add_fixed_expense, get_summary, get_category,
delete_last, set_total_budget, set_category_budget,
remaining_total, remaining_category, reset,
get_fixed_expenses, reset_fixed_expenses, get_month_summary

קטגוריות:
בגדים, אוכל, תחבורה, דיור, חשבונות, כללי, בלתי צפוי, אוכל בחוץ

חוקים:
- לא לנחש קטגוריה
- אם לא בטוח → category = null
- תמיד להחזיר JSON בלבד
"""
        },
        {"role": "user", "content": text}
    ]

    response = ask_gpt(messages)
    logger.info(f"RAW GPT RESPONSE: {response}")

    if not response:
        return {"action": "unknown"}

    response = response.strip()

    # ניקוי ```json
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
    # 🔧 תיקון קטגוריה
    # -----------------------
    if data.get("action") in ["add_expense", "add_fixed_expense"]:

        gpt_category = data.get("category")

        fixed = fix_category(text, gpt_category)

        logger.info(f"TEXT: {text}")
        logger.info(f"GPT CATEGORY: {gpt_category}")
        logger.info(f"FIXED CATEGORY: {fixed}")

        if fixed:
            data["category"] = fixed

            # ✅ לומד רק מילים נקיות
            learn_category(text, fixed)

        else:
            # ❗ גורם למערכת לשאול את המשתמש
            data["category"] = None

    return data