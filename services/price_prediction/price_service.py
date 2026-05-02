"""
EstateMind — Price Prediction Microservice
==========================================
Location: estatemind/services/price_prediction/price_service.py

Run from project root:
  uvicorn services.price_prediction.price_service:app --port 8001 --reload

Endpoints:
  GET  /health
  GET  /model/info
  POST /predict
  POST /predict/batch
  POST /train
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.price_prediction.price_predictor import PricePredictor

MODEL_DIR    = os.getenv("MODEL_DIR",  str(ROOT / "model_artefact"))
DATA_PATH    = os.getenv("DATA_PATH",  str(ROOT / "data_cleaned" / "bigfinal_realestate_Cleaned.csv"))
MODEL_FILE   = "best_model.pkl"
ENCODER_FILE = "target_encoder.pkl"
META_FILE    = "model_meta.pkl"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EstateMind Price Prediction Service",
    description="Predicts fair market value for Tunisian real-estate listings.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_service      = None
_model_loaded = False


class PriceService:
    def __init__(self, model_dir: str = MODEL_DIR):
        import joblib
        d = Path(model_dir)
        self.model      = joblib.load(d / MODEL_FILE)
        self.encoder    = joblib.load(d / ENCODER_FILE)
        meta            = joblib.load(d / META_FILE)
        self.num_feats  = meta["NUM_FEATS"]
        self.cat_feats  = meta["CAT_FEATS"]
        self.all_feats  = self.num_feats + self.cat_feats
        self.model_name = meta.get("BEST_MODEL_NAME", "unknown")
        self.metrics    = meta.get("metrics", {})
        logger.info("PriceService ready — model: %s", self.model_name)

    @staticmethod
    def _haversine(lat, lon, lat2=36.8065, lon2=10.1815):
        import numpy as np
        R = 6371
        phi1, phi2 = np.radians(lat), np.radians(lat2)
        a = np.sin(np.radians(lat2-lat)/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(np.radians(lon2-lon)/2)**2
        return float(R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))

    def _build_features(self, raw):
        import numpy as np, pandas as pd
        row     = {f: raw.get(f) for f in self.all_feats}
        surface = raw.get("surface") or 0
        pieces  = raw.get("pieces")  or 0
        etage   = raw.get("etage",  0) or 0
        has_asc = raw.get("has_ascenseur", 0) or 0
        lat, lon = raw.get("latitude"), raw.get("longitude")
        amenity_keys = ["has_ascenseur","has_balcon","has_chaffage","has_climatisation",
                        "has_garage","has_gardien","has_jardin","has_parking","has_piscine","has_terrasse"]
        if surface > 0 and pieces > 0:
            row["surface_per_piece"] = surface / pieces
        if "price_per_m2"       in self.num_feats: row["price_per_m2"]       = None
        if "etage_x_ascenseur"  in self.num_feats: row["etage_x_ascenseur"]  = etage * has_asc
        if "total_amenities"    in self.num_feats: row["total_amenities"]    = sum(raw.get(k,0) or 0 for k in amenity_keys)
        if "dist_to_center"     in self.num_feats and lat and lon: row["dist_to_center"] = self._haversine(lat, lon)
        df = pd.DataFrame([row])
        for col in self.all_feats:
            if col not in df.columns: df[col] = np.nan
        return df[self.all_feats]

    def predict(self, raw):
        df    = self._build_features(raw)
        X_enc = self.encoder.transform(df)
        X_enc = X_enc.infer_objects(copy=False).fillna(X_enc.median())
        return {"predicted_price": round(float(self.model.predict(X_enc)[0]), 2),
                "currency": "TND", "model_name": self.model_name}

    def batch_predict(self, records):
        import pandas as pd
        dfs   = [self._build_features(r) for r in records]
        df_all = pd.concat(dfs, ignore_index=True)
        X_enc  = self.encoder.transform(df_all)
        X_enc  = X_enc.infer_objects(copy=False).fillna(X_enc.median())
        return [{"predicted_price": round(float(p), 2), "currency": "TND", "model_name": self.model_name}
                for p in self.model.predict(X_enc)]


@app.on_event("startup")
async def startup_event():
    global _service, _model_loaded
    if (Path(MODEL_DIR) / MODEL_FILE).exists():
        try:
            _service = PriceService(MODEL_DIR)
            _model_loaded = True
        except Exception as e:
            logger.error("Failed to load model: %s", e)
    else:
        logger.warning("No model found at %s — call POST /train first.", MODEL_DIR)


class PropertyInput(BaseModel):
    surface:           Optional[float] = None
    pieces:            Optional[float] = None
    etage:             Optional[float] = None
    gouvernerat:       Optional[str]   = None
    ville:             Optional[str]   = None
    type:              Optional[str]   = None
    contrat:           Optional[str]   = None
    latitude:          Optional[float] = None
    longitude:         Optional[float] = None
    has_ascenseur:     Optional[int]   = Field(0, ge=0, le=1)
    has_balcon:        Optional[int]   = Field(0, ge=0, le=1)
    has_chaffage:      Optional[int]   = Field(0, ge=0, le=1)
    has_climatisation: Optional[int]   = Field(0, ge=0, le=1)
    has_garage:        Optional[int]   = Field(0, ge=0, le=1)
    has_gardien:       Optional[int]   = Field(0, ge=0, le=1)
    has_jardin:        Optional[int]   = Field(0, ge=0, le=1)
    has_parking:       Optional[int]   = Field(0, ge=0, le=1)
    has_piscine:       Optional[int]   = Field(0, ge=0, le=1)
    has_terrasse:      Optional[int]   = Field(0, ge=0, le=1)
    class Config: extra = "allow"

class PredictionResult(BaseModel):
    predicted_price: float
    currency:        str = "TND"
    model_name:      str

class BatchRequest(BaseModel):
    properties: List[PropertyInput]

class BatchResult(BaseModel):
    predictions: List[PredictionResult]
    count:       int

class TrainRequest(BaseModel):
    data_path: Optional[str] = None

class TrainResult(BaseModel):
    status:     str
    metrics:    Dict[str, float]
    model_name: str

class ModelInfo(BaseModel):
    loaded:       bool
    model_name:   str
    model_dir:    str
    num_features: int
    cat_features: List[str]
    metrics:      Dict[str, float]


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "model_loaded": _model_loaded,
            "model_name": _service.model_name if _service else None}

@app.get("/model/info", response_model=ModelInfo, tags=["System"])
def model_info():
    if not _model_loaded:
        raise HTTPException(503, "Model not loaded.")
    return ModelInfo(loaded=True, model_name=_service.model_name, model_dir=MODEL_DIR,
                     num_features=len(_service.num_feats), cat_features=_service.cat_feats,
                     metrics=_service.metrics)

@app.post("/predict", response_model=PredictionResult, tags=["Prediction"])
def predict(prop: PropertyInput):
    """Predict fair market price for a single property."""
    if not _model_loaded:
        raise HTTPException(503, "Model not loaded. Call POST /train first.")
    try:
        return PredictionResult(**_service.predict(prop.dict()))
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(500, str(e))

@app.post("/predict/batch", response_model=BatchResult, tags=["Prediction"])
def predict_batch(request: BatchRequest):
    """Predict prices for a list of properties in one call."""
    if not _model_loaded:
        raise HTTPException(503, "Model not loaded. Call POST /train first.")
    try:
        results = _service.batch_predict([p.dict() for p in request.properties])
        return BatchResult(predictions=[PredictionResult(**r) for r in results], count=len(results))
    except Exception as e:
        logger.exception("Batch prediction failed")
        raise HTTPException(500, str(e))

@app.post("/train", response_model=TrainResult, tags=["Admin"])
def train(request: TrainRequest):
    """Retrain the model and hot-reload the service."""
    global _service, _model_loaded
    data = request.data_path or DATA_PATH
    if not Path(data).exists():
        raise HTTPException(400, f"CSV not found: {data}")
    try:
        predictor     = PricePredictor()
        metrics       = predictor.train(data, MODEL_DIR)
        _service      = PriceService(MODEL_DIR)
        _model_loaded = True
        return TrainResult(status="trained", metrics=metrics, model_name=_service.model_name)
    except Exception as e:
        logger.exception("Training failed")
        raise HTTPException(500, str(e))