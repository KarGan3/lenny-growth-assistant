"""
Retrieval layer for the Lenny Growth Assistant.

Wraps the Chroma collection built by index.py. Given a query, returns
the top-k chunks with similarity scores and ready-to-render citations
(episode title, guest, timestamped YouTube deep link). Also exposes a
grounding check: if the best match's similarity is below a threshold,
the caller should tell the user the knowledge base doesn't support an
answer rather than guessing.
"""

import argparse
import re
import json
from dataclasses import dataclass
from pathlib import Path

import chromadb

from index import COLLECTION_NAME, build_embedder


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    guest: str
    title: str
    youtube_url: str
    start_timestamp: str
    publish_date: str
    distance: float  # cosine distance (lower = more similar)
    source_path: str = ''
    source_revision: str = 'be8ab89a890a833cbba2c892178f823fff178c65'

    @property
    def source_url(self) -> str:
        path = self.source_path or f'episodes/{self.chunk_id.split("::")[0]}/transcript.md'
        return f'https://github.com/ChatPRD/lennys-podcast-transcripts/blob/{self.source_revision}/' + path

    @property
    def similarity(self) -> float:
        return max(0.0, 1.0 - self.distance)

    @property
    def deep_link(self) -> str:
        if not self.youtube_url:
            return self.source_url
        ts_parts = [int(p) for p in self.start_timestamp.split(":")]
        while len(ts_parts) < 3:
            ts_parts.insert(0, 0)
        h, m, s = ts_parts
        seconds = h * 3600 + m * 60 + s
        sep = "&" if "?" in self.youtube_url else "?"
        return f"{self.youtube_url}{sep}t={seconds}s"

    def citation(self) -> str:
        return f"{self.guest} — \"{self.title}\" ({self.publish_date}) @ {self.start_timestamp} — {self.deep_link}"


