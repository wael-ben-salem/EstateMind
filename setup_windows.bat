@echo off
REM ============================================================
REM  SAT Reproduction — One-click setup for Windows + RTX GPU
REM  Works on RTX 5070 Ti (CUDA 12.8) and any CUDA 11.8+ GPU
REM ============================================================

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Download from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
python --version

echo.
echo [2/5] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists, skipping.
)

echo.
echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [4/5] Installing PyTorch with CUDA 12.8 support (RTX 5070 Ti compatible)...
REM PyTorch 2.7+ with CUDA 12.8 is required for Blackwell (RTX 50xx) GPUs
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

echo.
echo [5/5] Installing project dependencies...
pip install kagglehub nltk tqdm pillow pandas matplotlib jupyter notebook openai-clip ipywidgets

echo.
echo ============================================================
echo  Setup complete!
echo.
echo  IMPORTANT: You need a Kaggle API key to download Flickr8k.
echo  1. Go to https://www.kaggle.com/settings ^> API ^> Create New Token
echo  2. Save kaggle.json to: C:\Users\%USERNAME%\.kaggle\kaggle.json
echo.
echo  To start the notebook:
echo    .venv\Scripts\activate.bat
echo    jupyter notebook SAT_Reproduction_Local.ipynb
echo ============================================================
pause
