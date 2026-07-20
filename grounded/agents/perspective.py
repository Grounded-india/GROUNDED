"""Agent 4 - Perspective Agent, implemented as a multi-agent debate.

Per the product spec this agent runs as *multiple Nemotron agents*: a framing
agent plus two debaters (see ``debate.py``). It steel-mans both sides using only
facts from the sources.

For ground-reality events with no primary/government citation (e.g. Reddit), the
crew elevates this debate to the centerpiece of the story instead of dropping the
event - that routing happens in the editor/crew; here we just always produce the
two-sided, fact-grounded debate.
"""

from __future__ import annotations

from grounded.agents.debate import run_debate
from grounded.agents.llm import LLMBackend
from grounded.agents.schemas import EventView, SourceDoc, VerifiedClaim


def build_perspective(
    event: EventView,
    claims: list[VerifiedClaim],
    docs: list[SourceDoc],
    backend: LLMBackend,
) -> str:
    # Debate over verified claims when we have them; otherwise (ground-reality,
    # nothing cleared verification) debate over every grounded claim.
    focus = [c for c in claims if c.verified] or [c for c in claims if c.source_item_ids]
    return run_debate(event, focus, docs, backend).markdown
