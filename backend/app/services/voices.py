# app/services/voices.py
"""
Returns the list of available TTS voices for the UI.
- XTTS default is always offered when USE_XTTS is enabled.
- XTTS (Cloned) is offered only if a reference voice file exists.
- Piper entries can be added later when the engine is wired (kept out to avoid UI -> 500s).
"""
from __future__ import annotations
import os
import logging

# Prefer central settings if available, but keep env fallback (matches your current behavior)
try:
    from ..config.settings import USE_XTTS  # type: ignore
except Exception:  # settings not imported yet or missing
    USE_XTTS = os.getenv("USE_XTTS", "0") in ("1", "true", "True")

from . import xtts_engine

logger = logging.getLogger("cognomegafx.voices")

def _xtts_voices() -> list[dict]:
    items: list[dict] = []
    if not USE_XTTS:
        return items

    # Always expose the default XTTS voice
    items.append({"id": "xtts_default", "label": "XTTS Default", "engine": "xtts"})

    # Only expose cloned option if we really have a reference wav
    try:
        if xtts_engine.has_reference_voice():
            items.append({"id": "xtts_cloned", "label": "XTTS (Cloned)", "engine": "xtts"})
    except Exception as e:
        # Be resilient: log and continue with default voice only
        logger.warning("xtts_engine.has_reference_voice failed: %s", e)

    return items

def list_voices() -> dict:
    """
    Public API used by the router.
    Shape: { "voices": [ { id, label, engine }, ... ] }
    """
    voices: list[dict] = []
    voices.extend(_xtts_voices())

    # NOTE: Piper is intentionally not listed until the piper engine is wired.
    # If/when you enable it, add something like:
    #
    # if piper_is_ready():
    #     voices.append({"id": "piper_default", "label": "Piper Default", "engine": "piper"})
    #
    # (and ensure selecting Piper won’t 500 from /speak)

    return {"voices": voices}
