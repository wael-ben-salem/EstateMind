@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo  Apartment Listing Generator  ^|  Windows
echo ================================================
echo.

REM ── 1. Python check ────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo.
    echo Download from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during install, then rerun this script.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Python: %%v

REM ── 2. Heal or create .venv ────────────────────────────────────────────────
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo Virtual environment is broken ^(likely copied from another machine^).
        echo Removing and recreating...
        rmdir /s /q .venv
    )
)

if not exist ".venv" (
    echo.
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Done.
)

REM ── 3. Activate ────────────────────────────────────────────────────────────
call .venv\Scripts\activate.bat

REM ── 4. Install dependencies (skipped if already installed) ─────────────────
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies ^(first time only^)...
    pip install --upgrade pip --quiet

    REM Detect NVIDIA GPU and pick the right PyTorch wheel
    nvidia-smi >nul 2>&1
    if !errorlevel! == 0 (
        echo NVIDIA GPU detected — installing PyTorch with CUDA 12.8 support...
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 --quiet
    ) else (
        echo No NVIDIA GPU detected — installing CPU-only PyTorch...
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
    )

    pip install -r requirements.txt --quiet
    echo.
    echo Dependencies installed successfully.
)

REM ── 5. Warn if model bundle is missing ─────────────────────────────────────
if not exist "best_model_bundle.pth" (
    echo.
    echo NOTE: best_model_bundle.pth not found.
    echo The SAT model tab will be unavailable, but BLIP-2 will still work.
)

REM ── 6. Launch ──────────────────────────────────────────────────────────────
echo.
echo Starting app at http://localhost:8501
echo Press Ctrl+C in this window to stop.
echo.
streamlit run app.py
