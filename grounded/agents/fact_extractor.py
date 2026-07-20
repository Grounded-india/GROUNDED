"""Agent 1 - Fact Extractor.

Pulls atomic, verifiable claims out of the source material. Every claim must be
grounded to one or more real source item ids; the LLM is asked for ids and any
id it invents (not present in the event) is discarded here in code. A claim left
with no valid source is dropped - grounding is enforced, not requested.

The local backend uses a simple extractive fallback (sentence selection) so the
pipeline runs offline and deterministically.
"""

from __future__ import annotations

import logging
import re
from uuid import UUID

from grounded.agents.llm import LLMBackend, extract_json
from grounded.agents.schemas import ClaimDraft, EventView, SourceDoc

log = logging.getLogger(__name__)

MAX_CLAIMS = 14
_LOCAL_MAX_PER_DOC = 3
_LOCAL_MIN_LEN = 40
_LOCAL_MAX_LEN = 320
_SOURCE_TEXT_BUDGET = 1600  # chars of each source shown to the model

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

SYSTEM = (
    "You are a meticulous news fact extractor. You output only atomic, verifiable "
    "factual claims that are directly supported by the provided sources. You never "
    "invent facts, numbers, or attributions, and you never use outside knowledge."
)


def _source_digest(docs: list[SourceDoc]) -> str:
    blocks = []
    for d in docs:
        body = (d.text or "").strip()
        if len(body) > _SOURCE_TEXT_BUDGET:
            body = body[:_SOURCE_TEXT_BUDGET] + " ..."
        blocks.append(
            f"[SOURCE id={d.id} name={d.source_name} tier={d.source_tier.name.lower()}]\n"
            f"{(d.title or '').strip()}\n{body}"
        )
    return "\n\n".join(blocks)


def build_prompt(event: EventView, docs: list[SourceDoc]) -> str:
    return (
        f"EVENT: {event.title}\n\n"
        f"SOURCES:\n{_source_digest(docs)}\n\n"
        "Extract every distinct, atomic, verifiable factual claim that the sources "
        "above support. For each claim list the source id(s) that back it. Use only "
        "the ids shown above - do not invent ids. Prefer claims backed by primary "
        "(official) sources or by multiple independent outlets.\n\n"
        'Respond ONLY with JSON of the form:\n'
        '{"claims": [{"text": "<claim>", "source_ids": ["<id>", "..."]}]}'
    )


def parse_response(raw: str, valid_ids: set[UUID]) -> list[ClaimDraft]:
    """Parse an LLM response into grounded ClaimDrafts, dropping invalid ids."""
    data = extract_json(raw)
    items = data.get("claims", []) if isinstance(data, dict) else data
    out: list[ClaimDraft] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if not text:
            continue
        raw_ids = item.get("source_ids") or item.get("source_item_ids") or []
        ids: list[UUID] = []
        for candidate in raw_ids:
            try:
                uid = UUID(str(candidate))
            except (ValueError, TypeError):
                continue
            if uid in valid_ids and uid not in ids:
                ids.append(uid)
        if not ids:
            continue  # ungrounded -> drop
        out.append(ClaimDraft(text=text, source_item_ids=ids))
    return out[:MAX_CLAIMS]


def _local_extract(docs: list[SourceDoc]) -> list[ClaimDraft]:
    """Deterministic extractive fallback: pick informative sentences per source,
    primary/wire first, grounded to that source."""
    ordered = sorted(docs, key=lambda d: (int(d.source_tier), str(d.id)))
    out: list[ClaimDraft] = []
    seen: set[str] = set()
    for d in ordered:
        text = (d.text or "").strip()
        if not text:
            continue
        picked = 0
        for sentence in _SENTENCE_SPLIT.split(text):
            s = " ".join(sentence.split())
            if not (_LOCAL_MIN_LEN <= len(s) <= _LOCAL_MAX_LEN):
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(ClaimDraft(text=s, source_item_ids=[d.id]))
            picked += 1
            if picked >= _LOCAL_MAX_PER_DOC or len(out) >= MAX_CLAIMS:
                break
        if len(out) >= MAX_CLAIMS:
            break
    return out[:MAX_CLAIMS]


def extract_claims(
    event: EventView, docs: list[SourceDoc], backend: LLMBackend
) -> list[ClaimDraft]:
    if backend.is_local:
        return _local_extract(docs)

    valid_ids = {d.id for d in docs}
    raw = backend.complete(
        system=SYSTEM,
        user=build_prompt(event, docs),
        max_tokens=2000,
        temperature=0.0,
    )
    try:
        claims = parse_response(raw, valid_ids)
    except ValueError as e:
        log.warning("fact extractor JSON parse failed (%s); using local fallback", e)
        return _local_extract(docs)
    if not claims:
        log.warning("fact extractor returned no grounded claims; using local fallback")
        return _local_extract(docs)
    return claims
