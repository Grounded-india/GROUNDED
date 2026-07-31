"""Enrichment: attach related government / official responses to a ground-reality event.

When the pipeline picks up a ground-reality story (protest, crackdown, arrest,
scandal), the corresponding official response usually lives in a separate
primary-source item — a PIB press release, a PMO tweet, a court order, an RBI
notification — that clustered as its own event (or didn't cluster at all).
Layer 2's single-linkage clustering keeps those apart because a PIB readout
about "student welfare" and a wire report about "students lathi-charged at
Parliament" don't share enough surface vocabulary.

For story-building we want them together: the reader benefits from seeing
"here's what happened on the ground AND here's the official response, N hours
later." This module runs a pgvector similarity query for each ground-reality
event and attaches any topically-close recent primary-tier items as extra
SourceDocs, tagged with a `-response` suffix and a timestamp prefix so the
citation shows how long after the event the official statement came.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

import numpy as np

from grounded.agents.schemas import EventView, SourceDoc
from grounded.db import cursor
from grounded.models import SourceTier
from grounded.pipeline.embed import parse_pgvector, to_pgvector

log = logging.getLogger(__name__)

# Cosine DISTANCE (not similarity) — lower = more similar. pgvector's <=> op
# returns distance. 0.35 corresponds to ~0.65 cosine similarity — loose enough
# to catch related official statements but tight enough not to grab unrelated
# gov readouts on the same day.
_RESPONSE_SIMILARITY_DISTANCE = 0.35
_RESPONSE_WINDOW_HOURS = 48
_MAX_RESPONSE_DOCS = 3


def _event_centroid(event_id: UUID) -> np.ndarray | None:
    """Average embedding across the event's raw_items."""
    with cursor() as cur:
        cur.execute(
            """
            SELECT r.embedding
            FROM raw_items r
            JOIN event_items ei ON ei.raw_item_id = r.id
            WHERE ei.event_id = %s AND r.embedding IS NOT NULL
            """,
            (event_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return None
    vecs = np.array([parse_pgvector(r["embedding"]) for r in rows], dtype=float)
    centroid = vecs.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    return centroid


def _event_last_seen(event_id: UUID) -> datetime | None:
    with cursor() as cur:
        cur.execute("SELECT last_seen_at FROM events WHERE id = %s", (event_id,))
        row = cur.fetchone()
    return row["last_seen_at"] if row else None


def attach_government_response(event: EventView, docs: list[SourceDoc]) -> list[SourceDoc]:
    """Return ``docs`` with up to N government-response SourceDocs appended.

    Idempotent: if no matching primary items exist, or the event has no
    embedding centroid, returns the original ``docs`` list unchanged. Never
    raises — enrichment failures are logged and swallowed.
    """
    try:
        centroid = _event_centroid(event.id)
        if centroid is None:
            return docs
        event_last_seen = _event_last_seen(event.id)

        with cursor() as cur:
            # pgvector cosine distance = 1 - cosine similarity. Lower = closer.
            # Exclude items already in this event (they'd be duplicates).
            cur.execute(
                f"""
                SELECT r.id, r.source_name, r.source_url, r.title, r.content,
                       r.fetched_at,
                       (r.embedding <=> %s::vector) AS distance
                FROM raw_items r
                WHERE r.embedding IS NOT NULL
                  AND r.source_tier = %s
                  AND r.fetched_at >= NOW() - INTERVAL '{_RESPONSE_WINDOW_HOURS} hours'
                  AND NOT EXISTS (
                      SELECT 1 FROM event_items ei
                      WHERE ei.raw_item_id = r.id AND ei.event_id = %s
                  )
                  AND (r.embedding <=> %s::vector) < %s
                ORDER BY r.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    to_pgvector(centroid),
                    int(SourceTier.PRIMARY),
                    event.id,
                    to_pgvector(centroid),
                    _RESPONSE_SIMILARITY_DISTANCE,
                    to_pgvector(centroid),
                    _MAX_RESPONSE_DOCS,
                ),
            )
            rows = cur.fetchall()
    except Exception as e:
        log.warning("gov-response enrichment failed for event %s: %s", event.id, e)
        return docs

    if not rows:
        return docs

    extras: list[SourceDoc] = []
    for r in rows:
        gap_hours = None
        if event_last_seen and r["fetched_at"]:
            # last_seen_at is timestamptz; fetched_at same. Both aware.
            ev_dt = event_last_seen
            rs_dt = r["fetched_at"]
            if ev_dt.tzinfo is None:
                ev_dt = ev_dt.replace(tzinfo=timezone.utc)
            if rs_dt.tzinfo is None:
                rs_dt = rs_dt.replace(tzinfo=timezone.utc)
            gap_hours = int((rs_dt - ev_dt).total_seconds() / 3600)
        gap_label = (
            f"[response {gap_hours:+d}h from main event] "
            if gap_hours is not None
            else "[official response] "
        )
        extras.append(
            SourceDoc(
                id=r["id"],
                source_name=f"{r['source_name']}-response",
                source_tier=SourceTier.PRIMARY,
                source_url=r["source_url"] or "",
                title=(gap_label + (r["title"] or "").strip())[:280],
                text=(r["content"] or "").strip(),
            )
        )
    log.info(
        "event %s: attached %d government-response doc(s)",
        event.id, len(extras),
    )
    return list(docs) + extras
