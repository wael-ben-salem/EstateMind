# Apartment Listing Generator

Upload apartment photos → AI generates a polished real-estate listing description.

The trained SAT model (`best_model_bundle.pth`) is already included — **no training required**.

---

## Quick start

### Windows — double-click `launch.bat`

That's it. The script will:
1. Create a virtual environment (first time only)
2. Auto-detect your GPU and install the right PyTorch wheel
3. Install all dependencies
4. Open the app at `http://localhost:8501`

### Linux / Mac

```bash
chmod +x launch.sh
./launch.sh
```

Same automatic setup + launch.

> **Moving to a new PC?** Just copy the folder (skip `.venv/` — it's regenerated automatically). Run `launch.bat` / `launch.sh` on the new machine and setup runs again from scratch.

---

## What's in this folder

| File | Purpose |
|---|---|
| `app.py` | Streamlit app — the main UI |
| `best_model_bundle.pth` | Trained SAT model (encoder + decoder + vocab) |
| `launch.bat` | One-click launcher for Windows |
| `launch.sh` | One-click launcher for Linux / Mac |
| `requirements.txt` | App dependencies |
| `requirements_train.txt` | Extra deps needed only for re-training |
| `setup_windows.bat` | Original training-focused setup (advanced) |
| `setup_linux_mac.sh` | Original training-focused setup (advanced) |

---

## Caption models

The app offers two models selectable from the sidebar:

| Model | Quality | Setup |
|---|---|---|
| **BLIP-2** (default) | Rich 30–50 word room descriptions | Downloads ~15 GB on first use, cached after |
| **SAT model** | Shorter academic-style captions | Instant — loaded from `best_model_bundle.pth` |

---

## BLIP-2 first-time download

On first launch with BLIP-2 selected, the app downloads weights from HuggingFace Hub (~15 GB) and caches them at `~/.cache/huggingface/hub/`. Every subsequent launch loads from cache in seconds.

| Variant | Download | VRAM (fp16) |
|---|---|---|
| `blip2-opt-2.7b` (default) | ~15.8 GB | ~3.5 GB |
| `blip2-flan-t5-xl` | ~6.6 GB | ~2.5 GB |

If BLIP-2 fails to load, the app automatically tries the smaller 1 GB fallback model. If both fail, a "Use SAT model instead" button appears in the main area — the SAT model always works with no download.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `launch.bat` opens and immediately closes | Right-click → "Run as administrator", or open a terminal and run it manually |
| `python not found` | Install Python from python.org; check "Add Python to PATH" |
| BLIP-2 download fails | Check internet connection; first download needs ~15 GB free on C: drive |
| BLIP-2 `OSError: [Errno 28]` | Disk full in HuggingFace cache — free space or set `HF_HOME` to another drive |
| `OutOfMemoryError` on GPU | Switch to `blip2-flan-t5-xl` variant in the sidebar |
| `ModuleNotFoundError: clip` | Run: `.venv\Scripts\pip install openai-clip` (Windows) |
| App is slow (no GPU) | CPU mode works but takes ~1–3 min per photo; BLIP-2 is not practical on CPU |
| SAT model tab shows "File not found" | Make sure `best_model_bundle.pth` is in the same folder as `app.py` |

Use the **🔬 Run diagnostics** button in the sidebar to check CUDA, disk space, HuggingFace connectivity, and package versions all at once.

---

## Re-training from scratch (optional)

If you want to retrain the SAT model yourself, you need the Flickr8k dataset and a Kaggle API key.

**Extra dependencies:**
```
pip install -r requirements_train.txt
```

**Kaggle API key:**
1. Go to kaggle.com → Settings → API → Create New Token
2. Save `kaggle.json` to:
   - Windows: `C:\Users\<YourName>\.kaggle\kaggle.json`
   - Linux/Mac: `~/.kaggle/kaggle.json`

**Launch the training notebook:**
```
# Windows
.venv\Scripts\activate.bat
jupyter notebook SAT_Local_Training_LocalData.ipynb

# Linux / Mac
source .venv/bin/activate
jupyter notebook SAT_Local_Training_LocalData.ipynb
```

The notebook downloads Flickr8k automatically and saves the trained bundle as `best_model_bundle.pth`.

---

## GPU notes

The launch scripts detect your GPU automatically:

- **NVIDIA GPU** (any model with CUDA 12.x drivers): installs PyTorch with CUDA 12.8 support
- **No GPU / CPU only**: installs CPU-only PyTorch — the app works but BLIP-2 inference is slow

RTX 5070 Ti (Blackwell) specifically requires CUDA 12.8+ and PyTorch 2.7+ — both installed automatically.
