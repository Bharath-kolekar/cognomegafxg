# app/services/lang_detect.py
from langdetect import detect, DetectorFactory

# Make langdetect deterministic
DetectorFactory.seed = 42

# Map langdetect codes -> XTTS codes where they differ or we want to limit set
LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "es": "es",
    "de": "de",
    "fr": "fr",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "ar": "ar",
    "bn": "bn",
    "ja": "ja",
    "ko": "ko",
    "zh-cn": "zh",  # normalize simplified -> zh
    "zh-tw": "zh",
    "zh": "zh",
}

def detect_lang(text: str, fallback: str = "en") -> str:
    try:
        raw = detect(text)
        # normalize special cases
        raw = raw.lower()
        if raw in LANG_MAP:
            return LANG_MAP[raw]
        # sometimes langdetect returns full locale like 'pt-BR'
        short = raw.split("-")[0]
        return LANG_MAP.get(short, fallback)
    except Exception:
        return fallback

# add at bottom of file
import regex as re

DEVANAGARI = re.compile(r"\p{Script=Devanagari}")

def guess_lang_by_script(text: str, fallback: str = "en") -> str:
    # if at least 30% chars are Devanagari, call it Hindi
    if not text:
        return fallback
    total = len(text)
    dev = len(DEVANAGARI.findall(text))
    if total and (dev / total) >= 0.30:
        return "hi"
    return fallback
