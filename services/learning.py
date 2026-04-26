from storage.db import learn_words, get_learning_scores
import re

# מילים שלא רוצים ללמוד
STOPWORDS = {
    "על", "עם", "של", "את", "זה", "זו",
    "קניתי", "קונה", "שילמתי", "הוצאתי",
    "שקל", "שח", "₪",
    "לי", "שלי", "פה", "שם",
    "הוצאה", "עלה", "כמה", "זה", "יש"
}


def clean_word(w):
    return (
        w.strip()
        .replace(",", "")
        .replace(".", "")
        .replace("₪", "")
    )


def is_number(w):
    return w.replace(".", "", 1).isdigit()


def tokenize(text):
    words = re.findall(r'[א-ת]+', text.lower())

    return [
        w for w in words
        if len(w) >= 3 and w not in STOPWORDS
    ]


def learn(description, category):
    # ❌ לא לומדים אם אין קטגוריה תקינה
    if not category:
        return

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

    # ❌ הגנה אם DB מחזיר משהו מוזר
    scores = {k: v for k, v in scores.items() if v > 0}

    if not scores:
        return None, 0

    best = max(scores, key=scores.get)
    total = sum(scores.values())

    confidence = scores[best] / total if total > 0 else 0

    # ❗ אם הביטחון נמוך מדי → לא לסמוך על זה
    if confidence < 0.4:
        return None, 0

    return best, confidence