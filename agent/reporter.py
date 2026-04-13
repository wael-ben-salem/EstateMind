from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"

def main():
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        clean_count = conn.execute(text("SELECT COUNT(*) FROM clean_tayara")).scalar()
        agg_count = conn.execute(text("SELECT COUNT(*) FROM agg_price_by_location")).scalar()

        print(f"[REPORT] clean_tayara rows: {clean_count}")
        print(f"[REPORT] agg_price_by_location rows: {agg_count}")

        top_locations = conn.execute(text("""
            SELECT location_finale, avg_price
            FROM agg_price_by_location
            ORDER BY avg_price DESC
            LIMIT 5
        """)).fetchall()

        print("[REPORT] Top 5 locations by avg_price:")
        for row in top_locations:
            print(row)

if __name__ == "__main__":
    main()