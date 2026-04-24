from storage.db import load_data, save_data
from services.normalizer import normalize_category

data = load_data()

for e in data:
    e["category"] = normalize_category(
        e.get("category", ""),
        e.get("description", "")
    )

save_data(data)

print("Done fixing categories")