"""
Register all news sources here.

Design decisions:
- **Tier 1 (primary)**: government/court/statistical bodies. Reached via Google News
  `site:` queries because most official Indian sites either lack RSS or expose flaky
  feeds. Switch to direct feeds once we validate stability per source.
- **Tier 2 (wire)**: major wires filtered via Google News queries scoped to their domains.
- **Tier 3 (signal)**: Reddit subs via their native RSS feeds. Never a truth source —
  only used as topic radar in Layer 2.

To add a new source, instantiate GoogleNewsSource or RssSource and pass it to
register_source() below.
"""

from grounded.ingest.base import register_source
from grounded.ingest.google_news import GoogleNewsSource
from grounded.ingest.rss import RssSource
from grounded.models import SourceTier

# ------------------------------------------------------------
# Tier 1 — primary sources (government, court, statistics)
# ------------------------------------------------------------

register_source(
    GoogleNewsSource(
        name="pib",
        tier=SourceTier.PRIMARY,
        query="site:pib.gov.in",
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="supreme_court",
        tier=SourceTier.PRIMARY,
        query='site:sci.gov.in OR "supreme court of india"',
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="rbi",
        tier=SourceTier.PRIMARY,
        query="site:rbi.org.in",
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="prs_india",
        tier=SourceTier.PRIMARY,
        query="site:prsindia.org",
        when="7d",  # PRS publishes less frequently — widen the window
    )
)

# ------------------------------------------------------------
# Tier 2 — wire services
# ------------------------------------------------------------

register_source(
    GoogleNewsSource(
        name="reuters_india",
        tier=SourceTier.WIRE,
        query="site:reuters.com India",
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="ap_india",
        tier=SourceTier.WIRE,
        query="site:apnews.com India",
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="the_hindu",
        tier=SourceTier.WIRE,
        query="site:thehindu.com",
        when="1d",
    )
)

register_source(
    GoogleNewsSource(
        name="indian_express",
        tier=SourceTier.WIRE,
        query="site:indianexpress.com",
        when="1d",
    )
)

# ------------------------------------------------------------
# Tier 3 — signal (topic radar only)
# ------------------------------------------------------------

# Reddit RSS is free and requires only a real User-Agent.
register_source(
    RssSource(
        name="reddit_india",
        tier=SourceTier.SIGNAL,
        feed_url="https://www.reddit.com/r/india/.rss",
    )
)

# Reddit rate-limits when we hit multiple subs in rapid succession.
# 3s spacing has been reliable in testing.
register_source(
    RssSource(
        name="reddit_indianews",
        tier=SourceTier.SIGNAL,
        feed_url="https://www.reddit.com/r/indianews/.rss",
        request_delay_seconds=3.0,
    )
)

register_source(
    RssSource(
        name="reddit_indiaspeaks",
        tier=SourceTier.SIGNAL,
        feed_url="https://www.reddit.com/r/IndiaSpeaks/.rss",
        request_delay_seconds=3.0,
    )
)

# Broad Google News India feed for topic radar.
register_source(
    GoogleNewsSource(
        name="google_news_india",
        tier=SourceTier.SIGNAL,
        query="India",
        when="1d",
        max_entries=100,
    )
)
