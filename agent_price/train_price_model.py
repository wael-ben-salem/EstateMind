import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

INPUT_FILE = "/opt/project/agent_price/data/training_data.csv"
MODEL_DIR = "/opt/project/agent_price/models_by_type_xgb"
METRICS_FILE = os.path.join(MODEL_DIR, "metrics_by_type_xgb.json")

MIN_ROWS_PER_GROUP = 120


def normalize_type(value):
    if pd.isna(value):
        return None
    v = str(value).strip().lower()
    mapping = {
        "appartement": "appartement",
        "villa": "villa",
        "maison": "maison",
        "studio": "studio",
        "immeuble": "immeuble",
    }
    return mapping.get(v, v)


def map_model_group(property_type):
    if property_type in ["villa", "maison"]:
        return "house_like"
    if property_type == "appartement":
        return "appartement"
    return None


def build_pipeline():
    numeric_features = [
        "superficie_finale",
        "nbr_chambres_final",
        "nbr_sdb_final",
        "image_count",
        "latitude",
        "longitude",
        "year",
        "month",
        "day_of_week",
        "quarter",
        "days_since_start",
    ]

    categorical_features = [
        "ville",
        "location_finale",
        "usage_extrait",
    ]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median"))
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    features = numeric_features + categorical_features
    return pipeline, features


def train_one_group(df_group, group_name, output_dir):
    pipeline, features = build_pipeline()

    X = df_group[features].copy()
    y_real = df_group["price_num"].copy()
    y = np.log1p(y_real)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline.fit(X_train, y_train)

    y_pred_log = pipeline.predict(X_test)
    y_test_real = np.expm1(y_test)
    y_pred_real = np.expm1(y_pred_log)

    mae = mean_absolute_error(y_test_real, y_pred_real)
    mse = mean_squared_error(y_test_real, y_pred_real)
    rmse = mse ** 0.5
    r2 = r2_score(y_test_real, y_pred_real)

    model_path = os.path.join(output_dir, f"price_model_{group_name}_log_xgb.joblib")
    joblib.dump(pipeline, model_path)

    metrics = {
        "group_name": group_name,
        "rows_total": int(len(df_group)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2),
        "model_path": model_path,
    }

    return metrics


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    df["type_bien_extrait_norm"] = df["type_bien_extrait"].apply(normalize_type)
    df["model_group"] = df["type_bien_extrait_norm"].apply(map_model_group)

    df = df[df["model_group"].notna()].copy()

    counts = df["model_group"].value_counts()
    eligible_groups = counts[counts >= MIN_ROWS_PER_GROUP].index.tolist()

    print("Eligible model groups:")
    for g in eligible_groups:
        print(f"- {g}: {counts[g]} rows")

    all_metrics = []

    for group_name in eligible_groups:
        df_group = df[df["model_group"] == group_name].copy()

        print(f"\nTraining XGBoost model for group: {group_name}")
        print(f"Rows: {len(df_group)}")

        metrics = train_one_group(df_group, group_name, MODEL_DIR)
        all_metrics.append(metrics)

        print(f"Saved model: {metrics['model_path']}")
        print(f"MAE: {metrics['mae']:.2f}")
        print(f"RMSE: {metrics['rmse']:.2f}")
        print(f"R2: {metrics['r2']:.4f}")

    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)

    print(f"\nMetrics saved to {METRICS_FILE}")


if __name__ == "__main__":
    main()