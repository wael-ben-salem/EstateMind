#!/usr/bin/env bash
# ================================================
#  Apartment Listing Generator  |  Linux / Mac
# ================================================
set -e

echo "================================================"
echo " Apartment Listing Generator  |  Linux / Mac"
echo "================================================"
echo

# ── 1. Python check ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo
    echo "Install it first:"
    echo "  Ubuntu/Debian : sudo apt install python3 python3-venv python3-pip"
    echo "  Mac           : brew install python"
    exit 1
fi
echo "Python: $(python3 --version)"

# ── 2. Heal or create .venv ──────────────────────────────────────────────────
if [ -d ".venv" ] && ! .venv/bin/python -c "import sys" &>/dev/null 2>&1; then
    echo
    echo "Virtual environment is broken (likely copied from another machine)."
    echo "Removing and recreating..."
    rm -rf .venv
fi

if [ ! -d ".venv" ]; then
    echo
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Done."
fi

# ── 3. Activate ──────────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source .venv/bin/activate

# ── 4. Install dependencies (skipped if already installed) ───────────────────
if ! python -c "import streamlit" &>/dev/null 2>&1; then
    echo
    echo "Installing dependencies (first time only)..."
    pip install --upgrade pip --quiet

    # Detect NVIDIA GPU and pick the right PyTorch wheel
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
        echo "NVIDIA GPU detected — installing PyTorch with CUDA 12.8 support..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 --quiet
    else
        echo "No NVIDIA GPU detected — installing CPU-only PyTorch..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
    fi

    pip install -r requirements.txt --quiet
    echo
    echo "Dependencies installed successfully."
fi

# ── 5. Warn if model bundle is missing ───────────────────────────────────────
if [ ! -f "best_model_bundle.pth" ]; then
    echo
    echo "NOTE: best_model_bundle.pth not found."
    echo "The SAT model tab will be unavailable, but BLIP-2 will still work."
fi

# ── 6. Launch ────────────────────────────────────────────────────────────────
echo
echo "Starting app at http://localhost:8501"
echo "Press Ctrl+C to stop."
echo
streamlit run app.py
