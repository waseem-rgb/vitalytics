"""RAG — Semantic retrieval from the Harrison's vector store."""

from apps.api.engine.rag.embeddings import embed_text
from apps.api.engine.rag.vector_store import search


def build_clinical_query(patterns: list[dict], lab_results: dict) -> str:
    """Build a semantic query string from detected patterns and lab results."""
    parts = []

    for pattern in patterns:
        parts.append(pattern.get("name", ""))
        parts.append(pattern.get("interpretation", "")[:100])

    # Add abnormal test names
    abnormal = [k.replace("_", " ") for k, v in lab_results.items() if v is not None]
    if abnormal:
        parts.append("laboratory findings: " + ", ".join(abnormal[:10]))

    # Add clinical keywords
    for pattern in patterns:
        cat = pattern.get("category", "")
        if cat:
            parts.append(f"{cat} diagnosis differential treatment")

    query = " ".join(parts)
    return query[:1000]  # Limit query length


def retrieve_context(
    query: str,
    clinical_domain: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Retrieve relevant chunks from the vector store."""
    query_embedding = embed_text(query)

    where = None
    if clinical_domain:
        where = {"clinical_domain": clinical_domain}

    results = search(query_embedding, top_k=top_k, where=where)

    # If domain-filtered search returns too few results, search without filter
    if len(results) < 2 and clinical_domain:
        results = search(query_embedding, top_k=top_k)

    return results
