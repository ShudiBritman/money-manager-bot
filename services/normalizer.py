from services.learning import predict_category_with_confidence
from storage.db import get_categories
import difflib
import re


DEFAULT_CATEGORIES = [
    "אוכל",
    "אוכל בחוץ",
    "תחבורה",
    "דיור",
    "בגדים",
    "חשבונות",
    "בלתי צפוי",
    "כללי"
]


KEYWORDS = {
    "אוכל בחוץ": [
        "מסעדה", "פיצה", "המבורגר", "שווארמה",
        "סושי", "גלידה", "אייס", "קפה"
    ],
    "אוכל": [
        "סופר", "מזון", "מצרכים"
    ],
    "תחבורה": ["דלק", "אוטובוס", "רכבת", "מונית"],
    "דיור": ["שכירות", "דירה", "משכנתא"],
    "בגדים": ["בגדים", "חולצה", "נעליים", "זארה", "nike", "כיפה"],
    "חשבונות": ["חשמל", "מים", "ארנונה", "אינטרנט", "טלפון"],
    "בלתי צפוי": ["תיקון", "קלקול", "רופא", "קנס", "תקלה"]
}


def get_all_categories():
    try:
        custom = get_categories() or []
    except:
        custom = []

    return list(set(DEFAULT_CATEGORIES + custom))


def tokenize(text):
    return re.findall(r'\w+', text.lower())


def normalize_category(category, description=""):

    # 🔥 הגנות
    if category is None:
        category = ""

    if description is None:
        description = ""

    ALL_CATEGORIES = get_all_categories()

    text = f"{category} {description}".lower()
    words = tokenize(text)

    scores = {cat: 0 for cat in ALL_CATEGORIES}

    # -----------------------
    # 🔹 1. מילות מפתח (חזק מאוד)
    # -----------------------
    for cat, kw_list in KEYWORDS.items():
        if cat not in scores:
            continue

        for kw in kw_list:
            if kw in text:
                scores[cat] += 3

    # -----------------------
    # 🔹 2. למידה מה־DB (חזק מאוד)
    # -----------------------
    predicted, confidence = predict_category_with_confidence(description)

    if predicted and predicted in scores:
        scores[predicted] += confidence * 6  # חיזוק!

    # -----------------------
    # 🔹 3. קטגוריה מה-GPT
    # -----------------------
    if category in scores:
        scores[category] += 1.5

    # -----------------------
    # 🔹 4. תיקון שגיאות כתיב
    # -----------------------
    if category:
        match = difflib.get_close_matches(category, ALL_CATEGORIES, n=1, cutoff=0.6)
        if match:
            scores[match[0]] += 1

    # -----------------------
    # 🔹 5. fallback חכם לפי מילים
    # -----------------------
    for word in words:
        for cat in ALL_CATEGORIES:
            if word == cat:
                scores[cat] += 2

    # -----------------------
    # 🔹 6. בחירה
    # -----------------------
    best = max(scores, key=scores.get)
    best_score = scores[best]

    # ❗ אין ביטחון → תשאל
    if best_score < 2:
        return None, 0

    total_score = sum(scores.values())
    confidence = best_score / total_score if total_score > 0 else 0

    return best, confidence