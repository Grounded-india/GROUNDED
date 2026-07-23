"""
Layer 2 — embeddings.

Reads raw_items whose ``embedding`` is NULL, turns each into a vector, and writes
it back so the clustering step can group items about the same real-world event.

Two backends:
  * ``voyage``  — Voyage AI ``voyage-3`` (1024-dim), used in production.
  * ``local``   — an offline, deterministic hashing vectorizer. No API key
                  needed, so it keeps dev/CI/tests runnable and reproducible.
                  Good enough for near-duplicate news clustering; not a
                  semantic model.

The backend is chosen by ``settings.embedding_backend`` ("auto" | "voyage" |
"local"). "auto" uses Voyage only when a real VOYAGE_API_KEY is configured.
"""

from __future__ import annotations

import logging
import time
from typing import Protocol

import numpy as np

from grounded.config import settings
from grounded.db import cursor

log = logging.getLogger(__name__)

EMBEDDING_DIM = 1024              # matches raw_items.embedding VECTOR(1024)
_EMBED_INPUT_CHARS = 2000        # truncate long content before embedding
# Voyage paid tier (standard rate limits: 300 RPM / 1M TPM). Runs at full speed.
# A fresh-run embed of ~500 items completes in ~4 API calls, ~8 seconds total.
#
# If you fall back to the free tier without a payment method, Voyage caps
# accounts at 3 RPM / 10K TPM regardless of model or key. Drop to:
#     _VOYAGE_MAX_BATCH = 5
#     _VOYAGE_BATCH_SLEEP_SECONDS = 21.0
# to stay under both limits sustainably.
_VOYAGE_MAX_BATCH = 128
_VOYAGE_BATCH_SLEEP_SECONDS = 0.0


def build_embed_text(title: str | None, content: str) -> str:
    """Combine title + content into the string we actually embed."""
    title = (title or "").strip()
    content = (content or "").strip()
    text = f"{title}\n\n{content}" if title and content else (title or content)
    return text[:_EMBED_INPUT_CHARS]


def to_pgvector(vec: list[float] | np.ndarray) -> str:
    """Serialize a vector to pgvector's text input format: ``[0.1,0.2,...]``."""
    arr = np.asarray(vec, dtype=float).ravel()
    return "[" + ",".join(repr(float(x)) for x in arr) + "]"


def parse_pgvector(value: object) -> np.ndarray:
    """Parse a pgvector value (returned as text by psycopg) into a numpy array."""
    if value is None:
        raise ValueError("cannot parse None as a vector")
    if isinstance(value, (list, tuple, np.ndarray)):
        return np.asarray(value, dtype=float)
    if isinstance(value, str):
        return np.fromstring(value.strip().lstrip("[").rstrip("]"), sep=",")
    raise TypeError(f"unsupported pgvector value type: {type(value)!r}")


class EmbeddingBackend(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalHashingBackend:
    """
    Deterministic offline embedding via scikit-learn's HashingVectorizer.

    Character-stable and dependency-light. It captures token/bigram overlap,
    which is what clustering near-duplicate news coverage actually relies on.
    Vectors are L2-normalized so a dot product equals cosine similarity.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        from sklearn.feature_extraction.text import HashingVectorizer

        self.dim = dim
        self._vec = HashingVectorizer(
            n_features=dim,
            alternate_sign=False,
            norm=None,
            stop_words="english",
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        matrix = self._vec.transform(texts).toarray().astype("float32")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix = matrix / norms
        return matrix.tolist()


class VoyageBackend:
    """Production embedding backend using Voyage AI (voyage-3 → 1024 dims)."""

    def __init__(self, model: str, dim: int = EMBEDDING_DIM) -> None:
        import voyageai

        self.dim = dim
        self.model = model
        self._client = voyageai.Client(api_key=settings.voyage_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        import voyageai.error as _verr

        out: list[list[float]] = []
        for i in range(0, len(texts), _VOYAGE_MAX_BATCH):
            if i > 0 and _VOYAGE_BATCH_SLEEP_SECONDS > 0:
                time.sleep(_VOYAGE_BATCH_SLEEP_SECONDS)
            chunk = texts[i : i + _VOYAGE_MAX_BATCH]
            # Retry transient network errors so one flaky call doesn't nuke
            # an hour-long publish. Rate-limit / auth errors are NOT retried.
            last_err: Exception | None = None
            for attempt in range(3):
                try:
                    resp = self._client.embed(chunk, model=self.model, input_type="document")
                    out.extend(resp.embeddings)
                    break
                except (_verr.APIConnectionError, _verr.Timeout) as e:
                    last_err = e
                    wait = 2 ** attempt * 5  # 5s, 10s, 20s
                    log.warning("voyage embed transient error (attempt %d/3): %s — sleeping %ds",
                                attempt + 1, e, wait)
                    time.sleep(wait)
            else:
                raise last_err  # type: ignore[misc]
        return out


def get_backend() -> EmbeddingBackend:
    choice = (settings.embedding_backend or "auto").lower()
    if choice == "auto":
        choice = "voyage" if settings.has_voyage_key() else "local"
    if choice == "voyage":
        log.info("embedding backend: voyage (%s)", settings.embedding_model)
        return VoyageBackend(settings.embedding_model)
    if choice == "local":
        log.info("embedding backend: local hashing vectorizer")
        return LocalHashingBackend()
    raise ValueError(f"unknown embedding backend: {settings.embedding_backend!r}")


def embed_pending(
    batch_size: int = 128,
    limit: int | None = None,
    source_names: list[str] | None = None,
) -> int:
    """
    Embed every raw_item that doesn't have an embedding yet.

    If ``source_names`` is given, only items from those sources are embedded.
    Used to split main-pipeline and deep-dive-pipeline embedding across two
    concurrent processes: they touch disjoint rows, so no race, and one
    Voyage timeout in one process no longer kills both flows.

    Returns the number of items embedded.
    """
    with cursor() as cur:
        if source_names:
            cur.execute(
                """
                SELECT id, title, content
                FROM raw_items
                WHERE embedding IS NULL AND source_name = ANY(%s)
                ORDER BY fetched_at
                LIMIT %s
                """,
                (list(source_names), limit if limit is not None else 1_000_000),
            )
        else:
            cur.execute(
                """
                SELECT id, title, content
                FROM raw_items
                WHERE embedding IS NULL
                ORDER BY fetched_at
                LIMIT %s
                """,
                (limit if limit is not None else 1_000_000,),
            )
        rows = cur.fetchall()

    if not rows:
        log.info("no items pending embedding")
        return 0

    backend = get_backend()
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        texts = [build_embed_text(r["title"], r["content"]) for r in batch]
        vectors = backend.embed(texts)
        with cursor() as cur:
            for row, vec in zip(batch, vectors, strict=True):
                cur.execute(
                    "UPDATE raw_items SET embedding = %s::vector WHERE id = %s",
                    (to_pgvector(vec), row["id"]),
                )
        total += len(batch)
        log.info("embedded %d/%d", total, len(rows))

    return total
