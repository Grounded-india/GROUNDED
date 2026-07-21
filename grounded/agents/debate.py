"""Multi-pass back-and-forth debate for controversial stories.

Prior version: three blind LLM calls (framing, argue A, argue B). Neither side
saw the other's argument, so the "debate" read as two monologues stapled
together - Side B could never actually respond to Side A, expose contradictions,
or call out hypocrisy.

This version: five calls that produce a genuine back-and-forth dialogue.

    1. Framing            -> name the two real sides and their positions
    2. Opening A          -> Side A opens, cited to sources
    3. Opening B          -> sees Opening A, responds to it AND makes own case
    4. Rebuttal A         -> sees Opening A + Opening B, replies to B
    5. Rebuttal B (close) -> sees all prior turns, closes

Prompts explicitly instruct each debater to address the other side's specific
claims and to call out contradictions or hypocrisy where the sources support it.
No fabrication - if a debater cannot ground a rebuttal in the provided facts,
they concede the point.

Offline (local backend) a deterministic 4-turn dialogue is produced instead so
the feature still works with no API keys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from grounded.agents.llm import LLMBackend, extract_json
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim

log = logging.getLogger(__name__)


def _today_line() -> str:
    now = datetime.now().astimezone()
    return f"TODAY IS {now:%A, %d %B %Y}."

_MODERATOR_SYSTEM = (
    "You are a neutral news moderator writing the closing takeaway on a "
    "back-and-forth debate that has just concluded. You have the facts block, "
    "both sides' opening statements, and both sides' rebuttals. You are NOT an "
    "advocate for either side.\n"
    "\n"
    "Write a compact 'bottom line' that:\n"
    "- Names what both sides agreed on (the settled facts of the story).\n"
    "- Names what they actually disagreed on and what the load-bearing question "
    "for the reader is.\n"
    "- Where a cited source clearly settles a factual point that one side "
    "denied, state that plainly and cite the source. Do NOT declare a winner on "
    "questions of judgement, policy, or values - only on facts the sources "
    "have already resolved.\n"
    "- Every factual claim must trace to a source in the facts block, cited in "
    "parentheses (outlet_name). No outside knowledge, no invented facts.\n"
    "- 2-4 sentences. Compact, readable, no lists, no headings, no meta-"
    "commentary about the debate itself."
)

_FRAMING_SYSTEM = (
    "Name the two real opposing sides of this Indian news event. Use the actual "
    "actor named in the sources ('Delhi Police', 'The Opposition', 'The CJP "
    "organisers', 'The BJP', 'The Ministry', 'The petitioners'), NOT generic "
    "'supporters/skeptics'. If one-sided, still name the strongest good-faith "
    "counter-position. JSON only, no prose."
)

_DEBATER_SYSTEM = (
    "You advocate one side of a live Indian news debate. Speak as a real person "
    "making the strongest possible case for your assigned side.\n"
    "\n"
    "VOICE\n"
    "- Your side's voice, your side's interest. Do not hedge. Do NOT say 'both "
    "sides have valid points' or 'the truth lies in the middle' - that is the "
    "moderator's line, not yours.\n"
    "- Steel-man: the strongest, most intelligent version of your position, not "
    "the loudest or most partisan.\n"
    "- Pointed and direct but never emotional. No sneering, no exclamation marks, "
    "no personal attacks, no imputed motives without a receipt.\n"
    "\n"
    "STRUCTURE (when responding to a prior turn)\n"
    "1. Paraphrase the other side's strongest specific claim in one line.\n"
    "2. Rebut it with your source-grounded counter.\n"
    "3. Extend with your own positive case only if you have new substance.\n"
    "Length: 2-5 sentences. LESS IS MORE. Once you have made your point, stop. "
    "A tight, sharp turn is better than a long one that dilutes the argument. "
    "Only go long when the material genuinely warrants it.\n"
    "\n"
    "THREE TIERS OF GROUNDING - use the correct tag for every point:\n"
    "\n"
    "1. **Cited fact** - `(outlet_name)` - a claim that traces to an entry in "
    "the facts block. This is the default and the ONLY tier allowed in your "
    "opening statement. Every load-bearing claim, especially in your positive "
    "case, must be this. Example: `Delhi Police issued a prohibitory order "
    "against assemblies of five or more (the_hindu).`\n"
    "\n"
    "2. **Internal contradiction** - `[internal contradiction]` - when the other "
    "side's own argument doesn't hold together (their numbers conflict, their "
    "premises rule each other out, they claim two things that cannot both be "
    "true). No citation needed because you are pointing at their own logic. "
    "Rebuttal turns only. Example: `[internal contradiction] They claimed only "
    "100 people attended, then said it was the largest gathering in Delhi's "
    "history - those two claims cannot both be true.`\n"
    "\n"
    "3. **Common-sense check** - `[common-sense check]` - narrow correction of a "
    "claim that violates basic math, well-known institutional definition, or "
    "self-evident structural fact that any reader would agree with instantly. "
    "Rebuttal turns only. Reserve for OBVIOUS things (impossible percentages, "
    "wrong meaning of an institution, wrong order of well-known events). Not "
    "for anything actually contested. Example: `[common-sense check] A 1000% "
    "single-year GDP growth would triple every sector; that number is not "
    "possible.`\n"
    "\n"
    "HYPOCRISY (when the sources support it)\n"
    "If the cited sources show the other side's own actor previously said or did "
    "the opposite of what they are now claiming, name it once, plainly, receipt "
    "attached. Example: `The Ministry now argues the scheme was always "
    "means-tested, but per (pib) its April notification described it as "
    "universal.` Do this soberly, do not moralise.\n"
    "\n"
    "TIME AWARENESS\n"
    "- The current date is given as 'TODAY IS ...' in your user prompt.\n"
    "- Where natural, use relative time (yesterday, today, three days ago, "
    "earlier this week, last month) alongside the specific dates from the "
    "sources. 'The protest yesterday' reads better than 'the protest on 21 "
    "July' when today is 22 July.\n"
    "- Never invent a date the sources do not give you.\n"
    "\n"
    "HARD LIMITS\n"
    "- Never invent facts, numbers, quotes, dates, motives, or events.\n"
    "- If you cannot rebut with tier 1, 2, or 3, CONCEDE the point rather than "
    "invent a 'widely known' fact to escape.\n"
    "- Represent the other side's view accurately before disagreeing. No "
    "strawmen.\n"
    "- No lists, no bullet points, no headings, no meta-commentary about the "
    "debate itself. Prose only. Answer directly, no reasoning aloud.\n"
    "\n"
    "ANTI-REPETITION\n"
    "- Never restate a claim you already made in a prior turn. If you already "
    "said 'the Ministry removed the NTA Director General', do not say it again.\n"
    "- Rebuttal turn = respond to what THEY said, AND add NEW substance you did "
    "not raise before. If you only repeat your opening, you have wasted the turn.\n"
    "- Closing turn = synthesise with a NEW angle or a concise final point. "
    "Not a re-list of your prior arguments.\n"
    "- If you genuinely have no new material to add, keep the turn short. "
    "Quality over quantity. Repetition weakens your argument."
)


@dataclass
class DebateResult:
    label_a: str
    label_b: str
    opening_a: str
    opening_b: str
    rebuttal_a: str
    rebuttal_b: str
    conclusion: str = ""
    trace: dict = field(default_factory=dict)

    @property
    def markdown(self) -> str:
        """Render as an actual dialogue, dropping any empty turns silently."""
        turns: list[tuple[str, str]] = []
        if self.opening_a.strip():
            turns.append((self.label_a, self.opening_a.strip()))
        if self.opening_b.strip():
            turns.append((self.label_b, self.opening_b.strip()))
        if self.rebuttal_a.strip():
            turns.append((f"{self.label_a} (rebuttal)", self.rebuttal_a.strip()))
        if self.rebuttal_b.strip():
            turns.append((f"{self.label_b} (closing)", self.rebuttal_b.strip()))
        body = "\n\n".join(f"**{label}:** {text}" for label, text in turns)
        if self.conclusion.strip():
            body += f"\n\n**Bottom line:** {self.conclusion.strip()}"
        return body


def _facts_block(claims: list[VerifiedClaim], docs: list[SourceDoc]) -> str:
    by_id = {d.id: d for d in docs}
    lines = []
    for c in claims:
        cites = ", ".join(
            sorted({by_id[i].source_name for i in c.source_item_ids if i in by_id})
        )
        lines.append(f"- {c.text} (sources: {cites or 'none'})")
    return "\n".join(lines) or "- (no grounded facts available)"


def _frame_sides(event: EventView, facts: str, backend: LLMBackend) -> tuple[str, str]:
    raw = backend.complete(
        system=_FRAMING_SYSTEM,
        user=(
            f"{_today_line()}\n\n"
            f"EVENT: {event.title}\n\nFACTS:\n{facts}\n\n"
            'Return JSON: {"side_a": "<short label>", "side_b": "<short label>"}'
        ),
        max_tokens=200,
        temperature=0.2,
        json_mode=True,
    )
    try:
        data = extract_json(raw)
        a = str(data.get("side_a") or "").strip()
        b = str(data.get("side_b") or "").strip()
        if a and b:
            return a, b
    except (ValueError, AttributeError):
        pass
    return "Supporters' account", "Skeptics' account"


def _argue(
    side_label: str,
    event: EventView,
    facts: str,
    prior_turns: list[tuple[str, str]],
    backend: LLMBackend,
    *,
    turn: str,
) -> str:
    """Run one debater turn. ``prior_turns`` is [(other_side_label, their_text), ...]."""
    prior_block = ""
    if prior_turns:
        chunks = [f"[{label}]\n{text}" for label, text in prior_turns]
        prior_block = "\n\nWHAT HAS BEEN SAID SO FAR IN THIS DEBATE:\n" + "\n\n".join(chunks)

    user = (
        f"{_today_line()}\n\n"
        f"EVENT: {event.title}\n\n"
        f"YOUR ASSIGNED SIDE: {side_label}\n\n"
        f"FACTS (all citations must trace to entries here):\n{facts}"
        f"{prior_block}\n\n"
        f"TURN: {turn}. Write your response now."
    )
    return backend.complete(
        system=_DEBATER_SYSTEM,
        user=user,
        max_tokens=700,
        temperature=0.4,
    ).strip()


def _moderate(
    event: EventView,
    facts: str,
    label_a: str,
    label_b: str,
    opening_a: str,
    opening_b: str,
    rebuttal_a: str,
    rebuttal_b: str,
    backend: LLMBackend,
) -> str:
    """Run the neutral moderator's closing takeaway."""
    turns_block = ""
    for label, text in [
        (label_a, opening_a),
        (label_b, opening_b),
        (f"{label_a} (rebuttal)", rebuttal_a),
        (f"{label_b} (closing)", rebuttal_b),
    ]:
        if text and text.strip():
            turns_block += f"\n\n[{label}]\n{text.strip()}"

    user = (
        f"{_today_line()}\n\n"
        f"EVENT: {event.title}\n\n"
        f"FACTS (all citations must trace to entries here):\n{facts}\n\n"
        f"THE DEBATE JUST HELD:{turns_block}\n\n"
        "Write the neutral 'bottom line' takeaway now."
    )
    return backend.complete(
        system=_MODERATOR_SYSTEM,
        user=user,
        max_tokens=500,
        temperature=0.3,
    ).strip()


