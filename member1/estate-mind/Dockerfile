# Outliers market-intel agent — CPU-only image.
# (No GPU needed: sklearn/lightgbm/catboost are CPU; CLIP runs on CPU here.)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

# libgomp is required by lightgbm; build-essential covers any C-extension fallbacks.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (layer cache); CPU-only torch from PyTorch's index.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.1 \
    && pip install -r requirements.txt

# Code + artifacts in /app (artifacts can be overridden via volume mount in compose).
COPY . /app
ENV ESTATEMIND_ROOT=/app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8001/healthz').status==200 else 1)"

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
