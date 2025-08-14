# app/services/tts_engine.py
from __future__ import annotations

import os
from typing import Optional, Tuple
from pathlib import Path

from .config.settings import (
    USE_XTTS,
    PIPER_BIN,
    PIPER_MODEL,
    DATA_DIR,
)
from . import xtts_engine
import logging

logger = logging.getLogger("cognomegafx.tts")

def _choose_engine(explicit: Optional[str]) -> str:
    """
    Decide which engine to use if 'auto' or None.
    Prefers XTTS if enabled; otherwise Piper if configured; otherwise error.
    """
    if explicit and explicit != "auto":
        return explicit

    if USE_XTTS:
        return "xtts"
    if (PIPER_BIN or "").strip() and (PIPER_MODEL or "").strip():
        return "piper"
    raise RuntimeError("No TTS engine available: enable XTTS or configure Piper in .env")

def synthesize_to_wav(
    text: str,
    engine: Optional[str] = "auto",
    cloned: bool = False,
    language: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Main entrypoint used by the router.
    Returns (absolute_output_path, engine_used).
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text.")

    engine_used = _choose_engine(engine)

    if engine_used == "xtts":
        out_path = xtts_engine.synthesize_xtts(text=text, cloned=cloned, language=language)
        return out_path, "xtts"

    if engine_used == "piper":
        # (Optional) Implement Piper path here if you later enable it.
        # For now, fail clearly so the API caller sees a good error.
        raise RuntimeError("Piper TTS is not configured in this build.")

    # Should never reach here
    raise RuntimeError(f"Unknown TTS engine: {engine_used}")
