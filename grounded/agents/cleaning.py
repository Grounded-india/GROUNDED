"""Shared text hygiene: strip website chrome / paywall boilerplate that leaks in
from scraped article bodies (login prompts, subscribe walls, cookie notices,
navigation) so it never becomes a claim, a debate point, or edition copy.

Kept deliberately conservative: every pattern is a high-confidence UI phrase, so
real reporting is never dropped (e.g. "active subscription" matches paywall
chrome but a story about a "subscription policy" does not).
"""

from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# A line left with only bullet/markdown markers and parenthetical citations after
# its chrome sentence was removed - e.g. "- (the_hindu)" - carries no content.
_ONLY_CHROME = re.compile(r"^[\s\-\*•>]*(\([^)]*\)\s*)*[\s\-\*•>]*$")

_BOILERPLATE = re.compile(
    r"""(
        you\ are\ logged\ in
      | logged\ in
      | loading\.\.\.
      | subscribe\ now
      | subscribed\ with\ another\ email
      | already\ a\ subscriber
      | active\ subscription
      | subscription\ benefits
      | premium\ stories
      | sign\ in\b
      | \blog\ in\b
      | create\ (an|a\ free)\ account
      | manage\ your\ account
      | gift\ this\ article
      | enable\ javascript
      | accept\ (all\ )?cookies
      | cookie\ (policy|settings|preferences)
      | advertisement
      | all\ rights\ reserved
      | terms\ (of\ (use|service)|\&\ conditions)
      | privacy\ policy
      | follow\ us\ on
      | download\ the\ app
      | continue\ reading
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def is_boilerplate(text: str) -> bool:
    """True if the segment is website chrome / paywall noise, not reporting."""
    return bool(_BOILERPLATE.search(text or ""))


def strip_boilerplate(text: str) -> str:
    """Drop boilerplate sentences from a blob, keeping the real content.

    Works line by line then sentence by sentence so a chrome sentence sitting
    next to real text ("You are logged in. The RBI cut rates.") loses only the
    chrome half.
    """
    if not text:
        return text
    kept_lines: list[str] = []
    for line in text.splitlines():
        parts = _SENTENCE_SPLIT.split(line)
        kept = [p for p in parts if p.strip() and not is_boilerplate(p)]
        if not kept:
            continue
        rejoined = " ".join(kept)
        # Drop lines reduced to a bare citation once their chrome text is removed.
        if _ONLY_CHROME.match(rejoined):
            continue
        kept_lines.append(rejoined)
    return "\n".join(kept_lines).strip()
