"""Unit tests for the editor / hallucination-auditor gate."""

from __future__ import annotations

from uuid import UUID

from grounded.agents.editor import audit_and_assemble
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim
from grounded.models import SourceTier

PRIMARY = UUID(int=1)
WIRE = UUID(int=2)


def _docs():
    return [
        SourceDoc(PRIMARY, "PIB", SourceTier.PRIMARY, "https://pib.test/x", "t", "x"),
        SourceDoc(WIRE, "AP", SourceTier.WIRE, "https://ap.test/y", "t", "x"),
    ]


def _event():
    return EventView(id=UUID(int=100), title="Cabinet approves scheme", summary="A summary.")


def test_ungrounded_claims_are_cut():
    claims = [
        VerifiedClaim("grounded", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
        VerifiedClaim("ghost", [], verified=False, tier_1_backed=False, distinct_sources=0),
    ]
    pkg = audit_and_assemble(_event(), claims, "ctx", "persp", _docs())
    assert len(pkg.claims) == 1
    assert pkg.claims[0].text == "grounded"
    assert "cut 1 unsupported/ungrounded" in pkg.editor_notes


def test_approved_when_verified_claim_present():
    claims = [
        VerifiedClaim("c", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
    ]
    pkg = audit_and_assemble(_event(), claims, "ctx", "persp", _docs())
    assert pkg.editor_approved is True


def test_rejected_when_no_verified_claim():
    claims = [
        VerifiedClaim(
            "c", [WIRE], verified=False, tier_1_backed=False, distinct_sources=1, note="single"
        ),
    ]
    pkg = audit_and_assemble(_event(), claims, "ctx", "persp", _docs())
    assert pkg.editor_approved is False
    assert "rejected" in pkg.editor_notes


def test_markdown_has_sections_and_citations():
    claims = [
        VerifiedClaim("verified fact", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
        VerifiedClaim(
            "flagged fact", [WIRE], verified=False, tier_1_backed=False, distinct_sources=1, note="single-source"
        ),
    ]
    pkg = audit_and_assemble(_event(), claims, "some context", "some perspective", _docs())
    body = pkg.body_markdown
    assert "# Cabinet approves scheme" in body
    assert "## What we know" in body
    assert "[PIB](https://pib.test/x)" in body
    assert "## Flagged" in body
    assert "[AP](https://ap.test/y)" in body
    assert "## Context" in body and "some context" in body
    assert "## Perspectives" in body and "some perspective" in body
    assert "## Sources" in body


def test_dek_prefers_event_summary():
    claims = [
        VerifiedClaim("c", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
    ]
    pkg = audit_and_assemble(_event(), claims, "", "", _docs())
    assert pkg.dek == "A summary."


SIGNAL = UUID(int=3)


class _FakeBackend:
    name = "fake"
    is_local = False

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def complete(self, *, system, user, max_tokens=1500, temperature=0.2, json_mode=False):
        self.calls.append(user)
        return self._responses.pop(0) if self._responses else "{}"


def _no_primary_docs():
    return [
        SourceDoc(WIRE, "AP", SourceTier.WIRE, "https://ap.test/y", "t", "x"),
        SourceDoc(SIGNAL, "Reddit", SourceTier.SIGNAL, "https://reddit.test/z", "t", "x"),
    ]


def test_debate_mode_approves_without_primary():
    # ground-reality event: no primary source, only flagged claims
    claims = [
        VerifiedClaim("locals report a protest", [SIGNAL], verified=False,
                      tier_1_backed=False, distinct_sources=1, note="single"),
    ]
    pkg = audit_and_assemble(
        _event(), claims, "ctx", "**Side A**\n\nx\n\n**Side B**\n\ny", _no_primary_docs(),
        mode="debate",
    )
    assert pkg.editor_approved is True
    assert "mode=debate" in pkg.editor_notes
    assert "## Debate" in pkg.body_markdown
    assert "presented as a fact-based debate" in pkg.body_markdown


def test_debate_mode_rejects_when_no_grounded_points():
    pkg = audit_and_assemble(
        _event(), [], "ctx", "persp", _no_primary_docs(), mode="debate"
    )
    assert pkg.editor_approved is False
    assert "no grounded points" in pkg.editor_notes


def _corroborated(text, verified=True):
    # non-primary, corroborated across two wires; cuttable by the LLM audit
    return VerifiedClaim(
        text, [WIRE], verified=verified, tier_1_backed=False, distinct_sources=2
    )


def test_llm_cut_removes_unsupported_and_sets_headline():
    claims = [
        _corroborated("kept0"),
        _corroborated("bogus"),
        _corroborated("kept2"),
        _corroborated("kept3"),
    ]
    backend = _FakeBackend(
        ['{"unsupported": [1]}', '{"headline": "Clean headline", "dek": "A dek."}']
    )
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    texts = [c.text for c in pkg.claims]
    assert "bogus" not in texts
    assert len(texts) == 3
    assert pkg.headline == "Clean headline"
    assert pkg.dek == "A dek."


def test_soft_unsupported_protects_primary_claims():
    # a borderline (non-conflicting) call cannot remove primary-anchored claims
    claims = [
        VerifiedClaim("p0", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
        VerifiedClaim("p1", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
    ]
    backend = _FakeBackend(['{"unsupported": [0, 1]}', '{"headline": "H", "dek": "D"}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    assert len(pkg.claims) == 2


def test_contradiction_cuts_even_primary_claim():
    # a half-lie against a government cite is removed, not just flagged
    claims = [
        VerifiedClaim("p0 misquotes doc", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
        VerifiedClaim("p1", [PRIMARY], verified=True, tier_1_backed=True, distinct_sources=1),
    ]
    backend = _FakeBackend(['{"contradicted": [0]}', '{"headline": "H", "dek": "D"}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    texts = [c.text for c in pkg.claims]
    assert "p0 misquotes doc" not in texts
    assert len(texts) == 1


def test_one_claim_half_lie_is_cut_and_rejected():
    # a story that is only a half-lie should be dropped entirely
    claims = [_corroborated("sole false claim")]
    backend = _FakeBackend(['{"contradicted": [0]}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    assert pkg.claims == []
    assert pkg.editor_approved is False


def test_soft_cut_is_capped_to_half():
    # model flags every claim as merely unsupported, but at most 50% may be cut
    claims = [_corroborated(f"c{i}") for i in range(4)]
    backend = _FakeBackend(['{"unsupported": [0, 1, 2, 3]}', '{"headline": "H", "dek": "D"}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    assert len(pkg.claims) == 2
    assert pkg.editor_approved is True


def test_soft_cut_keeps_last_verified_claim():
    # model tries to cut the only verified claim on a soft call -> kept, story stays approved
    claims = [
        _corroborated("only verified"),
        _corroborated("flagged", verified=False),
    ]
    backend = _FakeBackend(['{"unsupported": [0]}', '{"headline": "H", "dek": "D"}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    assert "only verified" in [c.text for c in pkg.claims]
    assert pkg.editor_approved is True


def test_one_claim_story_not_soft_trimmed():
    claims = [_corroborated("sole claim")]
    backend = _FakeBackend(['{"unsupported": [0]}', '{"headline": "H", "dek": "D"}'])
    pkg = audit_and_assemble(_event(), claims, "", "", _docs(), backend=backend)
    assert [c.text for c in pkg.claims] == ["sole claim"]
