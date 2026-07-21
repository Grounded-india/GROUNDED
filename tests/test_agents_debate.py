"""Unit tests for the multi-agent debate (the Perspective Agent)."""

from __future__ import annotations

from uuid import UUID

from grounded.agents.debate import run_debate
from grounded.agents.llm import LocalBackend
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim
from grounded.models import SourceTier

WIRE = UUID(int=2)
SIGNAL = UUID(int=3)


def _docs():
    return [
        SourceDoc(SIGNAL, "Reddit", SourceTier.SIGNAL, "https://r.test/z", "t", "protesters gathered"),
        SourceDoc(WIRE, "AP", SourceTier.WIRE, "https://ap.test/y", "t", "police responded"),
    ]


def _claims():
    return [
        VerifiedClaim("protesters gathered downtown", [SIGNAL], verified=False,
                      tier_1_backed=False, distinct_sources=1),
        VerifiedClaim("police responded to the crowd", [WIRE], verified=False,
                      tier_1_backed=False, distinct_sources=1),
    ]


def _event():
    return EventView(id=UUID(int=9), title="Protest downtown")


class _FakeBackend:
    name = "nemotron"
    is_local = False

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def complete(self, *, system, user, max_tokens=1500, temperature=0.2, json_mode=False):
        self.calls.append(user)
        return self._responses.pop(0) if self._responses else "{}"


def test_local_debate_has_two_grounded_sides():
    result = run_debate(_event(), _claims(), _docs(), LocalBackend())
    md = result.markdown
    assert "Side A" in md and "Side B" in md
    # local debate cites the source outlets by name
    assert "Reddit" in md or "AP" in md


def test_llm_debate_runs_framing_and_two_debaters():
    backend = _FakeBackend(
        ['{"side_a": "Protesters", "side_b": "Police"}', "Argument A (AP)", "Argument B (Reddit)"]
    )
    result = run_debate(_event(), _claims(), _docs(), backend)
    assert result.side_a_label == "Protesters"
    assert result.side_b_label == "Police"
    assert "Argument A" in result.side_a_md
    assert "Argument B" in result.side_b_md
    # framing + two debaters => three model calls ("multiple nemotron agents")
    assert len(backend.calls) == 3


def test_llm_debate_falls_back_when_framing_unparseable():
    backend = _FakeBackend(["not json at all", "Argument A", "Argument B"])
    result = run_debate(_event(), _claims(), _docs(), backend)
    assert result.side_a_label and result.side_b_label  # default labels used
