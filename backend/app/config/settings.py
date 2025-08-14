# app/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# load .env from backend/ (one level above /app)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# --- XTTS related envs ---
USE_XTTS = os.getenv("USE_XTTS", "0") in ("1", "true", "True")
XTTS_LANGUAGE = os.getenv("XTTS_LANGUAGE") or "en"
XTTS_REFERENCE_VOICE = os.getenv("XTTS_REFERENCE_VOICE") or ""

# optional caches (safe if empty)
HF_HOME = os.getenv("HF_HOME", "")
HUGGINGFACE_HUB_CACHE = os.getenv("HUGGINGFACE_HUB_CACHE", "")
TRANSFORMERS_CACHE = os.getenv("TRANSFORMERS_CACHE", "")
TORCH_HOME = os.getenv("TORCH_HOME", "")

# coqui tos marker; we only read it—set from your shell/env
COQUI_TOS_AGREED = os.getenv("COQUI_TOS_AGREED", "")

# temp output directory
TMP_OUT = BACKEND_DIR / "backend" / "data"
TMP_OUT.mkdir(parents=True, exist_ok=True)
