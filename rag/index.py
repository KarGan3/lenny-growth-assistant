"""
Embeds chunks.jsonl and loads them into a persistent ChromaDB collection.

Uses Chroma's bundled ONNX MiniLM embedding function by default (local,
CPU-only, no API key, no torch dependency — keeps setup light for an
evaluator running this on a laptop). The embedding function is swappable:
pass --embedder ollama to use a local Ollama embedding model instead
(e.g. nomic-embed-text), matching the "flexible LLM configuration"
requirement's spirit for the retrieval side too.
"""

import argparse
import json
import pickle
from pathlib import Path

import chromadb
import numpy as np
from chromadb.utils import embedding_functions
from chromadb.api.types import EmbeddingFunction

COLLECTION_NAME = "lennys_podcast"
BATCH_SIZE = 256


class LocalLexicalEmbedder(EmbeddingFunction):
    """
    TF-IDF + truncated-SVD (LSA) embedding function requiring no model
    download — used as an offline-friendly fallback when the ONNX-MiniLM
    weights (fetched from S3) or an Ollama server aren't reachable. Fit
    once at index time and persisted alongside the Chroma collection so
    query-time embedding uses the exact same vectorizer/SVD.
    """

    def __init__(self, persist_dir: Path, n_components: int = 256):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self.persist_dir = Path(persist_dir)
        self.model_path = self.persist_dir / "local_lexical_embedder.pkl"
        self.n_components = n_components
        self.vectorizer = None
        self.svd = None
        self._TfidfVectorizer = TfidfVectorizer
        self._TruncatedSVD = TruncatedSVD
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                self.vectorizer, self.svd = pickle.load(f)

    def fit(self, texts: list[str]):
        self.vectorizer = self._TfidfVectorizer(
            max_features=20000, ngram_range=(1, 2), min_df=2, sublinear_tf=True
        )
        tfidf = self.vectorizer.fit_transform(texts)
        self.svd = self._TruncatedSVD(n_components=self.n_components, random_state=42)
        self.svd.fit(tfidf)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump((self.vectorizer, self.svd), f)

    def name(self) -> str:
        return "local-lexical-tfidf-svd"

    def __call__(self, input: list[str]):
        if self.vectorizer is None or self.svd is None:
            raise RuntimeError("LocalLexicalEmbedder not fit yet — call fit() at index time")
        tfidf = self.vectorizer.transform(input)
        vecs = self.svd.transform(tfidf)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (vecs / norms).tolist()


def build_embedder(kind: str, ollama_model: str, ollama_url: str, persist_dir: str):
    if kind == "onnx-minilm":
        return embedding_functions.ONNXMiniLM_L6_V2()
    if kind == "ollama":
        return embedding_functions.OllamaEmbeddingFunction(
            url=ollama_url, model_name=ollama_model
        )
    if kind == "local-lexical":
        return LocalLexicalEmbedder(Path(persist_dir))
    raise ValueError(f"unknown embedder: {kind}")


def load_chunks(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    ap = argparse.ArgumentParser(description="Index transcript chunks into ChromaDB")
    ap.add_argument("--chunks", default="data/chunks.jsonl")
    ap.add_argument("--persist-dir", default="data/chroma")
    ap.add_argument("--embedder", choices=["onnx-minilm", "ollama", "local-lexical"], default="onnx-minilm")
    ap.add_argument("--ollama-model", default="nomic-embed-text")
    ap.add_argument("--ollama-url", default="http://localhost:11434/api/embeddings")
    ap.add_argument("--reset", action="store_true", help="drop and rebuild the collection")
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.persist_dir)
    embedder = build_embedder(args.embedder, args.ollama_model, args.ollama_url, args.persist_dir)

    if args.embedder == "local-lexical":
        print("Fitting local TF-IDF+SVD vectorizer on the full corpus (no downloads)...")
        all_texts = [c["text"] for c in load_chunks(Path(args.chunks))]
        embedder.fit(all_texts)
        print(f"Fit complete: {len(all_texts)} docs -> {embedder.n_components}-dim vectors")

    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
        metadata={"hnsw:space": "cosine"},
    )

    ids, docs, metas = [], [], []
    total = 0

    def flush():
        nonlocal ids, docs, metas
        if ids:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
            ids, docs, metas = [], [], []

    for c in load_chunks(Path(args.chunks)):
        ids.append(c["chunk_id"])
        docs.append(c["text"])
        metas.append({
            "episode_slug": c["episode_slug"],
            "guest": c["guest"],
            "title": c["title"],
            "youtube_url": c["youtube_url"],
            "video_id": c["video_id"],
            "publish_date": c["publish_date"],
            "start_timestamp": c["start_timestamp"],
            "source_path": c["source_path"],
        })
        total += 1
        if len(ids) >= BATCH_SIZE:
            flush()
            print(f"  indexed {total} chunks...", end="\r")
    flush()
    print(f"\nIndexed {total} chunks into collection '{COLLECTION_NAME}' at {args.persist_dir}")
    print(f"Collection count: {collection.count()}")


if __name__ == "__main__":
    main()
