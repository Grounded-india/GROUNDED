"""Multi-agent debate (the Perspective Agent, run as multiple Nemotron agents).

This is the mechanism for ground-reality stories: when an event has no
primary/government citation - e.g. something surfaced from Reddit - we do not
drop it. Instead a debate crew presents both sides of the story, arguing *only
with facts drawn from the sources*, so the reader gets the contested picture
rather than a single unverified take.

Crew (each a separate model call -> "multiple nemotron agents"):
  1. Framing agent  -> names the two genuine sides
  2. Debater A      -> steel-mans side A using only provided facts
  3. Debater B      -> steel-mans side B using only provided facts

Offline (local backend) a deterministic two-sided summary is produced instead,
so the feature still works with no API keys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from grounded.agents.llm import LLMBackend, extract_json
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim

log = logging.getLogger(__name__)

_FRAMING_SYSTEM = (
    "You identify the two genuine, opposing sides of a public debate around a "
    "news event. You never invent positions; if the material is one-sided, still "
    "name the strongest good-faith counter-position. Respond only with JSON."
)

_DEBATER_SYSTEM = (
    "You are a debater. Argue the assigned side of the debate using ONLY the facts "
    "listed below. Do not invent facts, numbers, or quotes, and do not use outside "
    "knowledge. Cite the source name in parentheses after each factual point. Write "
    "2-4 sentences of plain prose."
)


@dataclass
class DebateResult:
    side_a_label: str
    side_a_md: str
    side_b_label: str
    side_b_md: str
    trace: dict = field(default_factory=dict)

    @property
    def markdown(self) -> str:
        return (
            f"**Side A — {self.side_a_label}**\n\n{self.side_a_md.strip()}\n\n"
            f"**Side B — {self.side_b_label}**\n\n{self.side_b_md.strip()}"
        )


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
            f"EVENT: {event.title}\n\nFACTS:\n{facts}\n\n"
            'Return JSON: {"side_a": "<short label>", "side_b": "<short label>"}'
        ),
        max_tokens=200,
        temperature=0.2,
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


def _argue(side: str, event: EventView, facts: str, backend: LLMBackend) -> str:
    return backend.complete(
        system=_DEBATER_SYSTEM,
        user=(
            f"EVENT: {event.title}\n\nSIDE TO ARGUE: {side}\n\nFACTS:\n{facts}\n\n"
            "Write your argument now."
        ),
        max_tokens=500,
        temperature=0.4,
    ).strip()


def _local_debate(
    event: EventView, claims: list[VerifiedClaim], docs: list[SourceDoc]
) -> DebateResult:
    by_id = {d.id: d for d in docs}
    reported = []
    for c in claims:
        cites = ", ".join(
            sorted({by_id[i].source_name for i in c.source_item_ids if i in by_id})
        )
        reported.append(f"- {c.text} ({cites})")
    reported_md = "\n".join(reported) or "- No grounded facts were reported."

    outlets = sorted({d.source_name for d in docs})
    skeptic_md = (
        "No primary or official source has confirmed this account; it rests on "
        f"{len(outlets)} non-primary outlet(s) ({', '.join(outlets)}). Until an "
        "official record corroborates it, the specifics above should be treated as "
        "unverified reporting rather than established fact."
    )
    return DebateResult(
        side_a_label="What is being reported",
        side_a_md=reported_md,
        side_b_label="Why it remains unverified",
        side_b_md=skeptic_md,
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
    side_a = _argue(label_a, event, facts, backend) or "(no argument produced)"
    side_b = _argue(label_b, event, facts, backend) or "(no argument produced)"
    return DebateResult(
        side_a_label=label_a,
        side_a_md=side_a,
        side_b_label=label_b,
        side_b_md=side_b,
        trace={"mode": backend.name, "sides": [label_a, label_b]},
    )
