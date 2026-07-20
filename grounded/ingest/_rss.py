"""RSS/Atom feed helpers built on feedparser + httpx."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from grounded.ingest._http import make_client
from grounded.models import RawItem, SourceTier

log = logging.getLogger(__name__)


def html_to_text(value: str | None) -> str:
    if not value:
        return ""
    return BeautifulSoup(value, "lxml").get_text(separator=" ", strip=True)


def _extract_content(entry: dict) -> str:
    # Feedparser stores content in several possible places depending on feed format.
    if entry.get("content"):
        parts = [c.get("value", "") for c in entry["content"] if c.get("value")]
        if parts:
            return html_to_text("\n\n".join(parts))
    for key in ("summary", "description"):
        if entry.get(key):
            return html_to_text(entry[key])
    return ""


def _extract_published(entry: dict) -> datetime | None:
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            try:
                dt = dateparser.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except (ValueError, TypeError):
                continue
    return None


def fetch_feed(
    feed_url: str,
    *,
    source_name: str,
    source_tier: SourceTier,
    user_agent: str | None = None,
    max_entries: int = 100,
) -> Iterator[RawItem]:
    """Fetch and parse a single RSS/Atom feed, yielding RawItem for each entry."""
    with make_client(user_agent) as client:
        resp = client.get(feed_url)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)

    if parsed.bozo and parsed.get("entries") is None:
        log.warning("Feed %s parse error: %s", feed_url, parsed.bozo_exception)
        return

    for entry in parsed.entries[:max_entries]:
        link = entry.get("link")
        if not link:
            continue

        content = _extract_content(entry)
        if not content:
            # Some feeds only give title. Fall back to title as content.
            content = entry.get("title", "")
        if not content:
            continue

        yield RawItem(
            source_name=source_name,
            source_tier=source_tier,
            source_url=link,
            title=entry.get("title") or None,
            content=content,
            published_at=_extract_published(entry),
            raw_data={
                "feed_url": feed_url,
                "entry_id": entry.get("id"),
                "author": entry.get("author"),
                "tags": [t.get("term") for t in entry.get("tags", []) if t.get("term")],
            },
        )
