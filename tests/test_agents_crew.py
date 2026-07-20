"""Full-crew test using the offline local backend (no network, deterministic)."""

from __future__ import annotations

from uuid import UUID

from grounded.agents.crew import build_story
from grounded.agents.llm import LocalBackend
from grounded.agents.schemas import EventView, SourceDoc
from grounded.models import SourceTier

EVENT_ID = UUID(int=500)
PRIMARY = UUID(int=1)
WIRE = UUID(int=2)


def _docs():
    return [
        SourceDoc(
            id=PRIMARY,
            source_name="PIB",
            source_tier=SourceTier.PRIMARY,
            source_url="https://pib.test/scheme",
            title="Cabinet approves scheme",
            text=(
                "The Union Cabinet approved a new manufacturing scheme on Monday. "
                "The scheme will run for four years with a defined budget outlay. "
                "It aims to boost domestic production and employment."
            ),
        ),
        SourceDoc(
            id=WIRE,
            source_name="AP",
            source_tier=SourceTier.WIRE,
            source_url="https://ap.test/scheme",
            title="India approves manufacturing plan",
            text=(
                "India approved a manufacturing incentive plan expected to run several years. "
                "Analysts said the measure could support new factory investment nationwide."
            ),
        ),
    ]


def _event():
    return EventView(id=EVENT_ID, title="Cabinet approves manufacturing scheme", summary="Cabinet clears scheme.")


def test_crew_produces_grounded_story_offline():
    docs = _docs()
    valid_ids = {d.id for d in docs}
    pkg = build_story(_event(), docs, LocalBackend())

    assert pkg.event_id == EVENT_ID
    assert pkg.claims, "expected at least one claim"
    for claim in pkg.claims:
        assert claim.source_item_ids, "every claim must be grounded"
        assert set(claim.source_item_ids) <= valid_ids, "claims cite only real event sources"

    assert "# Cabinet approves manufacturing scheme" in pkg.body_markdown
    assert pkg.agent_trace["mode"] == "report"
    assert pkg.agent_trace["models"]["fact_extractor"] == "local"
    assert "fact_extractor" in pkg.agent_trace
    assert "verifier" in pkg.agent_trace


def test_crew_is_deterministic_offline():
    a = build_story(_event(), _docs(), LocalBackend())
    b = build_story(_event(), _docs(), LocalBackend())
    assert a.body_markdown == b.body_markdown
    assert a.editor_approved == b.editor_approved


def test_crew_raises_without_sources():
    import pytest

    with pytest.raises(ValueError):
        build_story(_event(), [], LocalBackend())
