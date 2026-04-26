from services.learning import predict_category_with_confidence
import difflib


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


# 🔥 סדר חשוב: קודם קטגוריות יותר ספציפיות
KEYWORDS = {
    "אוכל בחוץ": [
        "מסעדה", "פיצה", "המבורגר", "שווארמה",
        "סושי", "גלידה", "אייס קפה", "קפה"
    ],
    "אוכל": [
        "סופר", "מזון", "קניות אוכל", "מצרכים", "שפע", "שפע ברכת ה'"
    ],
    "תחבורה": ["דלק", "אוטובוס", "רכבת", "מונית"],
    "דיור": ["שכירות", "דירה", "משכנתא"],
    "בגדים": ["בגדים", "חולצה", "נעליים", "זארה", "nike"],
    "חשבונות": ["חשמל", "מים", "ארנונה", "אינטרנט", "טלפון"],
    "בלתי צפוי": [
        "תיקון", "קלקול", "רופא", "קנס",
        "בעיה", "שבר", "החלפה", "פתאום",
        "נשבר", "תקלה"
    ]
}


def normalize_category(category, description=""):
    text = f"{category} {description}".lower()

    # 🔹 1. למידה (הכי חזק)
    predicted, confidence = predict_category_with_confidence(description)
    if predicted and predicted in VALID_CATEGORIES and confidence >= 0.7:
        return predicted, confidence

    # 🔹 2. מילות מפתח (לפי סדר!)
    for cat, words in KEYWORDS.items():
        for word in words:
            if word in text:
                return cat, 0.85

    # 🔹 3. תיקון שגיאות כתיב
    match = difflib.get_close_matches(category, VALID_CATEGORIES, n=1, cutoff=0.6)
    if match:
        return match[0], 0.7
    

    # 🔹 4. fallback
    return None, 0.0