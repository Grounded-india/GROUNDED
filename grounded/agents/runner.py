"""Top-level Layer 3 entry: load selected events -> run crew -> persist stories."""

from __future__ import annotations

import logging
from uuid import UUID

from grounded.agents.crew import build_story
from grounded.agents.loader import load_events_needing_stories
from grounded.agents.router import as_router
from grounded.agents.store import save_story

log = logging.getLogger(__name__)


def build_stories(
    *,
    force: bool = False,
    limit: int | None = None,
    event_id: UUID | None = None,
    backend=None,
) -> dict:
    """Build (and persist) stories for selected events.

    ``backend`` may be ``None`` (multi-model router from env), a single
    ``LLMBackend``, or a router. Returns a summary dict with counts and the
    per-role model map that was used.
    """
    router = as_router(backend)
    work = load_events_needing_stories(force=force, limit=limit, event_id=event_id)

    models = ", ".join(f"{r}={n}" for r, n in router.summary().items())
    log.info("model routing: %s", models)
    log.info("processing %d candidate event(s)", len(work))

    built = approved = rejected = skipped = debates = 0
    for idx, (event, docs) in enumerate(work, start=1):
        log.info("=== event %d/%d ===", idx, len(work))
        if not docs:
            log.warning("event %s has no sources; skipping", event.id)
            skipped += 1
            continue
        package = build_story(event, docs, router)
        save_story(package)
        built += 1
        if package.agent_trace.get("mode") == "debate":
            debates += 1
        if package.editor_approved:
            approved += 1
        else:
            rejected += 1

    return {
        "models": router.summary(),
        "candidates": len(work),
        "built": built,
        "approved": approved,
        "rejected": rejected,
        "debates": debates,
        "skipped": skipped,
    }
