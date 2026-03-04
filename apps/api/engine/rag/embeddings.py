"""RAG — Embedding generation using sentence-transformers (local, no API needed)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    model = _get_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()


def embed_chunks(chunks: list, show_progress: bool = True) -> list[list[float]]:
    """Embed a list of Chunk objects, returning list of vectors."""
    model = _get_model()
    texts = [c.text if hasattr(c, "text") else str(c) for c in chunks]

    if show_progress:
        try:
            from tqdm import tqdm
            batch_size = 64
            all_embeddings = []
            for i in tqdm(range(0, len(texts), batch_size), desc="Embedding chunks"):
                batch = texts[i:i + batch_size]
                embs = model.encode(batch, show_progress_bar=False)
                all_embeddings.extend(embs.tolist())
            return all_embeddings
        except ImportError:
            pass

    embeddings = model.encode(texts, show_progress_bar=show_progress)
    return embeddings.tolist()
