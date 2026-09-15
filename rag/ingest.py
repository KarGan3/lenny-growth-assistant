"""
Ingestion pipeline for Lenny's Podcast transcript archive.

Parses each episodes/{guest}/transcript.md (YAML frontmatter + timestamped
dialogue), splits into overlapping chunks aligned to speaker turns, and
writes a JSONL file of chunks ready for embedding. Every chunk carries
enough metadata (guest, title, youtube_url, video_id, publish_date,
timestamp, source path) to construct a citation and a deep link back to
the exact moment in the source video.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

# Three transcript formats found in the archive:
#   1. "Speaker (HH:MM:SS):"        — the vast majority of episodes
#   2. "[HH:MM:SS] Speaker:"        — a small number of episodes (e.g. ryan-hoover)
#   3. "Speaker:" with no timestamp — rare (e.g. adriel-frederick); timestamp
#      is carried forward from the last known one (or "00:00:00" at the start)
TURN_RE_SUFFIX = re.compile(r"^([A-Za-z0-9 .'\-]+?)\s*\((\d{1,2}:\d{2}(?::\d{2})?)\):\s*$")
TURN_RE_PREFIX = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([A-Za-z0-9 .'\-]+?):\s*(.*)$")
TURN_RE_NO_TS = re.compile(r"^([A-Za-z0-9 .'\-]+?):\s*$")
CONTINUATION_RE = re.compile(r"^\((\d{1,2}:\d{2}(?::\d{2})?)\):\s*(.*)$")


@dataclass
class Chunk:
    chunk_id: str
    episode_slug: str
    guest: str
    title: str
    youtube_url: str
    video_id: str
    publish_date: str
    start_timestamp: str  # HH:MM:SS of first turn in this chunk
    source_path: str
    text: str
    token_estimate: int


def _rough_tokens(text: str) -> int:
    # ~4 chars/token is a reasonable estimate without pulling in a tokenizer
    return max(1, len(text) // 4)


def parse_transcript(path: Path) -> tuple[dict, list[tuple[str, str, str]]]:
    """Returns (frontmatter_dict, list of (speaker, timestamp, text) turns)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.startswith("---"):
        raise ValueError(f"{path} missing YAML frontmatter")
    end = raw.index("\n---", 3)
    fm = yaml.safe_load(raw[3:end])
    body = raw[end + 4:]

    # Drop everything before the "## Transcript" heading if present
    if "## Transcript" in body:
        body = body.split("## Transcript", 1)[1]

    lines = body.splitlines()
    turns: list[tuple[str, str, str]] = []
    speaker, ts, buf = None, "00:00:00", []

    def flush():
        if speaker is not None and buf:
            turns.append((speaker, ts, " ".join(buf).strip()))

    for line in lines:
        stripped = line.strip()
        m_suffix = TURN_RE_SUFFIX.match(stripped)
        m_prefix = TURN_RE_PREFIX.match(stripped)
        continuation = CONTINUATION_RE.match(stripped)
        m_no_ts = TURN_RE_NO_TS.match(stripped) if not m_suffix and not m_prefix else None
        if m_suffix:
            flush()
            speaker, ts, buf = m_suffix.group(1).strip(), m_suffix.group(2), []
        elif m_prefix:
            flush()
            ts, speaker = m_prefix.group(1), m_prefix.group(2).strip()
            buf = [m_prefix.group(3).strip()] if m_prefix.group(3).strip() else []
        elif continuation and speaker is not None:
            flush()
            ts, buf = continuation.group(1), []
            if continuation.group(2):
                buf.append(continuation.group(2))
        elif m_no_ts:
            flush()
            speaker, buf = m_no_ts.group(1).strip(), []
            # ts carries forward from the previous turn (or the "00:00:00" default)
        elif stripped:
            buf.append(stripped)
    flush()
    return fm, turns


