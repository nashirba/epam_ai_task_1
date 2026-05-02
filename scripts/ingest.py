"""Ingest data/ into Weaviate.

Usage: uv run python -m scripts.ingest [--reset]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rich import print

from pia.config import get_settings
from pia.embeddings import get_embedding_provider
from pia.rag.chunker import chunk_markdown
from pia.rag.loaders import load_documents
from pia.rag.store import WeaviateStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    s = get_settings()
    print(f"Embedding provider: [bold]{s.embedding_provider}[/]  model: {s.embedding_model}")
    embeddings = get_embedding_provider()
    store = WeaviateStore(embeddings=embeddings, collection="KB", reset=args.reset)

    items = []
    for doc in load_documents(Path(s.data_dir)):
        for chunk in chunk_markdown(doc.text, max_tokens=120, overlap_tokens=24):
            items.append((doc, chunk))
    print(f"Ingesting {len(items)} chunks…")
    store.upsert(items)
    store.close()
    print("[green]Done.")


if __name__ == "__main__":
    main()
