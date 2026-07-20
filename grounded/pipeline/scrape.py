"""
Layer 2.5 - full-article scraping for items in selected events.

The RSS layer only captures the ``<summary>`` or ``<description>`` field of
each feed entry (typically 1-3 sentences). Layer 3 needs the actual article
body to extract cited claims, so this module fetches the source URL and
extracts the article text with trafilatura.

Only items belonging to ``status='selected'`` events are scraped. This keeps
the network budget bounded and independent of ingestion volume - a 20-event
selection with ~3 items each is ~60 URLs per pipeline run, not 400+.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
import trafilatura
from googlenewsdecoder import gnewsdecoder

from grounded.db import cursor
from grounded.ingest._http import make_client
from grounded.models import EventStatus

log = logging.getLogger(__name__)

# Minimum seconds between successive requests to the same host. Small enough
# that a full run still finishes in under a minute, large enough to be a
# reasonable neighbor.
_MIN_INTERVAL_PER_HOST_SECONDS = 2.0

# Cap on how long we spend on a single URL (network + parse).
_PER_URL_TIMEOUT_SECONDS = 25.0


def _host(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def _resolve_url(url: str) -> str:
    """
    Google News RSS URLs are opaque redirect wrappers that land on a JS
    interstitial page, not the publisher. Decode them back to the real
    publisher URL before scraping. Non-Google-News URLs pass through unchanged.
    """
    host = _host(url)
    if host != "news.google.com":
        return url
    try:
        result = gnewsdecoder(url, interval=1)
    except Exception as e:
        log.warning("gnewsdecoder threw on %s: %s", url, e)
        return url
    if isinstance(result, dict) and result.get("status") and result.get("decoded_url"):
        return result["decoded_url"]
    return url


def _load_pending_items(force: bool = False) -> list[dict]:
    """Return raw_items belonging to selected events that still need scraping."""
    filter_clause = "" if force else "AND r.full_content IS NULL"
    with cursor() as cur:
        cur.execute(
            f"""
            SELECT DISTINCT r.id, r.source_name, r.source_url
            FROM raw_items r
            JOIN event_items ei ON ei.raw_item_id = r.id
            JOIN events e       ON e.id = ei.event_id
            WHERE e.status = %s
              {filter_clause}
            ORDER BY r.id
            """,
            (EventStatus.SELECTED,),
        )
        return list(cur.fetchall())


def _extract_body(url: str, html: str) -> str:
    """Run trafilatura on the fetched HTML. Return "" if nothing usable comes back."""
    try:
        text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
    except Exception as e:
        log.warning("trafilatura extract failed for %s: %s", url, e)
        return ""
    return (text or "").strip()


def _store(item_id, body: str) -> None:
    """
    Persist the scrape result. Empty string is stored intentionally so we do
    not retry the same failing URL every run.
    """
    with cursor() as cur:
        cur.execute(
            """
            UPDATE raw_items
            SET full_content = %s,
                full_content_fetched_at = %s
            WHERE id = %s
            """,
            (body, datetime.now(UTC), item_id),
        )


def scrape_selected_events(force: bool = False) -> dict:
    """
    Fetch and extract full article bodies for every raw_item belonging to a
    currently-selected event that does not yet have ``full_content``.

    Returns a summary dict: ``{"pending": n, "scraped": n, "empty": n, "failed": n}``.
    """
    pending = _load_pending_items(force=force)
    if not pending:
        log.info("no items pending scrape")
        return {"pending": 0, "scraped": 0, "empty": 0, "failed": 0}

    log.info("scraping %d item(s) for selected events", len(pending))

    last_hit: dict[str, float] = defaultdict(lambda: 0.0)
    scraped = 0
    empty = 0
    failed = 0

    with make_client() as client:
        for row in pending:
            raw_url = row["source_url"]
            url = _resolve_url(raw_url)  # decode Google News redirects to publisher URL
            host = _host(url)

            # Per-host politeness.
            wait = _MIN_INTERVAL_PER_HOST_SECONDS - (time.monotonic() - last_hit[host])
            if wait > 0:
                time.sleep(wait)
            last_hit[host] = time.monotonic()

            try:
                resp = client.get(url, timeout=_PER_URL_TIMEOUT_SECONDS)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.warning("[%s] fetch failed for %s: %s", row["source_name"], url, e)
                _store(row["id"], "")  # store empty to avoid retrying next run
                failed += 1
                continue

            body = _extract_body(str(resp.url), resp.text)
            _store(row["id"], body)
            if body:
                scraped += 1
            else:
                empty += 1

    log.info(
        "scrape done: %d with body, %d empty, %d fetch failure(s)",
        scraped,
        empty,
        failed,
    )
    return {
        "pending": len(pending),
        "scraped": scraped,
        "empty": empty,
        "failed": failed,
    }
