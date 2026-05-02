"""
EstateMind — Shared Feature Engineering
========================================
Gold+ pipeline shared by both the price prediction and anomaly detection services.
Both services import from here — never duplicate this logic.

Location: estatemind/shared/feature_engineering.py
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

TARGET = "prix"
CENTER_LAT, CENTER_LON = 36.8065, 10.1815  # Tunis city center

TABULAR_COLS = [
    "surface", "pieces", "etage", "prix",
    "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
    "has_garage", "has_gardien", "has_jardin", "has_parking",
    "has_piscine", "has_terrasse",
    "gouvernerat", "ville", "type", "contrat",
    "latitude", "longitude",
]

CAT_FEATS = ["type", "contrat", "gouvernerat"]

AMENITY_COLS = [
    "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
    "has_garage", "has_gardien", "has_jardin", "has_parking",
    "has_piscine", "has_terrasse",
]

# Tunisian governorate centroids — used as fallback when lat/lon is missing
GOV_COORDS = {
    "Tunis":      (36.8189, 10.1658), "Ariana":     (36.8665, 10.1647),
    "Ben Arous":  (36.7533, 10.2282), "Manouba":    (36.8093, 10.0963),
    "Nabeul":     (36.4561, 10.7376), "Zaghouan":   (36.4029, 10.1434),
    "Bizerte":    (37.2744,  9.8739), "Beja":       (36.7333,  9.1833),
    "Jendouba":   (36.5011,  8.7757), "Le Kef":     (36.1825,  8.7147),
    "Siliana":    (36.0851,  9.3709), "Sousse":     (35.8288, 10.6363),
    "Monastir":   (35.7643, 10.8113), "Mahdia":     (35.5047, 11.0622),
    "Sfax":       (34.7400, 10.7600), "Kairouan":   (35.6781, 10.0968),
    "Kasserine":  (35.1672,  8.8306), "Sidi Bouzid":(35.0382,  9.4849),
    "Gabes":      (33.8828, 10.0982), "Medenine":   (33.3549, 10.5055),
    "Tataouine":  (32.9293, 10.4509), "Gafsa":      (34.4250,  8.7842),
    "Tozeur":     (33.9197,  8.1335), "Kebili":     (33.7050,  8.9690),
}


# ─────────────────────────────────────────────────────────────────────────────
# Geo helper
# ─────────────────────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Haversine distance in km between two points (or arrays of points)."""
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────────────────
# Gold+ feature pipeline
# ─────────────────────────────────────────────────────────────────────────────

def build_gold_plus_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the Gold+ feature set from a raw real-estate dataframe.

    Steps:
      - Keep only known tabular columns present in df
      - Drop rows with missing prix
      - Compute derived features: price_per_m2, surface_per_piece,
        etage_x_ascenseur, total_amenities, dist_to_center

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe, column names matching the dataset schema.

    Returns
    -------
    pd.DataFrame
        Enriched dataframe ready for ML encoding.
    """
    # Ensure target column exists
    if TARGET not in df.columns:
        df = df.copy()
        df[TARGET] = np.nan

    present_tabular = [c for c in TABULAR_COLS if c in df.columns]
    df_gp = df[present_tabular].copy()
    df_gp = df_gp.dropna(subset=[TARGET]).copy()

    # Derived features
    if "surface" in df_gp.columns:
        df_gp["price_per_m2"] = df_gp[TARGET] / df_gp["surface"].replace(0, np.nan)

    if "surface" in df_gp.columns and "pieces" in df_gp.columns:
        df_gp["surface_per_piece"] = df_gp["surface"] / df_gp["pieces"].replace(0, np.nan)

    if "has_ascenseur" in df_gp.columns and "etage" in df_gp.columns:
        df_gp["etage_x_ascenseur"] = (
            df_gp["etage"].fillna(0) * df_gp["has_ascenseur"].fillna(0)
        )

    present_amenities = [c for c in AMENITY_COLS if c in df_gp.columns]
    df_gp["total_amenities"] = df_gp[present_amenities].fillna(0).sum(axis=1)

    if "latitude" in df_gp.columns and "longitude" in df_gp.columns:
        df_gp["latitude"]  = df_gp["latitude"].fillna(df_gp["latitude"].median())
        df_gp["longitude"] = df_gp["longitude"].fillna(df_gp["longitude"].median())
        df_gp["dist_to_center"] = haversine(
            df_gp["latitude"], df_gp["longitude"], CENTER_LAT, CENTER_LON
        )

    logger.info("Gold+ features built: %d rows × %d cols", *df_gp.shape)
    return df_gp


# ─────────────────────────────────────────────────────────────────────────────
# Target encoding
# ─────────────────────────────────────────────────────────────────────────────

def _install(pkg: str):
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=False)


def encode_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: Optional[pd.DataFrame] = None,
    cat_feats: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Any]:
    """
    Fit a TargetEncoder on X_train; apply to X_test if provided.

    Returns
    -------
    (X_train_enc, X_test_enc, encoder)
    X_test_enc is None when X_test is not passed.
    """
    try:
        import category_encoders as ce
    except ImportError:
        _install("category_encoders")
        import category_encoders as ce

    cats = [c for c in (cat_feats or CAT_FEATS) if c in X_train.columns]
    te = ce.TargetEncoder(cols=cats, smoothing=10)

    X_train_enc = te.fit_transform(X_train, y_train)
    med = X_train_enc.median()
    X_train_enc = X_train_enc.fillna(med)

    X_test_enc = None
    if X_test is not None:
        X_test_enc = te.transform(X_test).fillna(med)

    return X_train_enc, X_test_enc, te