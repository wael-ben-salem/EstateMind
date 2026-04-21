from pathlib import Path
import math
import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from recommender.data_loader import load_clean_data
from recommender.recommender_service import run_recommender_pipeline

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "estatemind_ui.html"

app = FastAPI(title="EstateMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement dataset une seule fois
df = load_clean_data()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/")
def serve_ui():
    return FileResponse(HTML_PATH)


@app.post("/api/recommend")
def recommend(req: QueryRequest):
    result = run_recommender_pipeline(
        user_query=req.query,
        df=df,
        top_k=req.top_k,
    )
    return sanitize_for_json(result)

@app.get("/")
def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]

    if isinstance(obj, tuple):
        return [sanitize_for_json(v) for v in obj]

    if isinstance(obj, (np.floating, float)):
        if math.isnan(float(obj)) or math.isinf(float(obj)):
            return None
        return float(obj)

    if isinstance(obj, (np.integer, int)):
        return int(obj)

    return obj