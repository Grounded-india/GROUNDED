"""Agent 5 - Editor / Hallucination Auditor.

Deterministic gate first, Gemini second (and only to make things stricter):

* Ungrounded claims are always cut.
* Optional Gemini audit (when a backend is supplied) may cut additional claims -
  it can never re-approve a cut claim. It separates two cases:
    - ``contradicted`` (conflicts with the source, or states a detail the source
      never contains - a half-truth): ALWAYS cut, even a primary/government cite,
      even the only claim. Half-lies must never reach the reader.
    - ``unsupported`` (no direct conflict, just not clearly backed): cut subject to
      anti-over-pruning caps so a borderline model call cannot gut a story.
* Approval rule depends on the story mode:
    - ``report``  : needs >= 1 GROUNDED claim (traceable to a source, not
                    hallucinated). Cross-source "verified" status is a
                    quality signal shown to the reader but NOT an approval
                    gate — a single-source Indian Express or Newslaundry
                    piece is still worth publishing.
    - ``debate``  : ground-reality event with no primary source; approved when it
                    has >= 1 grounded point and presented as a two-sided debate
                    rather than rejected.

It then assembles the citation-rich markdown body.
"""

from __future__ import annotations

import logging
from uuid import UUID

from grounded.agents.llm import LLMBackend, extract_json
from grounded.agents.schemas import EventView, SourceDoc, StoryPackage, VerifiedClaim

log = logging.getLogger(__name__)

MIN_VERIFIED_CLAIMS = 1

# Anti-over-pruning cap for SOFT ("unsupported") cuts only. Contradictions /
# half-truths are never subject to this cap - they are always cut. The cap stops a
# borderline model call from gutting a story:
#   * a soft cut never removes a primary (tier-1) anchored claim
#   * a soft cut is bounded to this fraction of grounded claims and skipped for a
#     one-claim story, and never removes the story's last verified claim
_MAX_CUT_FRACTION = 0.5

_AUDIT_SYSTEM = (
    "You are a final hallucination auditor guarding against half-truths. For each "
    "numbered claim, compare it against the cited SOURCE TEXT at the level of every "
    "specific detail (numbers, dates, names, amounts, scope, qualifiers). Classify "
    "each claim as 'contradicted' (conflicts with the source, or asserts a detail "
    "the source never states - even for an official/government source) or "
    "'unsupported' (not clearly backed, but no direct conflict). Respond only with "
    "JSON."
)
_HEADLINE_SYSTEM = (
    "You are a news copy editor. Write a factual, non-sensational headline and a "
    "one-sentence dek grounded strictly in the given facts. Respond only with JSON."
)


def _cite(ids: list[UUID], by_id: dict[UUID, SourceDoc]) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for i in ids:
        doc = by_id.get(i)
        if not doc or doc.source_name in seen:
            continue
        seen.add(doc.source_name)
        parts.append(f"[{doc.source_name}]({doc.source_url})")
    return ", ".join(parts)


def _llm_cut(
    claims: list[VerifiedClaim], docs: list[SourceDoc], backend: LLMBackend
) -> list[VerifiedClaim]:
    by_id = {d.id: d for d in docs}
    if not claims:
        return claims

    entries = []
    for n, c in enumerate(claims):
        src = " || ".join(
            f"{by_id[j].source_name}: {(by_id[j].text or '')[:300]}"
            for j in c.source_item_ids
            if j in by_id
        )
        entries.append(f"{n}. CLAIM: {c.text}\n   SOURCE TEXT: {src}")
    user = (
        "Check each claim against its cited source text at the level of every "
        "specific detail.\n\n"
        + "\n\n".join(entries)
        + '\n\nReturn JSON: {"contradicted": [<indices that conflict with the source '
        'or assert details the source never states>], "unsupported": [<indices not '
        "clearly backed but without direct conflict>]}"
    )
    # Real backend only (callers gate on is_local): run it or fail loudly.
    data = extract_json(
        backend.complete(
            system=_AUDIT_SYSTEM, user=user, max_tokens=400, temperature=0.0, json_mode=True
        )
    )
    # Gemini sometimes returns just a JSON list at the top level instead of the
    # requested {"contradicted": [...], "unsupported": [...]} object. Treat a
    # bare list as "these indices are contradicted; nothing extra unsupported".
    if isinstance(data, list):
        data = {"contradicted": data, "unsupported": []}
    elif not isinstance(data, dict):
        data = {"contradicted": [], "unsupported": []}
    contradicted = {int(x) for x in (data.get("contradicted") or []) if str(x).lstrip("-").isdigit()}
    unsupported = {int(x) for x in (data.get("unsupported") or []) if str(x).lstrip("-").isdigit()}

    n = len(claims)
    # Contradictions / half-truths: always cut, incl. primary sources and lone
    # claims. Presenting a false detail is the harm we most want to prevent.
    cut = {i for i in contradicted if 0 <= i < n}

    # Soft "unsupported": primary-protected, capped, and skipped on one-claim
    # stories so a borderline call cannot gut a thin story.
    if n >= 2:
        soft = [
            i
            for i in unsupported
            if 0 <= i < n and i not in cut and not claims[i].tier_1_backed
        ]
        max_cuts = int(n * _MAX_CUT_FRACTION)
        if len(soft) > max_cuts:
            soft = sorted(soft, key=lambda i: (claims[i].verified, i))[:max_cuts]
            log.info("editor capping soft cuts to %d of %d claims", max_cuts, n)
        cut |= set(soft)

    # A soft cut must never remove the story's last verified claim; a contradiction
    # still can (a story that is only a half-lie should be dropped).
    verified_positions = [i for i, c in enumerate(claims) if c.verified]
    if verified_positions and all(i in cut for i in verified_positions):
        restorable = [i for i in verified_positions if i not in contradicted]
        if restorable:
            cut.discard(restorable[0])

    return [c for i, c in enumerate(claims) if i not in cut]


