"""
Register all news sources here.

Design decisions:
- **Tier 1 (primary)**: government/court/statistical bodies and court-reporting
  outlets that quote primary documents verbatim. Reached via Google News
  `site:` queries because most official Indian sites lack RSS or expose flaky
  feeds.
- **Tier 2 (wire)**: major wires + accessible Indian outlets filtered via
  Google News queries scoped to their domains.
- **Tier 3 (signal)**: Reddit multi-URL feeds via `old.reddit.com` (less
  scraper-hostile than `www.reddit.com`) and a broad Google News India feed.
  Never a truth source — used as topic radar in Layer 2.

New sources default to ``max_entries=30`` so a wider source pool does not
double the daily ingest volume. Existing wire/primary sources keep the
default of 50 because they were sized before the source pool grew.

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

# LiveLaw and Bar and Bench report court proceedings + quote primary court
# documents (judgments, orders) verbatim. Treated as tier 1 because their
# claims are auditable against the primary record.
register_source(
    GoogleNewsSource(
        name="livelaw",
        tier=SourceTier.PRIMARY,
        query="site:livelaw.in",
        when="1d",
        max_entries=30,
    )
)

register_source(
    GoogleNewsSource(
        name="bar_and_bench",
        tier=SourceTier.PRIMARY,
        query="site:barandbench.com",
        when="1d",
        max_entries=30,
    )
)

# ------------------------------------------------------------
# Tier 2 — wire services + accessible Indian outlets
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

# Additional accessible Indian outlets (all serve full content to scrapers,
# unlike Reuters/NYT/FT which are paywalled or bot-blocked).
register_source(
    GoogleNewsSource(
        name="the_wire",
        tier=SourceTier.WIRE,
        query="site:thewire.in",
        when="1d",
        max_entries=30,
    )
)

register_source(
    GoogleNewsSource(
        name="scroll",
        tier=SourceTier.WIRE,
        query="site:scroll.in",
        when="1d",
        max_entries=30,
    )
)

register_source(
    GoogleNewsSource(
        name="the_print",
        tier=SourceTier.WIRE,
        query="site:theprint.in",
        when="1d",
        max_entries=30,
    )
)

register_source(
    GoogleNewsSource(
        name="news_minute",
        tier=SourceTier.WIRE,
        query="site:thenewsminute.com",
        when="1d",
        max_entries=30,
    )
)

register_source(
    GoogleNewsSource(
        name="livemint",
        tier=SourceTier.WIRE,
        query="site:livemint.com",
        when="1d",
        max_entries=30,
    )
)

# ------------------------------------------------------------
# Tier 3 — signal (topic radar only)
# ------------------------------------------------------------

# Reddit multi-URL feeds at old.reddit.com (less scraper-hostile than www).
# One HTTP call per multi-URL returns posts from all listed subs, so wider
# coverage without inflating the Reddit request count.

# Political / news:
register_source(
    RssSource(
        name="reddit_news",
        tier=SourceTier.SIGNAL,
        feed_url="https://old.reddit.com/r/india+indianews+IndiaSpeaks/.rss",
        max_entries=30,
    )
)

# Regional / city subs — for state-level and city-level ground reality:
register_source(
    RssSource(
        name="reddit_cities",
        tier=SourceTier.SIGNAL,
        feed_url=(
            "https://old.reddit.com/"
            "r/mumbai+delhi+bangalore+chennai+kolkata+kerala+hyderabad/.rss"
        ),
        max_entries=30,
    )
)

# Domain-specialised discussion (economy, academia, defence, geopolitics):
register_source(
    RssSource(
        name="reddit_topical",
        tier=SourceTier.SIGNAL,
        feed_url=(
            "https://old.reddit.com/"
            "r/IndianEconomy+IndianAcademia+IndianDefence+geopolitics/.rss"
        ),
        max_entries=30,
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
