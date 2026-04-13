import os
import pandas as pd
from sqlalchemy import create_engine

POSTGRES_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"
OUTPUT_DIR = "/opt/project/agent_price/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "training_data.csv")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    engine = create_engine(POSTGRES_URL)

    query = """
    SELECT
        id,
        price_num,
        superficie_finale,
        nbr_chambres_final,
        nbr_sdb_final,
        image_count,
        ville,
        location_finale,
        transaction_type_final,
        type_bien_extrait,
        usage_extrait,
        latitude,
        longitude,
        published_at_from_id
    FROM clean_tayara
    WHERE price_num IS NOT NULL
      AND superficie_finale IS NOT NULL
      AND ville IS NOT NULL
      AND transaction_type_final IS NOT NULL
      AND usage_extrait IS NOT NULL
    """

    df = pd.read_sql(query, engine)

    # Keep only sale + habitation for the first model
    df = df[
        df["transaction_type_final"].astype(str).str.lower().isin(["à vendre", "a vendre"])
    ]
    df = df[
        df["usage_extrait"].astype(str).str.lower() == "habitation"
    ]

    # Convert date safely
    df["published_at_from_id"] = pd.to_datetime(df["published_at_from_id"], errors="coerce")

    # Create date features
    df["year"] = df["published_at_from_id"].dt.year
    df["month"] = df["published_at_from_id"].dt.month
    df["day_of_week"] = df["published_at_from_id"].dt.dayofweek
    df["quarter"] = df["published_at_from_id"].dt.quarter

    # Optional: days since first date in dataset
    min_date = df["published_at_from_id"].min()
    if pd.notna(min_date):
        df["days_since_start"] = (df["published_at_from_id"] - min_date).dt.days
    else:
        df["days_since_start"] = None

    # Remove obvious outliers
    df = df[(df["price_num"] > 10000) & (df["price_num"] < 10000000)]
    df = df[(df["superficie_finale"] > 20) & (df["superficie_finale"] < 2000)]

    # Drop duplicates on id if any
    df = df.drop_duplicates(subset=["id"]).copy()

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Training data saved to {OUTPUT_FILE}")
    print(f"Rows kept: {len(df)}")
    print("Columns:")
    print(df.columns.tolist())


if __name__ == "__main__":
    main()