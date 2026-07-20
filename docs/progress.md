# Everything Done Until Now

Handoff doc for the Layer 2 work. Layer 1 (source ingestion) is complete and running. This file explains what exists, how it's structured, and what the second layer will build on.

## What Layer 1 does

Fetches news items from many sources and stores them in Postgres as raw records. No editorial touch. Every item gets tagged with:

- which source it came from (`source_name`)
- how much we trust that source (`source_tier`: 1 primary, 2 wire, 3 signal)
- the original URL, title, content, publish date
- the timestamp when we fetched it

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

    pipeline\               # Layer 2 (built): embed, cluster, importance, scrape
    agents\                 # Layer 3 (built): five-agent story-building crew
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

| Name               | Tier      | Kind             | How                                           |
| ------------------ | --------- | ---------------- | --------------------------------------------- |
| pib                | 1 primary | GoogleNewsSource | `site:pib.gov.in`                             |
| supreme_court      | 1 primary | GoogleNewsSource | `site:sci.gov.in OR "supreme court of india"` |
| rbi                | 1 primary | GoogleNewsSource | `site:rbi.org.in`                             |
| prs_india          | 1 primary | GoogleNewsSource | `site:prsindia.org` (7 day window)            |
| reuters_india      | 2 wire    | GoogleNewsSource | `site:reuters.com India`                      |
| ap_india           | 2 wire    | GoogleNewsSource | `site:apnews.com India`                       |
| the_hindu          | 2 wire    | GoogleNewsSource | `site:thehindu.com`                           |
| indian_express     | 2 wire    | GoogleNewsSource | `site:indianexpress.com`                      |
| reddit_india       | 3 signal  | RssSource        | `reddit.com/r/india/.rss`                     |
| reddit_indianews   | 3 signal  | RssSource        | `reddit.com/r/indianews/.rss` (3s delay)      |
| reddit_indiaspeaks | 3 signal  | RssSource        | `reddit.com/r/IndiaSpeaks/.rss` (3s delay)    |
| google_news_india  | 3 signal  | GoogleNewsSource | `India` (broad topic radar, 100 items)        |

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

- Python 3.13 in `.venv`
- Postgres 16 with pgvector running as Docker container `grounded-postgres` (port 5432, db `grounded`, user `grounded`, password `grounded`)
- `.env` file already created with the correct `DATABASE_URL`
- `pip install -e .` has been run, so the `grounded` command is on the path when the venv is active

## What Layer 2 needs to build

From the README architecture:

1. **Embeddings**: read `raw_items` where `embedding IS NULL`, call Voyage `voyage-3`, write vectors back. Batch the API calls.
2. **Clustering**: cluster raw items into `events` using cosine similarity on the vector plus a time-proximity window (something like: same cluster if similarity > 0.8 and within 48 hours of each other).
3. **Importance ranking**: score each event. Rough signal weights:
   - has a tier 1 source: big positive
   - has a tier 2 source: positive
   - signal-only (only tier 3): small or zero
   - number of independent sources
   - recency
     The ranker deliberately does not care about engagement or virality.
4. **Selection**: mark top ~5 events per day as `status = 'selected'` for Layer 3 to pick up.

Suggested file layout in `grounded/pipeline/`:

```
embed.py         # fill raw_items.embedding via Voyage
clustering.py    # cluster raw_items into events + event_items
importance.py    # score events, update importance_score and status
```

Then a CLI command in `grounded/cli.py` like `grounded cluster` that runs the three steps in order.

## Update after Layer 2 was built and reviewed (2026-07-20)

Friend shipped Layer 2 (embed, cluster, rank, pipeline commands) and it works. On the first live run the top 5 selected events were all lone government press releases (PIB Cabinet approvals, PRS bills), while the actual biggest story of the day (a 5-source, 32-item cross-source ground-reality protest) was not in the top 5. Two changes made on top of Layer 2 to fix this:

### 1. Ranker rebalance in `grounded/pipeline/importance.py`

- Primary-source anchoring bonus reduced: `has_tier1` `+4.0` to `+2.5`, `has_tier2` `+2.0` to `+1.5`. A lone government press release should not automatically outrank a well-corroborated cross-source story.
- Distinct-source corroboration raised: `min(n, 6) * 0.6` to `min(n, 8) * 0.9`. Cross-source clustering is now the strongest single signal, which is the whole point (protest coverage across Reuters + AP + Reddit will outrank a single PIB item).
- Added a "multi-wire" bonus mirroring the existing multi-primary bonus: `min(tier2_sources, 4) * 0.5`.
- Added a `GROUND_REALITY_KEYWORDS` list (protest, march, strike, arrest, killed, resignation, verdict, etc.) scored equal to `POLICY_IMPACT_KEYWORDS` at `min(hits, 5) * 0.5`. This gives ground-reality events keyword credit that used to only go to policy language.
- `EventFeatures` grew two fields: `ground_reality_hits` and `matched_ground_reality_keywords`.
- Selection gate untouched: `tier_1_anchor` (primary or wire source present) is still required to advance. A Reddit-only story with no wire confirmation still cannot become news. Only the ordering within the eligible pool changed.
- Existing test baselines in `tests/test_importance.py` will need refreshing because numeric outputs shifted. Flag this in the commit.

