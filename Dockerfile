# GPU-ready FastAPI container for the photo → listing pipeline.
# Base image already has Python 3.11 + PyTorch 2.4 + CUDA 12.4 + cuDNN 9.
FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Minimal system deps. libgl1 + libglib2.0-0 are needed by Pillow / OpenCV.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY pipeline.py api.py ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
