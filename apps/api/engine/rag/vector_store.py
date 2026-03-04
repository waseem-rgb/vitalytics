"""RAG — Numpy-based vector store (local, persistent). No ChromaDB needed."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from apps.api.app.core.config import CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

COLLECTION_NAME = "harrison_medical"

_store: dict | None = None


def _store_dir() -> Path:
    d = Path(CHROMA_PERSIST_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_store() -> dict:
    """Load persisted embeddings and metadata from disk."""
    global _store
    if _store is not None:
        return _store

    store_dir = _store_dir()
    emb_path = store_dir / "embeddings.npy"
    meta_path = store_dir / "metadata.json"
    docs_path = store_dir / "documents.json"

    if emb_path.exists() and meta_path.exists() and docs_path.exists():
        embeddings = np.load(str(emb_path))
        with open(meta_path) as f:
            metadatas = json.load(f)
        with open(docs_path) as f:
            documents = json.load(f)
        _store = {
            "embeddings": embeddings,
            "metadatas": metadatas,
            "documents": documents,
        }
        logger.info(f"Loaded vector store with {len(documents)} documents")
    else:
        _store = {
            "embeddings": np.empty((0, 0)),
            "metadatas": [],
            "documents": [],
        }

    return _store


def init_chroma(collection_name: str = COLLECTION_NAME):
    """Initialize the store (kept for API compatibility)."""
    store = _load_store()
    logger.info(f"Collection '{collection_name}' ready with {len(store['documents'])} documents")
    return store


def get_collection():
    """Get the store (compatibility wrapper)."""
    return _load_store()


def add_documents(chunks: list, embeddings: list[list[float]]):
    """Add chunks with their embeddings to the vector store and persist."""
    global _store
    store_dir = _store_dir()

    documents = [c.text if hasattr(c, "text") else str(c) for c in chunks]
    metadatas = []
    for c in chunks:
        meta = c.metadata if hasattr(c, "metadata") else {}
        clean_meta = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)
        metadatas.append(clean_meta)

    emb_array = np.array(embeddings, dtype=np.float32)

    # Persist to disk
    np.save(str(store_dir / "embeddings.npy"), emb_array)
    with open(store_dir / "metadata.json", "w") as f:
        json.dump(metadatas, f)
    with open(store_dir / "documents.json", "w") as f:
        json.dump(documents, f)

    _store = {
        "embeddings": emb_array,
        "metadatas": metadatas,
        "documents": documents,
    }

    logger.info(f"Added {len(chunks)} documents to vector store")


def search(query_embedding: list[float], top_k: int = 5, where: dict | None = None) -> list[dict]:
    """Search the vector store using cosine similarity."""
    store = _load_store()

    if len(store["documents"]) == 0:
        return []

    emb_matrix = store["embeddings"]
    query_vec = np.array(query_embedding, dtype=np.float32)

    # Cosine similarity
    norms = np.linalg.norm(emb_matrix, axis=1)
    query_norm = np.linalg.norm(query_vec)
    norms = np.where(norms == 0, 1e-10, norms)
    if query_norm == 0:
        query_norm = 1e-10

    similarities = emb_matrix @ query_vec / (norms * query_norm)

    # Apply metadata filter if specified
    if where:
        mask = np.ones(len(store["documents"]), dtype=bool)
        for key, val in where.items():
            for i, meta in enumerate(store["metadatas"]):
                if meta.get(key) != val:
                    mask[i] = False
        similarities = np.where(mask, similarities, -1.0)

    # Get top-k indices
    k = min(top_k, len(store["documents"]))
    top_indices = np.argsort(similarities)[-k:][::-1]

    output = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score <= 0:
            continue
        output.append({
            "text": store["documents"][idx],
            "metadata": store["metadatas"][idx],
            "distance": 1 - score,
            "score": score,
        })

    return output


def is_ready() -> bool:
    """Check if the vector store has documents."""
    try:
        store = _load_store()
        return len(store["documents"]) > 0
    except Exception:
        return False
