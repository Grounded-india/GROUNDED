from datetime import datetime
from enum import IntEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceTier(IntEnum):
    PRIMARY = 1   # government, court, official statistics
    WIRE = 2      # Reuters, AP, AFP, PTI, ANI
    SIGNAL = 3    # Reddit, X, YouTube captions — topic radar only


class EventStatus:
    CANDIDATE = "candidate"
    SELECTED = "selected"
    PUBLISHED = "published"
    REJECTED = "rejected"


class RawItem(BaseModel):
    """A single ingested item from a source, before any editorial processing."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    source_name: str
    source_tier: SourceTier
    source_url: str
    title: str | None = None
    content: str
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    raw_data: dict[str, Any] | None = None


class Event(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    title: str
    summary: str | None = None
    importance_score: float | None = None
    tier_1_anchor: bool = False
    first_seen_at: datetime
    last_seen_at: datetime
    status: str = EventStatus.CANDIDATE


class Claim(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    story_id: UUID | None = None
    claim_text: str
    verified: bool = False
    tier_1_backed: bool = False
    ordinal: int | None = None
    source_item_ids: list[UUID] = Field(default_factory=list)


class Story(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    event_id: UUID
    headline: str | None = None
    dek: str | None = None
    body_markdown: str | None = None
    editor_approved: bool = False
    editor_notes: str | None = None
    agent_trace: dict[str, Any] | None = None
    created_at: datetime | None = None
    published_at: datetime | None = None
    claims: list[Claim] = Field(default_factory=list)
