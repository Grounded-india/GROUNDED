# Everything Done Until Now

Handoff doc for the Layer 2 work. Layer 1 (source ingestion) is complete and running. This file explains what exists, how it's structured, and what the second layer will build on.

## What Layer 1 does

Fetches news items from many sources and stores them in Postgres as raw records. No editorial touch. Every item gets tagged with:

* which source it came from (`source_name`)
* how much we trust that source (`source_tier`: 1 primary, 2 wire, 3 signal)
* the original URL, title, content, publish date
* the timestamp when we fetched it

All "is this true / is it important / is it biased" questions are for Layer 2 and Layer 3, not here.

## Project layout

```
D:\PROJECTS\news\
  pyproject.toml            # deps + `grounded` CLI entry point
  .env.example              # env template (copy to .env)
  .gitignore
  README.md                 # full vision + architecture
  SETUP.md                  # how to run locally
  everything done until now.md  # this file

  infra\
    docker-compose.yml      # Postgres 16 + pgvector on port 5432

  db\
    schema.sql              # all tables for Layers 1, 2, 3 (already loaded)

  grounded\
    __init__.py
    config.py               # env loading (pydantic-settings)
    db.py                   # psycopg3 connection pool
    models.py               # RawItem, Event, Story, Claim + SourceTier
    cli.py                  # `grounded` CLI: sources, ingest, status, recent

    ingest\
      __init__.py
      base.py               # Source protocol, registry, store_raw_items
      _http.py              # shared httpx client with real UA
      _rss.py               # feedparser wrapper (content extraction, HTML strip, date parsing)
      rss.py                # RssSource dataclass (direct RSS feeds)
      google_news.py        # GoogleNewsSource dataclass (Google News search RSS)
      sources.py            # registers all 12 sources

    pipeline\               # empty; Layer 2 lives here
    agents\                 # empty; Layer 3 lives here
```

## Database schema (relevant bits for Layer 2)

The tables Layer 2 will read and write are already created. See `db\schema.sql` for the full definitions.

**`raw_items`** (Layer 1 writes to this. Layer 2 will read from it and update `embedding`.)

```
id            uuid, primary key
source_name   text
source_tier   smallint  (1 primary, 2 wire, 3 signal)
source_url    text
title         text
content       text
published_at  timestamptz
fetched_at    timestamptz
embedding     vector(1024)   -- Layer 2 fills this
raw_data      jsonb          -- original feed entry stored for later use
```

Unique constraint on `(source_name, source_url)` so dedup is free.

**`events`** (Layer 2 will create rows here)

```
id                uuid, primary key
title             text
summary           text
importance_score  real
tier_1_anchor     boolean  (does this event have any tier 1 or 2 source?)
first_seen_at     timestamptz
last_seen_at      timestamptz
status            text  ('candidate' | 'selected' | 'published' | 'rejected')
```

**`event_items`** (join table: which raw items belong to which event)

```
event_id      uuid
raw_item_id   uuid
```

`stories`, `claims`, `claim_sources` also exist but are Layer 3's concern.

## Sources registered (12 total, 11 currently returning data)

| Name | Tier | Kind | How |
|---|---|---|---|
| pib | 1 primary | GoogleNewsSource | `site:pib.gov.in` |
| supreme_court | 1 primary | GoogleNewsSource | `site:sci.gov.in OR "supreme court of india"` |
| rbi | 1 primary | GoogleNewsSource | `site:rbi.org.in` |
| prs_india | 1 primary | GoogleNewsSource | `site:prsindia.org` (7 day window) |
| reuters_india | 2 wire | GoogleNewsSource | `site:reuters.com India` |
| ap_india | 2 wire | GoogleNewsSource | `site:apnews.com India` |
| the_hindu | 2 wire | GoogleNewsSource | `site:thehindu.com` |
| indian_express | 2 wire | GoogleNewsSource | `site:indianexpress.com` |
| reddit_india | 3 signal | RssSource | `reddit.com/r/india/.rss` |
| reddit_indianews | 3 signal | RssSource | `reddit.com/r/indianews/.rss` (3s delay) |
| reddit_indiaspeaks | 3 signal | RssSource | `reddit.com/r/IndiaSpeaks/.rss` (3s delay) |
| google_news_india | 3 signal | GoogleNewsSource | `India` (broad topic radar, 100 items) |

Adding a new source is one call to `register_source(...)` in `grounded/ingest/sources.py`.

## CLI

Package installs a `grounded` command:

```
grounded sources                        # list registered sources
grounded ingest                         # run everything
grounded ingest --source pib            # run one source
grounded ingest --tier 1                # run only primary tier
grounded status                         # counts by tier and by source
grounded recent --limit 20              # last N items
grounded recent --source reuters_india  # filter recent by source
```

## First run results (2026-07-20)

```
Total raw items: 433

By tier:
  tier 1 (PRIMARY): 83
  tier 2 (WIRE):    200
  tier 3 (SIGNAL):  150

SOURCE             TIER  COUNT
pib                1     50
prs_india          1     15
rbi                1     2
supreme_court      1     16
ap_india           2     50
indian_express     2     50
reuters_india      2     50
the_hindu          2     50
google_news_india  3     100
reddit_india       3     25
reddit_indianews   3     25
```

`reddit_indiaspeaks` returned 0 (Reddit rate-limited us with a 429). Error handling caught it and the run continued. It will recover on the next attempt.

Sample of what came in today: a wave of coverage on the "Cockroach Janta Party" march to parliament, across DW, BBC, wires, and Reddit. This is a good real-world case for Layer 2 because the same event is being covered by multiple tiers at once.

## Known quirks Layer 2 should know about

1. **Google News URLs are redirect URLs.** For sources that use `GoogleNewsSource`, the stored `source_url` looks like `https://news.google.com/rss/articles/CBMi...`. It still resolves to the real article on click, but if Layer 2 wants the direct publisher URL for citation clarity it will need to follow the redirect. This is 8 of 12 sources.
2. **Reddit occasionally 429s.** Not fatal, just a temporary gap in signal data. Adding a delay helped for two of three subs.
3. **`embedding` column is empty.** Layer 2 needs to fill it. Voyage AI's `voyage-3` model outputs 1024-dim vectors, which matches the column type. `VOYAGE_API_KEY` slot already exists in `.env.example`.

## Environment

* Python 3.13 in `.venv`
* Postgres 16 with pgvector running as Docker container `grounded-postgres` (port 5432, db `grounded`, user `grounded`, password `grounded`)
* `.env` file already created with the correct `DATABASE_URL`
* `pip install -e .` has been run, so the `grounded` command is on the path when the venv is active

## What Layer 2 needs to build

From the README architecture:

1. **Embeddings**: read `raw_items` where `embedding IS NULL`, call Voyage `voyage-3`, write vectors back. Batch the API calls.
2. **Clustering**: cluster raw items into `events` using cosine similarity on the vector plus a time-proximity window (something like: same cluster if similarity > 0.8 and within 48 hours of each other).
3. **Importance ranking**: score each event. Rough signal weights:
   * has a tier 1 source: big positive
   * has a tier 2 source: positive
   * signal-only (only tier 3): small or zero
   * number of independent sources
   * recency
   The ranker deliberately does not care about engagement or virality.
4. **Selection**: mark top ~5 events per day as `status = 'selected'` for Layer 3 to pick up.

Suggested file layout in `grounded/pipeline/`:

```
embed.py         # fill raw_items.embedding via Voyage
clustering.py    # cluster raw_items into events + event_items
importance.py    # score events, update importance_score and status
```

Then a CLI command in `grounded/cli.py` like `grounded cluster` that runs the three steps in order.