def _llm_headline(
    event: EventView, claims: list[VerifiedClaim], backend: LLMBackend
) -> tuple[str, str]:
    facts = "\n".join(f"- {c.text}" for c in claims[:6]) or f"- {event.title}"
    raw = backend.complete(
        system=_HEADLINE_SYSTEM,
        user=f"EVENT: {event.title}\nFACTS:\n{facts}\n\n"
        'Return JSON: {"headline": "...", "dek": "..."}',
        max_tokens=200,
        temperature=0.3,
        json_mode=True,
    )
    data = extract_json(raw)
    headline = str(data.get("headline") or "").strip() or event.title
    dek = str(data.get("dek") or "").strip()
    return headline, dek


def _assemble_markdown(
    *,
    headline: str,
    dek: str,
    mode: str,
    verified: list[VerifiedClaim],
    flagged: list[VerifiedClaim],
    grounded: list[VerifiedClaim],
    context_md: str,
    perspective_md: str,
    docs: list[SourceDoc],
    by_id: dict[UUID, SourceDoc],
) -> str:
    lines = [f"# {headline}", "", f"*{dek}*", ""]

    if mode == "debate":
        lines += [
            "> No primary or official source backs this event; it is presented as a "
            "fact-based debate rather than as confirmed reporting.",
            "",
            "## Debate",
            perspective_md.strip() or "_No debate could be constructed._",
            "",
            "## Reported points (grounded, unverified)",
        ]
        if grounded:
            for c in grounded:
                lines.append(f"- {c.text} — {_cite(c.source_item_ids, by_id)}")
        else:
            lines.append("- _No grounded points._")
        lines.append("")
        if context_md.strip():
            lines += ["## Context", context_md.strip(), ""]
    else:
        lines.append("## What we know")
        if verified:
            for c in verified:
                lines.append(f"- {c.text} — {_cite(c.source_item_ids, by_id)}")
        else:
            lines.append("- _No claims cleared verification._")
        lines.append("")

        if flagged:
            lines.append("## Flagged — single-source / unverified")
            for c in flagged:
                lines.append(f"- {c.text} — {_cite(c.source_item_ids, by_id)} _({c.note})_")
            lines.append("")

        if context_md.strip():
            lines += ["## Context", context_md.strip(), ""]
        if perspective_md.strip():
            lines += ["## Perspectives", perspective_md.strip(), ""]

    lines.append("## Sources")
    for d in sorted(docs, key=lambda d: (int(d.source_tier), d.source_name)):
        lines.append(f"- [{d.source_name}]({d.source_url}) — tier {int(d.source_tier)}")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def audit_and_assemble(
    event: EventView,
    claims: list[VerifiedClaim],
    context_md: str,
    perspective_md: str,
    docs: list[SourceDoc],
    *,
    mode: str = "report",
    backend: LLMBackend | None = None,
) -> StoryPackage:
    by_id = {d.id: d for d in docs}

    grounded = [c for c in claims if c.source_item_ids]
    dropped = len(claims) - len(grounded)

    if backend is not None and not backend.is_local:
        before = len(grounded)
        grounded = _llm_cut(grounded, docs, backend)
        dropped += before - len(grounded)

    verified = [c for c in grounded if c.verified]
    flagged = [c for c in grounded if not c.verified]

    if mode == "debate":
        approved = len(grounded) >= 1
    else:
        # REPORT approves on GROUNDED, not verified. See module docstring.
        # Cross-source verification is shown as a quality signal, not a gate.
        approved = len(grounded) >= MIN_VERIFIED_CLAIMS

    notes: list[str] = [f"mode={mode}"]
    if dropped:
        notes.append(f"cut {dropped} unsupported/ungrounded claim(s)")
    if mode == "debate":
        if approved:
            notes.append(f"presented as debate on {len(grounded)} grounded point(s)")
        else:
            notes.append("rejected: no grounded points to debate")
    else:
        if flagged:
            notes.append(f"{len(flagged)} claim(s) single-source (kept, marked)")
        if approved:
            notes.append(
                f"approved on {len(grounded)} grounded claim(s) "
                f"({len(verified)} cross-source verified)"
            )
        else:
            notes.append("rejected: no grounded claims survived hallucination audit")

    # Headline / dek: deterministic by default; Gemini-polished when available.
    headline = event.title
    if verified:
        dek = event.summary or verified[0].text
    elif grounded:
        dek = event.summary or grounded[0].text
    else:
        dek = event.summary or event.title
    if mode == "debate":
        dek = f"Contested: {len({d.source_name for d in docs})} outlet(s), no primary source."

    if approved and backend is not None and not backend.is_local:
        headline, llm_dek = _llm_headline(event, grounded, backend)
        if llm_dek:
            dek = llm_dek if mode != "debate" else f"{dek} {llm_dek}"

    body = _assemble_markdown(
        headline=headline,
        dek=dek,
        mode=mode,
        verified=verified,
        flagged=flagged,
        grounded=grounded,
        context_md=context_md,
        perspective_md=perspective_md,
        docs=docs,
        by_id=by_id,
    )

    return StoryPackage(
        event_id=event.id,
        headline=headline,
        dek=dek,
        body_markdown=body,
        claims=grounded,
        editor_approved=approved,
        editor_notes="; ".join(notes),
    )
