"""
Layer 2 — event clustering.

Groups raw_items that describe the same real-world event. The rule, per the v1
design, is deliberately simple and auditable: two items join the same cluster
when their embeddings are cosine-similar above a threshold AND they were
published within a time window of each other. Clusters are the connected
components of that relation (single-linkage).

The pure clustering logic (:func:`cluster_items`) has no DB or model
dependencies so it can be unit-tested directly. :func:`build_events` is the
thin DB wrapper that persists clusters as ``events`` + ``event_items``.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import numpy as np

from grounded.config import settings
from grounded.db import cursor
from grounded.models import SourceTier
from grounded.pipeline.embed import parse_pgvector

log = logging.getLogger(__name__)


@dataclass
class ClusterableItem:
    """Minimal view of a raw_item needed for clustering."""

    id: Any
    embedding: np.ndarray
    timestamp: datetime


class _UnionFind:
    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, x: int) -> int:
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[x] != root:  # path compression
            self._parent[x], x = root, self._parent[x]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cluster_items(
    items: list[ClusterableItem],
    similarity_threshold: float = 0.80,
    time_window_hours: float = 48.0,
) -> list[list[int]]:
    """
    Cluster items by cosine similarity + time proximity (single-linkage).

    Returns a list of clusters, each a list of indices into ``items``.
    Singletons are returned as one-element clusters. Ordering is stable:
    clusters are sorted by their smallest member index.
    """
    n = len(items)
    if n == 0:
        return []
    if n == 1:
        return [[0]]

    embeddings = _normalize_rows(np.array([it.embedding for it in items], dtype=float))
    similarity = embeddings @ embeddings.T
    window = timedelta(hours=time_window_hours)

    uf = _UnionFind(n)
    for i in range(n):
        ti = items[i].timestamp
        for j in range(i + 1, n):
            if similarity[i, j] < similarity_threshold:
                continue
            if abs(ti - items[j].timestamp) > window:
                continue
            uf.union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for idx in range(n):
        groups[uf.find(idx)].append(idx)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0])


def _load_unclustered_items(source_names: list[str] | None = None) -> list[dict]:
    """Fetch embedded raw_items that are not yet attached to any event.

    Optional ``source_names`` restricts the query to items from a specific set
    of sources.
    """
    where_extra = ""
    params: tuple = ()
    if source_names:
        where_extra = "AND r.source_name = ANY(%s)"
        params = (list(source_names),)
    with cursor() as cur:
        cur.execute(
            f"""
            SELECT r.id,
                   r.source_name,
                   r.source_tier,
                   r.title,
                   r.content,
                   COALESCE(r.published_at, r.fetched_at) AS ts,
                   r.embedding
            FROM raw_items r
            LEFT JOIN event_items ei ON ei.raw_item_id = r.id
            WHERE r.embedding IS NOT NULL
              AND ei.raw_item_id IS NULL
              {where_extra}
            ORDER BY ts
            """,
            params,
        )
        return cur.fetchall()


def _pick_representative(rows: list[dict]) -> dict:
    """Best item for the event title: highest trust tier, then most recent."""
    return min(
        rows,
        key=lambda r: (int(r["source_tier"]), -(r["ts"].timestamp() if r["ts"] else 0)),
    )


def build_events(
    similarity_threshold: float | None = None,
    time_window_hours: float | None = None,
    source_names: list[str] | None = None,
) -> int:
    """Cluster un-clustered embedded items into events and persist them.

    Idempotent: items already attached to an event are skipped, so re-running
    only clusters newly-embedded items. Returns the number of events created.
    """
    similarity_threshold = (
        settings.cluster_similarity if similarity_threshold is None else similarity_threshold
    )
    time_window_hours = (
        settings.cluster_window_hours if time_window_hours is None else time_window_hours
    )

    rows = _load_unclustered_items(source_names=source_names)
    if not rows:
        log.info("no un-clustered embedded items")
        return 0

    items = [
        ClusterableItem(id=r["id"], embedding=parse_pgvector(r["embedding"]), timestamp=r["ts"])
        for r in rows
    ]
    clusters = cluster_items(items, similarity_threshold, time_window_hours)
    log.info("formed %d clusters from %d items", len(clusters), len(rows))

    created = 0
    with cursor() as cur:
        for cluster in clusters:
            member_rows = [rows[i] for i in cluster]
            rep = _pick_representative(member_rows)
            timestamps = [r["ts"] for r in member_rows if r["ts"] is not None]
            first_seen = min(timestamps) if timestamps else rep["ts"]
            last_seen = max(timestamps) if timestamps else rep["ts"]
            has_anchor = any(int(r["source_tier"]) <= SourceTier.WIRE for r in member_rows)
            title = (rep["title"] or rep["content"] or "Untitled event").strip()[:280]
            summary = (rep["content"] or "").strip()[:500] or None

            cur.execute(
                """
                INSERT INTO events
                    (title, summary, tier_1_anchor,
                     first_seen_at, last_seen_at, status)
                VALUES (%s, %s, %s, %s, %s, 'candidate')
                RETURNING id
                """,
                (title, summary, has_anchor, first_seen, last_seen),
            )
            event_id: UUID = cur.fetchone()["id"]

            for r in member_rows:
                cur.execute(
                    """
                    INSERT INTO event_items (event_id, raw_item_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (event_id, r["id"]),
                )
            created += 1

    log.info("created %d events", created)
    return created
