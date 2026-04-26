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

# 🔥 מספרים במילים (מאוחד)
NUMBER_WORDS = {
    "אפס": 0,
    "אחד": 1, "אחת": 1,
    "שתיים": 2, "שניים": 2,
    "שלוש": 3, "שלושה": 3,
    "ארבע": 4,
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

# 🔥 ביטול
CANCEL_WORDS = ["בטל", "עזוב", "cancel", "stop", "תבטל"]


# -----------------------
# 🧠 מספרים במילים → ספרות (משופר!)
# -----------------------
def extract_number_from_text(text):
    text = text.lower()

    # חיפוש לפי מילים שלמות בלבד
    for word, value in NUMBER_WORDS.items():
        if re.search(rf'\b{word}\b', text):
            return value

    return None


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

    # זיכרון קודם
    for word, cat in memory.items():
        if word in text_lower:
            return cat

    # חוקים
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

    text_lower = text.lower()

    # =========================
    # 🔥 יציאה מהלופ
    # =========================
    if any(re.search(rf'\b{w}\b', text_lower) for w in CANCEL_WORDS):
        return {"action": "cancel"}

    # =========================
    # ➕ הוספת קטגוריה
    # =========================
    if "קטגוריה" in text_lower and ("הוסף" in text_lower or "תוסיף" in text_lower):
        name = re.sub(r'(תוסיף|הוסף|קטגוריה)', '', text_lower).strip()

        if not name:
            return {"action": "unknown"}

        return {
            "action": "add_category",
            "name": name
        }

    # =========================
    # 🔢 מספרים במילים
    # =========================
    number = extract_number_from_text(text_lower)

    messages = [
        {
            "role": "system",
            "content": """
אתה מערכת לניהול הוצאות.

תחזיר JSON בלבד.

אם יש מספר במילים (למשל "עשרים") – תחזיר אותו ב amount כמספר.

פעולות:
add_expense, add_fixed_expense, get_summary, get_category,
delete_last, set_total_budget, set_category_budget,
remaining_total, remaining_category, reset,
get_fixed_expenses, reset_fixed_expenses, get_month_summary,
add_category, cancel

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

    # =========================
    # 🔢 תיקון מספר אם GPT פספס
    # =========================
    if number and not data.get("amount"):
        data["amount"] = number

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
    # ❌ מחיקת הוצאה קבועה לפי ID
    # -----------------------
    match = re.search(r'\b(\d+)\b', text_lower)

    if "קבוע" in text_lower and ("מחק" in text_lower or "תמחק" in text_lower) and match:
        return {
            "action": "delete_fixed_by_id",
            "id": int(match.group(1))
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
        else:
            data["category"] = None

    return data