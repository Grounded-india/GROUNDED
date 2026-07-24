"""Agent 6 — Long-form reporter.

Runs only for REPORT-mode stories. Turns the verified claims + context +
available full source content into a proper article-style narrative (400-700
words) instead of the previous "dek + short context + bullet list" layout.

The output is a `body_markdown` string that the edition renderer drops
directly under the story heading in place of the "### What we know" bullets.

Anti-repetition rules are baked into the prompt:
  * Never restate the headline in the first sentence.
  * Never repeat a fact you have already stated.
  * Every substantive detail must trace to a cited source (outlet name in
    parentheses).
  * If the material is thin, WRITE LESS. Do not pad. Quality over quantity.

Offline fallback: assembles a short deterministic narrative from the
verified claims so the pipeline still yields a usable body.
"""

from __future__ import annotations

import logging

from grounded.agents.llm import LLMBackend
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim

log = logging.getLogger(__name__)

_SYSTEM = (
    "You are writing a news article for an India-focused fact-driven "
    "newsletter. Not a summary. Not a bullet list. A proper piece of "
    "news prose that a reader could read on its own.\n"
    "\n"
    "STRICT RULES:\n"
    "- 400 to 700 words. If the material is thin, write LESS. Do not pad, "
    "do not invent detail, do not repeat a fact you already stated.\n"
    "- Do NOT restate the headline in your opening sentence. Start with a "
    "concrete detail, quote, or action.\n"
    "- Every substantive factual claim must trace to the facts block. Cite "
    "the outlet in parentheses after the claim, e.g. '(the_hindu)'. Never "
    "invent facts, numbers, quotes, dates, or motives.\n"
    "- If the sources include a full article body (marked FULL BODY below), "
    "use its detail, quotes, and context. Do not paraphrase word-for-word.\n"
    "- Weave the facts into flowing paragraphs. Each new paragraph should "
    "add something the previous one did not.\n"
    "- Neutral voice. No editorialising, no adjectives that pick a side, "
    "no rhetorical questions.\n"
    "- Structure loosely as: (1) opening paragraph with the concrete lede, "
    "(2) main narrative with details, actors, timeline, (3) background / "
    "why it matters if the sources establish it, (4) a closing line naming "
    "what remains uncertain or unanswered where applicable.\n"
    "- Output plain markdown paragraphs. No headings, no bullet lists, "
    "no meta-commentary about the article itself. Answer directly."
)


def _facts_block(
    claims: list[VerifiedClaim], docs: list[SourceDoc], max_body_chars: int = 3000
) -> str:
    """Assemble the source material the reporter sees.

    Includes:
      * The verified claims with citation index.
      * A trimmed FULL BODY excerpt for each source that has one (up to
        ``max_body_chars``), which gives the reporter genuine narrative
        material instead of just claim bullets.
    """
    by_id = {d.id: d for d in docs}
    lines: list[str] = ["VERIFIED CLAIMS:"]
    for c in claims:
        cites = ", ".join(
            sorted({by_id[i].source_name for i in c.source_item_ids if i in by_id})
        )
        marker = " [tier-1 backed]" if c.tier_1_backed else ""
        lines.append(f"- {c.text} (sources: {cites or 'none'}){marker}")

    lines.append("")
    lines.append("FULL BODY EXCERPTS (use for detail, quotes, context):")
    any_body = False
    for d in docs:
        text = (getattr(d, "text", "") or "").strip()
        if not text:
            continue
        any_body = True
        excerpt = text[:max_body_chars]
        if len(text) > max_body_chars:
            excerpt += "..."
        lines.append(f"\n[{d.source_name}]\n{excerpt}")
    if not any_body:
        lines.append("(no full-body content available for this event; "
                     "work from the verified claims only)")
    return "\n".join(lines)


def _local_report(
    event: EventView, claims: list[VerifiedClaim], docs: list[SourceDoc]
) -> str:
    """Deterministic offline fallback — one paragraph summary from claims."""
    by_id = {d.id: d for d in docs}
    if not claims:
        return "This story is reconstructed from the ingested sources; no verified claims are available."
    paragraphs = [(event.title or "").strip()]
    for c in claims[:8]:
        cites = ", ".join(
            sorted({by_id[i].source_name for i in c.source_item_ids if i in by_id})
        )
        paragraphs.append(f"{c.text.rstrip('.')} ({cites}).")
    return "\n\n".join(paragraphs)


def build_report(
    event: EventView,
    claims: list[VerifiedClaim],
    context_md: str,
    docs: list[SourceDoc],
    backend: LLMBackend,
) -> str:
    """Produce a 400-700 word article-style body for a REPORT-mode story."""
    if backend.is_local:
        return _local_report(event, claims, docs)

    facts = _facts_block(claims, docs)
    context = (context_md or "").strip()
    user = (
        f"EVENT: {event.title}\n\n"
        f"BACKGROUND (from the Context Agent; use to frame the story but "
        f"do not repeat verbatim):\n{context or '(none)'}\n\n"
        f"{facts}\n\n"
        "Write the article now. Plain markdown prose. Answer directly."
    )
    body = backend.complete(
        system=_SYSTEM,
        user=user,
        max_tokens=2000,
        temperature=0.4,
    ).strip()
    return body
