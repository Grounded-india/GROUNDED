"""Top-level Layer 3 entry: load selected events -> run crew -> persist stories."""

from __future__ import annotations

import logging
from uuid import UUID

from grounded.agents.crew import build_story
from grounded.agents.loader import load_events_needing_stories
from grounded.agents.router import as_router
from grounded.agents.schemas import StoryPackage
from grounded.agents.store import save_story

log = logging.getLogger(__name__)


def _save_failure_stub(event_id: UUID, reason: str) -> None:
    """Persist a rejected stub for a crew failure so the event does not get
    re-picked by ``load_events_needing_stories`` on the next top-up pass.

    Without this, a transient LLM 404 or timeout would leave the event
    SELECTED-without-a-story, and every subsequent ``build_stories()`` call
    would re-attempt it — the candidate pool would snowball each pass.
    """
    try:
        save_story(
            StoryPackage(
                event_id=event_id,
                headline="",
                dek="",
                body_markdown="",
                claims=[],
                editor_approved=False,
                editor_notes=f"crew failed: {reason}",
                agent_trace={"failure_reason": reason},
            )
        )
    except Exception:
        log.exception("could not persist failure stub for event %s", event_id)


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

    built = approved = rejected = skipped = failed = debates = 0
    for idx, (event, docs) in enumerate(work, start=1):
        log.info("=== event %d/%d ===", idx, len(work))
        if not docs:
            log.warning("event %s has no sources; skipping", event.id)
            skipped += 1
            continue
        # Isolate per-event failures (e.g. a provider truncating a response beyond
        # recovery) so one bad event doesn't abort the whole batch. The failure is
        # logged loudly and counted - it is not silently swallowed or faked.
        try:
            package = build_story(event, docs, router)
            save_story(package)
        except Exception as e:
            log.exception("event %s failed; skipping to next", event.id)
            _save_failure_stub(event.id, f"{type(e).__name__}: {e}"[:400])
            failed += 1
            continue
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
        "failed": failed,
    }
