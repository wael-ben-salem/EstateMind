# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# --- CPU OPTIMIZATION FOR 3.13 ---
# Pre-install CPU version of Torch. 
# In 2026, Docling (>=2.18.0) supports Python 3.13 perfectly.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install your requirements (docling, qdrant, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final lightweight image
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies required by Docling, PyMuPDF, and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-xcb1 \
    libxrender1 \
    libxext6 \
    libsm6 \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy your source code
COPY src/ ./src/
COPY api/ ./api/
COPY config/ ./config/
COPY main.py run_api.py ./

# Performance & Stability Env Vars
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Force CPU threading limits to prevent container freezes
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

EXPOSE 8000

CMD ["python", "run_api.py"]