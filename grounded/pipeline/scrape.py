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
from bs4 import BeautifulSoup
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

# Hostnames that consistently return 401/403 to unauthenticated scrapers.
# Skipped upfront (no HTTP request, no politeness delay burned). The item's
# RSS summary is still available for clustering / fact extraction — we just
# do not fetch a body we know we cannot get. Add here as new paywalls are
# discovered.
_PAYWALLED_HOSTS: frozenset[str] = frozenset({
    "www.reuters.com", "reuters.com",
    "www.bloomberg.com", "bloomberg.com",
    "www.nytimes.com", "nytimes.com",
    "www.ft.com", "ft.com",
    "www.wsj.com", "wsj.com",
    "www.washingtonpost.com", "washingtonpost.com",
    "www.economist.com", "economist.com",
    "www.pib.gov.in", "pib.gov.in",
    "www.ndtv.com", "ndtv.com",
    "newlinesmag.com", "www.newlinesmag.com",
    "www.newyorker.com", "newyorker.com",
    "www.theatlantic.com", "theatlantic.com",
})


def _is_paywalled(host: str) -> bool:
    return host.lower() in _PAYWALLED_HOSTS


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


def _is_reddit(host: str) -> bool:
    return host == "reddit.com" or host.endswith(".reddit.com")


# How many top comments to include when scraping a Reddit post. Reddit is tier-3
# (topic radar), so we keep the bodies compact but preserve real ground-signal
# from the crowd - useful when a protest/incident thread has firsthand accounts.
_REDDIT_TOP_COMMENTS = 8
# Truncate any single comment past this length.
_REDDIT_MAX_COMMENT_CHARS = 800


def _fetch_reddit_body(client: httpx.Client, url: str) -> str:
    """
    Scrape a Reddit post from ``old.reddit.com`` HTML.

    Reddit's JSON API is closed to unauthenticated clients (403 blocked),
    and ``www.reddit.com`` is a JS-rendered SPA that returns an empty
    shell to plain HTTP clients. ``old.reddit.com`` serves the exact
    same live data (same posts, same time, same subreddits) via
    server-rendered HTML that a normal ``httpx`` + ``BeautifulSoup``
    pass can parse without any auth.

    Extracts: post title, selftext (for text posts), linked URL (for link
    posts), and the top-level comments. Nested reply chains are skipped
    on purpose — Layer 3 does not need them.
    """
    # Rewrite www.reddit.com / reddit.com → old.reddit.com. Same data, scrapable HTML.
    old_url = url
    for prefix in ("://www.reddit.com/", "://reddit.com/"):
        if prefix in old_url:
            old_url = old_url.replace(prefix, "://old.reddit.com/", 1)
            break

    # One-shot retry on 5xx (Reddit occasionally returns transient 500s that
    # clear on retry). 4xx stays terminal.
    resp = None
    for attempt in (1, 2):
        try:
            resp = client.get(old_url, timeout=_PER_URL_TIMEOUT_SECONDS)
            resp.raise_for_status()
            break
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if 500 <= status < 600 and attempt == 1:
                log.info("reddit %s on %s; retrying in 3s", status, old_url)
                time.sleep(3.0)
                continue
            log.warning("reddit fetch failed for %s: %s", old_url, e)
            return ""
        except httpx.HTTPError as e:
            log.warning("reddit fetch failed for %s: %s", old_url, e)
            return ""
    if resp is None:
        return ""

    soup = BeautifulSoup(resp.text, "lxml")
    parts: list[str] = []

    # Title. old.reddit sets <title> to "Post title : subreddit" — strip the suffix.
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        if " : " in title:
            title = title.rsplit(" : ", 1)[0].strip()
        if title:
            parts.append(title)

    # OP block: div.link.thing wraps the post itself.
    op = soup.select_one("div.link.thing")
    if op is not None:
        # For text posts, the selftext is inside .expando .usertext-body.
        body_div = op.select_one("div.expando div.usertext-body")
        if body_div is not None:
            selftext = body_div.get_text(separator=" ", strip=True)
            if selftext:
                parts.append(selftext)

        # For link posts, capture the outbound URL so Layer 3 can follow it.
        title_link = op.select_one("a.title")
        if title_link is not None:
            href = title_link.get("href") or ""
            if href.startswith("http") and href != url:
                parts.append(f"Linked URL: {href}")

    # Top-level comments only (direct children of the top comment container).
    comment_divs = soup.select("div.sitetable.nestedlisting > div.thing.comment")
    top_comments: list[str] = []
    for c in comment_divs:
        if len(top_comments) >= _REDDIT_TOP_COMMENTS:
            break
        body_div = c.select_one("div.usertext-body")
        if body_div is None:
            continue
        body_text = body_div.get_text(separator=" ", strip=True)
        if not body_text or body_text in ("[deleted]", "[removed]"):
            continue
        author_el = c.select_one("a.author")
        author = author_el.get_text(strip=True) if author_el else "unknown"
        score_el = c.select_one("span.score.unvoted")
        score = ""
        if score_el is not None:
            score = score_el.get("title") or score_el.get_text(strip=True)
        if len(body_text) > _REDDIT_MAX_COMMENT_CHARS:
            body_text = body_text[:_REDDIT_MAX_COMMENT_CHARS].rstrip() + "..."
        top_comments.append(f"[u/{author} | {score}] {body_text}")

    if top_comments:
        parts.append("Top comments:\n" + "\n\n".join(top_comments))

    return "\n\n".join(parts).strip()


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
    paywalled = 0

    with make_client() as client:
        for row in pending:
            raw_url = row["source_url"]
            url = _resolve_url(raw_url)  # decode Google News redirects to publisher URL
            host = _host(url)

            # Known paywalled/bot-blocked hosts — skip immediately. No HTTP
            # request, no politeness delay. RSS summary is still available for
            # clustering / fact extraction; we simply do not fetch the body.
            if _is_paywalled(host):
                log.info("[paywalled] skipped %s (%s)", host, row["source_name"])
                _store(row["id"], "")
                paywalled += 1
                continue

            # Per-host politeness.
            wait = _MIN_INTERVAL_PER_HOST_SECONDS - (time.monotonic() - last_hit[host])
            if wait > 0:
                time.sleep(wait)
            last_hit[host] = time.monotonic()

            # Reddit needs the JSON API - HTML pages give trafilatura nothing.
            if _is_reddit(host):
                body = _fetch_reddit_body(client, url)
                _store(row["id"], body)
                if body:
                    scraped += 1
                else:
                    failed += 1
                continue

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
        "scrape done: %d with body, %d empty, %d fetch failure(s), %d paywalled",
        scraped,
        empty,
        failed,
        paywalled,
    )
    return {
        "pending": len(pending),
        "scraped": scraped,
        "empty": empty,
        "failed": failed,
        "paywalled": paywalled,
    }