class Retriever:
    def __init__(self, persist_dir: str = "data/chroma", embedder_kind: str = "local-lexical",
                 ollama_model: str = "nomic-embed-text", ollama_url: str = "http://localhost:11434/api/embeddings",
                 min_similarity: float = 0.15):
        # NOTE on grounding: min_similarity is a cheap circuit-breaker for
        # near-zero-overlap queries, not the primary grounding mechanism.
        # The lexical (TF-IDF+SVD) embedder used offline doesn't separate
        # on-topic from off-topic queries cleanly enough for a hard
        # threshold alone (semantically unrelated queries can still score
        # 0.3-0.5 on lexical overlap). The agent layer's system prompt is
        # the real grounding enforcement: it's instructed to answer only
        # from the retrieved context and to say explicitly when that
        # context doesn't support an answer, rather than trusting this
        # score. Switching --embedder to onnx-minilm or ollama (real
        # semantic embeddings) tightens this threshold's usefulness
        # significantly and is the recommended config for deployment.
        self.min_similarity = min_similarity
        manifest = Path(persist_dir) / 'corpus-manifest.json'
        corpus = json.loads(manifest.read_text()) if manifest.exists() else {}
        self.source_revision = corpus.get('revision', 'be8ab89a890a833cbba2c892178f823fff178c65')
        self.known_guests = {episode['guest'] for episode in corpus.get('episodes', []) if episode.get('guest')}
        embedder = build_embedder(embedder_kind, ollama_model, ollama_url, persist_dir)
        client = chromadb.PersistentClient(path=persist_dir)
        self.collection = client.get_collection(COLLECTION_NAME, embedding_function=embedder)

    def query(self, question: str, k: int = 5) -> list[RetrievedChunk]:
        if k <= 0:
            return []
        count = self.collection.count()
        if not count:
            return []
        normalized_question = re.sub(r'\W+', ' ', question).lower().strip()
        requested_guests = set()
        # Use the complete episode catalog, not just names in the first search
        # results: a less similar episode must still be reachable by guest name.
        for guest in getattr(self, 'known_guests', set()):
            normalized_guest = re.sub(r'\W+', ' ', guest).lower().strip()
            if len(normalized_guest.split()) >= 2 and re.search(r'\b'+re.escape(normalized_guest)+r'\b', normalized_question):
                requested_guests.add(guest)
        if requested_guests:
            res = self.collection.query(query_texts=[question], n_results=min(count, k * 5),
                                        where={'guest': {'$in': sorted(requested_guests)}})
        else:
            res = self.collection.query(query_texts=[question], n_results=min(count, k * 5))
            # Compatibility with older indexes without an episode catalog.
            for meta in res['metadatas'][0]:
                guest = meta.get('guest', '')
                name = re.sub(r'\W+', ' ', guest).lower().strip()
                if len(name.split()) >= 2 and re.search(r'\b'+re.escape(name)+r'\b', normalized_question):
                    requested_guests.add(guest)
            if requested_guests:
                res = self.collection.query(query_texts=[question], n_results=min(count, k * 5),
                                            where={'guest': {'$in': sorted(requested_guests)}})
        out = []
        seen = []
        for chunk_id, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            words = re.findall(r"\w+", doc.lower())
            shingles = {tuple(words[i:i + 5]) for i in range(max(0, len(words) - 4))}
            episode = meta.get("episode_slug") or meta.get("youtube_url") or meta.get("title", "")
            if any(episode == prior_episode and shingles and prior_shingles
                   and len(shingles & prior_shingles) / min(len(shingles), len(prior_shingles)) >= 0.65
                   for prior_episode, prior_shingles in seen):
                continue
            seen.append((episode, shingles))
            guest = meta.get('guest', '')
            title = meta.get('title', '')
            normalized_title = re.sub(r'\W+', ' ', title).lower()
            normalized_guest = re.sub(r'\W+', ' ', guest).lower().strip()
            uncertain = bool(normalized_guest and normalized_guest not in normalized_title)
            out.append(RetrievedChunk(
                chunk_id=chunk_id,
                text=doc,
                guest=guest,
                title=f'{guest} — podcast transcript (source metadata uncertain)' if uncertain else title,
                youtube_url='' if uncertain else meta.get('youtube_url', ''),
                start_timestamp=meta.get("start_timestamp", "00:00:00"),
                publish_date='' if uncertain else meta.get('publish_date', ''),
                distance=dist,
                source_path=meta.get('source_path', ''),
                source_revision=getattr(self, 'source_revision', 'be8ab89a890a833cbba2c892178f823fff178c65'),
            ))
        # Prefer independent episodes; reuse additional passages only when needed.
        selected=[]; deferred=[]; episodes=set()
        for chunk in out:
            episode_key=chunk.source_path or chunk.chunk_id.split('::')[0]
            if episode_key in episodes:
                deferred.append(chunk)
            else:
                selected.append(chunk);episodes.add(episode_key)
        selected=(selected+deferred)[:k]
        return sorted(selected,key=lambda chunk:chunk.distance)

    def is_grounded(self, chunks: list[RetrievedChunk]) -> bool:
        return bool(chunks) and chunks[0].similarity >= self.min_similarity


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Formats retrieved chunks as a numbered context block + citation list,
    the shape the agent layer's system prompt will consume."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] {c.citation()}\n{c.text}")
    return "\n\n".join(blocks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Query the transcript retriever from the CLI")
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--persist-dir", default="data/chroma")
    ap.add_argument("--embedder", default="local-lexical")
    args = ap.parse_args()

    r = Retriever(persist_dir=args.persist_dir, embedder_kind=args.embedder)
    chunks = r.query(args.query, k=args.k)
    print(f"Grounded: {r.is_grounded(chunks)}\n")
    for i, c in enumerate(chunks, 1):
        print(f"[{i}] sim={c.similarity:.3f}  {c.citation()}")
        print(f"    {c.text[:220].replace(chr(10), ' ')}...")
        print()
