import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    size,
    when,
    trim,
    coalesce,
    to_timestamp,
    expr,
    length,
    upper,
    regexp_replace,
    lower
)
from sqlalchemy import create_engine

INPUT_PATH = "/opt/spark_app/data/TayaraDataEnrichedLocated.json"
POSTGRES_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"

spark = (
    SparkSession.builder
    .appName("tayara_etl")
    .getOrCreate()
)

df = spark.read.option("multiline", "true").json(INPUT_PATH)

# 1) Basic cleaning + normalization + safe casting
clean_df = (
    df.dropDuplicates(["id"])
      .withColumn("title", trim(col("title")))
      .withColumn("description", trim(col("description")))
      .withColumn("location", upper(trim(regexp_replace(col("location"), r"\s+", " "))))
      .withColumn("transaction_type", trim(regexp_replace(col("transaction_type"), r"\s+", " ")))
      .withColumn("transaction_type_extrait", trim(regexp_replace(col("transaction_type_extrait"), r"\s+", " ")))
      .withColumn("ville", upper(trim(regexp_replace(col("ville"), r"\s+", " "))))
      .withColumn("quartier", upper(trim(regexp_replace(col("quartier"), r"\s+", " "))))
      .withColumn("delegation", upper(trim(regexp_replace(col("delegation"), r"\s+", " "))))
      .withColumn("gouvernorat", upper(trim(regexp_replace(col("gouvernorat"), r"\s+", " "))))

      # remove common accents
      .withColumn("ville", regexp_replace(col("ville"), "É", "E"))
      .withColumn("ville", regexp_replace(col("ville"), "È", "E"))
      .withColumn("ville", regexp_replace(col("ville"), "Ê", "E"))
      .withColumn("ville", regexp_replace(col("ville"), "À", "A"))
      .withColumn("ville", regexp_replace(col("ville"), "Â", "A"))
      .withColumn("ville", regexp_replace(col("ville"), "Ù", "U"))
      .withColumn("ville", regexp_replace(col("ville"), "Û", "U"))
      .withColumn("ville", regexp_replace(col("ville"), "Ô", "O"))
      .withColumn("ville", regexp_replace(col("ville"), "Î", "I"))

      .withColumn("quartier", regexp_replace(col("quartier"), "É", "E"))
      .withColumn("quartier", regexp_replace(col("quartier"), "È", "E"))
      .withColumn("quartier", regexp_replace(col("quartier"), "Ê", "E"))
      .withColumn("quartier", regexp_replace(col("quartier"), "À", "A"))
      .withColumn("quartier", regexp_replace(col("quartier"), "Â", "A"))

      .withColumn("delegation", regexp_replace(col("delegation"), "É", "E"))
      .withColumn("delegation", regexp_replace(col("delegation"), "È", "E"))
      .withColumn("delegation", regexp_replace(col("delegation"), "Ê", "E"))
      .withColumn("delegation", regexp_replace(col("delegation"), "À", "A"))
      .withColumn("delegation", regexp_replace(col("delegation"), "Â", "A"))

      .withColumn("location", regexp_replace(col("location"), "É", "E"))
      .withColumn("location", regexp_replace(col("location"), "È", "E"))
      .withColumn("location", regexp_replace(col("location"), "Ê", "E"))
      .withColumn("location", regexp_replace(col("location"), "À", "A"))
      .withColumn("location", regexp_replace(col("location"), "Â", "A"))

      .withColumn("title_clean", upper(regexp_replace(col("title"), r"[^\w\s]", " ")))
      .withColumn("description_clean", upper(regexp_replace(col("description"), r"[^\w\s]", " ")))
      .withColumn("ville_clean", upper(regexp_replace(col("ville"), r"[^\w\s]", " ")))
      .withColumn("quartier_clean", upper(regexp_replace(col("quartier"), r"[^\w\s]", " ")))
      .withColumn("delegation_clean", upper(regexp_replace(col("delegation"), r"[^\w\s]", " ")))

      .withColumn("price_num", expr("try_cast(price as double)"))
      .withColumn("superficie_num", expr("try_cast(superficie as double)"))
      .withColumn("nbr_chambres_num", expr("try_cast(nbr_chambres as double)"))
      .withColumn("nbr_sdb_num", expr("try_cast(nbr_salles_de_bain as double)"))
      .withColumn("surface_extraite_num", expr("try_cast(surface_extraite as double)"))
      .withColumn("nb_chambres_extrait_num", expr("try_cast(nb_chambres_extrait as double)"))
      .withColumn("nb_sdb_extrait_num", expr("try_cast(nb_sdb_extrait as double)"))
      .withColumn("image_count", size(col("images")))
      .withColumn("scraped_at_ts", to_timestamp(col("scraped_at")))
      .withColumn("published_at_from_id_ts", to_timestamp(col("published_at_from_id")))
      .withColumn(
          "pub_hours_ago",
          expr("try_cast(regexp_extract(lower(pub_date), '(\\\\d+)', 1) as int)")
      )

      # standardize transaction types
      .withColumn(
          "transaction_type_std",
          when(
              lower(col("transaction_type")).isin("a vendre", "à vendre", "vente", "بيع"),
              "A vendre"
          ).when(
              lower(col("transaction_type")).isin("a louer", "à louer", "location", "كراء", "إيجار", "3", "38", "45"),
              "A louer"
          ).otherwise(None)
      )
      .withColumn(
          "transaction_type_extrait_std",
          when(
              lower(col("transaction_type_extrait")).isin("a vendre", "à vendre", "vente", "بيع"),
              "A vendre"
          ).when(
              lower(col("transaction_type_extrait")).isin("a louer", "à louer", "location", "كراء", "إيجار", "3", "38", "45"),
              "A louer"
          ).otherwise(None)
      )
)

