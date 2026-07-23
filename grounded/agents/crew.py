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
from grounded.agents.reporter import build_report
from grounded.agents.router import as_router
from grounded.agents.schemas import EventView, SourceDoc, StoryPackage
from grounded.agents.verifier import verify_claims

log = logging.getLogger(__name__)


# Cheap keyword pre-filter — a broad hint that a story MIGHT be contested.
# This is not the decision: any candidate that hits a keyword goes through
# the LLM validator (:func:`_decide_mode`), which actually reads the source
# material and rules on whether a debate is warranted. The keyword list is
# deliberately generous so we don't miss real debates; the LLM prunes the
# false positives.
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

_CONTROVERSY_HIT_THRESHOLD = 1  # any hit = candidate; LLM makes the actual call


def _count_controversy_hits(docs: list[SourceDoc]) -> int:
    """Count distinct controversy keywords present across all docs."""
    blob = " \n ".join(f"{d.title or ''} {d.text or ''}" for d in docs).lower()
    return sum(1 for kw in CONTROVERSY_KEYWORDS if kw in blob)


_MODE_SYSTEM = (
    "You classify Indian news stories into DEBATE-format or REPORT-format. "
    "Return valid JSON only, no prose outside the object."
)

_MODE_USER_TEMPLATE = (
    "EVENT: __TITLE__\n\n"
    "SOURCE SNIPPETS:\n__SNIPPETS__\n\n"
    "You are deciding whether this Indian news event should be presented as a "
    "DEBATE (two actors argue their sides) or a REPORT (single-narrative "
    "reporting of facts).\n\n"
    "DEBATE — the sources contain TWO distinct actors/coalitions with "
    "CONFLICTING positions on the same question, AND each side has enough "
    "material in the sources for a debater to argue their position for a "
    "few paragraphs. Typical actor pairs: government vs opposition, "
    "protesters vs police, ministry vs court, party A vs party B, employer "
    "vs union, activists vs establishment, defenders vs critics. The "
    "'weaker side' does not need a wall of quotes — a coherent stated "
    "position with at least one substantive reason or counter-claim is "
    "enough. Denial + reasoning counts. Bare denial without reasoning "
    "does not.\n\n"
    "REPORT — a single-narrative event with no genuinely opposing actors "
    "represented in the material. Examples: a scheme was announced (no "
    "critic in the sources), a minister inaugurated a project, an "
    "accident occurred, a person died, a sports result, an obituary, a "
    "government readout with no rebuttal.\n\n"
    "DEFAULT — when in genuine doubt on a story that clearly has "
    "controversy signals (protest, allegation, dispute, denial, crackdown, "
    "condemnation), pick DEBATE. The reader benefits more from a two-sided "
    "presentation of a contested event than a one-sided report.\n\n"
    'Return JSON: {"mode": "debate" | "report", "reason": "<one short sentence identifying the two sides or explaining why only one exists>"}'
)


def _decide_mode(
    event: EventView, docs: list[SourceDoc], backend
) -> tuple[str, str]:
    """Two-stage mode decision: cheap keyword pre-filter, then LLM validator.

    Stage 1 — count distinct controversy keywords. If below threshold, the
    story is definitely a REPORT (skip the LLM call entirely — saves budget on
    the majority of daily events, which are single-narrative).

    Stage 2 — for the candidates that pass the pre-filter, ask an LLM whether
    the sources actually contain substantive opposing actors. The LLM's answer
    is final; keyword hits alone never promote to debate.

    Fallback path — if the LLM is unavailable (local backend) or the call
    errors, hedge to whatever the keyword pre-filter suggested: pre-filter
    hits → debate (preserve legacy offline behaviour); no hits → report.
    """
    hits = _count_controversy_hits(docs)
    if hits < _CONTROVERSY_HIT_THRESHOLD:
        return "report", f"no substantive controversy signal ({hits} keyword hit(s))"

    if backend is None or getattr(backend, "is_local", False):
        return "debate", f"keyword pre-filter ({hits} hits); no LLM validator available"

    from grounded.agents.llm import extract_json

    snippets = "\n---\n".join(
        f"[{d.source_name}] {(d.title or '').strip()}\n"
        f"{(d.text or '').strip()[:400]}"
        for d in docs[:6]
    )
    # Use plain .replace instead of str.format so the JSON example in the
    # template ('{"mode": ...}') is not read as a format placeholder.
    user = _MODE_USER_TEMPLATE.replace(
        "__TITLE__", (event.title or "")[:200]
    ).replace("__SNIPPETS__", snippets)
    try:
        raw = backend.complete(
            system=_MODE_SYSTEM,
            user=user,
            max_tokens=200,
            temperature=0.0,
            json_mode=True,
        )
        data = extract_json(raw)
        if not isinstance(data, dict):
            return "debate", f"LLM returned non-object; kept keyword verdict ({hits} hits)"
        mode = str(data.get("mode") or "").strip().lower()
        reason = str(data.get("reason") or "").strip()[:200]
        if mode not in ("debate", "report"):
            return "debate", f"LLM returned unknown mode {mode!r}; kept keyword verdict"
        return mode, reason or f"{hits} keyword hits; LLM classified as {mode}"
    except Exception as e:
        log.warning("mode classifier failed (%s); keeping keyword verdict", e)
        return "debate", f"validator error: {e}; kept keyword verdict ({hits} hits)"


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
    # Two-stage decision: cheap keyword pre-filter (drops obvious reports),
    # then LLM validator (checks the survivors for substantive opposing sides).
    # The LLM uses the editor backend (Gemini) since it's a small structured
    # JSON call and Gemini is fast + cheap for that.
    mode, mode_reason = _decide_mode(event, docs, ed_be)
    log.info(
        "event %s: building %s-mode story from %d source(s) [primary=%s] [%s] — %s",
        event.id, mode, len(docs), has_primary, (event.title or "")[:60], mode_reason,
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

    # REPORT mode: run the dedicated reporter to produce a long-form article
    # body. Only for approved reports (skip if editor rejected — the story
    # will be filtered out downstream anyway).
    if mode == "report" and package.editor_approved:
        rp_be = router.for_role("reporter")
        log.info("  [+report] reporter (%s)...", rp_be.name)
        report_body = build_report(event, package.claims, context_md, docs, rp_be)
        if report_body:
            package.body_markdown = report_body

    package.agent_trace = {
        "mode": mode,
        "mode_reason": mode_reason,
        "has_primary": has_primary,
        "controversy_hits": _count_controversy_hits(docs),
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
