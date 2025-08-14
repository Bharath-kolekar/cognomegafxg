# app/utils/audio_tools.py
import os
import tempfile
from typing import Optional

def ensure_wav(raw_bytes: bytes, input_mime: Optional[str] = None) -> str:
    """
    Very simple passthrough: if input is already a wav, just write to temp .wav.
    For other formats you'd integrate ffmpeg or soundfile; out of scope for now.
    """
    suffix = ".wav" if (input_mime or "").lower() == "audio/wav" else ".wav"
    fd, path = tempfile.mkstemp(prefix="upload_", suffix=suffix)
    os.close(fd)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return path
