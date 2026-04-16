import json
import os
import sys

INPUT_FILE = "/opt/spark_app/data/TayaraDataEnrichedLocated.json"

def main():
    if not os.path.exists(INPUT_FILE):
        print(json.dumps({"status": "failed", "reason": "Input file not found"}))
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        print(json.dumps({"status": "failed", "reason": "Empty or invalid JSON"}))
        sys.exit(1)

    total = len(data)
    valid_records = 0
    missing_title = 0
    missing_price = 0
    city_filled = 0
    geo_filled = 0

    for item in data:
        if not isinstance(item, dict):
            continue

        if not item.get("title"):
            missing_title += 1
        if not item.get("price"):
            missing_price += 1
        if item.get("ville"):
            city_filled += 1
        if item.get("latitude") is not None and item.get("longitude") is not None:
            geo_filled += 1
        if item.get("id") and item.get("title"):
            valid_records += 1

    result = {
        "status": "ok",
        "total_records": total,
        "valid_records": valid_records,
        "missing_title_ratio": round(missing_title / total, 4),
        "missing_price_ratio": round(missing_price / total, 4),
        "city_fill_ratio": round(city_filled / total, 4),
        "geo_fill_ratio": round(geo_filled / total, 4),
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()