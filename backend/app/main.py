# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.voice import router as voice_router

app = FastAPI(title="Cognomegafx API", version="0.3.0-max")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "version": "0.3.0-max"}

# Mount optional content router (only if present)
try:
    from .routers import content as content_router  # lazy import so missing module won't break startup
    app.include_router(content_router.router, prefix="/api/v1/content", tags=["content"])
except Exception:
    # It's fine if content router doesn't exist (or has import-time issues)
    pass

# Voice routes
app.include_router(voice_router, prefix="/api/v1/voice", tags=["voice"])
