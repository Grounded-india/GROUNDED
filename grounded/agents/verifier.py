"""Agent 2 - Primary Source Verifier.

Two layers, floor-first:

1. Deterministic backing (always on, no LLM): a claim is ``verified`` only if it
   is anchored by a PRIMARY (tier-1) source OR corroborated by >= 2 distinct
   outlets. Single non-primary claims are flagged, never promoted. This is the
   un-gameable floor and is fully unit-tested.

2. Optional semantic check (Gemini, when a backend is supplied): the model reads
   each *already-verified* claim against its cited source text at the level of
   specific details (numbers, dates, names, amounts, scope, qualifiers) and may
   DEMOTE - never promote - so a model cannot be talked into approving junk.

   It returns two kinds of problems, handled differently:
     * ``contradicted`` - the claim conflicts with the cited source OR asserts a
       specific detail the source never states (a "half-truth"). This is treated
       as the worst case: it is ALWAYS demoted, even for a PRIMARY (government)
       source and even if it is the story's only claim. Half-lies must never pass,
       including in official-cited reporting.
     * ``unsupported`` - no direct conflict, the source just does not clearly back
       the claim. These are demoted subject to anti-over-pruning caps so a model
       cannot gut a story on borderline wording.
"""

from __future__ import annotations

import logging

from grounded.agents.llm import LLMBackend, extract_json
from grounded.agents.schemas import ClaimDraft, SourceDoc, VerifiedClaim
from grounded.models import SourceTier

log = logging.getLogger(__name__)

MIN_CORROBORATION = 2

# Anti-over-pruning cap for SOFT ("unsupported") demotions only. Contradictions /
# half-truths are never subject to this cap - they are always demoted. The cap
# stops the model from gutting a story on borderline wording:
#   * a soft demotion never removes a primary (tier-1) anchored claim
#   * at most this fraction of verified claims can be soft-demoted in one pass
#   * a soft demotion never removes the story's last standing verified claim
_MAX_DEMOTE_FRACTION = 0.5

_ENTAILMENT_SYSTEM = (
    "You are a strict fact-checker guarding against half-truths. For each numbered "
    "claim, compare it against the cited SOURCE TEXT at the level of specific "
    "details: numbers, dates, names, amounts, scope, and qualifiers. Classify each "
    "claim as one of:\n"
    "  contradicted - the claim conflicts with the source, OR asserts a specific "
    "detail the source does not contain (a half-truth). Applies even if the source "
    "is an official/government document.\n"
    "  unsupported  - the source does not clearly support the claim, but there is "
    "no direct conflict.\n"
    "Judge solely on the provided text, never on plausibility. Respond only with JSON."
)


def _deterministic(claim: ClaimDraft, docs_by_id: dict) -> VerifiedClaim:
    sources = [docs_by_id[i] for i in claim.source_item_ids if i in docs_by_id]
    distinct_names = {s.source_name for s in sources}
    tiers = {s.source_tier for s in sources}

    tier_1_backed = SourceTier.PRIMARY in tiers
    distinct = len(distinct_names)
    verified = tier_1_backed or distinct >= MIN_CORROBORATION

    note = ""
    if not sources:
        note = "no valid source"
    elif not verified:
        only_signal = tiers == {SourceTier.SIGNAL}
        note = (
            "single unverified social/signal source"
            if only_signal
            else "single-source, no primary anchor"
        )

    return VerifiedClaim(
        text=claim.text,
        source_item_ids=[s.id for s in sources],
        verified=verified,
        tier_1_backed=tier_1_backed,
        distinct_sources=distinct,
        note=note,
    )


def _semantic_demote(
    claims: list[VerifiedClaim], docs: list[SourceDoc], backend: LLMBackend
) -> list[VerifiedClaim]:
    by_id = {d.id: d for d in docs}
    verified_positions = [i for i, c in enumerate(claims) if c.verified]
    if not verified_positions:
        return claims

    entries = []
    for n, pos in enumerate(verified_positions):
        c = claims[pos]
        src_text = " || ".join(
            f"{by_id[j].source_name}: {(by_id[j].text or '')[:400]}"
            for j in c.source_item_ids
            if j in by_id
        )
        entries.append(f"{n}. CLAIM: {c.text}\n   SOURCE TEXT: {src_text}")

    user = (
        "Check each claim against its cited source text at the level of every "
        "specific detail.\n\n"
        + "\n\n".join(entries)
        + '\n\nReturn JSON: {"contradicted": [<indices that conflict with the source '
        'or assert details the source never states>], "unsupported": [<indices the '
        "source does not clearly support but does not directly conflict>]}"
    )
    # Real backend only (callers gate on is_local): run it or fail loudly. We do
    # not silently skip the fidelity check - a broken verifier must be visible.
    raw = backend.complete(
        system=_ENTAILMENT_SYSTEM, user=user, max_tokens=500, temperature=0.0, json_mode=True
    )
    data = extract_json(raw)
    contradicted = {int(x) for x in (data.get("contradicted") or [])}
    unsupported = {int(x) for x in (data.get("unsupported") or [])}

    def _valid(n: int) -> bool:
        return 0 <= n < len(verified_positions)

    # Contradictions / half-truths: always demote, incl. primary sources and lone
    # claims. This is the "check every detail against the government doc" rule.
    contradicted_pos = {verified_positions[n] for n in contradicted if _valid(n)}

    # Soft "unsupported": capped, primary-protected, keep >= 1 verified claim.
    soft = [
        verified_positions[n]
        for n in sorted(unsupported)
        if _valid(n)
        and n not in contradicted
        and not claims[verified_positions[n]].tier_1_backed
    ]
    max_soft = int(len(verified_positions) * _MAX_DEMOTE_FRACTION)
    if len(soft) > max_soft:
        log.info("verifier capping soft demotions %d -> %d", len(soft), max_soft)
        soft = soft[:max_soft]
    survivors = [
        p for p in verified_positions if p not in contradicted_pos and p not in soft
    ]
    if not survivors and soft:
        # never reject a story purely on a borderline (soft) call - keep one
        soft = soft[1:]

    for pos in contradicted_pos:
        claims[pos].verified = False
        _append_note(claims[pos], "contradicts cited source")
    for pos in soft:
        _append_note(claims[pos], "not supported by cited source")
        claims[pos].verified = False
    return claims


def _append_note(claim: VerifiedClaim, suffix: str) -> None:
    claim.note = f"{claim.note}; {suffix}" if claim.note else suffix


def verify_claims(
    claims: list[ClaimDraft],
    docs: list[SourceDoc],
    backend: LLMBackend | None = None,
) -> list[VerifiedClaim]:
    by_id = {d.id: d for d in docs}
    out = [_deterministic(c, by_id) for c in claims]
    if backend is not None and not backend.is_local:
        out = _semantic_demote(out, docs, backend)
    return out
