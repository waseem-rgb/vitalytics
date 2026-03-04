#!/usr/bin/env python3
"""CLI: Ingest Harrison's PDF into ChromaDB vector store.

Usage: python scripts/ingest_harrison.py [--path /path/to/harrisons.pdf]
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from apps.api.app.core.config import HARRISON_PDF_PATH


def main():
    parser = argparse.ArgumentParser(description="Ingest Harrison's Medicine PDF into vector store")
    parser.add_argument("--path", type=str, default=HARRISON_PDF_PATH, help="Path to Harrison's PDF")
    args = parser.parse_args()

    pdf_path = Path(args.path)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"Loading PDF: {pdf_path}")
    print("=" * 60)

    # Step 1: Ingest PDF
    from apps.api.engine.rag.ingestion import ingest_pdf
    start = time.time()
    print("Step 1/3: Extracting and chunking PDF...")
    chunks = ingest_pdf(pdf_path)
    ingest_time = time.time() - start
    print(f"  Extracted {len(chunks)} chunks in {ingest_time:.1f}s")

    # Step 2: Generate embeddings
    from apps.api.engine.rag.embeddings import embed_chunks
    start = time.time()
    print("Step 2/3: Generating embeddings...")
    embeddings = embed_chunks(chunks, show_progress=True)
    embed_time = time.time() - start
    print(f"  Generated {len(embeddings)} embeddings in {embed_time:.1f}s")

    # Step 3: Store in ChromaDB
    from apps.api.engine.rag.vector_store import init_chroma, add_documents
    start = time.time()
    print("Step 3/3: Storing in ChromaDB...")
    init_chroma()
    add_documents(chunks, embeddings)
    store_time = time.time() - start
    print(f"  Stored {len(chunks)} documents in {store_time:.1f}s")

    print()
    print("=" * 60)
    print("INGESTION COMPLETE")
    print(f"  Total chunks:    {len(chunks)}")
    print(f"  Embeddings:      {len(embeddings)}")
    print(f"  Ingest time:     {ingest_time:.1f}s")
    print(f"  Embedding time:  {embed_time:.1f}s")
    print(f"  Storage time:    {store_time:.1f}s")
    print(f"  Total time:      {ingest_time + embed_time + store_time:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
