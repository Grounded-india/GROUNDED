"""Crew orchestrator - runs the five agents sequentially for one event.

Each agent role is routed to its assigned model (see ``router.py``): Nemotron for
extraction/context/perspective, Gemini for verification/editing, with a local
offline fallback. Every stage is recorded in ``agent_trace`` (including which
model ran it and the story mode) so a finished story can be audited end to end.

Story mode:
  * ``report`` - the event is a straightforward reporting of facts; no evident
    opposing sides in the source material.
  * ``debate`` - the source material contains explicit opposition, criticism,
    contest, allegation, or dispute keywords; the event is presented as a
    fact-grounded back-and-forth debate.

Mode selection is driven by CONTROVERSY signals in the source content, not by
presence/absence of a primary source. A sports final has no debate. A Cabinet
approval with opposition rebuttal has one. That difference matters more to the
reader than whether PIB has covered it.
"""

from __future__ import annotations

import logging

from grounded.agents.context import build_context
from grounded.agents.editor import audit_and_assemble
from grounded.agents.fact_extractor import extract_claims
from grounded.agents.perspective import build_perspective
from grounded.agents.router import as_router
from grounded.agents.schemas import EventView, SourceDoc, StoryPackage
from grounded.agents.verifier import verify_claims

log = logging.getLogger(__name__)


# Keywords that indicate genuine controversy / opposition / dispute in the
# source material. When any of these appears, the story is presented as a
# debate instead of a plain report. Matched case-insensitively as substrings
# of title+content across all docs for the event.
CONTROVERSY_KEYWORDS: tuple[str, ...] = (
    "opposition", "opposed", "opponent", "rival",
    "critic", "critics", "criticise", "criticised", "criticize", "criticized",
    "criticism", "denounced", "denounce", "condemned", "condemn",
    "accuse", "accused", "accusation", "allegation", "alleged",
    "deny", "denies", "denied", "denial",
    "reject", "rejected", "rejection", "reject the",
    "controversial", "contested", "contest", "dispute", "disputed",
    "backlash", "outrage", "protest", "protests", "protested",
    "hypocrisy", "hypocritical", "hypocrite",
    "u-turn", "flip flop", "flip-flop",
    "contradict", "contradicts", "contradicted", "contradictory",
    "clash", "row", "spat", "war of words", "slam", "slammed",
    "scandal", "cover up", "cover-up",
    "resign", "resignation", "sacked", "dismissed",
    "walkout", "boycott", "no confidence",
)


def _count_controversy_hits(docs: list[SourceDoc]) -> int:
    """Count distinct controversy keywords present across all docs."""
    blob = " \n ".join(f"{d.title or ''} {d.text or ''}" for d in docs).lower()
    return sum(1 for kw in CONTROVERSY_KEYWORDS if kw in blob)


def build_story(event: EventView, docs: list[SourceDoc], backend=None) -> StoryPackage:
    """Run the crew for one event.

    ``backend`` may be ``None`` (default multi-model router), a single
    ``LLMBackend`` (forces every role onto it - used by tests/offline), or a
    router instance.
    """
    if not docs:
        raise ValueError(f"event {event.id} has no source documents")

    router = as_router(backend)

    ex_be = router.for_role("fact_extractor")
    vf_be = router.for_role("verifier")
    ctx_be = router.for_role("context")
    per_be = router.for_role("perspective")
    ed_be = router.for_role("editor")

    has_primary = any(d.is_primary for d in docs)
    controversy_hits = _count_controversy_hits(docs)
    mode = "debate" if controversy_hits >= 1 else "report"
    log.info(
        "event %s: building %s-mode story from %d source(s) [primary=%s, controversy_hits=%d] [%s]",
        event.id, mode, len(docs), has_primary, controversy_hits, (event.title or "")[:60],
    )

    log.info("  [1/5] fact extractor (%s)...", ex_be.name)
    drafts = extract_claims(event, docs, ex_be)
    log.info("  [2/5] verifier (%s) on %d claim(s)...", vf_be.name, len(drafts))
    verified = verify_claims(drafts, docs, backend=vf_be)
    log.info("  [3/5] context (%s)...", ctx_be.name)
    context_md = build_context(event, verified, docs, ctx_be)
    log.info("  [4/5] perspective/debate (%s)...", per_be.name)
    perspective_md = build_perspective(event, verified, docs, per_be)
    log.info("  [5/5] editor/auditor (%s)...", ed_be.name)
    package = audit_and_assemble(
        event, verified, context_md, perspective_md, docs, mode=mode, backend=ed_be
    )
    log.info(
        "  -> %s (%d claim(s) kept)",
        "APPROVED" if package.editor_approved else "REJECTED",
        len(package.claims),
    )

    package.agent_trace = {
        "mode": mode,
        "has_primary": has_primary,
        "controversy_hits": controversy_hits,
        "models": router.summary(),
        "n_sources": len(docs),
        "fact_extractor": {
            "n_claims": len(drafts),
            "claims": [
                {"text": d.text, "source_item_ids": [str(i) for i in d.source_item_ids]}
                for d in drafts
            ],
        },
        "verifier": {
            "verified": sum(1 for c in verified if c.verified),
            "flagged": sum(1 for c in verified if not c.verified),
            "tier_1_backed": sum(1 for c in verified if c.tier_1_backed),
        },
        "context": context_md,
        "perspective": perspective_md,
        "editor": {
            "approved": package.editor_approved,
            "notes": package.editor_notes,
        },
    }
    return package
