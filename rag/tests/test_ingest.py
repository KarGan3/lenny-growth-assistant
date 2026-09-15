import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingest import parse_transcript, chunk_episode  # noqa: E402

FM_HEADER = """---
guest: Test Guest
title: A Test Episode
youtube_url: https://www.youtube.com/watch?v=abc123
video_id: abc123
publish_date: 2024-01-01
---

"""

SUFFIX_FORMAT = FM_HEADER + """# A Test Episode

## Transcript

Lenny (00:00:00):
Welcome to the show, let's talk about growth.

Test Guest (00:00:15):
Thanks for having me, happy to dig into growth loops.

Lenny (00:00:42):
Great, let's start with acquisition.
"""

PREFIX_FORMAT = FM_HEADER + """# A Test Episode

## Transcript

[00:00:00] Lenny: Welcome to the show, let's talk about growth.
[00:00:15] Test Guest: Thanks for having me, happy to dig into growth loops.
"""

NO_TS_FORMAT = FM_HEADER + """# A Test Episode

## Transcript

Lenny:
Welcome to the show, let's talk about growth.

Test Guest:
Thanks for having me, happy to dig into growth loops.
"""


def _write(tmp_path, content):
    ep_dir = tmp_path / "test-guest"
    ep_dir.mkdir(parents=True, exist_ok=True)
    p = ep_dir / "transcript.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_suffix_timestamp_format(tmp_path):
    p = _write(tmp_path, SUFFIX_FORMAT)
    fm, turns = parse_transcript(p)
    assert fm["guest"] == "Test Guest"
    assert len(turns) == 3
    assert turns[0] == ("Lenny", "00:00:00", "Welcome to the show, let's talk about growth.")
    assert turns[1][0] == "Test Guest"
    assert turns[1][1] == "00:00:15"


def test_parse_bracket_prefix_timestamp_format(tmp_path):
    p = _write(tmp_path, PREFIX_FORMAT)
    fm, turns = parse_transcript(p)
    assert len(turns) == 2
    assert turns[0] == ("Lenny", "00:00:00", "Welcome to the show, let's talk about growth.")
    assert turns[1][0] == "Test Guest"


def test_parse_no_timestamp_format_carries_forward(tmp_path):
    p = _write(tmp_path, NO_TS_FORMAT)
    fm, turns = parse_transcript(p)
    assert len(turns) == 2
    # No explicit timestamps in source -> defaults carried forward from "00:00:00"
    assert turns[0][1] == "00:00:00"
    assert turns[1][1] == "00:00:00"


def test_chunk_episode_preserves_metadata_and_citation_fields():
    fm, turns = parse_transcript(_write(Path(tempfile.mkdtemp()), SUFFIX_FORMAT))
    chunks = chunk_episode(fm, turns, "test-guest", "episodes/test-guest/transcript.md", target_tokens=10)
    assert len(chunks) >= 1
    c = chunks[0]
    assert c.guest == "Test Guest"
    assert c.youtube_url == "https://www.youtube.com/watch?v=abc123"
    assert c.start_timestamp == "00:00:00"
    assert "Lenny (00:00:00):" in c.text


def test_chunking_never_drops_turns_and_advances():
    fm, turns = parse_transcript(_write(Path(tempfile.mkdtemp()), SUFFIX_FORMAT))
    chunks = chunk_episode(fm, turns, "test-guest", "x", target_tokens=5, overlap_turns=1)
    # Long turns now span multiple bounded chunks; every segment must survive.
    from ingest import split_long_turns
    all_chunk_text = " ".join(c.text for c in chunks)
    pieces = list(split_long_turns(turns, 5))
    assert ' '.join(text for _, _, text in pieces).split() == ' '.join(text for _, _, text in turns).split()
    for _, _, text in pieces:
        assert text in all_chunk_text


def test_long_turn_is_bounded_and_all_words_are_preserved():
    from ingest import split_long_turns
    text = ' '.join(f'word{i}' for i in range(2000))
    turns = [('Test Guest', '00:05:00', text)]
    pieces = list(split_long_turns(turns, 350))
    assert ' '.join(piece[2] for piece in pieces) == text
    chunks = chunk_episode({}, turns, 'long', 'x', 350, 2)
    assert all(chunk.token_estimate <= 350 for chunk in chunks)
    assert all(chunk.start_timestamp == '00:05:00' for chunk in chunks)
    assert all('Test Guest (00:05:00):' in chunk.text for chunk in chunks)


def test_continuation_timestamp_keeps_speaker_and_updates_source_location(tmp_path):
    p = _write(tmp_path, FM_HEADER + '## Transcript\n\nGuest (00:00:01):\nFirst point.\n\n(00:02:00):\nSecond point.')
    _, turns = parse_transcript(p)
    assert turns == [('Guest', '00:00:01', 'First point.'), ('Guest', '00:02:00', 'Second point.')]
