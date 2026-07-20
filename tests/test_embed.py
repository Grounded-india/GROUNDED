"""Tests for the embedding layer (pure logic, no API calls)."""

from __future__ import annotations

import numpy as np

from grounded.pipeline.embed import (
    EMBEDDING_DIM,
    LocalHashingBackend,
    build_embed_text,
    parse_pgvector,
    to_pgvector,
)


def test_build_embed_text_combines_title_and_content():
    text = build_embed_text("RBI holds repo rate", "The central bank kept rates unchanged.")
    assert "RBI holds repo rate" in text
    assert "central bank" in text


def test_build_embed_text_handles_missing_title():
    assert build_embed_text(None, "body only") == "body only"
    assert build_embed_text("title only", "") == "title only"


def test_build_embed_text_truncates_long_content():
    text = build_embed_text("t", "x" * 10_000)
    assert len(text) <= 2000


def test_to_and_from_pgvector_roundtrip():
    vec = [0.1, -0.25, 0.0, 3.5]
    serialized = to_pgvector(vec)
    assert serialized.startswith("[") and serialized.endswith("]")
    restored = parse_pgvector(serialized)
    assert np.allclose(restored, np.array(vec))


def test_parse_pgvector_accepts_list():
    restored = parse_pgvector([1.0, 2.0, 3.0])
    assert np.allclose(restored, np.array([1.0, 2.0, 3.0]))


class TestLocalHashingBackend:
    def test_output_dimension_matches_column(self):
        backend = LocalHashingBackend()
        vectors = backend.embed(["hello world"])
        assert len(vectors) == 1
        assert len(vectors[0]) == EMBEDDING_DIM

    def test_is_deterministic(self):
        backend = LocalHashingBackend()
        a = backend.embed(["Supreme Court delivers verdict on electoral bonds"])
        b = backend.embed(["Supreme Court delivers verdict on electoral bonds"])
        assert np.allclose(np.array(a), np.array(b))

    def test_vectors_are_l2_normalized(self):
        backend = LocalHashingBackend()
        vec = np.array(backend.embed(["some non-empty news headline about policy"])[0])
        assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-5)

    def test_similar_texts_more_similar_than_different(self):
        backend = LocalHashingBackend()
        vecs = backend.embed(
            [
                "RBI keeps repo rate unchanged at 6.5 percent",
                "Reserve Bank of India holds repo rate steady at 6.5%",
                "Bollywood actor announces new film at box office",
            ]
        )
        a, b, c = (np.array(v) for v in vecs)
        sim_related = float(a @ b)
        sim_unrelated = float(a @ c)
        assert sim_related > sim_unrelated
