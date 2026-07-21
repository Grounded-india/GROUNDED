"""Unit tests for the Fact Extractor's grounding + local fallback."""

from __future__ import annotations

from uuid import UUID

from grounded.agents.fact_extractor import (
    _local_extract,
    extract_claims,
    parse_response,
)
from grounded.agents.llm import LocalBackend
from grounded.agents.schemas import EventView, SourceDoc
from grounded.models import SourceTier

ID_A = UUID("00000000-0000-0000-0000-0000000000a1")
ID_B = UUID("00000000-0000-0000-0000-0000000000b2")


def _doc(uid, tier, text, name="Src"):
    return SourceDoc(
        id=uid,
        source_name=name,
        source_tier=tier,
        source_url=f"https://example.test/{uid}",
        title="t",
        text=text,
    )


def test_parse_response_keeps_only_valid_ids():
    raw = (
        '{"claims": ['
        f'{{"text": "valid claim", "source_ids": ["{ID_A}", "not-a-uuid"]}},'
        f'{{"text": "ungrounded", "source_ids": ["{UUID(int=999)}"]}}'
        "]}"
    )
    claims = parse_response(raw, valid_ids={ID_A})
    assert len(claims) == 1
    assert claims[0].text == "valid claim"
    assert claims[0].source_item_ids == [ID_A]


def test_parse_response_dedupes_ids():
    raw = f'{{"claims": [{{"text": "c", "source_ids": ["{ID_A}", "{ID_A}"]}}]}}'
    claims = parse_response(raw, valid_ids={ID_A})
    assert claims[0].source_item_ids == [ID_A]


def test_parse_response_drops_empty_text():
    raw = f'[{{"text": "  ", "source_ids": ["{ID_A}"]}}]'
    assert parse_response(raw, valid_ids={ID_A}) == []


def test_parse_response_salvages_truncated_json():
    # model was cut off mid-array (finish_reason=length): keep the complete objects
    raw = (
        '{"claims": ['
        f'{{"text": "first complete claim", "source_ids": ["{ID_A}"]}},'
        f'{{"text": "second complete claim", "source_ids": ["{ID_A}"]}},'
        f'{{"text": "third truncated cla'
    )
    claims = parse_response(raw, valid_ids={ID_A})
    assert [c.text for c in claims] == ["first complete claim", "second complete claim"]


def test_parse_response_salvages_with_preamble_and_unclosed_wrapper():
    # the real failure: a reasoning preamble + the outer {"claims":[...]} wrapper
    # never closes (truncated). Inner complete objects must still be recovered.
    raw = (
        "We need to extract the most important claims. Here is the JSON:\n"
        '{"claims": [\n'
        f'  {{"text": "claim one", "source_ids": ["{ID_A}"]}},\n'
        f'  {{"text": "claim two", "source_ids": ["{ID_A}"]}},\n'
        f'  {{"text": "claim three cut off here'
    )
    claims = parse_response(raw, valid_ids={ID_A})
    assert [c.text for c in claims] == ["claim one", "claim two"]


def test_parse_response_salvages_after_reasoning_block():
    # a <think> block (with stray braces) before truncated JSON must not confuse salvage
    raw = (
        "<think>maybe I should output {something} weird</think>\n"
        '{"claims": ['
        f'{{"text": "kept claim", "source_ids": ["{ID_A}"]}},'
        f'{{"text": "partial'
    )
    claims = parse_response(raw, valid_ids={ID_A})
    assert [c.text for c in claims] == ["kept claim"]


def test_parse_response_raises_when_nothing_salvageable():
    import pytest

    with pytest.raises(ValueError):
        parse_response("total garbage no json", valid_ids={ID_A})


def test_local_extract_is_grounded_and_deterministic():
    text = (
        "The cabinet approved the new manufacturing scheme on Monday. "
        "Officials said the plan will run for four years and cost a lot. "
        "Industry groups welcomed the announcement in official statements."
    )
    docs = [_doc(ID_A, SourceTier.PRIMARY, text)]
    first = _local_extract(docs)
    second = _local_extract(docs)
    assert [c.text for c in first] == [c.text for c in second]
    assert first, "expected at least one extracted claim"
    for claim in first:
        assert claim.source_item_ids == [ID_A]


def test_local_extract_respects_per_doc_cap():
    sentences = " ".join(
        f"This is a sufficiently long sentence number {i} to be kept as a claim."
        for i in range(10)
    )
    docs = [_doc(ID_A, SourceTier.WIRE, sentences)]
    claims = _local_extract(docs)
    assert len(claims) <= 3


def test_local_extract_orders_primary_before_wire():
    long_sentence = "This is a sufficiently long informative sentence to be kept as a claim."
    docs = [
        _doc(ID_B, SourceTier.WIRE, long_sentence, name="Wire"),
        _doc(ID_A, SourceTier.PRIMARY, long_sentence, name="Gov"),
    ]
    claims = _local_extract(docs)
    # primary source is processed first, so its claim (if unique) appears first
    assert claims[0].source_item_ids == [ID_A]


def test_extract_claims_uses_local_when_backend_local():
    docs = [_doc(ID_A, SourceTier.PRIMARY, "A long enough sentence to become a claim here.")]
    event = EventView(id=ID_A, title="e")
    claims = extract_claims(event, docs, LocalBackend())
    assert claims and all(c.source_item_ids == [ID_A] for c in claims)
