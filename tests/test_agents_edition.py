"""Unit tests for the edition renderer's pure helpers (no DB required)."""

from __future__ import annotations

from grounded.agents.edition import _humanize, _render_story, _slug


def test_humanize_outlet_slugs():
    assert _humanize("the_hindu") == "The Hindu"
    assert _humanize("reuters_india") == "Reuters India"
    assert _humanize("ap_india") == "AP India"
    assert _humanize("prs_india") == "PRS India"
    assert _humanize("rbi") == "RBI"


def test_slug_matches_heading_anchor_style():
    assert _slug("1. Rahul Gandhi's remark") == "1-rahul-gandhis-remark"


def _story(claims, *, mode="report", context="", perspective=""):
    return {
        "id": "s1",
        "headline": "Test headline",
        "dek": "A dek.",
        "editor_approved": True,
        "editor_notes": "",
        "agent_trace": {
            "mode": mode,
            "n_sources": len(claims),
            "verifier": {"verified": len(claims)},
            "context": context,
            "perspective": perspective,
        },
        "claims": claims,
    }


def _claim(text, outlets, *, tier1=False):
    return {
        "claim_text": text,
        "verified": True,
        "tier_1_backed": tier1,
        "ordinal": 0,
        "outlets": outlets,
    }


def test_render_story_drops_boilerplate_claims():
    claims = [
        _claim("You are logged in Loading...", ["the_hindu"]),
        _claim("The cabinet cleared the scheme on Monday.", ["pib"], tier1=True),
    ]
    md = "\n".join(_render_story(1, _story(claims)))
    assert "logged in" not in md.lower()
    assert "cleared the scheme" in md
    assert "1 claim(s) kept" in md  # boilerplate claim not counted


def test_render_story_cleans_context_and_debate_prose():
    claims = [_claim("Real grounded point about the event.", ["reuters_india"])]
    story = _story(
        claims,
        mode="debate",
        context="Subscribe now. This event concerns a shipping attack.",
        perspective="**Side A**\n\n- You are logged in Loading...\n- A real cited point (reuters_india)",
    )
    md = "\n".join(_render_story(1, story))
    assert "subscribe now" not in md.lower()
    assert "logged in" not in md.lower()
    assert "shipping attack" in md
    assert "real cited point" in md.lower()
