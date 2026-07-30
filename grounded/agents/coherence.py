"""End-of-pipeline coherence check.

Catches stories where the headline / dek do not describe the article body — the
symptom of a Layer-2 clustering bug that merges two unrelated events into one
cluster, tags it with the title of one, and lets the reporter write the body
from the sources of the other. Real example from 07-29: headline was
"U.S. and Saudi Arabia Strike Iran-Backed Militia Sites in Iraq" but the body
was entirely about a 7.1-magnitude earthquake in Japan.

Runs a two-stage repair:

1. **Check** — send Gemini the story headline, dek, and (truncated)
   ``body_markdown`` and ask whether they describe the same event.
2. **Repair** — if incoherent, ask Gemini to write a new headline + dek
   grounded in the body. Re-check the rewritten pair; if still incoherent,
   the body itself is a jumbled mix (rewrite cannot help), so drop the
   story by setting ``editor_approved = FALSE``.

Failure isolation: Gemini errors are non-fatal. A story that cannot be
checked keeps its current headline/dek and remains approved (i.e. the
coherence pass never makes a story worse than it already was).
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from grounded.agents.llm import extract_json, make_gemini
from grounded.db import cursor

# Gemini free tier caps at 15 requests / minute per model. The coherence check
# is 1 call per story (2 if a rewrite happens); a 20-story edition needs
# roughly 25 calls, so sleeping 4.5s between iterations keeps us comfortably
# under the ceiling instead of burning through retries.
_INTER_STORY_SLEEP_SECONDS = 4.5

log = logging.getLogger(__name__)


# Cap on body characters sent to the LLM. The Layer-3 reporter caps its
# output around 700 words, so 2000 chars comfortably covers the lede + first
# two paragraphs — enough for the LLM to tell whether the body is on-topic
# without paying for every subsequent paragraph.
_BODY_CHARS = 2000


_CHECK_SYSTEM = (
    "You are a copy editor auditing a news story for internal coherence. Given "
    "a headline, dek, and the opening of the body, decide whether the headline "
    "and dek describe the SAME event the body is actually reporting on.\n"
    "\n"
    "COHERENT — the body's lede and main narrative are about the event the "
    "headline names. Minor tangents or 'meanwhile in ...' segments in later "
    "paragraphs are fine; the story is coherent if the primary subject aligns.\n"
    "\n"
    "INCOHERENT — the body opens with and primarily narrates a different event "
    "than the headline names (different actor, different location, different "
    "incident). This is the symptom of a clustering bug that merged two events; "
    "the reader would be badly misled.\n"
    "\n"
    "Respond only with JSON."
)


_REWRITE_SYSTEM = (
    "You are a news copy editor. The current headline and dek do not match the "
    "article body. Rewrite them to accurately describe what the body is actually "
    "reporting on. Ground every word in the body — do not invent details, "
    "numbers, quotes, or attributions the body does not contain. Neutral voice, "
    "factual, non-sensational.\n"
    "\n"
    "Respond only with JSON."
)


def _load_approved_stories() -> list[dict]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT id, headline, dek, body_markdown
            FROM stories
            WHERE editor_approved = TRUE
              AND body_markdown IS NOT NULL
              AND length(body_markdown) > 200
            ORDER BY created_at DESC
            """
        )
        return list(cur.fetchall())


def _check_coherent(
    backend, headline: str, dek: str, body: str
) -> tuple[bool, str]:
    """Return (coherent, reason)."""
    user = (
        f"HEADLINE: {headline}\n"
        f"DEK: {dek}\n"
        f"BODY (opening):\n{body[:_BODY_CHARS]}\n\n"
        'Return JSON: {"coherent": true | false, "reason": "<one short sentence naming the two subjects if incoherent, or confirming the match if coherent>"}'
    )
    raw = backend.complete(
        system=_CHECK_SYSTEM,
        user=user,
        max_tokens=200,
        temperature=0.0,
        json_mode=True,
    )
    data = extract_json(raw)
    if not isinstance(data, dict):
        raise ValueError(f"unexpected shape: {data!r}")
    return bool(data.get("coherent")), str(data.get("reason") or "").strip()[:300]


