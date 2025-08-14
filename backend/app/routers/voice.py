# app/routers/voice.py
from __future__ import annotations

import logging, uuid, traceback, tempfile, os
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..services.tts_engine import synthesize_to_wav
from ..services.stt_engine import transcribe_wav
from ..utils.audio_tools import ensure_wav
from ..services.voices import list_voices
from ..services import xtts_engine

# Optional deps with safe fallbacks
try:
    from ..services.text_chunker import chunk_text
except Exception:
    def chunk_text(text: str, max_chars: int = 500) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        max_chars = max(50, int(max_chars or 500))
        parts, buf, n = [], [], 0
        for ch in text:
            buf.append(ch); n += 1
            if n >= max_chars and ch in ".!?\n":
                parts.append("".join(buf).strip()); buf, n = [], 0
        if buf:
            parts.append("".join(buf).strip())
        return parts

try:
    from ..utils.wav_tools import concat_wavs
except Exception:
    import wave
    def concat_wavs(paths: List[str], out_path: str) -> str:
        if not paths:
            raise RuntimeError("No WAV parts to concatenate")
        with wave.open(paths[0], "rb") as w0:
            params = w0.getparams()
            frames = [w0.readframes(w0.getnframes())]
        for p in paths[1:]:
            with wave.open(p, "rb") as wi:
                if wi.getparams() != params:
                    raise RuntimeError("WAV parameter mismatch while concatenating")
                frames.append(wi.readframes(wi.getnframes()))
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with wave.open(out_path, "wb") as wo:
            wo.setparams(params)
            for fr in frames:
                wo.writeframes(fr)
        return out_path

logger = logging.getLogger("cognomegafx.voice")
router = APIRouter()

# Where we put generated files if we want a persistent output
DATA_DIR = Path(__file__).resolve().parents[2] / "backend" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class SpeakRequest(BaseModel):
    text: str
    engine: str | None = "auto"     # "auto" | "xtts" | "piper"
    cloned: bool | None = False     # relevant for XTTS
    voice: str | None = None        # "xtts_default" | "xtts_cloned" | "piper_default"
    language: str | None = None     # e.g. "en"

class SpeakLongRequest(BaseModel):
    text: str
    voice: str | None = None
    language: str | None = None
    auto_language: bool | None = True
    max_chars: int | None = 500

@router.get("/voices")
def get_voices():
    return JSONResponse(list_voices())

@router.get("/debug")
def debug():
    return {"xtts": xtts_engine.diagnostics()}

@router.post("/speak", response_class=FileResponse)
def speak(req: SpeakRequest, response: Response, request: Request):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    try:
        text = (req.text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is empty.")

        cloned = bool(req.cloned)
        if req.voice == "xtts_default":
            use_engine, cloned = "xtts", False
        elif req.voice == "xtts_cloned":
            use_engine, cloned = "xtts", True
        elif req.voice == "piper_default":
            use_engine = "piper"
        else:
            use_engine = req.engine or "auto"

        logger.info("[%s] /speak start engine=%s cloned=%s voice=%s lang=%s len=%s",
                    rid, use_engine, cloned, req.voice, req.language, len(text))

        out_path, engine_used = synthesize_to_wav(
            text, engine=use_engine, cloned=cloned, language=req.language
        )
        response.headers["X-TTS-Engine"] = engine_used
        response.headers["X-Request-ID"] = rid

        logger.info("[%s] /speak ok engine=%s file=%s", rid, engine_used, out_path)
        return FileResponse(out_path, media_type="audio/wav", filename="speech.wav")

    except HTTPException:
        logger.warning("[%s] /speak 4xx:\n%s", rid, traceback.format_exc())
        raise
    except Exception as e:
        logger.exception("[%s] /speak 5xx: %s", rid, e)
        raise HTTPException(status_code=500, detail=f"TTS error (request_id={rid}). Check backend logs.")

@router.post("/speak_long", response_class=FileResponse)
def speak_long(req: SpeakLongRequest, response: Response, request: Request):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    try:
        text = (req.text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is empty.")

        if req.voice == "xtts_default":
            use_engine, cloned = "xtts", False
        elif req.voice == "xtts_cloned":
            use_engine, cloned = "xtts", True
        elif req.voice == "piper_default":
            use_engine, cloned = "piper", False
        else:
            use_engine, cloned = req.engine or "auto", False

        max_chars = int(req.max_chars or 500)
        parts_in = chunk_text(text, max_chars=max_chars)
        if not parts_in:
            raise HTTPException(status_code=400, detail="No chunks to synthesize.")

        logger.info("[%s] /speak_long start engine=%s cloned=%s voice=%s lang=%s chunks=%d",
                    rid, use_engine, cloned, req.voice, req.language, len(parts_in))

        tmpdir = tempfile.mkdtemp(prefix="long_tts_")
        part_paths: List[str] = []
        engine_used = use_engine
        for i, part in enumerate(parts_in, 1):
            out_path, engine_used = synthesize_to_wav(
                part, engine=use_engine, cloned=cloned, language=req.language
            )
            new_path = os.path.join(tmpdir, f"part_{i:04d}.wav")
            os.replace(out_path, new_path)
            part_paths.append(new_path)

        final_path = os.path.join(tmpdir, "speech_full.wav")
        concat_wavs(part_paths, final_path)

        response.headers["X-TTS-Engine"] = engine_used
        response.headers["X-Request-ID"] = rid
        logger.info("[%s] /speak_long ok engine=%s file=%s", rid, engine_used, final_path)
        return FileResponse(final_path, media_type="audio/wav", filename="speech.wav")

    except HTTPException:
        logger.warning("[%s] /speak_long 4xx:\n%s", rid, traceback.format_exc())
        raise
    except Exception as e:
        logger.exception("[%s] /speak_long 5xx: %s", rid, e)
        raise HTTPException(status_code=500, detail=f"TTS long error (request_id={rid}). Check backend logs.")

@router.post("/transcribe")
def transcribe(request: Request, audio: UploadFile = File(...)):
    # NOTE: Request must be non-optional for FastAPI DI
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    raw = audio.file.read()
    try:
        wav_path = ensure_wav(raw, input_mime=audio.content_type)
        text = transcribe_wav(wav_path)
        return {"text": text, "request_id": rid}
    except Exception as e:
        logger.exception("[%s] /transcribe 5xx: %s", rid, e)
        raise HTTPException(status_code=500, detail=f"STT error (request_id={rid}).")
