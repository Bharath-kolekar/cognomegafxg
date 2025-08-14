# app/services/xtts_engine.py
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from .config.settings import (
    USE_XTTS,
    XTTS_REFERENCE_VOICE,
    XTTS_LANGUAGE,
    DATA_DIR,  # ensure DATA_DIR points to backend/backend/data in settings
    HF_HOME,   # optional, but we read it for diagnostics
)
import logging

logger = logging.getLogger("cognomegafx.xtts")

# Lazy import TTS to avoid import cost at module load
_TTS = None

def _get_tts():
    global _TTS
    if _TTS is None:
        # import here so that startup doesn't pay the cost until first request
        from TTS.api import TTS
        # Use the official multi-lang XTTS v2 model
        _TTS = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    return _TTS

def has_reference_voice() -> bool:
    p = (XTTS_REFERENCE_VOICE or "").strip()
    return bool(p and os.path.isfile(p))

def _effective_language(language: Optional[str]) -> str:
    lang = (language or "").strip()
    if not lang:
        lang = (XTTS_LANGUAGE or "en").strip() or "en"
    return lang

def synthesize_xtts(
    text: str,
    cloned: bool = False,
    language: Optional[str] = None,
) -> str:
    """
    Returns absolute path to a generated wav file.
    """
    if not USE_XTTS:
        raise RuntimeError("XTTS is disabled by configuration (USE_XTTS=0).")

    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text.")

    lang = _effective_language(language)

    # Output file under backend/backend/data
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    out_path = str(Path(DATA_DIR) / f"xtts_{uuid.uuid4().hex}.wav")

    # Build kwargs for TTS
    tts = _get_tts()
    kwargs = {
        "text": text,
        "language": lang,
        "file_path": out_path,
    }

    # If we have a reference voice and we are in cloned mode, pass it.
    # NOTE: Some environments/models behave more robustly when a reference is provided.
    ref = (XTTS_REFERENCE_VOICE or "").strip()
    if cloned:
        if not ref or not os.path.isfile(ref):
            raise RuntimeError("XTTS cloned voice is selected, but XTTS_REFERENCE_VOICE is missing/not a file.")
        kwargs["speaker_wav"] = ref
    else:
        # Optionally, you can ALSO pass the reference for default if you want it to
        # sound like your voice even in 'default' mode. To keep semantics:
        # don't pass it here. If you keep seeing failures in default mode, uncomment:
        # if ref and os.path.isfile(ref):
        #     kwargs["speaker_wav"] = ref
        pass

    logger.info("XTTS synth start cloned=%s lang=%s out=%s", cloned, lang, out_path)
    try:
        # Do the synthesis
        tts.tts_to_file(**kwargs)
    except Exception as e:
        logger.exception("XTTS synthesis failed")
        # Re-throw with a compact message (router will wrap as 500)
        raise RuntimeError(f"XTTS synthesis failed: {e}") from e

    if not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("XTTS produced an empty or missing output file.")

    logger.info("XTTS synth ok -> %s", out_path)
    return out_path

def diagnostics():
    return {
        "USE_XTTS": bool(USE_XTTS),
        "XTTS_LANGUAGE": (XTTS_LANGUAGE or ""),
        "XTTS_REFERENCE_VOICE": (XTTS_REFERENCE_VOICE or ""),
        "isfile": has_reference_voice(),
        "HF_HOME": (HF_HOME or ""),
    }
