from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import numpy as np

app = FastAPI(title="EstateMind API", description="Estimation immobilier tunisien", version="1.0.0")

class ListingFeatures(BaseModel):
    surface: Optional[float] = Field(None, ge=5, le=50000)
    pieces: Optional[int] = Field(None, ge=0, le=20)
    etage: Optional[int] = Field(None, ge=-1, le=50)
    gouvernerat: Optional[str] = None
    ville: Optional[str] = None
    type: Optional[str] = None
    contrat: Optional[str] = None
    has_ascenseur: Optional[int] = Field(None, ge=0, le=1)
    has_piscine: Optional[int] = Field(None, ge=0, le=1)
    has_parking: Optional[int] = Field(None, ge=0, le=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    images: Optional[str] = None
    full_pipeline: bool = False

class PredictPriceResponse(BaseModel):
    predicted_price: float
    confidence: float
    interval_low: Optional[float] = None
    interval_high: Optional[float] = None

class ValuationResponse(BaseModel):
    predicted_price: float
    confidence: float
    opportunity_label: str
    residual: Optional[float] = None
    shap_summary: Optional[Dict[str, Any]] = None
    explanation_text: Optional[str] = None

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0"}

@app.post("/predict-price", response_model=PredictPriceResponse)
def predict_price(listing: ListingFeatures):
    # En production : charger le modele serialise et feature pipeline
    dummy_price = 350000.0
    return PredictPriceResponse(predicted_price=dummy_price, confidence=0.72,
                                 interval_low=dummy_price*0.85, interval_high=dummy_price*1.15)

@app.post("/valuation", response_model=ValuationResponse)
def valuation(listing: ListingFeatures):
    return ValuationResponse(
        predicted_price=350000.0, confidence=0.72, opportunity_label="fair",
        shap_summary={"top_features": [{"feature": "surface", "shap_contribution": 50000, "direction": "positive"}]},
        explanation_text="Ce bien est estime a 350 000 TND en raison de sa superficie et de sa localisation.")

@app.post("/similar")
def similar_listings(listing: ListingFeatures, top_k: int = 5):
    return {"message": "Qdrant index not yet built", "top_k": top_k}