def split_long_turns(turns, target_tokens):
    """Bound passage length without losing words, speaker identity or timestamps."""
    max_chars = target_tokens * 4
    for speaker, timestamp, text in turns:
        parts = timestamp.split(':')
        if len(parts) == 2:
            parts.insert(0, '00')
        timestamp = ':'.join(f'{int(part):02d}' for part in parts)
        remaining = text
        while len(remaining) > max_chars:
            boundary = remaining.rfind(' ', 0, max_chars + 1)
            if boundary <= 0:
                boundary = max_chars
            # Prefer complete sentences when one ends in the latter half.
            sentences = list(re.finditer(r'[.!?]\s+', remaining[:boundary + 1]))
            if sentences and sentences[-1].end() >= max_chars // 2:
                boundary = sentences[-1].end()
            yield speaker, timestamp, remaining[:boundary].strip()
            remaining = remaining[boundary:].strip()
        if remaining:
            yield speaker, timestamp, remaining


def chunk_episode(
    fm: dict,
    turns: list[tuple[str, str, str]],
    episode_slug: str,
    source_path: str,
    target_tokens: int = 350,
    overlap_turns: int = 2,
) -> list[Chunk]:
    if target_tokens <= 0 or overlap_turns < 0:
        raise ValueError('target_tokens must be positive and overlap_turns nonnegative')
    turns = list(split_long_turns(turns, target_tokens))
    chunks: list[Chunk] = []
    i = 0
    idx = 0
    n = len(turns)
    while i < n:
        window: list[tuple[str, str, str]] = []
        tok_count = 0
        j = i
        while j < n and tok_count < target_tokens:
            spk, ts, txt = turns[j]
            if window and tok_count + _rough_tokens(txt) > target_tokens:
                break
            window.append((spk, ts, txt))
            tok_count += _rough_tokens(txt)
            j += 1
        if not window:
            break
        text = "\n\n".join(f"{spk} ({ts}): {txt}" for spk, ts, txt in window)
        chunks.append(
            Chunk(
                chunk_id=f"{episode_slug}::{idx}",
                episode_slug=episode_slug,
                guest=str(fm.get("guest", "")),
                title=str(fm.get("title", "")),
                youtube_url=str(fm.get("youtube_url", "")),
                video_id=str(fm.get("video_id", "")),
                publish_date=str(fm.get("publish_date", "")),
                start_timestamp=window[0][1],
                source_path=source_path,
                text=text,
                token_estimate=tok_count,
            )
        )
        idx += 1
        # advance, keeping the last `overlap_turns` turns for context continuity
        step = max(1, len(window) - overlap_turns)
        i += step
    return chunks


def ingest(repo_root: Path, out_path: Path, target_tokens: int, overlap_turns: int) -> int:
    episodes_dir = repo_root / "episodes"
    if not episodes_dir.is_dir():
        print(f"ERROR: {episodes_dir} not found", file=sys.stderr)
        return 0
    total = 0
    skipped = 0
    with out_path.open("w", encoding="utf-8") as out:
        for ep_dir in sorted(episodes_dir.iterdir()):
            tpath = ep_dir / "transcript.md"
            if not tpath.exists():
                continue
            try:
                fm, turns = parse_transcript(tpath)
            except Exception as e:
                print(f"SKIP {tpath}: {e}", file=sys.stderr)
                skipped += 1
                continue
            if not turns:
                print(f"SKIP {tpath}: no parsed turns", file=sys.stderr)
                skipped += 1
                continue
            chunks = chunk_episode(
                fm, turns, ep_dir.name, str(tpath.relative_to(repo_root)),
                target_tokens=target_tokens, overlap_turns=overlap_turns,
            )
            for c in chunks:
                out.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
            total += len(chunks)
    print(f"Wrote {total} chunks from {episodes_dir} ({skipped} episodes skipped) -> {out_path}")
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Chunk Lenny's Podcast transcripts for RAG ingestion")
    ap.add_argument("--repo", default="data_repo", help="path to cloned lennys-podcast-transcripts repo")
    ap.add_argument("--out", default="data/chunks.jsonl")
    ap.add_argument("--target-tokens", type=int, default=350)
    ap.add_argument("--overlap-turns", type=int, default=2)
    args = ap.parse_args()

    repo_root = Path(args.repo)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ingest(repo_root, out_path, args.target_tokens, args.overlap_turns)
