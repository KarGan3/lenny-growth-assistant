import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from retrieve import Retriever  # noqa: E402

PERSIST_DIR = str(Path(__file__).resolve().parents[1].parent / "data" / "chroma")


@pytest.fixture(scope="module")
def retriever():
    return Retriever(persist_dir=PERSIST_DIR, embedder_kind="local-lexical")


def test_retrieval_returns_relevant_results(retriever):
    results = retriever.query("how do you find product market fit", k=5)
    assert len(results) == 5
    guests = [r.guest for r in results]
    # Known-relevant guests for this exact query in the corpus
    assert any(g in ("Rahul Vohra", "Todd Jackson") for g in guests)


def test_results_are_sorted_by_similarity_descending(retriever):
    results = retriever.query("pricing strategy for SaaS products", k=5)
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)


def test_deep_link_includes_correct_timestamp_seconds(retriever):
    results = retriever.query("product market fit", k=1)
    c = results[0]
    h, m, s = (int(x) for x in c.start_timestamp.split(":"))
    expected_seconds = h * 3600 + m * 60 + s
    assert f"t={expected_seconds}s" in c.deep_link


def test_citation_includes_guest_and_title(retriever):
    results = retriever.query("growth loops", k=3)
    for r in results:
        citation = r.citation()
        assert r.guest in citation
        assert r.title in citation


def test_is_grounded_true_for_reasonable_query(retriever):
    results = retriever.query("how should I think about onboarding new users", k=5)
    assert retriever.is_grounded(results) is True


def test_empty_query_still_returns_without_crashing(retriever):
    results = retriever.query("xyzzy nonsense query unrelated to anything", k=3)
    assert isinstance(results, list)


def test_named_speaker_question_preserves_relevant_passages_from_that_guest(retriever):
    results = retriever.query('How does Rahul Vohra measure product-market fit?', k=5)
    assert len(results) == 5
    assert all(result.guest == 'Rahul Vohra' for result in results)
