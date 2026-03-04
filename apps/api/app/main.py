"""FastAPI application — Vitalytics Lab Intelligence Engine."""

import os
import sys
from pathlib import Path

# Ensure the project root is on the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.routers import analysis, upload, reference

app = FastAPI(
    title="Vitalytics",
    description="Medical Lab Intelligence Engine — 3-Tier Clinical Decision Support",
    version="1.0.0",
)

# CORS — read origins from env, fall back to localhost defaults
_default_origins = "http://localhost:3002,http://127.0.0.1:3002"
_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analysis.router)
app.include_router(upload.router)
app.include_router(reference.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    rag_ready = False
    try:
        from apps.api.engine.rag.vector_store import is_ready
        rag_ready = is_ready()
    except Exception:
        pass

    return {"status": "ok", "rag_ready": rag_ready}


@app.get("/api/v1/rag/status")
async def rag_status():
    """RAG pipeline status endpoint."""
    try:
        from apps.api.engine.rag.vector_store import get_collection, is_ready
        from apps.api.app.core.config import ANTHROPIC_API_KEY
        ingested = is_ready()
        total_chunks = 0
        if ingested:
            store = get_collection()
            total_chunks = len(store.get("documents", []))
        return {
            "ingested": ingested,
            "total_chunks": total_chunks,
            "collection_name": "harrison_medical",
            "embedding_model": "all-MiniLM-L6-v2",
            "api_key_set": bool(ANTHROPIC_API_KEY),
        }
    except Exception:
        return {
            "ingested": False,
            "total_chunks": 0,
            "collection_name": "harrison_medical",
            "embedding_model": "all-MiniLM-L6-v2",
            "api_key_set": False,
        }
