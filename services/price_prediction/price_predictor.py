"""
EstateMind — Price Predictor Service
======================================
Proper CLI module. Run as:
    python -m services.price_prediction.price_predictor train \
        --data data_cleaned/bigfinal_realestate_Cleaned.csv \
        --model-dir model_artefact

Trains the full Model Arena (10+ models), tunes Random Forest & LightGBM,
builds a Stacking ensemble, selects the best model by MAE, and saves artefacts.
"""

import argparse
import json
import logging
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend — safe for CLI
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
    StackingRegressor,
)
from sklearn.linear_model import ElasticNet, HuberRegressor, Lasso, Ridge, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import (
    PolynomialFeatures,
    RobustScaler,
    StandardScaler,
)

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("price_predictor")

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

PALETTE = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B", "#44BBA4"]

# ── Price sanity bounds (TND) ─────────────────────────────────────────────────
PRIX_MIN = 50_000        # below this → placeholder / rent / data error
PRIX_MAX = 20_000_000   # above this → data error


# ─────────────────────────────────────────────────────────────────────────────
# Lazy optional imports
# ─────────────────────────────────────────────────────────────────────────────
def _import_lgb():
    import lightgbm as lgb
    return lgb


def _import_xgb():
    import xgboost as xgb
    return xgb


def _import_catboost():
    from catboost import CatBoostRegressor
    return CatBoostRegressor