def _local_debate(
    event: EventView, claims: list[VerifiedClaim], docs: list[SourceDoc]
) -> DebateResult:
    """Deterministic offline fallback that still produces a 4-turn dialogue shape."""
    by_id = {d.id: d for d in docs}
    reported = []
    for c in claims:
        cites = ", ".join(
            sorted({by_id[i].source_name for i in c.source_item_ids if i in by_id})
        )
        reported.append(f"- {c.text} ({cites})")
    reported_md = "\n".join(reported) or "No grounded facts were reported."

    outlets = sorted({d.source_name for d in docs})
    tier1 = [d.source_name for d in docs if d.is_primary]

    opening_a = f"The reporting summarizes what the cited outlets say:\n{reported_md}"
    opening_b = (
        f"No primary or official source has confirmed this account; it rests on "
        f"{len(outlets)} non-primary outlet(s) ({', '.join(outlets)}). Until an "
        "official record corroborates it, treat the specifics above as unverified "
        "reporting rather than established fact."
    )
    rebuttal_a = (
        "The outlets above are independent of one another, and cross-source "
        "corroboration is itself a form of verification even without a government "
        "statement."
        if len(outlets) > 1
        else "This account depends on a single outlet; treat with caution."
    )
    rebuttal_b = (
        f"Independent outlets can still repeat one another; without a primary "
        f"source ({', '.join(tier1) if tier1 else 'none available'}), the "
        "underlying claim remains uncorroborated by any official record."
    )
    conclusion = (
        f"Both sides accept the outlets summarized above. What is contested is "
        f"whether {len(outlets)} independent non-primary outlet(s) constitute "
        "sufficient corroboration in the absence of an official record. Until a "
        "primary source confirms the specifics, treat this as reporting rather "
        "than established fact."
    )
    return DebateResult(
        label_a="What is being reported",
        label_b="Why it remains unverified",
        opening_a=opening_a,
        opening_b=opening_b,
        rebuttal_a=rebuttal_a,
        rebuttal_b=rebuttal_b,
        conclusion=conclusion,
        trace={"mode": "local"},
    )


