"""
EstateMind — Anomaly Detection & Market Opportunity Scoring
============================================================
Location: estatemind/services/anomaly_detection/anomaly_detector.py

Loads price model artefacts produced by the new price_predictor.py
(best_model.pkl / target_encoder.pkl / model_meta.pkl)
then runs the full anomaly pipeline: Z-score + IQR + Isolation Forest → consensus.

Usage (PowerShell — use backticks for line continuation):
  python -m services.anomaly_detection.anomaly_detector `
      --data data_cleaned/bigfinal_realestate_Cleaned.csv `
      --model-dir model_artefact

Or one line:
  python -m services.anomaly_detection.anomaly_detector --data data_cleaned/bigfinal_realestate_Cleaned.csv --model-dir model_artefact
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

ROOT = Path(__file__).resolve().parents[2]   # estatemind/

# Artefact filenames — must match what price_predictor.py saved
MODEL_FILE   = "best_model.pkl"
ENCODER_FILE = "target_encoder.pkl"
META_FILE    = "model_meta.pkl"

DEFAULT_MODEL_DIR = ROOT / "model_artefact"
DEFAULT_DATA      = ROOT / "data_cleaned" / "bigfinal_realestate_Cleaned.csv"
DEFAULT_OUTPUTS   = ROOT / "outputs"

PRIX_MIN = 5_000
PRIX_MAX = 20_000_000

GOV_COORDS = {
    "Tunis":       (36.8189, 10.1658), "Ariana":      (36.8665, 10.1647),
    "Ben Arous":   (36.7533, 10.2282), "Manouba":     (36.8093, 10.0963),
    "Nabeul":      (36.4561, 10.7376), "Zaghouan":    (36.4029, 10.1434),
    "Bizerte":     (37.2744,  9.8739), "Beja":        (36.7333,  9.1833),
    "Jendouba":    (36.5011,  8.7757), "Le Kef":      (36.1825,  8.7147),
    "Siliana":     (36.0851,  9.3709), "Sousse":      (35.8288, 10.6363),
    "Monastir":    (35.7643, 10.8113), "Mahdia":      (35.5047, 11.0622),
    "Sfax":        (34.7400, 10.7600), "Kairouan":    (35.6781, 10.0968),
    "Kasserine":   (35.1672,  8.8306), "Sidi Bouzid": (35.0382,  9.4849),
    "Gabes":       (33.8828, 10.0982), "Medenine":    (33.3549, 10.5055),
    "Tataouine":   (32.9293, 10.4509), "Gafsa":       (34.4250,  8.7842),
    "Tozeur":      (33.9197,  8.1335), "Kebili":      (33.7050,  8.9690),
}

LABEL_COLORS = {
    "Strong Opportunity": "green",
    "Opportunity":        "lightgreen",
    "Borderline":         "purple",
    "Slight Overpricing": "orange",
    "Overpriced Risk":    "red",
    "Normal":             "gray",
}


def _haversine(lat1, lon1, lat2=36.8065, lon2=10.1815):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    TABULAR_COLS = [
        "surface", "pieces", "etage", "prix",
        "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
        "has_garage", "has_gardien", "has_jardin", "has_parking",
        "has_piscine", "has_terrasse",
        "gouvernerat", "ville", "type", "contrat",
        "latitude", "longitude",
    ]
    AMENITY_COLS = [
        "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
        "has_garage", "has_gardien", "has_jardin", "has_parking",
        "has_piscine", "has_terrasse",
    ]
    present = [c for c in TABULAR_COLS if c in df.columns]
    df_gp   = df[present].copy()
    df_gp["prix"] = pd.to_numeric(df_gp["prix"], errors="coerce")
    df_gp = df_gp[df_gp["prix"].between(PRIX_MIN, PRIX_MAX)].copy()

    if "surface" in df_gp.columns:
        df_gp["price_per_m2"] = df_gp["prix"] / df_gp["surface"].replace(0, np.nan)
    if "surface" in df_gp.columns and "pieces" in df_gp.columns:
        df_gp["surface_per_piece"] = df_gp["surface"] / df_gp["pieces"].replace(0, np.nan)
    if "has_ascenseur" in df_gp.columns and "etage" in df_gp.columns:
        df_gp["etage_x_ascenseur"] = df_gp["etage"].fillna(0) * df_gp["has_ascenseur"].fillna(0)

    amenities = [c for c in AMENITY_COLS if c in df_gp.columns]
    df_gp["total_amenities"] = df_gp[amenities].fillna(0).sum(axis=1)

    if "latitude" in df_gp.columns and "longitude" in df_gp.columns:
        df_gp["latitude"]  = df_gp["latitude"].fillna(df_gp["latitude"].median())
        df_gp["longitude"] = df_gp["longitude"].fillna(df_gp["longitude"].median())
        df_gp["dist_to_center"] = _haversine(df_gp["latitude"], df_gp["longitude"])

    logger.info("Features built: %d rows x %d cols", *df_gp.shape)
    return df_gp


def compute_price_gap(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_gap"]     = df["prix"] - df["predicted_price"]
    df["price_gap_pct"] = (
        (df["prix"] - df["predicted_price"]) / df["predicted_price"].abs().clip(lower=1_000)
    ) * 100
    df["price_gap_pct"] = df["price_gap_pct"].clip(-200, 200)
    return df


def score_anomalies(df, iso_features=None, zscore_threshold=2.5,
                    iqr_multiplier=2.0, contamination=0.05, consensus_threshold=2):
    df  = df.copy()
    gap = df["price_gap_pct"].fillna(0)

    df["zscore_anomaly"] = (np.abs(stats.zscore(gap)) > zscore_threshold).astype(int)

    q1, q3 = gap.quantile(0.25), gap.quantile(0.75)
    iqr     = q3 - q1
    df["iqr_anomaly"] = (
        (gap < q1 - iqr_multiplier * iqr) | (gap > q3 + iqr_multiplier * iqr)
    ).astype(int)

    default_iso_feats = [
        c for c in ["prix", "predicted_price", "price_gap_pct", "surface",
                    "pieces", "dist_to_center", "total_amenities", "price_per_m2"]
        if c in df.columns
    ]
    feats = iso_features or default_iso_feats
    X_iso = df[feats].fillna(df[feats].median())
    iso = IsolationForest(n_estimators=200, contamination=contamination,
                          random_state=RANDOM_SEED, n_jobs=-1)
    df["iso_anomaly"]   = (iso.fit_predict(X_iso) == -1).astype(int)
    df["iso_raw_score"] = iso.decision_function(X_iso)

    df["anomaly_votes"] = df["zscore_anomaly"] + df["iqr_anomaly"] + df["iso_anomaly"]
    df["is_anomaly"]    = (df["anomaly_votes"] >= consensus_threshold).astype(int)

    n = df["is_anomaly"].sum()
    logger.info("Anomalies (>=%d/3): %d / %d  (%.1f%%)",
                consensus_threshold, n, len(df), n / len(df) * 100)
    logger.info("  Z-score: %d  |  IQR: %d  |  IsolationForest: %d",
                df["zscore_anomaly"].sum(), df["iqr_anomaly"].sum(), df["iso_anomaly"].sum())
    return df


def label_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    def _label(row):
        if row["is_anomaly"] == 0:
            return "Normal"
        gap = row["price_gap_pct"]
        if   gap < -20: return "Strong Opportunity"
        elif gap < -10: return "Opportunity"
        elif gap >  20: return "Overpriced Risk"
        elif gap >  10: return "Slight Overpricing"
        return "Borderline"

    df = df.copy()
    df["opportunity_label"] = df.apply(_label, axis=1)

    conf_df = pd.DataFrame({
        "abs_gap": df["price_gap_pct"].abs(),
        "z_score": np.abs(stats.zscore(df["price_gap_pct"].fillna(0))),
        "iso_neg": -df["iso_raw_score"],
        "votes":   df["anomaly_votes"],
    })
    conf_norm = MinMaxScaler().fit_transform(conf_df.fillna(0))
    df["anomaly_confidence"] = np.round(conf_norm.mean(axis=1), 3)
    df.loc[df["is_anomaly"] == 0, "anomaly_confidence"] = 0.0

    logger.info("Label distribution:\n%s", df["opportunity_label"].value_counts().to_string())
    return df


def build_anomaly_map(df_scored: pd.DataFrame, output_path: str) -> str:
    try:
        import folium
        from folium.plugins import HeatMap, MarkerCluster, MiniMap
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "folium", "-q"])
        import folium
        from folium.plugins import HeatMap, MarkerCluster, MiniMap

    df_map = df_scored[df_scored["is_anomaly"] == 1].copy()
    df_map["_lat"] = pd.to_numeric(df_map.get("latitude",  np.nan), errors="coerce")
    df_map["_lon"] = pd.to_numeric(df_map.get("longitude", np.nan), errors="coerce")

    if "gouvernerat" in df_map.columns:
        for gov, (lat_g, lon_g) in GOV_COORDS.items():
            mask = df_map["_lat"].isna() & df_map["gouvernerat"].str.contains(
                gov, case=False, na=False)
            df_map.loc[mask, "_lat"] = lat_g + np.random.uniform(-0.05, 0.05, mask.sum())
            df_map.loc[mask, "_lon"] = lon_g + np.random.uniform(-0.05, 0.05, mask.sum())

    df_map = df_map.dropna(subset=["_lat", "_lon"]).head(2000)
    logger.info("Building map — %d markers", len(df_map))

    m       = folium.Map(location=[33.8869, 9.5375], zoom_start=7, tiles="CartoDB positron")
    MiniMap(toggle_display=True).add_to(m)
    cluster = MarkerCluster(name="Anomalies").add_to(m)

    for _, row in df_map.iterrows():
        color = LABEL_COLORS.get(row["opportunity_label"], "gray")
        gap   = row["price_gap_pct"]
        popup = (
            f"<b>{str(row.get('titre', 'N/A'))[:80]}</b><br>"
            f"Actual: <b>{row['prix']:,.0f} TND</b><br>"
            f"Predicted: {row['predicted_price']:,.0f} TND<br>"
            f"Gap: <b style='color:{'green' if gap < 0 else 'red'}'>{gap:+.1f}%</b><br>"
            f"Label: <b>{row['opportunity_label']}</b><br>"
            f"Confidence: {row['anomaly_confidence']:.2f}"
        )
        folium.CircleMarker(
            location=[row["_lat"], row["_lon"]],
            radius=max(4, min(12, abs(gap) / 10)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{row['opportunity_label']} | {gap:+.0f}%",
        ).add_to(cluster)

    heat_data = [[r["_lat"], r["_lon"], r["anomaly_confidence"]] for _, r in df_map.iterrows()]
    HeatMap(heat_data, name="Anomaly Density", radius=15, blur=10, min_opacity=0.3).add_to(m)
    folium.LayerControl().add_to(m)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    logger.info("Map saved: %s", output_path)
    return output_path


class AnomalyDetector:
    def __init__(self, model_dir=None):
        self.model_dir    = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model       = None
        self._encoder     = None
        self._num_feats:  List[str] = []
        self._cat_feats:  List[str] = []
        self._model_name: str       = ""

    def _load(self):
        if self._model is not None:
            return
        for fname in [MODEL_FILE, ENCODER_FILE, META_FILE]:
            p = self.model_dir / fname
            if not p.exists():
                raise FileNotFoundError(
                    f"Artefact not found: {p}\n"
                    f"Train first: python -m services.price_prediction.price_predictor "
                    f"train --data <csv> --model-dir {self.model_dir}"
                )
        self._model      = joblib.load(self.model_dir / MODEL_FILE)
        self._encoder    = joblib.load(self.model_dir / ENCODER_FILE)
        meta             = joblib.load(self.model_dir / META_FILE)
        self._num_feats  = meta["NUM_FEATS"]
        self._cat_feats  = meta["CAT_FEATS"]
        self._model_name = meta.get("BEST_MODEL_NAME", "unknown")
        logger.info("Loaded model: %s  from %s", self._model_name, self.model_dir)

    def _predict_prices(self, df_feat: pd.DataFrame) -> np.ndarray:
        self._load()
        all_feats = self._num_feats + self._cat_feats
        X = df_feat[[c for c in all_feats if c in df_feat.columns]].copy()
        for col in all_feats:
            if col not in X.columns:
                X[col] = np.nan
        X     = X[all_feats]
        X_enc = self._encoder.transform(X)
        X_enc = X_enc.infer_objects(copy=False).fillna(X_enc.median())
        return self._model.predict(X_enc)

    def run(self, data_path=None, min_price=10_000, max_price=5_000_000,
            max_gap_pct=90, build_map=True, report_path=None, map_path=None):
        csv        = Path(data_path) if data_path else DEFAULT_DATA
        report_out = report_path or str(DEFAULT_OUTPUTS / "anomaly_report.csv")
        map_out    = map_path    or str(DEFAULT_OUTPUTS / "anomaly_map.html")

        df      = pd.read_csv(csv, low_memory=False)
        logger.info("Loaded %d rows", len(df))
        df_feat = build_features(df)

        df_scored = df_feat.copy()
        df_scored["predicted_price"] = self._predict_prices(df_feat)
        df_scored = compute_price_gap(df_scored)

        before = len(df_scored)
        df_scored = df_scored[
            (df_scored["prix"]              >= min_price) &
            (df_scored["prix"]              <= max_price) &
            (df_scored["predicted_price"]   >= min_price) &
            (df_scored["predicted_price"]   <= max_price) &
            (df_scored["price_gap_pct"].abs() <= max_gap_pct)
        ].copy()
        logger.info("After filtering: %d rows kept (removed %d)",
                    len(df_scored), before - len(df_scored))

        df_scored = score_anomalies(df_scored)
        df_scored = label_opportunities(df_scored)

        Path(report_out).parent.mkdir(parents=True, exist_ok=True)
        df_scored.to_csv(report_out, index=True, encoding="utf-8-sig")
        logger.info("Report saved: %s", report_out)

        if build_map:
            for col in ["latitude", "longitude", "gouvernerat", "titre"]:
                if col in df.columns:
                    df_scored[col] = df.loc[df_scored.index, col]
            build_anomaly_map(df_scored, map_out)

        return df_scored

    def score_single(self, property_dict: Dict[str, Any]) -> Dict[str, Any]:
        self._load()
        if "prix" not in property_dict:
            raise ValueError("'prix' is required.")

        df_single = pd.DataFrame([property_dict])
        df_feat   = build_features(df_single)
        if df_feat.empty:
            raise ValueError(f"Prix must be between {PRIX_MIN:,} and {PRIX_MAX:,} TND.")

        df_feat["predicted_price"] = self._predict_prices(df_feat)
        df_feat = compute_price_gap(df_feat)

        gap        = float(df_feat["price_gap_pct"].iloc[0])
        is_anomaly = abs(gap) > 20
        if not is_anomaly:  label = "Normal"
        elif gap < -20:     label = "Strong Opportunity"
        elif gap < -10:     label = "Opportunity"
        elif gap >  20:     label = "Overpriced Risk"
        elif gap >  10:     label = "Slight Overpricing"
        else:               label = "Borderline"

        return {
            "predicted_price":    round(float(df_feat["predicted_price"].iloc[0]), 2),
            "actual_price":       float(property_dict["prix"]),
            "price_gap_pct":      round(gap, 2),
            "is_anomaly":         int(is_anomaly),
            "opportunity_label":  label,
            "anomaly_confidence": round(min(abs(gap) / 100, 1.0), 3),
            "model_name":         self._model_name,
        }


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="anomaly_detector",
        description="EstateMind Anomaly Detector",
    )
    parser.add_argument("--data",        default=str(DEFAULT_DATA))
    parser.add_argument("--model-dir",   default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--report",      default=str(DEFAULT_OUTPUTS / "anomaly_report.csv"))
    parser.add_argument("--map",         default=str(DEFAULT_OUTPUTS / "anomaly_map.html"))
    parser.add_argument("--no-map",      action="store_true")
    parser.add_argument("--min-price",   type=float, default=10_000)
    parser.add_argument("--max-price",   type=float, default=5_000_000)
    parser.add_argument("--max-gap-pct", type=float, default=90)
    return parser


def main():
    args     = _build_parser().parse_args()
    detector = AnomalyDetector(model_dir=args.model_dir)
    report   = detector.run(
        data_path=args.data,
        min_price=args.min_price,
        max_price=args.max_price,
        max_gap_pct=args.max_gap_pct,
        build_map=not args.no_map,
        report_path=args.report,
        map_path=args.map,
    )
    print(f"\n Done  {report['is_anomaly'].sum():,} anomalies / {len(report):,} listings\n")
    print(report["opportunity_label"].value_counts().to_string())


if __name__ == "__main__":
    main()