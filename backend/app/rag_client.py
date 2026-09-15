"""
Imports the standalone rag/ package (kept outside backend/ so it can be
run and tested independently of the API — see rag/README section in the
top-level README). Adds it to sys.path relative to this file.
"""

import sys
from pathlib import Path
from functools import lru_cache

_RAG_DIR = Path(__file__).resolve().parents[2] / "rag"
if str(_RAG_DIR) not in sys.path:
    sys.path.insert(0, str(_RAG_DIR))

from retrieve import Retriever  # noqa: E402

from app.config import Settings


@lru_cache
def get_retriever(persist_dir: str, embedder: str, min_similarity: float) -> Retriever:
    # Cached per (persist_dir, embedder, threshold) tuple so the vector
    # index and embedding model are loaded once per process, not per request.
    return Retriever(persist_dir=persist_dir, embedder_kind=embedder, min_similarity=min_similarity)


def retriever_for(settings: Settings) -> Retriever:
    return get_retriever(settings.RAG_PERSIST_DIR, settings.RAG_EMBEDDER, settings.RAG_MIN_SIMILARITY)
