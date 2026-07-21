"""Agent 1 - Fact Extractor.

Pulls atomic, verifiable claims out of the source material. Every claim must be
grounded to one or more real source item ids; the LLM is asked for ids and any
id it invents (not present in the event) is discarded here in code. A claim left
with no valid source is dropped - grounding is enforced, not requested.

The local backend uses a simple extractive fallback (sentence selection) so the
pipeline runs offline and deterministically.
"""

from __future__ import annotations

import json
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
_SOURCE_TEXT_BUDGET = 900  # chars of each source shown to the model
# Cap how many sources go into one prompt. A big cross-source event can have 20+
# items; feeding them all makes a 26k-char prompt and pushes the model to emit
# dozens of claims that overrun the token limit (truncated -> unterminated JSON)
# and a generation so long it trips the request timeout. Keep the most
# authoritative sources (primary/wire first).
_MAX_PROMPT_SOURCES = 8

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

SYSTEM = (
    "You are a meticulous news fact extractor. You output only atomic, verifiable "
    "factual claims that are directly supported by the provided sources. You never "
    "invent facts, numbers, or attributions, and you never use outside knowledge."
)


def _prompt_sources(docs: list[SourceDoc]) -> list[SourceDoc]:
    """Most authoritative sources first, capped so the prompt stays bounded."""
    ordered = sorted(docs, key=lambda d: (int(d.source_tier), -len(d.text or "")))
    return ordered[:_MAX_PROMPT_SOURCES]


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
        f"SOURCES:\n{_source_digest(_prompt_sources(docs))}\n\n"
        f"Extract the {MAX_CLAIMS} most important distinct, atomic, verifiable "
        "factual claims the sources above support (fewer is fine). Write each claim "
        "as ONE concise sentence. For each claim list the source id(s) that back it. "
        "Use only the ids shown above - do not invent ids. Prefer claims backed by "
        "primary (official) sources or by multiple independent outlets.\n\n"
        'Respond ONLY with JSON of the form:\n'
        '{"claims": [{"text": "<claim>", "source_ids": ["<id>", "..."]}]}'
    )


def _salvage_claim_objects(raw: str) -> list[dict]:
    """Recover complete claim objects from a truncated JSON array.

    A model can be cut off mid-array (finish_reason=length), leaving unterminated
    JSON. Rather than lose the whole batch, scan the ``claims`` array and keep
    every ``{...}`` object that closed cleanly, discarding only the partial tail.
    This uses the model's *real* output - it is not a local/offline substitution.
    """
    ci = raw.find('"claims"')
    start = raw.find("[", ci) if ci != -1 else raw.find("[")
    if start == -1:
        return []
    objs: list[dict] = []
    depth = 0
    in_str = esc = False
    obj_start: int | None = None
    for i in range(start + 1, len(raw)):
        ch = raw[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    objs.append(json.loads(raw[obj_start : i + 1]))
                except json.JSONDecodeError:
                    pass
                obj_start = None
        elif ch == "]" and depth == 0:
            break
    return [o for o in objs if isinstance(o, dict)]


def parse_response(raw: str, valid_ids: set[UUID]) -> list[ClaimDraft]:
    """Parse an LLM response into grounded ClaimDrafts, dropping invalid ids."""
    try:
        data = extract_json(raw)
        items = data.get("claims", []) if isinstance(data, dict) else data
    except ValueError:
        # Truncated / unterminated JSON: salvage the complete claim objects.
        items = _salvage_claim_objects(raw)
        if not items:
            raise
        log.warning("fact extractor response was truncated; salvaged %d claim(s)", len(items))
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
    # Explicit offline mode (tests / no-key dev). Not a fallback: chosen upfront.
    if backend.is_local:
        return _local_extract(docs)

    # Real backend: use it or fail loudly - no silent substitution of local text.
    valid_ids = {d.id for d in docs}
    raw = backend.complete(
        system=SYSTEM,
        user=build_prompt(event, docs),
        max_tokens=2500,
        temperature=0.0,
        json_mode=True,
    )
    claims = parse_response(raw, valid_ids)
    log.info("fact extractor (%s): %d grounded claim(s)", backend.name, len(claims))
    return claims
