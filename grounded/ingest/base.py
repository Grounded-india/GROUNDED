"""Ingest base: Source protocol, registry, and raw-item storage with dedup."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from typing import Protocol

from grounded.db import cursor
from grounded.models import RawItem, SourceTier

log = logging.getLogger(__name__)


class Source(Protocol):
    """A news source. Implementations yield RawItem objects — never store directly."""

    name: str
    tier: SourceTier

    def fetch(self) -> Iterable[RawItem]:
        """Fetch the latest items from this source. Should be idempotent — dedup happens on write."""
        ...


_registry: dict[str, Source] = {}


def register_source(source: Source) -> Source:
    if source.name in _registry:
        raise ValueError(f"Source '{source.name}' already registered")
    _registry[source.name] = source
    return source


def all_sources() -> list[Source]:
    return list(_registry.values())


def get_source(name: str) -> Source | None:
    return _registry.get(name)


def store_raw_items(items: Iterable[RawItem]) -> tuple[int, int]:
    """
    Insert raw items with (source_name, source_url) dedup.

    Returns (inserted, skipped).
    """
    inserted = 0
    skipped = 0
    with cursor() as cur:
        for item in items:
            cur.execute(
                """
                INSERT INTO raw_items
                    (source_name, source_tier, source_url, title, content,
                     published_at, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_name, source_url) DO NOTHING
                RETURNING id
                """,
                (
                    item.source_name,
                    int(item.source_tier),
                    item.source_url,
                    item.title,
                    item.content,
                    item.published_at,
                    json.dumps(item.raw_data) if item.raw_data is not None else None,
                ),
            )
            row = cur.fetchone()
            if row is None:
                skipped += 1
            else:
                inserted += 1
    return inserted, skipped
