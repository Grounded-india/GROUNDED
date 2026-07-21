"""Agent 3 - Context Agent.

Adds grounded background: why this event matters and what led here. Uses only
the supplied sources and verified claims - no outside knowledge - so the context
stays auditable. Local backend produces a short deterministic summary of the
sourcing so the pipeline still yields a usable section offline.
"""

from __future__ import annotations

from collections import Counter

from grounded.agents.llm import LLMBackend
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim

SYSTEM = (
    "You are a news context writer. Using only the provided claims and sources, "
    "write 2-4 sentences of neutral background explaining why this event matters "
    "and what led to it. Do not introduce facts that are not in the sources."
)


def build_prompt(
    event: EventView, claims: list[VerifiedClaim], docs: list[SourceDoc]
) -> str:
    claim_lines = "\n".join(f"- {c.text}" for c in claims if c.verified) or "- (none)"
    source_names = ", ".join(sorted({d.source_name for d in docs}))
    return (
        f"EVENT: {event.title}\n\n"
        f"VERIFIED CLAIMS:\n{claim_lines}\n\n"
        f"SOURCES: {source_names}\n\n"
        "Write the background/context section as plain prose (no markdown heading)."
    )


def _local_context(event: EventView, docs: list[SourceDoc]) -> str:
    tiers = Counter(d.source_tier.name.lower() for d in docs)
    breakdown = ", ".join(f"{n} {tier}" for tier, n in sorted(tiers.items()))
    outlets = sorted({d.source_name for d in docs})
    outlet_str = ", ".join(outlets[:6]) + (" and others" if len(outlets) > 6 else "")
    return (
        f"This story is reconstructed from {len(docs)} source item(s) "
        f"({breakdown}) across {len(outlets)} outlet(s): {outlet_str}. "
        "Background is limited to what these sources report; no outside "
        "information has been added."
    )


def build_context(
    event: EventView,
    claims: list[VerifiedClaim],
    docs: list[SourceDoc],
    backend: LLMBackend,
) -> str:
    if backend.is_local:
        return _local_context(event, docs)
    # Real backend: use it or fail loudly - no silent local substitution.
    return backend.complete(
        system=SYSTEM,
        user=build_prompt(event, claims, docs),
        max_tokens=600,
        temperature=0.3,
    ).strip()
