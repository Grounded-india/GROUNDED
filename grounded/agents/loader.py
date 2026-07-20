"""Read-only DB access for Layer 3: pull selected events and their sources.

Selects ``status='selected'`` events that do not yet have a story (unless
``force``). Layer 3 never mutates the events table, so it stays out of the way
of the Layer 1/2 status machine a teammate may be editing.
"""

from __future__ import annotations

from uuid import UUID

from grounded.agents.schemas import EventView, SourceDoc
from grounded.db import cursor
from grounded.models import EventStatus, SourceTier


def _best_text(full_content: str | None, content: str | None) -> str:
    full = (full_content or "").strip()
    if full:
        return full
    return (content or "").strip()


def load_event_docs(event_id: UUID) -> list[SourceDoc]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.source_name, r.source_tier, r.source_url,
                   r.title, r.content, r.full_content
            FROM raw_items r
            JOIN event_items ei ON ei.raw_item_id = r.id
            WHERE ei.event_id = %s
            ORDER BY r.source_tier, r.source_name, r.id
            """,
            (event_id,),
        )
        rows = cur.fetchall()
    return [
        SourceDoc(
            id=r["id"],
            source_name=r["source_name"],
            source_tier=SourceTier(r["source_tier"]),
            source_url=r["source_url"],
            title=r["title"],
            text=_best_text(r["full_content"], r["content"]),
        )
        for r in rows
    ]


def load_events_needing_stories(
    *,
    force: bool = False,
    limit: int | None = None,
    event_id: UUID | None = None,
) -> list[tuple[EventView, list[SourceDoc]]]:
    clauses = ["e.status = %s"]
    params: list[object] = [EventStatus.SELECTED]
    if not force:
        clauses.append("s.id IS NULL")
    if event_id is not None:
        clauses.append("e.id = %s")
        params.append(event_id)

    query = f"""
        SELECT e.id, e.title, e.summary, e.importance_score
        FROM events e
        LEFT JOIN stories s ON s.event_id = e.id
        WHERE {" AND ".join(clauses)}
        ORDER BY e.importance_score DESC NULLS LAST, e.last_seen_at DESC
    """
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    with cursor() as cur:
        cur.execute(query, tuple(params))
        events = cur.fetchall()

    result: list[tuple[EventView, list[SourceDoc]]] = []
    for row in events:
        view = EventView(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            importance_score=row["importance_score"],
        )
        result.append((view, load_event_docs(row["id"])))
    return result
