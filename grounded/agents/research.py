"""On-demand research: fetch + scrape URLs from a debater's targeted query.

During a multi-turn debate, a debater may realise that a specific factual
claim would meaningfully strengthen their case AND that claim is not in the
sources they were given. Instead of inventing the fact (banned) or conceding
the point (default), they can end their turn with a ``RESEARCH: <query>``
line. This module executes that query — Google News search, resolve each
result URL through the redirect decoder, skip known paywalls, scrape article
body via trafilatura — and returns fresh ``SourceDoc`` objects that get
folded into the next debate turn's facts block.

Budget: caller must enforce a per-debate cap (typically 2 research calls
total). This function itself only caps the URLs fetched per call and the
wall-clock. Failures are non-fatal — an empty list is returned so the debate
can continue with the original sources.
"""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from grounded.agents.schemas import SourceDoc
from grounded.ingest._http import make_client
from grounded.ingest._rss import fetch_feed
from grounded.ingest.google_news import build_query_url
from grounded.models import SourceTier
from grounded.pipeline.scrape import _extract_body, _is_paywalled, _resolve_url

log = logging.getLogger(__name__)

_MAX_URLS_PER_QUERY = 5           # top-N results considered
_MAX_DOCS_RETURNED = 3            # bail early once we have this many good bodies
_PER_URL_TIMEOUT_SECONDS = 12.0
_TOTAL_WALL_CLOCK_SECONDS = 20.0
_MAX_BODY_CHARS = 3000            # keep facts block manageable

# Match the LAST occurrence of RESEARCH: in the turn — the model sometimes
# puts it on its own line (as the prompt asks) and sometimes inlines it after
# a period. Both are treated as the directive. Everything from RESEARCH: to
# end-of-string is the query.
# Case-sensitive: the prompt tells the debater to write RESEARCH: in caps,
# so lowercase "research:" as a normal word (e.g. "peer-reviewed research:
# many outlets confirm...") does not trigger a false positive.
_RESEARCH_RE = re.compile(
    r"\bRESEARCH\s*:\s*(?P<query>.+?)\s*\Z",
    re.DOTALL,
)


def extract_research_query(turn_text: str) -> str | None:
    """Parse a debater's turn for a trailing ``RESEARCH: <query>`` directive.

    Returns the query (trimmed) or None. Also returns None if the query
    looks non-substantive (too short, all punctuation, question mark only).
    """
    if not turn_text:
        return None
    m = _RESEARCH_RE.search(turn_text)
    if not m:
        return None
    q = m.group("query").strip().strip("\"'`").rstrip(".")
    # A query can span multiple lines if the LLM wrapped it — collapse to one.
    q = " ".join(q.split())
    if len(q) < 6:
        return None
    return q


def strip_research_directive(turn_text: str) -> str:
    """Remove any trailing ``RESEARCH: ...`` content so it doesn't appear in
    the published dialogue. The directive is a control signal, not content.

    Also strips a trailing period/whitespace immediately before RESEARCH: so
    the visible text ends cleanly (e.g. ``"...syndicates.  RESEARCH: foo"``
    → ``"...syndicates."``).
    """
    if not turn_text:
        return turn_text
    # Look for RESEARCH: anywhere and cut from there. Preserve any trailing
    # period on the preceding sentence.
    m = re.search(r"\s*\bRESEARCH\s*:", turn_text)
    if not m:
        return turn_text
    return turn_text[: m.start()].rstrip()


def do_research(query: str) -> list[SourceDoc]:
    """Execute a research query. Returns up to 3 fresh SourceDoc objects.

    Never raises. On any failure returns an empty list; the caller falls
    back to the original source pool.
    """
    started = time.monotonic()
    query = (query or "").strip()
    if not query:
        return []

    feed_url = build_query_url(query, lang="en-IN", country="IN", when="7d")

    # Step 1: pull the top few Google News RSS entries for the query.
    try:
        items = list(
            fetch_feed(
                feed_url,
                source_name=f"research:{query[:40]}",
                source_tier=SourceTier.WIRE,
                max_entries=_MAX_URLS_PER_QUERY,
            )
        )
    except Exception as e:
        log.warning("research feed fetch failed for %r: %s", query, e)
        return []

    if not items:
        log.info("research: no results for %r", query)
        return []

    # Step 2: for each candidate, resolve the Google News redirect, skip if
    # paywalled, fetch, extract body. Bail once we hit _MAX_DOCS_RETURNED
    # good bodies or the wall clock runs out.
    docs: list[SourceDoc] = []
    with make_client() as client:
        for item in items:
            if len(docs) >= _MAX_DOCS_RETURNED:
                break
            if time.monotonic() - started > _TOTAL_WALL_CLOCK_SECONDS:
                log.info("research: wall clock hit for %r, stopping early", query)
                break

            raw_url = item.source_url
            try:
                resolved = _resolve_url(raw_url)
            except Exception as e:
                log.warning("research: url resolve failed for %s: %s", raw_url, e)
                continue

            host = urlparse(resolved).hostname or ""
            if _is_paywalled(host):
                log.info("research: skipping paywalled %s", host)
                continue

            try:
                resp = client.get(resolved, timeout=_PER_URL_TIMEOUT_SECONDS)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.info("research: fetch failed for %s: %s", resolved, e)
                continue

            body = _extract_body(resolved, resp.text)
            if not body or len(body) < 200:
                continue

            docs.append(
                SourceDoc(
                    id=uuid4(),
                    source_name=f"research:{query[:60]}",
                    source_tier=SourceTier.WIRE,
                    source_url=resolved,
                    title=(item.title or query)[:280],
                    text=body[:_MAX_BODY_CHARS],
                )
            )

    ms = int((time.monotonic() - started) * 1000)
    log.info("research: query=%r → %d doc(s) in %d ms", query, len(docs), ms)
    return docs
