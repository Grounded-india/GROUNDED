"""Unit tests for the deterministic verifier rules."""

from __future__ import annotations

from uuid import UUID

from grounded.agents.schemas import ClaimDraft, SourceDoc
from grounded.agents.verifier import verify_claims
from grounded.models import SourceTier

PRIMARY = UUID(int=1)
WIRE_1 = UUID(int=2)
WIRE_2 = UUID(int=3)
SIGNAL = UUID(int=4)


def _docs():
    return [
        SourceDoc(PRIMARY, "PIB", SourceTier.PRIMARY, "u1", "t", "x"),
        SourceDoc(WIRE_1, "AP", SourceTier.WIRE, "u2", "t", "x"),
        SourceDoc(WIRE_2, "Reuters", SourceTier.WIRE, "u3", "t", "x"),
        SourceDoc(SIGNAL, "Reddit", SourceTier.SIGNAL, "u4", "t", "x"),
    ]


def test_primary_anchor_is_verified_and_tier1():
    [c] = verify_claims([ClaimDraft("c", [PRIMARY])], _docs())
    assert c.verified is True
    assert c.tier_1_backed is True


def test_two_distinct_wires_are_corroborated():
    [c] = verify_claims([ClaimDraft("c", [WIRE_1, WIRE_2])], _docs())
    assert c.verified is True
    assert c.tier_1_backed is False
    assert c.distinct_sources == 2


def test_single_wire_is_flagged():
    [c] = verify_claims([ClaimDraft("c", [WIRE_1])], _docs())
    assert c.verified is False
    assert "single-source" in c.note


def test_single_signal_flag_mentions_social():
    [c] = verify_claims([ClaimDraft("c", [SIGNAL])], _docs())
    assert c.verified is False
    assert "social" in c.note or "signal" in c.note


def test_invalid_ids_yield_no_source():
    [c] = verify_claims([ClaimDraft("c", [UUID(int=999)])], _docs())
    assert c.source_item_ids == []
    assert c.verified is False
    assert c.note == "no valid source"


def test_same_outlet_twice_is_not_corroboration():
    docs = [
        SourceDoc(WIRE_1, "AP", SourceTier.WIRE, "u2", "t", "x"),
        SourceDoc(WIRE_2, "AP", SourceTier.WIRE, "u3", "t", "x"),
    ]
    [c] = verify_claims([ClaimDraft("c", [WIRE_1, WIRE_2])], docs)
    assert c.distinct_sources == 1
    assert c.verified is False


class _FakeBackend:
    name = "fake"
    is_local = False

    def __init__(self, responses):
        self._responses = list(responses)

    def complete(self, *, system, user, max_tokens=1500, temperature=0.2, json_mode=False):
        return self._responses.pop(0) if self._responses else "{}"


def _corroborated(text):
    # cites two distinct wire outlets -> verified, tier_1_backed False
    return ClaimDraft(text, [WIRE_1, WIRE_2])


def test_semantic_demote_protects_primary_and_caps():
    claims = [
        ClaimDraft("primary claim", [PRIMARY]),  # tier-1 anchored
        _corroborated("corrob 1"),
        _corroborated("corrob 2"),
        _corroborated("corrob 3"),
    ]
    # model flags everything as unsupported
    backend = _FakeBackend(['{"unsupported": [0, 1, 2, 3]}'])
    result = verify_claims(claims, _docs(), backend=backend)

    # primary-anchored claim is never demoted by the model
    assert result[0].verified is True
    # 4 verified -> at most 2 (50%) may be demoted
    assert sum(1 for c in result if c.verified) == 2


def test_semantic_demote_skips_thin_story():
    # only one verified claim -> left alone entirely (efficiency guardrail)
    backend = _FakeBackend(['{"unsupported": [0]}'])
    [c] = verify_claims([_corroborated("only claim")], _docs(), backend=backend)
    assert c.verified is True


def test_semantic_check_never_promotes():
    # single wire -> unverified deterministically; a model claiming support cannot promote it
    backend = _FakeBackend(['{"unsupported": []}'])
    [c] = verify_claims([ClaimDraft("c", [WIRE_1])], _docs(), backend=backend)
    assert c.verified is False


def test_semantic_check_skipped_when_local():
    from grounded.agents.llm import LocalBackend

    claims = [_corroborated("a"), _corroborated("b")]
    result = verify_claims(claims, _docs(), backend=LocalBackend())
    assert all(c.verified for c in result)


def test_contradicted_primary_claim_is_demoted():
    # half-lie against an official/government cite must be caught, even as a lone claim
    backend = _FakeBackend(['{"contradicted": [0], "unsupported": []}'])
    [c] = verify_claims([ClaimDraft("misquotes the gazette", [PRIMARY])], _docs(), backend=backend)
    assert c.verified is False
    assert "contradicts" in c.note


def test_soft_unsupported_spares_lone_primary():
    # a borderline (non-conflicting) call does not nuke a lone primary-cited claim
    backend = _FakeBackend(['{"contradicted": [], "unsupported": [0]}'])
    [c] = verify_claims([ClaimDraft("primary claim", [PRIMARY])], _docs(), backend=backend)
    assert c.verified is True


def test_contradictions_bypass_the_cap():
    # every claim flagged as a contradiction is demoted - the 50% cap is soft-only
    claims = [
        ClaimDraft("primary claim", [PRIMARY]),
        _corroborated("corrob 1"),
        _corroborated("corrob 2"),
        _corroborated("corrob 3"),
    ]
    backend = _FakeBackend(['{"contradicted": [0, 1, 2, 3], "unsupported": []}'])
    result = verify_claims(claims, _docs(), backend=backend)
    assert not any(c.verified for c in result)
