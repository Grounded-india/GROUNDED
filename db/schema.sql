-- Grounded — Postgres schema for Layers 1–3
-- Requires: pgvector extension (comes with pgvector/pgvector image).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- for gen_random_uuid()

-- ============================================================
-- Layer 1: raw ingested items (no editorial touch)
-- ============================================================

-- Source tier defines trust level.
--   1 = primary (government, court, official statistics)
--   2 = wire    (Reuters, AP, AFP, PTI, ANI)
--   3 = signal  (Reddit, Twitter/X, YouTube captions — topic radar only)
CREATE TABLE raw_items (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name   TEXT NOT NULL,
    source_tier   SMALLINT NOT NULL CHECK (source_tier BETWEEN 1 AND 3),
    source_url    TEXT NOT NULL,
    title         TEXT,
    content       TEXT NOT NULL,
    published_at  TIMESTAMPTZ,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding     VECTOR(1024),                -- filled by pipeline/embed.py (voyage-3 = 1024 dims)
    raw_data      JSONB,                       -- original feed entry / API response
    UNIQUE (source_name, source_url)
);

CREATE INDEX raw_items_fetched_at_idx  ON raw_items (fetched_at DESC);
CREATE INDEX raw_items_published_at_idx ON raw_items (published_at DESC NULLS LAST);
CREATE INDEX raw_items_tier_idx        ON raw_items (source_tier);
-- Vector index created after some data exists; comment for later:
-- CREATE INDEX raw_items_embedding_idx ON raw_items USING hnsw (embedding vector_cosine_ops);


-- ============================================================
-- Layer 2: events = clusters of raw_items about the same real-world event
-- ============================================================

CREATE TABLE events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT NOT NULL,           -- machine-generated brief title
    summary           TEXT,                    -- 1-2 sentence description
    importance_score  REAL,                    -- ranker output; higher = more important
    tier_1_anchor     BOOLEAN DEFAULT FALSE,   -- backed by at least one primary/wire source?
    first_seen_at     TIMESTAMPTZ NOT NULL,
    last_seen_at      TIMESTAMPTZ NOT NULL,
    status            TEXT NOT NULL DEFAULT 'candidate'
                       CHECK (status IN ('candidate', 'selected', 'published', 'rejected')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX events_importance_idx  ON events (importance_score DESC NULLS LAST);
CREATE INDEX events_status_score_idx ON events (status, importance_score DESC NULLS LAST);
CREATE INDEX events_last_seen_idx   ON events (last_seen_at DESC);

CREATE TABLE event_items (
    event_id     UUID NOT NULL REFERENCES events(id)     ON DELETE CASCADE,
    raw_item_id  UUID NOT NULL REFERENCES raw_items(id)  ON DELETE CASCADE,
    PRIMARY KEY (event_id, raw_item_id)
);

CREATE INDEX event_items_raw_idx ON event_items (raw_item_id);


-- ============================================================
-- Layer 3: stories = multi-agent output for an event
-- ============================================================

CREATE TABLE stories (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id          UUID UNIQUE NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    headline          TEXT,
    dek               TEXT,                    -- one-sentence sub-headline
    body_markdown     TEXT,                    -- final article as markdown
    editor_approved   BOOLEAN NOT NULL DEFAULT FALSE,
    editor_notes      TEXT,                    -- rejection reasons, flagged claims, etc.
    agent_trace       JSONB,                   -- full multi-agent trace for auditability
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at      TIMESTAMPTZ
);

CREATE INDEX stories_created_idx   ON stories (created_at DESC);
CREATE INDEX stories_published_idx ON stories (published_at DESC NULLS LAST);
CREATE INDEX stories_approved_idx  ON stories (editor_approved);


-- Individual claims within a story, each grounded to source items.
CREATE TABLE claims (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id       UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    claim_text     TEXT NOT NULL,
    verified       BOOLEAN NOT NULL DEFAULT FALSE,
    tier_1_backed  BOOLEAN NOT NULL DEFAULT FALSE,  -- has at least one tier-1 source
    ordinal        INT,                             -- ordering within the story
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX claims_story_idx ON claims (story_id, ordinal);

CREATE TABLE claim_sources (
    claim_id     UUID NOT NULL REFERENCES claims(id)    ON DELETE CASCADE,
    raw_item_id  UUID NOT NULL REFERENCES raw_items(id) ON DELETE RESTRICT,
    PRIMARY KEY (claim_id, raw_item_id)
);

CREATE INDEX claim_sources_raw_idx ON claim_sources (raw_item_id);
