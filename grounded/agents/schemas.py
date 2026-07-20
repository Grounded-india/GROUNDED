"""Typed I/O contracts passed between the Layer 3 agents.

These are deliberately plain dataclasses (not the DB pydantic models in
``grounded.models``) so the agent pipeline stays decoupled from the persistence
layer and from any Layer 1/2 changes a teammate might make.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from grounded.models import SourceTier


@dataclass(frozen=True)
class EventView:
    """The minimal event context an agent crew needs."""

    id: UUID
    title: str
    summary: str | None = None
    importance_score: float | None = None


@dataclass(frozen=True)
class SourceDoc:
    """One source item belonging to an event, with the best available text."""

    id: UUID
    source_name: str
    source_tier: SourceTier
    source_url: str
    title: str | None
    text: str

    @property
    def is_primary(self) -> bool:
        return self.source_tier == SourceTier.PRIMARY

    @property
    def is_wire(self) -> bool:
        return self.source_tier == SourceTier.WIRE

    @property
    def is_signal(self) -> bool:
        return self.source_tier == SourceTier.SIGNAL


@dataclass
class ClaimDraft:
    """A candidate claim from the Fact Extractor, grounded to source item ids."""

    text: str
    source_item_ids: list[UUID]


@dataclass
class VerifiedClaim:
    """A claim after the deterministic verifier has scored its backing."""

    text: str
    source_item_ids: list[UUID]
    verified: bool
    tier_1_backed: bool
    distinct_sources: int
    note: str = ""


@dataclass
class StoryPackage:
    """Final Layer 3 output for one event, ready to persist."""

    event_id: UUID
    headline: str
    dek: str
    body_markdown: str
    claims: list[VerifiedClaim]
    editor_approved: bool
    editor_notes: str
    agent_trace: dict[str, Any] = field(default_factory=dict)
