"""
EstateMind — Anomaly Detection Microservice
============================================
Location: estatemind/services/anomaly_detection/anomaly_service.py

Run from project root:
  uvicorn services.anomaly_detection.anomaly_service:app --port 8002 --reload

Endpoints:
  GET  /health
  POST /score
  POST /score/batch
  POST /run
  GET  /report/opportunities
  GET  /report/risks
  GET  /report/map
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]   # estatemind/
sys.path.insert(0, str(ROOT))

from services.anomaly_detection.anomaly_detector import AnomalyDetector

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_DIR   = os.getenv("MODEL_DIR",   str(ROOT / "model_artefacts"))
DATA_PATH   = os.getenv("DATA_PATH",   str(ROOT / "data" / "bigfinal_realestate_Cleaned.csv"))
REPORT_PATH = os.getenv("REPORT_PATH", str(ROOT / "outputs" / "anomaly_report.csv"))
MAP_PATH    = os.getenv("MAP_PATH",    str(ROOT / "outputs" / "anomaly_map.html"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EstateMind Anomaly Detection Service",
    description="Flags underpriced opportunities and overpriced risks in the Tunisian real-estate market.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

detector     = AnomalyDetector(model_dir=MODEL_DIR)
_last_report: Optional[pd.DataFrame] = None


# ── Schemas ───────────────────────────────────────────────────────────────────

class PropertyInput(BaseModel):
    prix:              float          = Field(..., description="Actual listed price in TND")
    surface:           Optional[float] = None
    pieces:            Optional[float] = None
    etage:             Optional[float] = None
    gouvernerat:       Optional[str]   = None
    ville:             Optional[str]   = None
    type:              Optional[str]   = None
    contrat:           Optional[str]   = None
    latitude:          Optional[float] = None
    longitude:         Optional[float] = None
    has_ascenseur:     Optional[float] = None
    has_balcon:        Optional[float] = None
    has_chaffage:      Optional[float] = None
    has_climatisation: Optional[float] = None
    has_garage:        Optional[float] = None
    has_gardien:       Optional[float] = None
    has_jardin:        Optional[float] = None
    has_parking:       Optional[float] = None
    has_piscine:       Optional[float] = None
    has_terrasse:      Optional[float] = None

    class Config:
        extra = "allow"


class AnomalyScore(BaseModel):
    predicted_price:    float
    actual_price:       float
    price_gap_pct:      float
    is_anomaly:         int
    opportunity_label:  str
    anomaly_confidence: float


class BatchScoreRequest(BaseModel):
    properties: List[PropertyInput]


class BatchScoreResult(BaseModel):
    results:     List[AnomalyScore]
    count:       int
    n_anomalies: int


class RunRequest(BaseModel):
    data_path:   Optional[str] = None
    min_price:   float = 10_000
    max_price:   float = 5_000_000
    max_gap_pct: float = 90
    build_map:   bool  = True


class RunResult(BaseModel):
    status:             str
    total_listings:     int
    n_anomalies:        int
    label_distribution: Dict[str, int]
    report_path:        str
    map_path:           Optional[str]


class OpportunityItem(BaseModel):
    index:              Any
    prix:               float
    predicted_price:    float
    price_gap_pct:      float
    anomaly_confidence: float
    opportunity_label:  str
    gouvernerat:        Optional[str]  = None
    ville:              Optional[str]  = None
    type:               Optional[str]  = None
    surface:            Optional[float] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {
        "status":        "ok",
        "model_dir":     MODEL_DIR,
        "report_ready":  _last_report is not None,
    }


@app.post("/score", response_model=AnomalyScore, tags=["Scoring"])
def score_single(prop: PropertyInput):
    try:
        return AnomalyScore(**detector.score_single(prop.dict()))
    except Exception as e:
        logger.exception("Scoring failed")
        raise HTTPException(500, str(e))


@app.post("/score/batch", response_model=BatchScoreResult, tags=["Scoring"])
def score_batch(request: BatchScoreRequest):
    try:
        results = [detector.score_single(p.dict()) for p in request.properties]
        return BatchScoreResult(
            results=[AnomalyScore(**r) for r in results],
            count=len(results),
            n_anomalies=sum(r["is_anomaly"] for r in results),
        )
    except Exception as e:
        logger.exception("Batch scoring failed")
        raise HTTPException(500, str(e))


@app.post("/run", response_model=RunResult, tags=["Pipeline"])
def run_pipeline(request: RunRequest):
    global _last_report
    data = request.data_path or DATA_PATH
    if not Path(data).exists():
        raise HTTPException(400, f"CSV not found: {data}")
    try:
        report = detector.run(
            data,
            min_price=request.min_price,
            max_price=request.max_price,
            max_gap_pct=request.max_gap_pct,
            build_map=request.build_map,
            report_path=REPORT_PATH,
            map_path=MAP_PATH,
        )
        _last_report = report
        return RunResult(
            status="completed",
            total_listings=len(report),
            n_anomalies=int(report["is_anomaly"].sum()),
            label_distribution=report["opportunity_label"].value_counts().to_dict(),
            report_path=REPORT_PATH,
            map_path=MAP_PATH if request.build_map else None,
        )
    except Exception as e:
        logger.exception("Pipeline run failed")
        raise HTTPException(500, str(e))


@app.get("/report/opportunities", response_model=List[OpportunityItem], tags=["Reports"])
def top_opportunities(limit: int = 20):
    if _last_report is None:
        raise HTTPException(404, "No report yet. Call POST /run first.")
    cols = ["prix", "predicted_price", "price_gap_pct", "anomaly_confidence",
            "opportunity_label", "gouvernerat", "ville", "type", "surface"]
    opps = (
        _last_report[_last_report["opportunity_label"].isin(["Strong Opportunity", "Opportunity"])]
        .sort_values("price_gap_pct", ascending=True)
        .head(limit)[[c for c in cols if c in _last_report.columns]]
        .reset_index()
    )
    return opps.to_dict(orient="records")


@app.get("/report/risks", response_model=List[OpportunityItem], tags=["Reports"])
def top_risks(limit: int = 20):
    if _last_report is None:
        raise HTTPException(404, "No report yet. Call POST /run first.")
    cols = ["prix", "predicted_price", "price_gap_pct", "anomaly_confidence",
            "opportunity_label", "gouvernerat", "ville", "type", "surface"]
    risks = (
        _last_report[_last_report["opportunity_label"].isin(["Overpriced Risk", "Slight Overpricing"])]
        .sort_values("price_gap_pct", ascending=False)
        .head(limit)[[c for c in cols if c in _last_report.columns]]
        .reset_index()
    )
    return risks.to_dict(orient="records")


@app.get("/report/map", tags=["Reports"])
def download_map():
    if not Path(MAP_PATH).exists():
        raise HTTPException(404, "Map not found. Call POST /run first.")
    return FileResponse(MAP_PATH, media_type="text/html", filename="anomaly_map.html")