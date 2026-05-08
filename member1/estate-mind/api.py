"""
Outliers market-intelligence agent — FastAPI wrapper around member1's artifacts.

Scope: anomaly/pocket detection, RAG comparables, POI scoring, CLIP style
classifier, Tunisian price lexicon, static price map. Price prediction is
owned by another teammate — intentionally NOT exposed here.

Pickle interfaces were not documented in member1's handoff. Endpoints try the
common sklearn-style methods (predict / predict_proba / transform / __call__);
if a pickle has a custom interface, /artifacts will surface the load error and
the endpoint will return 501 with the introspection payload so the frontend
can fall back gracefully.
"""
from __future__ import annotations

import io
import json
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

ROOT = Path(os.environ.get("ESTATEMIND_ROOT", "/app"))
MODELS = ROOT / "models"
SNAPSHOT = ROOT / "snapshot_20260503_220354"
ARTIFACTS = ROOT / "artifacts"
CONFIG = ROOT / "config" / "config.yaml"
MAP_HTML = ROOT / "carte_immobilier_tunisie.html"

app = FastAPI(
    title="Outliers — market intel agent",
    version="0.1.0",
    description="Anomaly detection, comparable search, POI/style scoring for Tunisian listings.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict[str, Any] = {}
_load_errors: dict[str, str] = {}


def _load(rel: str) -> Any:
    """Load a pickle (cached). Raises HTTPException(503) with a clear message on failure."""
    if rel in _cache:
        return _cache[rel]
    if rel in _load_errors:
        raise HTTPException(status_code=503, detail=f"artifact {rel} failed to load: {_load_errors[rel]}")
    path = ROOT / rel
    if not path.exists():
        _load_errors[rel] = "missing"
        raise HTTPException(status_code=503, detail=f"artifact {rel} not found at {path}")
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        _cache[rel] = obj
        return obj
    except Exception as e:
        _load_errors[rel] = f"{type(e).__name__}: {e}"
        raise HTTPException(status_code=503, detail=f"artifact {rel} failed to load: {_load_errors[rel]}")


def _try_call(obj: Any, X: Any) -> Any:
    """Best-effort: call predict / predict_proba / transform / __call__ on a pickle."""
    for method in ("predict", "predict_proba", "transform", "score_samples", "decision_function"):
        if hasattr(obj, method) and callable(getattr(obj, method)):
            try:
                return {"method": method, "result": getattr(obj, method)(X)}
            except Exception as e:
                last_err = f"{method} -> {type(e).__name__}: {e}"
                continue
    if callable(obj):
        try:
            return {"method": "__call__", "result": obj(X)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"object is callable but failed: {e}")
    raise HTTPException(status_code=501, detail=f"no usable method on {type(obj).__name__}; tried: predict/predict_proba/transform/score_samples/decision_function/__call__")


# -------------------- Health & introspection --------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "outliers", "version": app.version}


@app.get("/artifacts")
def artifacts_status():
    """Report which member1 pickles load successfully — useful for frontend dev."""
    targets = [
        "models/best_model.pkl",
        "models/best_model_logtransform.pkl",
        "models/target_encoder.pkl",
        "models/pca_model.pkl",
        "snapshot_20260503_220354/pocket_detector.pkl",
        "snapshot_20260503_220354/poi_analyzer.pkl",
        "snapshot_20260503_220354/rag_predictor.pkl",
        "snapshot_20260503_220354/style_classifier.pkl",
        "snapshot_20260503_220354/price_lexicon.pkl",
        "snapshot_20260503_220354/robust_scaler.pkl",
        "snapshot_20260503_220354/shap_values.pkl",
    ]
    out = {}
    for rel in targets:
        path = ROOT / rel
        if not path.exists():
            out[rel] = {"ok": False, "reason": "missing"}
            continue
        try:
            obj = _load(rel)
            methods = [m for m in dir(obj) if not m.startswith("_") and callable(getattr(obj, m, None))]
            out[rel] = {
                "ok": True,
                "type": f"{type(obj).__module__}.{type(obj).__name__}",
                "callable_methods": methods[:12],
                "size_bytes": path.stat().st_size,
            }
        except HTTPException as e:
            out[rel] = {"ok": False, "reason": e.detail}
    return out


@app.get("/manifest")
def manifest():
    """Return manifest.json + metadata.json so the frontend knows feature schema and metrics."""
    out = {}
    for name, path in [("manifest", ARTIFACTS / "manifest.json"), ("metadata", MODELS / "metadata.json")]:
        if path.exists():
            out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


# -------------------- Anomaly: under-valued pocket detection --------------------

class PocketRequest(BaseModel):
    """Features for the pocket detector. Schema matches df_gold_plus.csv tabular columns."""
    surface: float
    pieces: float | None = None
    etage: float | None = None
    latitude: float
    longitude: float
    gouvernerat: str
    type: str = "Appartement"
    contrat: str = "vente"
    prix: float = Field(..., description="Listed price in TND — what we're checking for under-valuation")
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional has_* / nlp_* / vis_* features if available")


@app.post("/detect-pocket")
def detect_pocket(req: PocketRequest):
    detector = _load("snapshot_20260503_220354/pocket_detector.pkl")
    row = {**req.model_dump(exclude={"extra"}), **req.extra}
    X = pd.DataFrame([row])
    res = _try_call(detector, X)
    out = res["result"]
    if isinstance(out, np.ndarray):
        out = out.tolist()
    return {"method_used": res["method"], "result": out, "input_columns": list(X.columns)}


# -------------------- RAG: comparable listings --------------------

class CompRequest(BaseModel):
    query_text: str | None = Field(None, description="Free-text description of the target listing")
    features: dict[str, Any] = Field(default_factory=dict, description="Tabular features of the target listing")
    top_k: int = 5


@app.post("/find-comparables")
def find_comparables(req: CompRequest):
    rag = _load("snapshot_20260503_220354/rag_predictor.pkl")
    payload = req.model_dump()
    # Try common RAG signatures defensively
    for attempt in [
        lambda: rag.predict(payload),
        lambda: rag.query(req.query_text or "", top_k=req.top_k),
        lambda: rag.search(req.features, top_k=req.top_k),
        lambda: rag(payload),
    ]:
        try:
            res = attempt()
            if isinstance(res, np.ndarray):
                res = res.tolist()
            return {"comparables": res}
        except Exception:
            continue
    raise HTTPException(status_code=501, detail=f"rag_predictor has unknown signature; type={type(rag).__name__}")


# -------------------- POI scoring --------------------

class POIRequest(BaseModel):
    latitude: float
    longitude: float
    gouvernerat: str | None = None


@app.post("/poi-score")
def poi_score(req: POIRequest):
    poi = _load("snapshot_20260503_220354/poi_analyzer.pkl")
    payload = req.model_dump()
    for attempt in [
        lambda: poi.score(req.latitude, req.longitude),
        lambda: poi.predict(pd.DataFrame([payload])),
        lambda: poi(req.latitude, req.longitude),
        lambda: poi.transform(pd.DataFrame([payload])),
    ]:
        try:
            res = attempt()
            if isinstance(res, np.ndarray):
                res = res.tolist()
            return {"poi_score": res, "lat": req.latitude, "lng": req.longitude}
        except Exception:
            continue
    raise HTTPException(status_code=501, detail=f"poi_analyzer has unknown signature; type={type(poi).__name__}")


# -------------------- CLIP architectural style --------------------

@app.post("/style-classify")
async def style_classify(file: UploadFile = File(...)):
    classifier = _load("snapshot_20260503_220354/style_classifier.pkl")
    raw = await file.read()
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot decode image: {e}")
    for attempt in [
        lambda: classifier.predict(img),
        lambda: classifier.classify(img),
        lambda: classifier(img),
    ]:
        try:
            res = attempt()
            if isinstance(res, np.ndarray):
                res = res.tolist()
            return {"filename": file.filename, "style": res}
        except Exception:
            continue
    raise HTTPException(status_code=501, detail=f"style_classifier has unknown signature; type={type(classifier).__name__}")


# -------------------- Tunisian price lexicon (just expose it) --------------------

@app.get("/price-keywords")
def price_keywords():
    """Return the 31-keyword Tunisian price lexicon as JSON. Useful for UI hints."""
    lex = _load("snapshot_20260503_220354/price_lexicon.pkl")
    if isinstance(lex, dict):
        return {"lexicon": lex, "shape": "dict", "size": len(lex)}
    if isinstance(lex, (list, tuple, set)):
        return {"lexicon": list(lex), "shape": "sequence", "size": len(lex)}
    if hasattr(lex, "to_dict"):
        return {"lexicon": lex.to_dict(), "shape": "to_dict()"}
    return {"lexicon_repr": repr(lex)[:2000], "shape": "unknown", "type": type(lex).__name__}


# -------------------- Static price map --------------------

@app.get("/map")
def price_map():
    """Serve the precomputed Folium price map of Tunisia."""
    if not MAP_HTML.exists():
        raise HTTPException(status_code=404, detail=f"map not found at {MAP_HTML}")
    return FileResponse(MAP_HTML, media_type="text/html")


@app.get("/")
def root():
    return JSONResponse(
        {
            "service": "outliers",
            "endpoints": [
                "GET  /healthz",
                "GET  /artifacts   — which pickles loaded ok",
                "GET  /manifest    — feature schema + training metrics",
                "POST /detect-pocket",
                "POST /find-comparables",
                "POST /poi-score",
                "POST /style-classify   (multipart image)",
                "GET  /price-keywords",
                "GET  /map         — Folium HTML",
            ],
            "notes": "price prediction is owned by another agent and not exposed here",
        }
    )
