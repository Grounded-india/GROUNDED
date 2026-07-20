"""Generic RSS/Atom source. Register instances of RssSource for each feed."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass

from grounded.ingest._rss import fetch_feed
from grounded.models import RawItem, SourceTier

log = logging.getLogger(__name__)


@dataclass
class RssSource:
    name: str
    tier: SourceTier
    feed_url: str
    user_agent: str | None = None
    max_entries: int = 100
    # Some domains (Reddit) rate-limit aggressively when we hit multiple feeds
    # from the same host back-to-back. Set this to insert a delay before the
    # request. Applies per-source, not globally.
    request_delay_seconds: float = 0.0

    def fetch(self) -> Iterable[RawItem]:
        if self.request_delay_seconds > 0:
            time.sleep(self.request_delay_seconds)
        log.info("[%s] fetching %s", self.name, self.feed_url)
        try:
            yield from fetch_feed(
                self.feed_url,
                source_name=self.name,
                source_tier=self.tier,
                user_agent=self.user_agent,
                max_entries=self.max_entries,
            )
        except Exception as e:
            log.error("[%s] fetch failed: %s", self.name, e)
            return
