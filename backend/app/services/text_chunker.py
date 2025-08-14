# app/services/text_chunker.py
"""
Robust sentence-ish chunker:
- Keep original behavior: sentence split -> merge tiny fragments -> pack to max_chars
- Extras:
  * Fallback splitting for ultra-long sentences (no punctuation)
  * Hard slicing if still too long
  * Bounds + whitespace normalization
"""
from __future__ import annotations
import re
from typing import List

# Original heuristic: split after . ! ? when followed by an uppercase/digit
# (kept from your version)
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

# Additional, softer boundaries used only for very long sentences
_SOFT_BREAK_RE = re.compile(r"\s*([,;:\u3001\u3002])\s*")  # commas/semicolons + CJK punctuation

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def split_sentences(text: str) -> List[str]:
    """
    1) Cheap sentence split (your original rule).
    2) Merge tiny fragments (<60 chars) with previous (your original rule).
    """
    text = (text or "").strip()
    if not text:
        return []

    parts = _SENT_RE.split(text)  # preserves punctuation on the left side
    merged: List[str] = []
    for p in parts:
        p = _normalize_ws(p)
        if not p:
            continue
        if merged and len(merged[-1]) < 60 and len(p) < 60:
            merged[-1] = f"{merged[-1]} {p}"
        else:
            merged.append(p)
    return merged

def _soft_split_very_long(s: str, target: int) -> List[str]:
    """
    Try to split very long single sentences on commas/semicolons first.
    If still too long, hard-slice.
    """
    s = _normalize_ws(s)
    if len(s) <= target:
        return [s]

    # 1) try soft splits
    # Rebuild keeping delimiters to avoid losing prosody hints
    tokens = _SOFT_BREAK_RE.split(s)
    # tokens like: [chunk, delim, chunk, delim, ...]
    chunks: List[str] = []
    buf = ""
    for i, t in enumerate(tokens):
        if not t:
            continue
        candidate = f"{buf}{t}" if not buf else f"{buf}{'' if t in ',;:，、。' else ' '}{t}"
        if len(candidate) <= target:
            buf = candidate
        else:
            if buf:
                chunks.append(buf.strip())
                buf = t
            else:
                # even single token too large → hard slice
                break
    if buf:
        chunks.append(buf.strip())

    if chunks and all(len(c) <= target for c in chunks):
        return chunks

    # 2) hard slice if still too long
    out: List[str] = []
    i = 0
    while i < len(s):
        out.append(s[i : i + target])
        i += target
    return out

def pack_chunks(sentences: List[str], max_chars: int = 500) -> List[str]:
    """
    Pack sentences into chunks up to max_chars.
    If a single sentence is longer than max_chars, we attempt soft split,
    then hard slice as a last resort.
    """
    max_chars = int(max(200, min(2000, max_chars or 500)))  # clamp
    chunks: List[str] = []
    cur = ""

    for s in sentences:
        s = _normalize_ws(s)
        if not s:
            continue

        if len(s) > max_chars:
            # flush current
            if cur:
                chunks.append(cur)
                cur = ""
            # split the very long sentence safely
            for piece in _soft_split_very_long(s, max_chars):
                if len(piece) <= max_chars:
                    chunks.append(piece)
                else:
                    # final safety: hard slice (should be rare now)
                    i = 0
                    while i < len(piece):
                        chunks.append(piece[i : i + max_chars])
                        i += max_chars
            continue

        if not cur:
            cur = s
            continue

        candidate = f"{cur} {s}"
        if len(candidate) <= max_chars:
            cur = candidate
        else:
            chunks.append(cur)
            cur = s

    if cur:
        chunks.append(cur)
    return chunks

def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """
    Public API: returns packed chunks.
    """
    return pack_chunks(split_sentences(text), max_chars=max_chars)
