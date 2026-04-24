from services.learning import predict_category_with_confidence
import difflib


VALID_CATEGORIES = ["אוכל", "תחבורה", "דיור", "בגדים", "חשבונות", "בלתי צפוי", "כללי"]

KEYWORDS = {
    "אוכל": ["אוכל", "מסעדה", "קפה", "סופר", "מזון", "פיצה", "המבורגר", "שווארמה", "סושי", "אייס קפה"],
    "תחבורה": ["דלק", "אוטובוס", "רכבת", "מונית"],
    "דיור": ["שכירות", "דירה", "משכנתא"],
    "בגדים": ["בגדים", "חולצה", "נעליים", "זארה", "nike"],
    "חשבונות": ["חשמל", "מים", "ארנונה", "אינטרנט", "טלפון"],

    "בלתי צפוי": [
        "תיקון",
        "קלקול",
        "רופא",
        "קנס",
        "בעיה",
        "שבר",
        "החלפה",
        "פתאום",
        "נשבר",
        "תקלה"
    ]
}


def normalize_category(category, description=""):
    text = f"{category} {description}".lower()

    for cat, words in KEYWORDS.items():
        for word in words:
            if word in text:
                return cat, 0.9

    predicted, confidence = predict_category_with_confidence(description)

    if predicted and confidence >= 0.7:
        return predicted, confidence

    for cat, words in KEYWORDS.items():
        for word in words:
            if word in text:
                return cat, 0.8

    match = difflib.get_close_matches(category, VALID_CATEGORIES, n=1, cutoff=0.6)
    if match:
        return match[0], 0.6

    return None, 0.0