# 2) Build final business columns
clean_df = (
    clean_df
      .withColumn("superficie_finale", coalesce(col("superficie_num"), col("surface_extraite_num")))
      .withColumn("nbr_chambres_final", coalesce(col("nbr_chambres_num"), col("nb_chambres_extrait_num")))
      .withColumn("nbr_sdb_final", coalesce(col("nbr_sdb_num"), col("nb_sdb_extrait_num")))
      .withColumn("transaction_type_final", coalesce(col("transaction_type_std"), col("transaction_type_extrait_std")))
      .withColumn("location_finale", coalesce(col("quartier"), col("delegation"), col("ville"), col("location")))
)

# 3) Calculate price per m²
clean_df = (
    clean_df
      .withColumn(
          "price_per_m2",
          when(
              (col("price_num").isNotNull()) &
              (col("superficie_finale").isNotNull()) &
              (col("superficie_finale") > 0),
              col("price_num") / col("superficie_finale")
          )
      )
)

# 4) Null-out obvious anomalies
clean_df = (
    clean_df
      .withColumn(
          "price_num",
          when((col("price_num") <= 0) | (col("price_num") > 100000000), None).otherwise(col("price_num"))
      )
      .withColumn(
          "superficie_finale",
          when((col("superficie_finale") <= 0) | (col("superficie_finale") > 100000), None).otherwise(col("superficie_finale"))
      )
      .withColumn(
          "price_per_m2",
          when((col("price_per_m2") <= 0) | (col("price_per_m2") > 1000000), None).otherwise(col("price_per_m2"))
      )
)

# 5) Quality flags
clean_df = (
    clean_df
      .withColumn("is_price_suspicious", when(col("price_num").isNull(), True).otherwise(False))
      .withColumn("is_surface_suspicious", when(col("superficie_finale").isNull(), True).otherwise(False))
      .withColumn(
          "is_city_missing",
          when(col("ville").isNull() | (length(trim(col("ville"))) == 0), True).otherwise(False)
      )
      .withColumn(
          "is_transaction_missing",
          when(col("transaction_type_final").isNull() | (length(trim(col("transaction_type_final"))) == 0), True).otherwise(False)
      )
      .withColumn(
          "is_geo_missing",
          when(col("latitude").isNull() | col("longitude").isNull(), True).otherwise(False)
      )
)

# 6) Drop rows with null/empty ville
filtered_df = (
    clean_df.filter(col("id").isNotNull())
            .filter(col("title").isNotNull())
            .filter(col("ville").isNotNull())
            .filter(length(trim(col("ville"))) > 0)
)

# 7) Build stricter analytics subset
analytics_df = (
    filtered_df.filter(col("price_num").isNotNull())
               .filter(col("superficie_finale").isNotNull())
               .filter(col("transaction_type_final").isNotNull())
               .filter(~col("is_price_suspicious"))
               .filter(~col("is_surface_suspicious"))
)

# 8) Aggregation
agg_df = (
    analytics_df.groupBy("location_finale", "transaction_type_final")
                .avg("price_num", "superficie_finale", "price_per_m2")
                .withColumnRenamed("avg(price_num)", "avg_price")
                .withColumnRenamed("avg(superficie_finale)", "avg_superficie")
                .withColumnRenamed("avg(price_per_m2)", "avg_price_per_m2")
)

# 9) Export tables to pandas
clean_pd = filtered_df.select(
    "id",
    "title",
    "description",
    "location",
    "location_finale",
    "transaction_type",
    "transaction_type_final",
    "price_num",
    "superficie_num",
    "superficie_finale",
    "nbr_chambres_num",
    "nbr_chambres_final",
    "nbr_sdb_num",
    "nbr_sdb_final",
    "image_count",
    "pub_hours_ago",
    "price_per_m2",
    "scraped_at",
    "published_at_from_id",
    "num_etage",
    "adresse_raw",
    "ville",
    "quartier",
    "delegation",
    "gouvernorat",
    "matched_state",
    "matched_delegation",
    "matched_locality_name",
    "matched_postal_code",
    "latitude",
    "longitude",
    "geo_match_level",
    "geo_source",
    "type_bien_extrait",
    "usage_extrait",
    "titre_foncier_extrait",
    "source_extraction",
    "extraction_confidence",
    "is_price_suspicious",
    "is_surface_suspicious",
    "is_city_missing",
    "is_transaction_missing",
    "is_geo_missing"
).toPandas()

analytics_pd = analytics_df.select(
    "id",
    "title",
    "location_finale",
    "transaction_type_final",
    "price_num",
    "superficie_finale",
    "price_per_m2",
    "ville",
    "latitude",
    "longitude",
    "type_bien_extrait",
    "usage_extrait"
).toPandas()

agg_pd = agg_df.toPandas()

# 10) Write to PostgreSQL
engine = create_engine(POSTGRES_URL)

clean_pd["id"] = clean_pd["id"].astype(str)
clean_pd = clean_pd.drop_duplicates(subset=["id"]).copy()
print(f"Rows to load into clean_tayara: {len(clean_pd)}")

# full refresh so old dirty rows are removed
clean_pd.to_sql("clean_tayara", engine, if_exists="replace", index=False)
print(f"Recreated clean_tayara with {len(clean_pd)} rows.")

analytics_pd.to_sql("clean_tayara_analytics", engine, if_exists="replace", index=False)
agg_pd.to_sql("agg_price_by_location", engine, if_exists="replace", index=False)

print("Derived tables refreshed successfully.")
print("ETL finished successfully.")

spark.stop()