`select_top_n` default in `grounded/config.py` bumped from `5` to `20` so both government stories and ground-reality stories fit into the daily edition.

### 2. Layer 2.5: full-article scraper

The RSS layer only stores the feed `<summary>` or `<description>` (1 to 3 sentences). Layer 3 needs full article bodies to extract cited claims. New module `grounded/pipeline/scrape.py` fetches full body only for raw_items belonging to `status='selected'` events (~60 to 100 URLs per run, bounded).

- Uses **trafilatura** for article body extraction.
- Uses **googlenewsdecoder** to resolve Google News RSS redirect URLs back to the real publisher URL first (without this step, all Google News URLs land on a JS interstitial and return 0 usable text).
- Per-host politeness: minimum 2s between requests to the same hostname.
- Failures are stored as empty string (not NULL) so we do not retry the same blocked URL every run.

Schema: `raw_items` grew two columns (already applied to the running DB via `ALTER TABLE`):

```
full_content              TEXT
full_content_fetched_at   TIMESTAMPTZ
```

CLI additions in `grounded/cli.py`:

```
grounded scrape                # fetch full bodies for currently-selected events
grounded scrape --force        # re-scrape even if full_content already set
grounded pipeline              # now also runs scrape at the end
grounded pipeline --skip-scrape  # keep the old behavior
```

Dependencies added to `pyproject.toml`: `trafilatura>=1.12`, `googlenewsdecoder>=0.1.7`.

### Second live run results

After the rebalance, top 20 selected events on 2026-07-20 look like:

```
11.40   src=5 items=32   CJP's Parliament march (ground-reality protest)
 8.55   src=3 items=13   US bombing of Iran expands
 7.18   src=2 items=2    Cabinet approves Urea policy
 6.58   src=3 items=6    Parliament Live Updates monsoon session
 6.57   src=3 items=4    Floods, landslides in northern India kill 25
 6.45   src=3 items=5    Sonam Wangchuk hunger strike
 6.40   src=3 items=19   Spain beat Argentina World Cup
 ...
```

Government press releases (PIB Semicon 2.0, MoHUA PARIVARTAN, MPMS, Foreign Contribution Bill) dropped to positions 11 to 19. Ranker is now doing what the project asked for.

Scrape run on the resulting 105 items in selected events:

- 52 scraped with full body (AP India, Indian Express, DW, ToI, The Hindu, Google News decoded)
- 13 empty (Reddit comment pages, Supreme Court PDFs, PIB blocks)
- 40 fetch failures (Reuters, NYT, FT, WaPo all return 401/403 to unauthenticated scrapers)

Real content lift where it worked: AP World Cup story `93 chars` to `39,730 chars`. Indian Express US-Iran coverage `141 chars` to `22,694 chars`. Layer 3 has real substance to extract claims from for the events that scraped successfully.

### Known limitations Layer 3 should plan around

1. **Reuters is bot-blocked.** All Reuters URLs return 401 to the scraper. Layer 3 will need to work with the RSS summary for Reuters items until we license a Reuters feed or route through a paid scraping service.
2. **Paywalled outlets (NYT, FT, WaPo) return 403.** Same story.
3. **Supreme Court cause lists are PDFs.** Not scrapable with trafilatura. Would need `pdfplumber` or similar.
4. **Reddit comment pages give no meaningful body via trafilatura.** They can still be topic radar, but we do not get citable text from them.

None of these block Layer 3 for the events that scraped successfully (~52 items across the top 20 events).

## Update after Layer 3 was built (2026-07-21)

Layer 3 (Multi-Agent Story Building) is implemented as a **self-contained `grounded/agents/` package**. It only *reads* the shared `config` / `db` / `models` and never edits Layer 1/2 modules, so it can be developed in parallel with someone still working on Layer 1/2 without merge conflicts. It has its own CLI (`python -m grounded.agents`) separate from the `grounded` CLI.

### The five-agent crew

One `selected` event (Layer 2 output) → one grounded story package:

| Agent                       | Model    | Job                                                                 |
| --------------------------- | -------- | ------------------------------------------------------------------ |
| Fact Extractor              | Nemotron | Pull atomic, verifiable claims, each grounded to source item IDs    |
| Primary Source Verifier     | Gemini   | Deterministic backing rules + optional semantic demotion            |
| Context Agent               | Nemotron | Grounded background — why this matters                              |
| Perspective Agent           | Nemotron | Multi-agent debate — steel-man both sides from facts                |
| Editor / Hallucination Auditor | Gemini | Deterministic gate + cut-only audit + headline/dek                 |

