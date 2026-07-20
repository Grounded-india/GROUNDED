"""
Google News RSS search source.

Google News exposes an RSS endpoint for arbitrary search queries:
    https://news.google.com/rss/search?q=QUERY&hl=en-IN&gl=IN&ceid=IN:en

We use it as a pragmatic aggregator: `site:pib.gov.in` for PIB, `site:reuters.com India`
for Reuters India, etc. Not a permanent solution — direct primary source feeds are
preferable — but it works today for a wide range of publishers with zero auth.

Note: each entry's link is Google's redirect URL, not the underlying article URL.
For citation purposes the redirect still lands the reader on the correct article.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlencode

from grounded.ingest._rss import fetch_feed
from grounded.models import RawItem, SourceTier

log = logging.getLogger(__name__)

_BASE = "https://news.google.com/rss/search"


def build_query_url(
    query: str,
    *,
    lang: str = "en-IN",
    country: str = "IN",
    when: str | None = "1d",
) -> str:
    q = f"{query} when:{when}" if when else query
    params = {
        "q": q,
        "hl": lang,
        "gl": country,
        "ceid": f"{country}:{lang.split('-')[0]}",
    }
    return f"{_BASE}?{urlencode(params)}"


@dataclass
class GoogleNewsSource:
    name: str
    tier: SourceTier
    query: str
    when: str | None = "1d"        # Google News time window: 1h, 1d, 7d, 1y, or None for all
    lang: str = "en-IN"
    country: str = "IN"
    max_entries: int = 50

    def fetch(self) -> Iterable[RawItem]:
        url = build_query_url(self.query, lang=self.lang, country=self.country, when=self.when)
        log.info("[%s] fetching %s", self.name, url)
        try:
            yield from fetch_feed(
                url,
                source_name=self.name,
                source_tier=self.tier,
                max_entries=self.max_entries,
            )
        except Exception as e:
            log.error("[%s] fetch failed: %s", self.name, e)
            return
