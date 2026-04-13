import json
import os
import pandas as pd
from sqlalchemy import create_engine, text

RAW_INPUT_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"
RAW_OUTPUT_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"
POSTGRES_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"


def get_existing_ids(engine, table_name="clean_tayara"):
    try:
        query = text(f"SELECT id FROM {table_name}")
        with engine.connect() as conn:
            df_ids = pd.read_sql(query, conn)
        return set(df_ids["id"].dropna().astype(str))
    except Exception as e:
        print(f"[INFO] Could not load existing ids from {table_name}: {e}")
        return set()


def main():
    if not os.path.exists(RAW_INPUT_FILE):
        raise FileNotFoundError(f"Raw file not found: {RAW_INPUT_FILE}")

    with open(RAW_INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Raw input is not a JSON list.")

    print(f"Scraped raw rows: {len(data)}")

    # Deduplicate inside the scraped batch first
    seen_ids = set()
    deduped_batch = []

    for item in data:
        item_id = item.get("id")
        if not item_id:
            continue
        item_id = str(item_id)
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            item["id"] = item_id
            deduped_batch.append(item)

    print(f"Rows after internal raw deduplication: {len(deduped_batch)}")

    engine = create_engine(POSTGRES_URL)
    existing_ids = get_existing_ids(engine, "clean_tayara")
    print(f"Existing ids already in DB: {len(existing_ids)}")

    new_rows = [row for row in deduped_batch if row["id"] not in existing_ids]
    print(f"New raw rows after DB duplicate filtering: {len(new_rows)}")

    with open(RAW_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_rows, f, ensure_ascii=False, indent=2)

    print(f"Filtered raw file saved to {RAW_OUTPUT_FILE}")


if __name__ == "__main__":
    main()