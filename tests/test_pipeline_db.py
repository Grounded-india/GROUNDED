"""
End-to-end Layer 2 test against a real Postgres.

Inserts synthetic raw_items with a unique source-name prefix, runs
embed -> cluster -> rank, asserts the expected events and selection, then
cleans up everything it created. Uses the local (offline) embedding backend so
no API key is required.

Run with:  pytest -m integration
Skipped automatically if Postgres isn't reachable.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _force_local_backend(monkeypatch):
    """Pin the offline embedding backend so this test is deterministic and never
    depends on a configured .env or spends real API credits, regardless of what
    EMBEDDING_BACKEND is set to locally."""
    from grounded.config import settings

    monkeypatch.setattr(settings, "embedding_backend", "local")


PREFIX = f"test_{uuid.uuid4().hex[:8]}"
BASE = datetime.now(UTC) - timedelta(hours=2)

# Two clear clusters + one lone social item.
#  - RBI repo-rate story: 1 primary + 2 wire  -> should rank high, be selected
#  - Court verdict story:  1 primary + 1 wire  -> should also be selected
#  - a lone reddit viral   -> signal only, must NOT be selected
FIXTURES = [
    ("pib", 1, "RBI keeps repo rate unchanged at 6.5 percent",
     "Reserve Bank of India monetary policy committee held the repo rate steady at 6.5 percent."),
    ("reuters_india", 2, "RBI holds repo rate steady at 6.5%",
     "Reserve Bank of India kept its key repo rate unchanged at 6.5 percent, panel said."),
    ("the_hindu", 2, "Reserve Bank of India keeps repo rate at 6.5 percent",
     "RBI monetary policy: the repo rate was left unchanged at 6.5 percent by the central bank."),
    ("supreme_court", 1, "Supreme Court delivers verdict on electoral bonds scheme",
     "Supreme Court of India ruling struck down the electoral bonds scheme, a landmark judgment."),
    ("ap_india", 2, "Supreme Court strikes down electoral bonds scheme",
     "India Supreme Court verdict declared the electoral bonds scheme unconstitutional."),
    ("reddit_india", 3, "Bollywood actor goes viral after wedding",
     "Netizens react as the celebrity wedding trends; trolls and fans spar in a viral thread."),
]


@pytest.fixture
def seeded_db(db_available):
    from grounded.db import cursor

    with cursor() as cur:
        cur.execute("SELECT id FROM events")
        existing_event_ids = {r["id"] for r in cur.fetchall()}

    inserted_ids = []
    with cursor() as cur:
        for i, (name, tier, title, content) in enumerate(FIXTURES):
            cur.execute(
                """
                INSERT INTO raw_items
                    (source_name, source_tier, source_url, title, content,
                     published_at, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    f"{PREFIX}_{name}",
                    tier,
                    f"https://example.test/{PREFIX}/{i}",
                    title,
                    content,
                    BASE + timedelta(minutes=i),
                    json.dumps({"test": True}),
                ),
            )
            inserted_ids.append(cur.fetchone()["id"])

    yield {"raw_ids": inserted_ids, "existing_event_ids": existing_event_ids}

    # teardown: delete test raw_items first (cascades event_items), then the
    # now-orphaned events this test created. Order matters: deleting events
    # first would let the raw_item cascade re-orphan them after cleanup.
    with cursor() as cur:
        cur.execute("DELETE FROM raw_items WHERE source_name LIKE %s", (f"{PREFIX}_%",))
        cur.execute(
            "DELETE FROM events "
            "WHERE id != ALL(%s) AND id NOT IN (SELECT event_id FROM event_items)",
            (list(existing_event_ids) or [uuid.uuid4()],),
        )


@pytest.mark.integration
def test_embed_cluster_rank_end_to_end(seeded_db):
    from grounded.db import cursor
    from grounded.pipeline.clustering import build_events
    from grounded.pipeline.embed import embed_pending
    from grounded.pipeline.importance import rank_events

    raw_ids = seeded_db["raw_ids"]
    existing = seeded_db["existing_event_ids"]

    # 1) embed: every test item gets a vector
    embedded = embed_pending()
    assert embedded >= len(raw_ids)
    with cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM raw_items WHERE id = ANY(%s) AND embedding IS NOT NULL",
            (raw_ids,),
        )
        assert cur.fetchone()["n"] == len(raw_ids)

    # 2) cluster: the 6 items collapse into 3 events (RBI, court, reddit).
    # The offline hashing backend separates these cleanly around 0.5 (cross-
    # cluster similarity stays < 0.1); the 0.8 default is tuned for Voyage.
    created = build_events(similarity_threshold=0.5)
    assert created >= 3

    def new_events():
        with cursor() as cur:
            cur.execute(
                """
                SELECT e.id, e.title, e.tier_1_anchor, e.status, e.importance_score,
                       (SELECT COUNT(DISTINCT r.source_name)
                          FROM event_items ei JOIN raw_items r ON r.id = ei.raw_item_id
                         WHERE ei.event_id = e.id) AS n_sources
                FROM events e
                WHERE e.id != ALL(%s)
                """,
                (list(existing) or [uuid.uuid4()],),
            )
            return cur.fetchall()

    events = new_events()
    # exactly the three clusters we seeded
    assert len(events) == 3
    multi = [e for e in events if e["n_sources"] >= 2]
    assert len(multi) == 2  # RBI (3 sources) and court (2 sources)

    # 3) rank: scores populated, anchored events selected, signal-only not
    result = rank_events()
    assert result["scored"] >= 3

    events = new_events()
    selected = [e for e in events if e["status"] == "selected"]
    assert len(selected) == 2
    assert all(e["tier_1_anchor"] for e in selected)

    signal = [e for e in events if not e["tier_1_anchor"]]
    assert len(signal) == 1
    assert signal[0]["status"] == "candidate"  # never advanced

    # anchored events outrank the social-only one
    top_score = max(e["importance_score"] for e in selected)
    assert top_score > (signal[0]["importance_score"] or 0.0)