### Generation vs. enforcement split (the un-gameable core)

- **Generation** (extraction, context, perspective) runs on an LLM backend (Nemotron), with a **deterministic offline fallback** so the whole crew runs with no API key — mirrors the local embedding backend in Layer 2.
- **Enforcement** (verification rules, grounding to real source IDs, the editor approval gate) is plain, unit-tested Python. A claim is `verified` only if PRIMARY (tier-1) anchored OR corroborated by ≥2 distinct outlets. The LLM can only ever make things **stricter** (demote / cut), never promote.

### Model routing

`grounded/agents/router.py` maps each role to a backend via `ROLE_PROVIDER`. Backends are OpenAI-compatible (`grounded/agents/llm.py`):

- Nemotron via NVIDIA NIM (`NVIDIA_API_KEY`, base `https://integrate.api.nvidia.com/v1`, model `nvidia/llama-3.3-nemotron-super-49b-v1.5`).
- Gemini via the OpenAI-compatible endpoint (`GEMINI_API_KEY`, base `.../v1beta/openai/`, model `gemini-2.5-flash`).
- Any role with no key falls back to the deterministic `LocalBackend`.

Keys are read from the environment or `.env`. **Requires `pip install openai`** (intentionally kept out of `pyproject.toml` for now to avoid a merge conflict with the person on Layer 1/2 — add it to deps when the branches merge).

### Detail-level fidelity check (catches half-truths, incl. government cites)

Both the Verifier and Editor compare each claim to its cited source at the level of **every specific detail** (numbers, dates, names, amounts, scope, qualifiers) and split problems into two buckets:

- **`contradicted` / half-truth** — conflicts with the source, or asserts a detail the source never states. **Always** demoted (verifier) and **cut** (editor), with *no* tier-1 exemption and *no* cap. A claim citing a real PIB release but misstating a figure is removed even if it's the only claim; a story that is only a half-lie is rejected.
- **`unsupported`** (no direct conflict) — handled subject to anti-over-pruning guardrails so a borderline model call can't gut a story: soft demotions/cuts skip primary-anchored claims, are capped at ~50% per pass, and never remove the last verified claim.

This was a deliberate design decision: official/government-cited news is held to the same detail-accuracy bar as everything else, but the pipeline stays efficient and doesn't over-reject good coverage.

### Debate mode

Ground-reality events with no primary source (protests, incidents, Reddit-surfaced stories) are **not** rejected. The Perspective Agent runs a multi-agent debate that steel-mans both sides from grounded facts, and the Editor approves the story in `debate` mode — clearly labelled as a fact-based debate rather than confirmed reporting.

### Files added

```
grounded/agents/
  __init__.py        # package entry (build_story, build_stories)
  __main__.py        # `python -m grounded.agents` CLI
  schemas.py         # EventView, SourceDoc, ClaimDraft, VerifiedClaim, StoryPackage
  llm.py             # pluggable OpenAI-compatible backends + local fallback + JSON helpers
  router.py          # per-agent model routing (ROLE_PROVIDER, ModelRouter)
  fact_extractor.py  # Nemotron; extractive local fallback; grounds claims to source IDs
  verifier.py        # deterministic backing + optional Gemini demote-only fidelity check
  context.py         # Nemotron grounded background
  debate.py          # multi-agent debate engine
  perspective.py     # delegates to debate.py
  editor.py          # deterministic gate + Gemini cut-only audit + headline/dek
  loader.py          # read-only DB access: pull selected events + their sources
  store.py           # persist StoryPackage into stories/claims/claim_sources (idempotent)
  runner.py          # orchestration: load → crew → store; returns model + debate summary
```

Tests added under `tests/`: `test_agents_llm.py`, `test_agents_router.py`, `test_agents_fact_extractor.py`, `test_agents_verifier.py`, `test_agents_debate.py`, `test_agents_editor.py`, `test_agents_crew.py` (offline full-crew), `test_agents_db.py` (Postgres round-trip). Full suite: **94 passing**.

### How to run Layer 3

```
# offline (no keys needed) — deterministic floor only, no semantic fidelity check
python -m grounded.agents build --limit 5

# with models — enables the detail-level fidelity check
pip install openai
# add to .env: NVIDIA_API_KEY=...  and  GEMINI_API_KEY=...
python -m grounded.agents build --limit 5
```

Output reports the per-role model in use, how many stories were built/approved/rejected, and how many were approved as debates.

### Known limitations Layer 4 should plan around

1. **Semantic fidelity check needs a real backend.** In pure offline mode only the deterministic floor runs; the contradiction/half-truth check is skipped (claims are still grounded and gated, just not detail-checked by an LLM).
2. **`openai` is not yet in `pyproject.toml`** (kept out to avoid a merge conflict). Add it when the Layer 1/2 branch merges.
3. **Reuters / paywalled bodies still missing** (carried over from Layer 2.5) — those events fall back to RSS-summary text, which yields fewer extractable claims.
