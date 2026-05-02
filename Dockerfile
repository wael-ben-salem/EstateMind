# ============================================================
# EstateMind Recommender — Dockerfile
# Image de base avec pandas/numpy déjà installés = plus rapide
# ============================================================

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installer les dépendances Python directement
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    "uvicorn[standard]==0.29.0" \
    pandas==2.2.2 \
    numpy==1.26.4 \
    pydantic==2.7.1 \
    python-multipart==0.0.9

# Copier le code et les données
COPY recommender/ ./recommender/
COPY data_cleaned/ ./data_cleaned/

EXPOSE 8000

CMD ["uvicorn", "recommender.api:app", "--host", "0.0.0.0", "--port", "8000"]
