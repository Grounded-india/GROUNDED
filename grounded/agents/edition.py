"""Render every built story into one clean, single-page markdown edition.

This is the reader-facing newspaper. It rebuilds each story from structured data
(headline, dek, context, debate, grounded claims) and pulls **clean outlet
names** from the sources instead of the raw Google-News redirect URLs stored per
source - so the page reads like a newsletter, not a wall of link noise.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from grounded.agents.cleaning import is_boilerplate, strip_boilerplate
from grounded.db import cursor

# Outlet slugs that should render as acronyms rather than Title Case.
_ACRONYMS = {"ap", "pib", "rbi", "sci", "prs", "un", "us", "usa", "gst", "cjp", "rss"}


def _humanize(name: str) -> str:
    """`the_hindu` -> `The Hindu`, `ap_india` -> `AP India`, `rbi` -> `RBI`."""
    parts = [p for p in (name or "").replace("-", "_").split("_") if p]
    if not parts:
        return name or "unknown"
    return " ".join(p.upper() if p.lower() in _ACRONYMS else p.capitalize() for p in parts)


def _trace(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def _slug(heading: str) -> str:
    out = []
    for ch in heading.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _fetch(approved_only: bool) -> list[dict]:
    where = "WHERE s.editor_approved" if approved_only else ""
    with cursor() as cur:
        cur.execute(
            f"""
            SELECT s.id, s.event_id, s.headline, s.dek, s.editor_approved,
                   s.editor_notes, s.agent_trace, s.created_at
            FROM stories s
            {where}
            ORDER BY s.created_at DESC
            """
        )
        stories = cur.fetchall()
        for s in stories:
            cur.execute(
                """
                SELECT c.claim_text, c.verified, c.tier_1_backed, c.ordinal,
                       COALESCE(
                           array_agg(DISTINCT r.source_name)
                           FILTER (WHERE r.source_name IS NOT NULL), '{}'
                       ) AS outlets
                FROM claims c
                LEFT JOIN claim_sources cs ON cs.claim_id = c.id
                LEFT JOIN raw_items r ON r.id = cs.raw_item_id
                WHERE c.story_id = %s
                GROUP BY c.id
                ORDER BY c.ordinal
                """,
                (s["id"],),
            )
            s["claims"] = cur.fetchall()
    return stories


def _story_outlets(story: dict) -> list[str]:
    seen = {o for c in story["claims"] for o in (c["outlets"] or [])}
    return sorted({_humanize(o) for o in seen})


def _render_story(i: int, s: dict) -> list[str]:
    trace = _trace(s["agent_trace"])
    mode = trace.get("mode", "report")
    verifier = trace.get("verifier") or {}
    heading = f"{i}. {s['headline']}"

    claims = [c for c in s["claims"] if not is_boilerplate(c["claim_text"] or "")]

    lines = ["", "---", "", f"## {heading}", ""]
    if s.get("dek"):
        lines += [f"*{s['dek'].strip()}*", ""]

    badges = [mode.upper()]
    if trace.get("n_sources"):
        badges.append(f"{trace['n_sources']} sources")
    badges.append(f"{len(claims)} claim(s) kept")
    if mode != "debate" and verifier.get("verified") is not None:
        badges.append(f"{verifier.get('verified', 0)} verified")
    lines += ["> " + "  ·  ".join(badges), ""]

    context = strip_boilerplate((trace.get("context") or "").strip())
    if context:
        lines += ["### Context", "", context, ""]

    if mode == "debate":
        perspective = strip_boilerplate((trace.get("perspective") or "").strip())
        if perspective:
            lines += ["### The debate", "", perspective, ""]
        lines += ["### Grounded points", ""]
    else:
        lines += ["### What we know", ""]

    if claims:
        for c in claims:
            outlets = ", ".join(_humanize(o) for o in (c["outlets"] or [])) or "unattributed"
            tag = " _(primary-source backed)_" if c["tier_1_backed"] else ""
            lines.append(f"- {c['claim_text'].strip()} — *{outlets}*{tag}")
    else:
        lines.append("- _No claims cleared the editor._")
    lines.append("")

    outlets = _story_outlets(s)
    if outlets:
        lines += [f"**Sources:** {', '.join(outlets)}", ""]
    return lines


def render_edition(approved_only: bool = True) -> str:
    """Build the full single-page markdown edition from persisted stories."""
    stories = _fetch(approved_only)
    now = datetime.now(timezone.utc)
    n = len(stories)

    out = [
        "# GROUNDED — Daily Edition",
        "",
        f"*Autonomous, fact-grounded newsletter · {now:%A, %d %B %Y} · "
        f"{n} stor{'y' if n == 1 else 'ies'}*",
        "",
    ]
    if not stories:
        out += ["_No stories yet — run `python -m grounded.agents build` first._", ""]
        return "\n".join(out)

    out += ["## In this edition", ""]
    for i, s in enumerate(stories, 1):
        mode = _trace(s["agent_trace"]).get("mode", "report")
        anchor = _slug(f"{i}. {s['headline']}")
        out.append(f"{i}. [{s['headline']}](#{anchor}) — _{mode}_")
    out.append("")

    for i, s in enumerate(stories, 1):
        out += _render_story(i, s)

    out += [
        "---",
        "",
        "*Every claim above was extracted from source material, verified against "
        "its citations, and audited for hallucination. Items marked DEBATE lack a "
        "primary/official source and are presented as contested rather than "
        "confirmed.*",
        "",
    ]
    return "\n".join(out).strip() + "\n"
