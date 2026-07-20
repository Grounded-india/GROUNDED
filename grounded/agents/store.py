"""Persist a StoryPackage into stories / claims / claim_sources.

Idempotent per event: ``stories.event_id`` is UNIQUE, so a re-run upserts the
story row and fully replaces its claims (cascading to claim_sources).
"""

from __future__ import annotations

import json
from uuid import UUID

from psycopg.types.json import Json

from grounded.agents.schemas import StoryPackage
from grounded.db import cursor


def _json(obj: object) -> Json:
    return Json(obj, dumps=lambda o: json.dumps(o, default=str))


def save_story(package: StoryPackage) -> UUID:
    with cursor() as cur:
        cur.execute(
            """
            INSERT INTO stories
                (event_id, headline, dek, body_markdown,
                 editor_approved, editor_notes, agent_trace)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE SET
                headline        = EXCLUDED.headline,
                dek             = EXCLUDED.dek,
                body_markdown   = EXCLUDED.body_markdown,
                editor_approved = EXCLUDED.editor_approved,
                editor_notes    = EXCLUDED.editor_notes,
                agent_trace     = EXCLUDED.agent_trace,
                created_at      = NOW()
            RETURNING id
            """,
            (
                package.event_id,
                package.headline,
                package.dek,
                package.body_markdown,
                package.editor_approved,
                package.editor_notes,
                _json(package.agent_trace),
            ),
        )
        story_id = cur.fetchone()["id"]

        cur.execute("DELETE FROM claims WHERE story_id = %s", (story_id,))

        for ordinal, claim in enumerate(package.claims):
            cur.execute(
                """
                INSERT INTO claims
                    (story_id, claim_text, verified, tier_1_backed, ordinal)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    story_id,
                    claim.text,
                    claim.verified,
                    claim.tier_1_backed,
                    ordinal,
                ),
            )
            claim_id = cur.fetchone()["id"]
            for raw_item_id in claim.source_item_ids:
                cur.execute(
                    """
                    INSERT INTO claim_sources (claim_id, raw_item_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (claim_id, raw_item_id),
                )
    return story_id
