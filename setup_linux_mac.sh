#!/usr/bin/env bash
# ============================================================
#  SAT Reproduction — One-click setup for Linux/Mac + NVIDIA GPU
#  Works on RTX 5070 Ti (CUDA 12.8) and any CUDA 11.8+ GPU
# ============================================================
set -e

echo "[1/5] Checking Python..."
python3 --version

echo ""
echo "[2/5] Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists, skipping."
fi

echo ""
echo "[3/5] Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "[4/5] Installing PyTorch with CUDA 12.8 support (RTX 5070 Ti compatible)..."
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

echo ""
echo "[5/5] Installing project dependencies..."
pip install kagglehub nltk tqdm pillow pandas matplotlib jupyter notebook openai-clip ipywidgets

echo ""
echo "============================================================"
echo " Setup complete!"
echo ""
echo " IMPORTANT: You need a Kaggle API key to download Flickr8k."
echo " 1. Go to https://www.kaggle.com/settings > API > Create New Token"
echo " 2. Save kaggle.json to: ~/.kaggle/kaggle.json"
echo " 3. Run: chmod 600 ~/.kaggle/kaggle.json"
echo ""
echo " To start the notebook:"
echo "   source .venv/bin/activate"
echo "   jupyter notebook SAT_Reproduction_Local.ipynb"
echo "============================================================"
