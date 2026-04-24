import json

FILE = "storage/pending.json"


def load_pending():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_pending(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


def set_pending(expense):
    data = {"expense": expense}
    save_pending(data)


def get_pending():
    return load_pending().get("expense")


def clear_pending():
    save_pending({})