def _import_ce():
    import category_encoders as ce
    return ce


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE only on rows where actual price > PRIX_MIN to avoid division explosions."""
    mask = y_true > PRIX_MIN
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _metrics(y_true, y_pred) -> Dict[str, float]:
    return {
        "MAE":    round(float(mean_absolute_error(y_true, y_pred)), 2),
        "RMSE":   round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "MAPE_pct": round(_safe_mape(np.array(y_true), np.array(y_pred)), 2),
        "R2":     round(float(r2_score(y_true, y_pred)), 4),
    }


def _haversine(lat1, lon1, lat2=36.8065, lon2=10.1815) -> np.ndarray:
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────────────────
# PricePredictor class
# ─────────────────────────────────────────────────────────────────────────────
class PricePredictor:
    """Full training pipeline: data → features → arena → tune → save."""

    # ── Data loading & cleaning ───────────────────────────────────────────────
    def _load(self, data_path: Path) -> pd.DataFrame:
        data_path = Path(data_path).resolve()
        if not data_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {data_path}\n"
                f"Current working directory: {Path.cwd()}"
            )
        df = pd.read_csv(data_path, low_memory=False)
        logger.info(f"Loaded {df.shape[0]:,} rows × {df.shape[1]} cols from {data_path.name}")

        # Ensure expected columns exist
        for col in ["titre", "description", "caracteristiques", "prix", "surface",
                    "pieces", "gouvernerat", "ville", "type", "contrat",
                    "latitude", "longitude", "images"]:
            if col not in df.columns:
                df[col] = None

        # ── Prix cleaning ────────────────────────────────────────────────────
        df["prix"] = pd.to_numeric(df["prix"], errors="coerce")
        before = len(df)
        df = df[df["prix"].between(PRIX_MIN, PRIX_MAX)].copy()
        logger.info(
            f"Price filter [{PRIX_MIN:,}–{PRIX_MAX:,} TND]: "
            f"kept {len(df):,} / {before:,} rows ({len(df)/before*100:.1f}%)"
        )

        q = df["prix"].quantile([.01, .05, .25, .50, .75, .95, .99])
        logger.info(f"Prix distribution:\n{q.to_string()}")
        return df

    # ── Feature engineering ───────────────────────────────────────────────────
    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        TABULAR_COLS = [
            "surface", "pieces", "etage", "prix",
            "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
            "has_garage", "has_gardien", "has_jardin", "has_parking",
            "has_piscine", "has_terrasse",
            "gouvernerat", "ville", "type", "contrat",
            "latitude", "longitude",
        ]
        TABULAR_COLS = [c for c in TABULAR_COLS if c in df.columns]
        df_gp = df[TABULAR_COLS].copy()
        df_gp = df_gp.dropna(subset=["prix"]).copy()

        if "surface" in df_gp.columns:
            df_gp["price_per_m2"] = df_gp["prix"] / df_gp["surface"].replace(0, np.nan)
        if "surface" in df_gp.columns and "pieces" in df_gp.columns:
            df_gp["surface_per_piece"] = df_gp["surface"] / df_gp["pieces"].replace(0, np.nan)
        if "has_ascenseur" in df_gp.columns and "etage" in df_gp.columns:
            df_gp["etage_x_ascenseur"] = (
                df_gp["etage"].fillna(0) * df_gp["has_ascenseur"].fillna(0)
            )

        amenity_cols = [c for c in [
            "has_ascenseur", "has_balcon", "has_chaffage", "has_climatisation",
            "has_garage", "has_gardien", "has_jardin", "has_parking",
            "has_piscine", "has_terrasse",
        ] if c in df_gp.columns]
        df_gp["total_amenities"] = df_gp[amenity_cols].fillna(0).sum(axis=1)

        if "latitude" in df_gp.columns and "longitude" in df_gp.columns:
            df_gp["latitude"] = df_gp["latitude"].fillna(df_gp["latitude"].median())
            df_gp["longitude"] = df_gp["longitude"].fillna(df_gp["longitude"].median())
            df_gp["dist_to_center"] = _haversine(df_gp["latitude"], df_gp["longitude"])

        logger.info(f"Gold+ features built: {df_gp.shape[0]:,} rows × {df_gp.shape[1]} cols")
        return df_gp

    # ── ML prep ───────────────────────────────────────────────────────────────
    def _prepare_ml(self, df_gp: pd.DataFrame):
        TARGET = "prix"
        ce = _import_ce()

        NUM_FEATS = [
            c for c in df_gp.columns
            if df_gp[c].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
            and c != TARGET
            and df_gp[c].notna().mean() > 0.05
        ]
        CAT_FEATS = [c for c in ["type", "contrat", "gouvernerat"] if c in df_gp.columns]

        df_ml = df_gp[[TARGET] + NUM_FEATS + CAT_FEATS].copy()
        df_ml[TARGET] = pd.to_numeric(df_ml[TARGET], errors="coerce")
        df_ml = df_ml.dropna(subset=[TARGET])

        df_train, df_test = train_test_split(
            df_ml, test_size=0.2, random_state=RANDOM_SEED, shuffle=True
        )
        y_train = df_train[TARGET].astype(float)
        y_test  = df_test[TARGET].astype(float)
        X_train = df_train[NUM_FEATS + CAT_FEATS].copy()
        X_test  = df_test[NUM_FEATS + CAT_FEATS].copy()

        logger.info(f"Split: train={len(df_train):,} | test={len(df_test):,} | "
                    f"features={len(NUM_FEATS)} num + {len(CAT_FEATS)} cat")

        encoder = ce.TargetEncoder(cols=CAT_FEATS, smoothing=10)
        X_train_enc = encoder.fit_transform(X_train, y_train)
        X_test_enc  = encoder.transform(X_test)

        med = X_train_enc.median()
        X_train_enc = X_train_enc.fillna(med)
        X_test_enc  = X_test_enc.fillna(med)

        return (
            X_train_enc, X_test_enc,
            y_train, y_test,
            NUM_FEATS, CAT_FEATS, encoder,
        )

    # ── Model evaluation helper ───────────────────────────────────────────────
    @staticmethod
    def _eval(name, model, X_tr, y_tr, X_te, y_te,
              use_pipeline=False) -> Tuple[Dict, np.ndarray]:
        t0 = time.time()
        if use_pipeline:
            inner = Pipeline([("sc", RobustScaler()), ("m", model)])
        else:
            inner = model

        fitted = TransformedTargetRegressor(
            regressor=inner,
            func=np.log1p,
            inverse_func=np.expm1,
        )
        fitted.fit(X_tr, y_tr)
        preds = fitted.predict(X_te)
        elapsed = round(time.time() - t0, 1)
        m = _metrics(y_te, preds)
        logger.info(
            f"  {name:<38} MAE={m['MAE']:>10,.0f}  RMSE={m['RMSE']:>10,.0f}  "
            f"MAPE={m['MAPE_pct']:>6.1f}%  R2={m['R2']:.3f}  ({elapsed}s)"
        )
        row = {"Model": name, **m, "Time_s": elapsed}
        return row, preds, fitted

    # ── Main training pipeline ────────────────────────────────────────────────
    def train(self, data_path: str, model_dir: str = "model_artefact") -> Dict[str, float]:
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)

        lgb  = _import_lgb()
        xgb  = _import_xgb()
        CatBoostRegressor = _import_catboost()

        # ── 1. Load & clean ──────────────────────────────────────────────────
        df    = self._load(data_path)
        df_gp = self._build_features(df)
        (X_train_enc, X_test_enc,
         y_train, y_test,
         NUM_FEATS, CAT_FEATS, encoder) = self._prepare_ml(df_gp)

        X_tr, X_te = X_train_enc.copy(), X_test_enc.copy()
        y_tr, y_te = y_train.copy(), y_test.copy()

        arena_rows:  List[Dict]       = []
        arena_preds: Dict[str, np.ndarray] = {}
        arena_fits:  Dict[str, Any]   = {}

        # ── 2. Model Arena ───────────────────────────────────────────────────
        logger.info("=" * 75)
        logger.info("MODEL ARENA")
        logger.info("=" * 75)

        # Linear (scaled pipeline)
        for name, mdl in [
            ("Ridge",         Ridge(alpha=1.0)),
            ("Lasso",         Lasso(alpha=10.0, max_iter=5000)),
            ("ElasticNet",    ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000)),
            ("HuberRegressor",HuberRegressor(max_iter=300)),
        ]:
            row, preds, fit = self._eval(name, mdl, X_tr, y_tr, X_te, y_te, use_pipeline=True)
            arena_rows.append(row); arena_preds[name] = preds; arena_fits[name] = fit

        # Tree ensembles (no scaling)
        for name, mdl in [
            ("Random Forest (200)", RandomForestRegressor(
                n_estimators=200, max_depth=20, n_jobs=-1, random_state=RANDOM_SEED)),
            ("Extra Trees (200)", ExtraTreesRegressor(
                n_estimators=200, max_depth=20, n_jobs=-1, random_state=RANDOM_SEED)),
            ("GradientBoosting", GradientBoostingRegressor(
                n_estimators=300, learning_rate=0.05, max_depth=5, random_state=RANDOM_SEED)),
            ("HistGradientBoosting", HistGradientBoostingRegressor(
                max_iter=500, learning_rate=0.05, max_depth=8,
                early_stopping=True, validation_fraction=0.1,
                n_iter_no_change=10, random_state=RANDOM_SEED)),
        ]:
            row, preds, fit = self._eval(name, mdl, X_tr, y_tr, X_te, y_te)
            arena_rows.append(row); arena_preds[name] = preds; arena_fits[name] = fit

        # XGBoost
        xgb_mdl = xgb.XGBRegressor(
            n_estimators=500, learning_rate=0.05, max_depth=7,
            subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
            random_state=RANDOM_SEED, n_jobs=-1, verbosity=0,
        )
        row, preds, fit = self._eval("XGBoost", xgb_mdl, X_tr, y_tr, X_te, y_te)
        arena_rows.append(row); arena_preds["XGBoost"] = preds; arena_fits["XGBoost"] = fit

        # CatBoost
        cat_mdl = CatBoostRegressor(
            iterations=500, learning_rate=0.05, depth=8,
            l2_leaf_reg=3, random_seed=RANDOM_SEED, verbose=0,
        )
        cat_mdl.fit(X_tr, y_tr, eval_set=(X_te, y_te))
        row, preds, fit = self._eval("CatBoost", cat_mdl, X_tr, y_tr, X_te, y_te)
        arena_rows.append(row); arena_preds["CatBoost"] = preds; arena_fits["CatBoost"] = fit

        # LightGBM baseline
        lgbm_mdl = TransformedTargetRegressor(
            regressor=lgb.LGBMRegressor(
                n_estimators=1000, learning_rate=0.05, num_leaves=64,
                subsample=0.8, colsample_bytree=0.8,
                reg_alpha=0.1, reg_lambda=0.1,
                random_state=RANDOM_SEED, n_jobs=-1, verbose=-1,
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        )
        lgbm_mdl.fit(X_tr, y_tr)   # pass raw y_tr — it transforms internally
        preds_lgbm = lgbm_mdl.predict(X_te)
        m_lgbm = _metrics(y_te, preds_lgbm)
        logger.info(f"  {'LightGBM (baseline)':<38} MAE={m_lgbm['MAE']:>10,.0f}  "
                    f"RMSE={m_lgbm['RMSE']:>10,.0f}  MAPE={m_lgbm['MAPE_pct']:>6.1f}%  "
                    f"R2={m_lgbm['R2']:.3f}")
        arena_rows.append({"Model": "LightGBM (baseline)", **m_lgbm, "Time_s": 0.0})
        arena_preds["LightGBM (baseline)"] = preds_lgbm
        arena_fits["LightGBM (baseline)"]  = lgbm_mdl

        arena_df = (pd.DataFrame(arena_rows)
                      .sort_values("MAE")
                      .reset_index(drop=True))
        arena_df.index += 1
        logger.info("\n--- Initial Arena Ranking ---\n" +
                    arena_df[["Model","MAE","RMSE","MAPE_pct","R2"]].to_string())

        # ── 3. Fine-tune Random Forest ───────────────────────────────────────
        logger.info("\n--- Fine-tuning Random Forest (RandomizedSearchCV n_iter=20, cv=3) ---")
        param_dist_rf = {
            "n_estimators":    [100, 200, 300, 500],
            "max_depth":       [10, 20, 30, None],
            "min_samples_split":[2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features":    ["sqrt", "log2", None],
        }
        rf_search = RandomizedSearchCV(
            RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1),
            param_dist_rf, n_iter=20, cv=3,          # faster: 20 iters, 3-fold
            scoring="neg_mean_absolute_error",
            verbose=2, random_state=RANDOM_SEED, n_jobs=-1,
        )
        rf_search.fit(X_tr, y_tr)
        logger.info(f"Best RF params: {rf_search.best_params_}")

        best_rf    = rf_search.best_estimator_
        preds_rf_t = best_rf.predict(X_te)
        m_rf_t     = _metrics(y_te, preds_rf_t)
        logger.info(f"Random Forest (tuned) — MAE: {m_rf_t['MAE']:,.0f}  "
                    f"MAPE: {m_rf_t['MAPE_pct']:.1f}%  R2: {m_rf_t['R2']:.3f}")

        arena_preds["Random Forest (tuned)"] = preds_rf_t
        arena_fits["Random Forest (tuned)"]  = best_rf
        rf_row = pd.DataFrame([{"Model": "Random Forest (tuned)", **m_rf_t,
                                 "Time_s": round(rf_search.cv_results_["mean_fit_time"].mean(), 1)}])
        arena_df = (pd.concat([arena_df, rf_row], ignore_index=True)
                      .sort_values("MAE").reset_index(drop=True))
        arena_df.index += 1

        # ── 4. Fine-tune LightGBM ────────────────────────────────────────────
        logger.info("\n--- Fine-tuning LightGBM (RandomizedSearchCV n_iter=20, cv=3) ---")
        param_dist_lgb = {
            "n_estimators":      [300, 500, 700, 1000],
            "learning_rate":     [0.01, 0.03, 0.05, 0.07],
            "num_leaves":        [31, 64, 128, 256],
            "subsample":         [0.6, 0.8, 1.0],
            "colsample_bytree":  [0.6, 0.8, 1.0],
            "reg_alpha":         [0.0, 0.1, 0.5, 1.0],
            "reg_lambda":        [0.0, 0.1, 0.5, 1.0],
            "min_child_samples": [5, 10, 20],
        }
        lgb_search = RandomizedSearchCV(
            lgb.LGBMRegressor(random_state=RANDOM_SEED, n_jobs=-1, verbose=-1),
            param_dist_lgb, n_iter=20, cv=3,
            scoring="neg_mean_absolute_error",
            verbose=1, random_state=RANDOM_SEED, n_jobs=1,  # n_jobs=1 avoids lgbm fork issues
        )
        lgb_search.fit(X_tr, y_tr)
        logger.info(f"Best LGB params: {lgb_search.best_params_}")

        best_lgbm    = lgb_search.best_estimator_
        preds_lgb_t  = best_lgbm.predict(X_te)
        m_lgb_t      = _metrics(y_te, preds_lgb_t)
        logger.info(f"LightGBM (tuned) — MAE: {m_lgb_t['MAE']:,.0f}  "
                    f"MAPE: {m_lgb_t['MAPE_pct']:.1f}%  R2: {m_lgb_t['R2']:.3f}")

        arena_preds["LightGBM (tuned)"] = preds_lgb_t
        arena_fits["LightGBM (tuned)"]  = best_lgbm
        lgb_row = pd.DataFrame([{"Model": "LightGBM (tuned)", **m_lgb_t,
                                  "Time_s": round(lgb_search.cv_results_["mean_fit_time"].mean(), 1)}])
        arena_df = (pd.concat([arena_df, lgb_row], ignore_index=True)
                      .sort_values("MAE").reset_index(drop=True))
        arena_df.index += 1

        # ── 5. Stacking Ensemble (top-3 + Ridge meta) ────────────────────────
        logger.info("\n--- Stacking Ensemble (top-3 + Ridge meta, cv=3) ---")
        arena_df = arena_df[~arena_df["Model"].str.contains("Stacking")].copy()
        top3_names = arena_df.head(3)["Model"].tolist()
        logger.info(f"Top-3 for stacking: {top3_names}")

        def _pick_estimator(name):
            if name in arena_fits:
                return arena_fits[name]
            return lgb.LGBMRegressor(n_estimators=300, random_state=RANDOM_SEED, verbose=-1)

        stack_estimators = [(f"m{i}", _pick_estimator(n)) for i, n in enumerate(top3_names)]
        stack_estimators.append(("ridge_div", Pipeline([
            ("sc", RobustScaler()), ("r", Ridge(alpha=1.0))
        ])))

        stacker = StackingRegressor(
            estimators=stack_estimators,
            final_estimator=Ridge(alpha=1.0),
            cv=3, n_jobs=-1, passthrough=False,
        )
        stacker.fit(X_tr, y_tr)
        preds_stack = stacker.predict(X_te)
        m_stack     = _metrics(y_te, preds_stack)
        logger.info(f"Stacking — MAE={m_stack['MAE']:,.0f}  "
                    f"MAPE={m_stack['MAPE_pct']:.1f}%  R2={m_stack['R2']:.3f}")

        arena_preds["Stacking (top3+Ridge)"] = preds_stack
        arena_fits["Stacking (top3+Ridge)"]  = stacker
        stack_row = pd.DataFrame([{"Model": "Stacking (top3+Ridge)", **m_stack, "Time_s": 0.0}])
        arena_df = (pd.concat([arena_df, stack_row], ignore_index=True)
                      .sort_values("MAE").reset_index(drop=True))
        arena_df.index += 1

        # ── 6. Select best model ─────────────────────────────────────────────
        best_row  = arena_df.loc[arena_df["MAE"].idxmin()]
        BEST_NAME = best_row["Model"]
        logger.info(f"\n🏆 BEST MODEL: {BEST_NAME}  |  MAE={best_row['MAE']:,.0f}  "
                    f"MAPE={best_row['MAPE_pct']:.1f}%  R2={best_row['R2']:.3f}")
        logger.info("\n" + arena_df[["Model","MAE","RMSE","MAPE_pct","R2"]].to_string())

        best_model_obj  = arena_fits[BEST_NAME]
        best_preds      = arena_preds[BEST_NAME]

        # ── 7. Price gap analysis ────────────────────────────────────────────
        test_results = X_test_enc.copy()
        test_results["actual_price"]    = y_test.values
        test_results["predicted_price"] = best_preds
        test_results["price_gap"]       = test_results["actual_price"] - test_results["predicted_price"]
        test_results["price_gap_pct"]   = (
            test_results["price_gap"] / test_results["actual_price"].replace(0, np.nan) * 100
        )

        # ── 8. Visualisations ────────────────────────────────────────────────
        self._plot_arena(arena_df, model_dir)
        self._plot_predictions(
            y_te, best_preds, BEST_NAME,
            best_row["MAE"], best_row["MAPE_pct"], model_dir,
        )

        # ── 9. Save artefacts ────────────────────────────────────────────────
        joblib.dump(best_model_obj, model_dir / "best_model.pkl")
        joblib.dump(encoder,        model_dir / "target_encoder.pkl")
        meta = {
            "BEST_MODEL_NAME": BEST_NAME,
            "NUM_FEATS":       NUM_FEATS,
            "CAT_FEATS":       CAT_FEATS,
            "PRIX_MIN":        PRIX_MIN,
            "PRIX_MAX":        PRIX_MAX,
            "metrics":         best_row[["MAE","RMSE","MAPE_pct","R2"]].to_dict(),
        }
        joblib.dump(meta, model_dir / "model_meta.pkl")
        (model_dir / "model_meta.json").write_text(
            json.dumps(meta, indent=2, default=str)
        )
        arena_df.to_csv(model_dir / "arena_results.csv", index=False)
        test_results.to_csv(model_dir / "test_predictions.csv", index=False)

        logger.info(f"Artefacts saved to {model_dir}")

        final_metrics = {
            "MAE":      best_row["MAE"],
            "RMSE":     best_row["RMSE"],
            "MAPE_pct": best_row["MAPE_pct"],
            "R2":       best_row["R2"],
        }
        return final_metrics

    # ── Plots ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _plot_arena(arena_df: pd.DataFrame, out_dir: Path):
        fig, axes = plt.subplots(1, 2, figsize=(16, max(6, len(arena_df) * 0.5)))
        fig.suptitle("EstateMind — Model Arena", fontsize=14, fontweight="bold")

        s_mae = arena_df.sort_values("MAE", ascending=True)
        colors = ["#F18F01" if i == 0 else "#2E86AB" for i in range(len(s_mae))]
        axes[0].barh(s_mae["Model"], s_mae["MAE"] / 1000,
                     color=colors, edgecolor="white")
        axes[0].set_xlabel("MAE (k TND)")
        axes[0].set_title("MAE — lower is better", fontweight="bold")

        s_r2 = arena_df.sort_values("R2", ascending=False)
        colors2 = ["#44BBA4" if i == 0 else "#A23B72" for i in range(len(s_r2))]
        axes[1].barh(s_r2["Model"], s_r2["R2"],
                     color=colors2, edgecolor="white")
        axes[1].set_xlabel("R²")
        axes[1].set_title("R² — higher is better", fontweight="bold")

        plt.tight_layout()
        path = out_dir / "model_arena_comparison.png"
        plt.savefig(path, dpi=130, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved: {path}")

    @staticmethod
    def _plot_predictions(y_te, preds, model_name, mae, mape, out_dir: Path):
        clip_q = float(np.quantile(y_te, 0.97))
        mask   = np.array(y_te) <= clip_q

        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        axes[0].scatter(np.array(y_te)[mask], np.array(preds)[mask],
                        alpha=0.3, s=8, color="#2E86AB")
        lo, hi = float(np.array(y_te)[mask].min()), float(np.array(y_te)[mask].max())
        axes[0].plot([lo, hi], [lo, hi], "r--", lw=1.5)
        axes[0].set_xlabel("Actual (TND)"); axes[0].set_ylabel("Predicted (TND)")
        axes[0].set_title(f"{model_name} — Actual vs Predicted", fontweight="bold")

        residuals = np.array(preds) - np.array(y_te)
        axes[1].hist(residuals.clip(-3e6, 3e6), bins=80, color="#A23B72",
                     edgecolor="white", lw=0.3)
        axes[1].axvline(0, color="black", lw=1.2, linestyle="--")
        axes[1].set_xlabel("Residual (TND)"); axes[1].set_title("Residuals", fontweight="bold")

        plt.suptitle(f"{model_name} — MAE: {mae:,.0f} TND | MAPE: {mape:.1f}%",
                     fontweight="bold")
        plt.tight_layout()
        path = out_dir / "best_model_predictions.png"
        plt.savefig(path, dpi=130)
        plt.close()
        logger.info(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="price_predictor",
        description="EstateMind Price Prediction — train & evaluate",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    train_p = sub.add_parser("train", help="Train the full model arena")
    train_p.add_argument("--data",      required=True, help="Path to cleaned CSV")
    train_p.add_argument("--model-dir", default="model_artefact",
                         help="Directory to save artefacts (default: model_artefact)")
    return parser


def main():
    parser = _build_parser()
    args   = parser.parse_args()

    if args.command == "train":
        predictor = PricePredictor()
        metrics   = predictor.train(args.data, args.model_dir)
        print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()