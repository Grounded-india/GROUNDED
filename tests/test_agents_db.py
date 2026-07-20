"""Integration test: Layer 3 end-to-end against Postgres, offline backend.

Creates a throwaway 'selected' event with two sources, runs the crew with the
local backend, and verifies the story/claims/claim_sources round-trip and that a
re-run is idempotent. All synthetic rows are removed in teardown.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from grounded.agents.llm import LocalBackend
from grounded.agents.runner import build_stories

pytestmark = pytest.mark.integration

_MARK = "layer3-selftest"


@pytest.fixture
def sample_event(db_available):
    from grounded.db import cursor

    now = datetime.now(UTC)
    with cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_items (source_name, source_tier, source_url, title, content, full_content)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            ("PIB", 1, f"https://pib.test/{_MARK}", "Cabinet approves scheme",
             "seed", "The Union Cabinet approved a new scheme on Monday for four years."),
        )
        primary_id = cur.fetchone()["id"]
        cur.execute(
            """
            INSERT INTO raw_items (source_name, source_tier, source_url, title, content, full_content)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            ("AP", 2, f"https://ap.test/{_MARK}", "India approves plan",
             "seed", "India approved a manufacturing incentive plan expected to run several years."),
        )
        wire_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO events (title, summary, importance_score, tier_1_anchor,
                                first_seen_at, last_seen_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'selected') RETURNING id
            """,
            (f"{_MARK} cabinet scheme", "Cabinet clears scheme.", 9.9, True, now, now),
        )
        event_id = cur.fetchone()["id"]

        for rid in (primary_id, wire_id):
            cur.execute(
                "INSERT INTO event_items (event_id, raw_item_id) VALUES (%s, %s)",
                (event_id, rid),
            )

    yield event_id

    with cursor() as cur:
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        cur.execute(
            "DELETE FROM raw_items WHERE id = ANY(%s)", ([primary_id, wire_id],)
        )


def _story_row(event_id):
    from grounded.db import cursor

    with cursor() as cur:
        cur.execute(
            "SELECT id, editor_approved FROM stories WHERE event_id = %s", (event_id,)
        )
        return cur.fetchone()


def _claim_count(story_id):
    from grounded.db import cursor

    with cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM claims WHERE story_id = %s", (story_id,))
        return cur.fetchone()["n"]


def test_build_stories_persists_grounded_story(sample_event):
    from grounded.db import cursor

    result = build_stories(force=True, event_id=sample_event, backend=LocalBackend())
    assert result["built"] == 1
    assert result["approved"] == 1  # primary-anchored -> verified -> approved

    story = _story_row(sample_event)
    assert story is not None
    assert story["editor_approved"] is True

    n_claims = _claim_count(story["id"])
    assert n_claims >= 1

    with cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS n FROM claim_sources cs
            JOIN claims c ON c.id = cs.claim_id
            WHERE c.story_id = %s
            """,
            (story["id"],),
        )
        assert cur.fetchone()["n"] >= 1


def test_rebuild_is_idempotent(sample_event):
    build_stories(force=True, event_id=sample_event, backend=LocalBackend())
    story = _story_row(sample_event)
    first = _claim_count(story["id"])

    build_stories(force=True, event_id=sample_event, backend=LocalBackend())
    story_again = _story_row(sample_event)

    # same story row (unique event_id), same claim count (fully replaced, not appended)
    assert story_again["id"] == story["id"]
    assert _claim_count(story_again["id"]) == first
