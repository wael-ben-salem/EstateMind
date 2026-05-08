"""
FastAPI service exposing the photo → listing pipeline.

Endpoints:
    GET  /healthz             — readiness probe
    POST /caption-listing     — multipart photo upload, returns full DB record
    POST /caption-only        — multipart photo upload, English captions only

Run:
    uvicorn api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env from the project root so ESPRIT_LLM_API_KEY etc. are available.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from pipeline import (
    OLLAMA_MODEL,
    OLLAMA_URL,
    caption_listing,
    load_blip2_model,
    load_blip_fallback,
)


BLIP2_MODEL_ID = os.environ.get("BLIP2_MODEL_ID", "Salesforce/blip2-flan-t5-xl")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

_state: dict = {"blip": None, "load_error": None}


def _available_vram_gb() -> float:
    """Return free GPU VRAM in GB, or 0 if no GPU."""
    try:
        import torch
        if not torch.cuda.is_available():
            return 0.0
        return torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        return 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    # BLIP-2 flan-t5-xl needs ~7.5 GB VRAM (fp16).  Anything smaller → BLIP-1.
    # BLIP-1 large (~1.5 GB) is fast on any GPU and adequate for listing captions.
    vram = _available_vram_gb()
    explicit = "BLIP2_MODEL_ID" in os.environ
    use_blip2 = explicit or vram >= 7.0
    if use_blip2:
        try:
            _state["blip"] = load_blip2_model(BLIP2_MODEL_ID)
        except Exception as primary:
            try:
                _state["blip"] = load_blip_fallback()
                _state["load_error"] = (
                    f"BLIP-2 ({type(primary).__name__}) failed; using BLIP-1 fallback."
                )
            except Exception as fallback:
                _state["load_error"] = (
                    f"BLIP-2 failed: {primary!r}; fallback failed: {fallback!r}"
                )
    else:
        try:
            _state["blip"] = load_blip_fallback()
            if vram > 0:
                _state["load_error"] = (
                    f"GPU has {vram:.1f} GB VRAM — using BLIP-1 (BLIP-2 needs ≥7 GB)."
                )
        except Exception as e:
            _state["load_error"] = f"BLIP-1 load failed: {type(e).__name__}: {e}"
    yield


app = FastAPI(title="Real-Estate Listing Captioner", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {
        "ok": _state["blip"] is not None,
        "model": _state["blip"]["model_id"] if _state["blip"] else None,
        "device": str(_state["blip"]["device"]) if _state["blip"] else None,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "load_error": _state["load_error"],
    }


@app.post("/caption-listing")
async def caption_listing_endpoint(files: list[UploadFile] = File(...)):
    if _state["blip"] is None:
        raise HTTPException(503, f"Model not loaded: {_state['load_error']}")
    if not files:
        raise HTTPException(400, "No files uploaded.")
    images = [(f.filename or "image", await f.read()) for f in files]
    return caption_listing(_state["blip"], images)


@app.post("/caption-only")
async def caption_only_endpoint(files: list[UploadFile] = File(...)):
    if _state["blip"] is None:
        raise HTTPException(503, f"Model not loaded: {_state['load_error']}")
    if not files:
        raise HTTPException(400, "No files uploaded.")
    images = [(f.filename or "image", await f.read()) for f in files]
    return caption_listing(_state["blip"], images, skip_ollama=True)
