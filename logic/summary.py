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

# 🔢 מספרים בעברית
NUMBER_WORDS = {
    "אפס": 0,
    "אחד": 1, "אחת": 1,
    "שתיים": 2, "שניים": 2,
    "שלוש": 3, "שלושה": 3,
    "ארבע": 4, "ארבעה": 4,
    "חמש": 5,
    "שש": 6,
    "שבע": 7,
    "שמונה": 8,
    "תשע": 9,
    "עשר": 10,
    "עשרים": 20,
    "שלושים": 30,
    "ארבעים": 40,
    "חמישים": 50,
    "מאה": 100
}

CANCEL_WORDS = ["בטל", "עזוב", "cancel", "stop", "תבטל"]

VALID_CATEGORIES = [
    "אוכל", "אוכל בחוץ", "תחבורה", "דיור",
    "בגדים", "חשבונות", "בלתי צפוי", "כללי"
]

# -----------------------
# 🔢 חילוץ מספר חכם
# -----------------------
def extract_number_from_text(text):
    words = re.findall(r'\w+', text)
    total = 0

    for w in words:
        clean = w
        if w.startswith("ו") and len(w) > 1:
            clean = w[1:]

        if clean in NUMBER_WORDS:
            total += NUMBER_WORDS[clean]

    return total if total > 0 else None


# -----------------------
# 📚 זיכרון
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

    return [
        w for w in words
        if not w.isdigit()
        and len(w) >= 3
        and w not in STOPWORDS
    ]


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
# 🔧 תיקון קטגוריה
# -----------------------
def fix_category(text, category):
    text_lower = text.lower()
    memory = load_memory()

    # זיכרון קודם
    for word, cat in memory.items():
        if word in text_lower:
            return cat

    # חוקים
    if any(w in text_lower for w in ["חולצה", "מכנס", "נעל", "בגד"]):
        return "בגדים"

    if any(w in text_lower for w in ["קפה", "מסעדה", "פיצה", "סופר"]):
        return "אוכל"

    if any(w in text_lower for w in ["דלק", "אוטובוס", "רכבת", "מונית"]):
        return "תחבורה"

    if any(w in text_lower for w in ["שכירות", "משכנתא"]):
        return "דיור"

    if any(w in text_lower for w in ["חשמל", "מים", "אינטרנט", "טלפון"]):
        return "חשבונות"

    # 👉 אם GPT כן נתן משהו — אל תהרוס
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
# 🧠 parser
# -----------------------
def parse_message(text):

    text_lower = text.lower()

    # ❌ cancel תמיד קודם
    if any(re.search(rf'\b{w}\b', text_lower) for w in CANCEL_WORDS):
        return {"action": "cancel"}

    # 📅 סיכום לפי חודש
    month = detect_month(text_lower)
    if "סיכום" in text_lower and month:
        return {
            "action": "get_month_summary",
            "month": month
        }

    # 📂 סיכום לפי קטגוריה
    if "סיכום" in text_lower:
        for cat in VALID_CATEGORIES:
            if cat in text_lower:
                return {
                    "action": "get_category",
                    "category": cat
                }

    # 📊 סיכום כללי
    if "סיכום" in text_lower:
        return {"action": "get_summary"}

    # 🔄 איפוס
    if "איפוס" in text_lower:
        return {"action": "reset"}

    # 📊 כמה הוצאתי
    if "כמה הוצאתי" in text_lower:
        return {"action": "get_summary"}

    # 📂 לפי קטגוריה
    if "כמה הוצאתי על" in text_lower:
        category = text_lower.replace("כמה הוצאתי על", "").strip()
        return {
            "action": "get_category",
            "category": category
        }

    # ❌ מחיקת קבועה לפי ID
    if "קבוע" in text_lower and ("מחק" in text_lower or "תמחק" in text_lower):

        # מספר רגיל
        match = re.search(r'\d+', text_lower)
        if match:
            return {
                "action": "delete_fixed_by_id",
                "id": int(match.group())
            }

        # מספר במילים
        word_number = extract_number_from_text(text_lower)
        if word_number:
            return {
                "action": "delete_fixed_by_id",
                "id": word_number
            }

    # ➕ הוספת קטגוריה
    if "קטגוריה" in text_lower and ("הוסף" in text_lower or "תוסיף" in text_lower):
        name = re.sub(r'(תוסיף|הוסף|קטגוריה)', '', text_lower).strip()

        if not name:
            return {"action": "unknown"}

        return {
            "action": "add_category",
            "name": name
        }

    # 🔢 מספרים
    number = extract_number_from_text(text_lower)

    # -----------------------
    # 🤖 GPT fallback
    # -----------------------
    messages = [
        {
            "role": "system",
            "content": """
אתה מערכת לניהול הוצאות.

תחזיר JSON בלבד.

פעולות:
add_expense, add_fixed_expense, get_summary, get_category,
delete_last, set_total_budget, set_category_budget,
remaining_total, reset,
get_fixed_expenses, reset_fixed_expenses, get_month_summary,
add_category, delete_fixed_by_id, cancel

קטגוריות:
בגדים, אוכל, תחבורה, דיור, חשבונות, כללי, בלתי צפוי, אוכל בחוץ

חוקים:
- לא לנחש קטגוריה
- אם לא בטוח → category = null
"""
        },
        {"role": "user", "content": text}
    ]

    response = ask_gpt(messages)
    logger.info(f"RAW GPT RESPONSE: {response}")

    if not response:
        return {"action": "unknown"}

    response = response.strip()

    # ניקוי markdown
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
        return {"action": "unknown", "raw": response}

    # 🔢 תיקון מספר אם GPT פספס
    if number and not data.get("amount"):
        data["amount"] = number

    # 🔧 תיקון קטגוריה
    if data.get("action") in ["add_expense", "add_fixed_expense"]:
        fixed = fix_category(text, data.get("category"))

        if fixed:
            data["category"] = fixed
        else:
            data["category"] = None

    return data