def _rewrite_headline(
    backend, current_headline: str, current_dek: str, body: str
) -> tuple[str, str]:
    """Ask the LLM for a corrected headline+dek that matches the body."""
    user = (
        f"CURRENT (broken) HEADLINE: {current_headline}\n"
        f"CURRENT (broken) DEK: {current_dek}\n\n"
        f"ARTICLE BODY (this is the source of truth):\n{body[:_BODY_CHARS]}\n\n"
        'Return JSON: {"headline": "...", "dek": "..."}'
    )
    raw = backend.complete(
        system=_REWRITE_SYSTEM,
        user=user,
        max_tokens=250,
        temperature=0.2,
        json_mode=True,
    )
    data = extract_json(raw)
    if not isinstance(data, dict):
        raise ValueError(f"unexpected shape: {data!r}")
    return (
        str(data.get("headline") or "").strip(),
        str(data.get("dek") or "").strip(),
    )


def _apply_rewrite(story_id: UUID, headline: str, dek: str, note: str) -> None:
    with cursor() as cur:
        cur.execute(
            """
            UPDATE stories
            SET headline = %s,
                dek = %s,
                editor_notes = COALESCE(editor_notes, '') || '; ' || %s
            WHERE id = %s
            """,
            (headline, dek, note[:300], story_id),
        )


def _apply_drop(story_id: UUID, note: str) -> None:
    with cursor() as cur:
        cur.execute(
            """
            UPDATE stories
            SET editor_approved = FALSE,
                editor_notes = COALESCE(editor_notes, '') || '; ' || %s
            WHERE id = %s
            """,
            (note[:300], story_id),
        )


def check_and_repair_coherence() -> dict:
    """Two-stage coherence pass over every approved story.

    Rewrites headline+dek where the LLM finds a mismatch; drops the story
    when the rewrite itself remains incoherent (body is a genuine mix).
    Gemini errors are non-fatal — the story is left as-is on error.
    """
    backend = make_gemini()
    if backend is None or getattr(backend, "is_local", False):
        log.warning("coherence: no Gemini backend; skipping")
        return {"stories": 0, "coherent": 0, "rewritten": 0, "dropped": 0, "errors": 0}

    stories = _load_approved_stories()
    coherent_count = rewritten = dropped = errors = 0

    for idx, s in enumerate(stories):
        if idx > 0:
            time.sleep(_INTER_STORY_SLEEP_SECONDS)
        story_id = s["id"]
        headline = s["headline"] or ""
        dek = s["dek"] or ""
        body = s["body_markdown"] or ""

        try:
            ok, reason = _check_coherent(backend, headline, dek, body)
        except Exception as e:
            log.warning("coherence check failed for %s: %s", headline[:60], e)
            errors += 1
            continue

        if ok:
            coherent_count += 1
            log.info("[coherent]   %s", headline[:80])
            continue

        log.info("[incoherent] %s — %s", headline[:60], reason)

        # Stage 2: rewrite, then re-check the rewrite.
        try:
            new_headline, new_dek = _rewrite_headline(backend, headline, dek, body)
        except Exception as e:
            log.warning("coherence rewrite failed for %s: %s", headline[:60], e)
            errors += 1
            continue

        if not new_headline or not new_dek:
            log.warning("rewrite empty for %s; dropping", headline[:60])
            _apply_drop(
                story_id,
                f"COHERENCE: dropped — rewrite empty; original: {reason}",
            )
            dropped += 1
            continue

        try:
            ok2, reason2 = _check_coherent(backend, new_headline, new_dek, body)
        except Exception as e:
            # Rewrite happened but re-check errored: accept the rewrite rather
            # than drop, since the incoherent original is worse than the
            # unverified rewrite.
            log.warning(
                "coherence re-check errored for %s (accepting rewrite): %s",
                headline[:60], e,
            )
            _apply_rewrite(
                story_id, new_headline, new_dek,
                f"COHERENCE: headline rewritten (re-check errored); original: {reason}",
            )
            rewritten += 1
            continue

        if ok2:
            _apply_rewrite(
                story_id, new_headline, new_dek,
                f"COHERENCE: headline rewritten to match body; original mismatch: {reason}",
            )
            rewritten += 1
            log.info("[rewritten]  -> %s", new_headline[:80])
        else:
            _apply_drop(
                story_id,
                f"COHERENCE: dropped — rewrite still incoherent ({reason2}); original mismatch: {reason}",
            )
            dropped += 1
            log.info("[dropped]    rewrite still incoherent: %s", reason2)

    return {
        "stories": len(stories),
        "coherent": coherent_count,
        "rewritten": rewritten,
        "dropped": dropped,
        "errors": errors,
    }
