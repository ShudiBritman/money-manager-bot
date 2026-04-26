from services.learning import predict_category_with_confidence
import difflib
import re


VALID_CATEGORIES = [
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


def tokenize(text):
    return re.findall(r'\w+', text.lower())


def normalize_category(category, description=""):

    # 🔥 הגנה מקריסה
    if category is None:
        category = ""

    if description is None:
        description = ""

    text = f"{category} {description}".lower()
    words = tokenize(text)

    scores = {cat: 0 for cat in VALID_CATEGORIES}

    # -----------------------
    # 🔹 1. מילות מפתח (חזק מאוד)
    # -----------------------
    for cat, kw_list in KEYWORDS.items():
        for kw in kw_list:
            if kw in text:
                scores[cat] += 3

    # -----------------------
    # 🔹 2. למידה מה־DB
    # -----------------------
    predicted, confidence = predict_category_with_confidence(description)

    if predicted and predicted in VALID_CATEGORIES:
        scores[predicted] += confidence * 5

    # -----------------------
    # 🔹 3. קטגוריה מה-GPT (חלש)
    # -----------------------
    if category in VALID_CATEGORIES:
        scores[category] += 1.5

    # -----------------------
    # 🔹 4. תיקון שגיאות כתיב
    # -----------------------
    if category:
        match = difflib.get_close_matches(category, VALID_CATEGORIES, n=1, cutoff=0.6)
        if match:
            scores[match[0]] += 1

    # -----------------------
    # 🔹 5. בחירת הכי חזק
    # -----------------------
    best = max(scores, key=scores.get)
    best_score = scores[best]

    # -----------------------
    # ❗ אין ביטחון → תשאל את המשתמש
    # -----------------------
    if best_score < 2:
        return None, 0

    # 🔥 נרמול confidence
    total_score = sum(scores.values())
    confidence = best_score / total_score if total_score > 0 else 0

    return best, confidence