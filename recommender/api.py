import math
import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from recommender.data_loader import load_clean_data
from recommender.recommender_service import run_recommender_pipeline

app = FastAPI(
    title="EstateMind Recommender API",
    description="Microservice de recommandation immobilière pour la Tunisie",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement du dataset une seule fois au démarrage
df = load_clean_data()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        if math.isnan(float(obj)) or math.isinf(float(obj)):
            return None
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    return obj


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "EstateMind Recommender API",
        "version": "1.0.0",
        "dataset_size": len(df),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/recommend")
def recommend(req: QueryRequest):
    result = run_recommender_pipeline(
        user_query=req.query,
        df=df,
        top_k=req.top_k,
    )
    return sanitize_for_json(result)
