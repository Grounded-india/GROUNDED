# Setup — Local Development

Layer 1 (source ingestion) is what's implemented right now. This guide gets you from a fresh clone to running `grounded ingest` and seeing raw news items land in Postgres.

## Prerequisites

- **Python 3.11+** (you have 3.13 already)
- **Docker Desktop** (for local Postgres + pgvector)

## 1. Start Postgres

```powershell
docker compose -f infra/docker-compose.yml up -d
```

This launches Postgres 16 with the `pgvector` extension on port 5432. On first boot it runs `db/schema.sql` automatically, creating the tables.

Verify it's up:

```powershell
docker compose -f infra/docker-compose.yml ps
```

## 2. Python environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## 3. Environment variables

```powershell
Copy-Item .env.example .env
```

For **Layer 1 only**, the only variable that must be correct is `DATABASE_URL`. The default in `.env.example` matches the docker-compose Postgres, so you don't need to change anything.

`ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` are not used by Layer 1 — leave them blank for now.

## 4. Verify

List registered sources:

```powershell
grounded sources
```

You should see PIB, Supreme Court, RBI, Reuters India, AP India, The Hindu, Indian Express, three Reddit subs, and a broad Google News India feed.

Run a single source (fastest way to check things work end-to-end):

```powershell
grounded ingest --source reddit_india
```

Run everything:

```powershell
grounded ingest
```

Check what landed:

```powershell
grounded status
grounded recent --limit 20
```

## 5. Reset the database (if needed)

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d
```

The `-v` flag removes the volume, wiping all data.

## Troubleshooting

**`connection refused` on Postgres** — container isn't running or is still starting. Wait ~10 seconds after `up -d` and retry.

**A specific source returns 0 items** — that source's feed may have moved or be temporarily blocked. Other sources should still work; check with `grounded ingest --source google_news_india` as a known-reliable fallback.

**Reddit returns 403** — Reddit occasionally rate-limits or blocks feeds. Wait a few minutes and retry, or comment that source out in `grounded/ingest/sources.py` temporarily.

**Windows encoding errors on `feedparser` output** — set `PYTHONUTF8=1` in your environment.
