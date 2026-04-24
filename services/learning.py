import json

FILE = "storage/learning.json"


def load_learning():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_learning(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


def learn(description, category):
    data = load_learning()

    words = description.lower().split()

    for word in words:
        if word not in data:
            data[word] = {}

        if category not in data[word]:
            data[word][category] = 0

        data[word][category] += 1

    save_learning(data)


def predict_category_with_confidence(description):
    data = load_learning()
    scores = {}

    words = description.lower().split()

    for word in words:
        if word in data:
            for cat, count in data[word].items():
                scores[cat] = scores.get(cat, 0) + count

    if not scores:
        return None, 0

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best] / total if total > 0 else 0

    return best, confidence