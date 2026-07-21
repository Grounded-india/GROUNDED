"""Unit tests for the LLM backend helpers (no network)."""

from __future__ import annotations

import pytest

from grounded.agents.llm import LocalBackend, extract_json, get_backend


def test_extract_json_plain_object():
    assert extract_json('{"a": 1, "b": [2, 3]}') == {"a": 1, "b": [2, 3]}


def test_extract_json_fenced_block():
    raw = "Here you go:\n```json\n{\"claims\": []}\n```\nHope that helps!"
    assert extract_json(raw) == {"claims": []}


def test_extract_json_object_embedded_in_prose():
    raw = 'Sure. {"text": "a claim", "source_ids": ["x"]} <- that is the answer'
    assert extract_json(raw) == {"text": "a claim", "source_ids": ["x"]}


def test_extract_json_array():
    assert extract_json("prefix [1, 2, 3] suffix") == [1, 2, 3]


def test_extract_json_handles_braces_inside_strings():
    raw = '{"text": "a } b { c", "n": 1}'
    assert extract_json(raw) == {"text": "a } b { c", "n": 1}


def test_extract_json_strips_reasoning_block():
    # reasoning models (Nemotron) wrap the answer in <think>...</think>
    raw = '<think>Let me consider {this} and {that}...</think>\n{"claims": [1]}'
    assert extract_json(raw) == {"claims": [1]}


def test_extract_json_strips_unterminated_reasoning_block():
    # a truncated/unclosed think block with stray braces must not be parsed as JSON
    raw = '<think>weighing options { partial'
    with pytest.raises(ValueError):
        extract_json(raw)


def test_extract_json_ignores_braces_in_reasoning():
    # braces inside the think block must not confuse the brace-matching scan
    raw = '<think>the source says {"x": 999} but</think> {"verified": true}'
    assert extract_json(raw) == {"verified": True}


def test_extract_json_raises_on_empty():
    with pytest.raises(ValueError):
        extract_json("   ")


def test_extract_json_raises_when_no_json():
    with pytest.raises(ValueError):
        extract_json("no json here at all")


def test_get_backend_local_is_offline():
    backend = get_backend(prefer="local")
    assert isinstance(backend, LocalBackend)
    assert backend.is_local is True


def test_local_backend_complete_refuses():
    with pytest.raises(RuntimeError):
        LocalBackend().complete(system="s", user="u")
