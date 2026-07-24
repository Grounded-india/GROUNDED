"""Agent 7 — post-build deduplication pass.

Layer 2 clusters raw items into events (single-linkage on cosine similarity +
time window). That works well within a single narrative but occasionally
splits the *same real-world story* into two or three events when different
outlets frame it differently — e.g. a protest march event and a police
crackdown event about the same protest end up in different clusters because
the two framings only share partial vocabulary.

This module runs after Layer 3 has finished building, catches those cases at
the story level, and merges duplicates so the reader does not see "the same
thing in different clothes" twice in one edition.

Two-stage design (same pattern as the mode classifier):
  1. **Embedding pre-filter** — embed all approved-story headlines via
     Voyage in a single batch, compare pairwise, only pairs with cosine
     similarity >= a threshold are considered candidates for dedup.
  2. **LLM validator** — for each candidate pair, ask Gemini "are these two
     stories about the same real-world event, just framed differently?
     YES/NO". Only YES gets deduped.

When two stories are judged the same story:
  * Keep the one with the higher event importance score.
  * Mark the other ``editor_approved = FALSE`` and append a note to
    ``editor_notes`` so the audit trail explains why. Rejected stories
    naturally fall out of the edition renderer (which filters on
    ``editor_approved``).

Fully idempotent: running the deduper twice on the same DB produces the same
outcome, because the second pass sees fewer approved stories and no new
pairs cross the threshold.
"""

from __future__ import annotations

import json
import logging

import numpy as np

from grounded.agents.llm import extract_json, make_gemini
from grounded.db import cursor
from grounded.pipeline.embed import get_backend as _get_embedding_backend

log = logging.getLogger(__name__)

_HEADLINE_SIMILARITY_THRESHOLD = 0.80
_LLM_SYSTEM = (
    "You judge whether two news story headlines and lede paragraphs describe "
    "the SAME real-world event (possibly with different framing / different "
    "quotes / different angle) or DIFFERENT events. Return JSON only."
)


def _load_approved_stories() -> list[dict]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.event_id, s.headline, s.dek, s.body_markdown,
                   s.editor_notes,
                   COALESCE(e.importance_score, 0.0) AS importance
            FROM stories s
            LEFT JOIN events e ON e.id = s.event_id
            WHERE s.editor_approved = TRUE
            ORDER BY e.importance_score DESC NULLS LAST, s.id
            """
        )
        return list(cur.fetchall())


def _embed_headlines(stories: list[dict]) -> np.ndarray:
    """One embedding call for all headlines. L2-normalised rows."""
    backend = _get_embedding_backend()
    texts = [
        f"{(s['headline'] or '').strip()}. {(s['dek'] or '').strip()}"
        for s in stories
    ]
    vecs = np.array(backend.embed(texts), dtype=float)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def _ask_llm_same_story(a: dict, b: dict, backend) -> bool:
    """Return True if the LLM says a and b are the same real-world story."""
    body_a = (a.get("body_markdown") or "")[:500]
    body_b = (b.get("body_markdown") or "")[:500]
    user = (
        f"STORY A:\nHeadline: {a['headline']}\nDek: {a.get('dek') or ''}\n"
        f"Body excerpt: {body_a}\n\n"
        f"STORY B:\nHeadline: {b['headline']}\nDek: {b.get('dek') or ''}\n"
        f"Body excerpt: {body_b}\n\n"
        "Are these two stories about the SAME real-world event (same "
        "underlying happening), just framed differently or reported from a "
        "different angle? Consider them 'same' if a reasonable reader would "
        'say "I already read this". Return JSON: {"same": true | false, '
        '"reason": "<one short sentence>"}'
    )
    try:
        raw = backend.complete(
            system=_LLM_SYSTEM,
            user=user,
            max_tokens=150,
            temperature=0.0,
            json_mode=True,
        )
        data = extract_json(raw)
        if isinstance(data, dict):
            return bool(data.get("same"))
    except Exception as e:
        log.warning("deduper LLM call failed for pair (%s, %s): %s", a["id"], b["id"], e)
    return False


def _reject_story(story_id, kept_headline: str) -> None:
    note = f"deduped: same story as \"{kept_headline}\" — dropped in favour of higher-ranked version"
    with cursor() as cur:
        cur.execute(
            """
            UPDATE stories
            SET editor_approved = FALSE,
                editor_notes = COALESCE(editor_notes || ' | ', '') || %s
            WHERE id = %s
            """,
            (note, story_id),
        )


def dedupe_stories(similarity_threshold: float | None = None) -> dict:
    """Run the two-stage dedup pass over all currently-approved stories.

    Returns a summary: ``{"pairs_checked": n, "dropped": n}``.
    """
    threshold = similarity_threshold or _HEADLINE_SIMILARITY_THRESHOLD
    stories = _load_approved_stories()
    if len(stories) < 2:
        log.info("dedupe: %d approved stor(y/ies); nothing to do", len(stories))
        return {"pairs_checked": 0, "dropped": 0}

    # Stage 1: embedding similarity pre-filter.
    vecs = _embed_headlines(stories)
    sim = vecs @ vecs.T
    n = len(stories)
    # Upper-triangle pairs above the threshold, sorted highest-similarity first.
    candidates: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= threshold:
                candidates.append((i, j, float(sim[i, j])))
    candidates.sort(key=lambda t: -t[2])
    log.info("dedupe: %d candidate pair(s) at similarity >= %.2f", len(candidates), threshold)
    if not candidates:
        return {"pairs_checked": 0, "dropped": 0}

    # Stage 2: LLM validator. Keep the higher-importance story on each YES.
    llm_backend = make_gemini()
    dropped_ids: set = set()
    pairs_checked = 0
    for i, j, sim_score in candidates:
        a, b = stories[i], stories[j]
        if a["id"] in dropped_ids or b["id"] in dropped_ids:
            continue  # already handled via a transitive merge
        pairs_checked += 1
        if llm_backend is None:
            # No LLM available — high-similarity is enough to dedupe. Rare,
            # since publish flow always has Gemini configured.
            same = sim_score >= 0.92
        else:
            same = _ask_llm_same_story(a, b, llm_backend)
        if not same:
            continue
        # Keep the higher-importance one; if tied, keep A (already earlier in sort).
        keeper, dropper = (a, b) if a["importance"] >= b["importance"] else (b, a)
        _reject_story(dropper["id"], keeper["headline"])
        dropped_ids.add(dropper["id"])
        log.info(
            "dedupe: dropped %s (kept %s) — cosine %.2f",
            (dropper["headline"] or "")[:60],
            (keeper["headline"] or "")[:60],
            sim_score,
        )

    log.info("dedupe done: %d pair(s) checked by LLM, %d stor(y/ies) dropped",
             pairs_checked, len(dropped_ids))
    return {"pairs_checked": pairs_checked, "dropped": len(dropped_ids)}
