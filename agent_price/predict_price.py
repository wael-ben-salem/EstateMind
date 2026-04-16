import os
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = "/opt/project/agent_price/models_by_type_xgb"


def normalize_type(value):
    if value is None:
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


def get_model_path(property_type):
    property_type = normalize_type(property_type)
    group_name = map_model_group(property_type)

    if group_name is None:
        raise ValueError(f"No model group defined for property type: {property_type}")

    model_path = os.path.join(MODEL_DIR, f"price_model_{group_name}_log_xgb.joblib")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No trained model found for group: {group_name}")

    return model_path


def predict_price(input_data: dict):
    property_type = input_data.get("type_bien_extrait")
    model_path = get_model_path(property_type)

    model = joblib.load(model_path)
    df = pd.DataFrame([input_data])
    pred_log = model.predict(df)[0]
    pred_real = np.expm1(pred_log)
    return float(pred_real)


if __name__ == "__main__":
    sample = {
        "superficie_finale": 180,
        "nbr_chambres_final": 3,
        "nbr_sdb_final": 2,
        "image_count": 8,
        "ville": "TUNIS",
        "location_finale": "TUNIS",
        "usage_extrait": "habitation",
        "type_bien_extrait": "appartement",
        "latitude": None,
        "longitude": None,
        "year": 2026,
        "month": 4,
        "day_of_week": 2,
        "quarter": 2,
        "days_since_start": 500,
    }

    price = predict_price(sample)
    print(f"Predicted price: {price:.2f}")