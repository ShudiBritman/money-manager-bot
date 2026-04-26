from storage.db import learn_words, get_learning_scores
import re


def tokenize(text):
    return re.findall(r'\w+', text.lower())


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