def run_debate(
    event: EventView,
    claims: list[VerifiedClaim],
    docs: list[SourceDoc],
    backend: LLMBackend,
) -> DebateResult:
    if backend.is_local:
        return _local_debate(event, claims, docs)

    facts = _facts_block(claims, docs)
    label_a, label_b = _frame_sides(event, facts, backend)

    # Turn 1: A opens with no prior context.
    opening_a = _argue(label_a, event, facts, prior_turns=[], backend=backend, turn="OPENING")

    # Turn 2: B opens seeing A's opening.
    opening_b = _argue(
        label_b, event, facts,
        prior_turns=[(label_a, opening_a)] if opening_a else [],
        backend=backend, turn="OPENING (responding to the other side's opening)",
    )

    # Turn 3: A rebuts, seeing B's opening.
    prior_for_a = [(label_a, opening_a), (label_b, opening_b)] if opening_a else []
    if not opening_a:
        prior_for_a = [(label_b, opening_b)] if opening_b else []
    rebuttal_a = _argue(
        label_a, event, facts,
        prior_turns=prior_for_a,
        backend=backend, turn="REBUTTAL (address the other side's opening)",
    )

    # Turn 4: B closes, seeing everything.
    prior_for_b_close = [
        (label_a, opening_a),
        (label_b, opening_b),
        (label_a + " (rebuttal)", rebuttal_a),
    ]
    prior_for_b_close = [(lbl, t) for lbl, t in prior_for_b_close if t]
    rebuttal_b = _argue(
        label_b, event, facts,
        prior_turns=prior_for_b_close,
        backend=backend, turn="CLOSING (address the other side's rebuttal)",
    )

    # Turn 5: neutral moderator wrap-up. Reads everything, states what is
    # settled and what remains contested. Does not pick a winner on judgement.
    conclusion = _moderate(
        event, facts,
        label_a, label_b,
        opening_a, opening_b, rebuttal_a, rebuttal_b,
        backend,
    )

    return DebateResult(
        label_a=label_a,
        label_b=label_b,
        opening_a=opening_a,
        opening_b=opening_b,
        rebuttal_a=rebuttal_a,
        rebuttal_b=rebuttal_b,
        conclusion=conclusion,
        trace={
            "mode": backend.name,
            "sides": [label_a, label_b],
            "turns": ["opening_a", "opening_b", "rebuttal_a", "rebuttal_b", "conclusion"],
        },
    )
