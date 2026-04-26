from storage.db import learn_words, get_learning_scores
import re

# מילים שלא רוצים ללמוד
STOPWORDS = {
    "על", "עם", "של", "את", "זה", "זו",
    "קניתי", "קונה", "שילמתי", "הוצאתי",
    "שקל", "שח", "₪",
    "לי", "שלי", "זה", "פה", "שם"
}


def tokenize(text):
    words = re.findall(r'\w+', text.lower())

    filtered = []

    for w in words:
        # ❌ סינון מספרים
        if w.isdigit():
            continue

        # ❌ סינון מילים קצרות מדי
        if len(w) < 3:
            continue

        # ❌ סינון מילים לא רלוונטיות
        if w in STOPWORDS:
            continue

        filtered.append(w)

    return filtered


def learn(description, category):
    words = tokenize(description)

    if not words:
        return

    learn_words(words, category)


def predict_category_with_confidence(description):
    words = tokenize(description)

    if not words:
        return None, 0

    scores = get_learning_scores(words)

    if not scores:
        return None, 0

    best = max(scores, key=scores.get)
    total = sum(scores.values())

    confidence = scores[best] / total if total > 0 else 0

    return best, confidence