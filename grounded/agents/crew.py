"""Crew orchestrator - runs the five agents sequentially for one event.

Each agent role is routed to its assigned model (see ``router.py``): Nemotron for
extraction/context/perspective, Gemini for verification/editing, with a local
offline fallback. Every stage is recorded in ``agent_trace`` (including which
model ran it and the story mode) so a finished story can be audited end to end.

Story mode:
  * ``report`` - the event has a primary/official source; standard write-up.
  * ``debate`` - no primary source (ground-reality, e.g. Reddit); the event is
    presented as a two-sided, fact-grounded debate instead of being dropped.
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
    mode = "report" if has_primary else "debate"
    log.info("building %s-mode story for event %s", mode, event.id)

    drafts = extract_claims(event, docs, ex_be)
    verified = verify_claims(drafts, docs, backend=vf_be)
    context_md = build_context(event, verified, docs, ctx_be)
    perspective_md = build_perspective(event, verified, docs, per_be)
    package = audit_and_assemble(
        event, verified, context_md, perspective_md, docs, mode=mode, backend=ed_be
    )

    package.agent_trace = {
        "mode": mode,
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
