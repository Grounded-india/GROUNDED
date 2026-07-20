"""Tests for the importance ranker (pure logic, no DB)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from grounded.pipeline.importance import (
    ItemView,
    extract_features,
    score_event,
    score_features,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def _item(source_name, tier, title="", content="", hours_ago=1):
    return ItemView(
        source_name=source_name,
        source_tier=tier,
        title=title,
        content=content,
        timestamp=NOW - timedelta(hours=hours_ago),
    )


# --- feature extraction -------------------------------------------------


def test_distinct_sources_counts_outlets_not_items():
    items = [
        _item("reuters_india", 2, "Budget passed"),
        _item("reuters_india", 2, "Budget passed again"),
        _item("the_hindu", 2, "Budget passed"),
    ]
    f = extract_features(items, now=NOW)
    assert f.num_items == 3
    assert f.distinct_sources == 2


def test_tier_flags_and_anchor():
    f = extract_features([_item("pib", 1, "Cabinet approves scheme")], now=NOW)
    assert f.has_tier1 is True
    assert f.tier_1_anchor is True

    f2 = extract_features([_item("reddit_india", 3, "viral thread")], now=NOW)
    assert f2.has_tier1 is False
    assert f2.has_tier2 is False
    assert f2.signal_only is True
    assert f2.tier_1_anchor is False


def test_policy_keywords_detected():
    f = extract_features(
        [_item("pib", 1, "Supreme Court verdict on tax bill", "new gst amendment")],
        now=NOW,
    )
    assert f.policy_impact_hits > 0
    assert "supreme court" in f.matched_policy_keywords


def test_downweight_keywords_detected():
    f = extract_features(
        [_item("reddit_india", 3, "Bollywood actor goes viral", "netizens react")],
        now=NOW,
    )
    assert f.downweight_hits > 0


def test_recency_hours_uses_most_recent_item():
    items = [
        _item("pib", 1, "old", hours_ago=40),
        _item("reuters_india", 2, "new", hours_ago=2),
    ]
    f = extract_features(items, now=NOW)
    assert 1.9 < f.recency_hours < 2.1


# --- scoring ------------------------------------------------------------


def test_primary_policy_event_outranks_signal_viral():
    policy = [
        _item("pib", 1, "Supreme Court verdict on electoral bonds", "bill amendment", 2),
        _item("reuters_india", 2, "Court strikes down scheme", "policy", 2),
    ]
    viral = [
        _item("reddit_india", 3, "Actor goes viral", "netizens slam, backlash", 2),
        _item("reddit_indianews", 3, "meme thread trends", "trolls", 2),
    ]
    assert score_event(policy, now=NOW)[0] > score_event(viral, now=NOW)[0]


def test_signal_only_event_is_heavily_penalized():
    viral = [_item("reddit_india", 3, "goes viral", "netizens outrage", 1)]
    score, _ = score_event(viral, now=NOW)
    assert score < 1.0


def test_more_corroboration_scores_higher():
    one = [_item("reuters_india", 2, "Ministry announces policy", "budget", 1)]
    many = [
        _item("reuters_india", 2, "Ministry announces policy", "budget", 1),
        _item("the_hindu", 2, "Ministry announces policy", "budget", 1),
        _item("ap_india", 2, "Ministry announces policy", "budget", 1),
    ]
    assert score_event(many, now=NOW)[0] > score_event(one, now=NOW)[0]


def test_primary_source_beats_wire_only_all_else_equal():
    primary = [_item("pib", 1, "Cabinet clears bill", "policy", 1)]
    wire = [_item("reuters_india", 2, "Cabinet clears bill", "policy", 1)]
    assert score_event(primary, now=NOW)[0] > score_event(wire, now=NOW)[0]


def test_downweight_reduces_score():
    plain = [_item("reuters_india", 2, "Government announces policy", "budget", 1)]
    outrage = [
        _item(
            "reuters_india",
            2,
            "Government announces policy",
            "budget viral netizens outrage backlash slams",
            1,
        )
    ]
    assert score_event(plain, now=NOW)[0] > score_event(outrage, now=NOW)[0]


def test_fresher_event_scores_higher():
    fresh = [_item("pib", 1, "Cabinet clears bill", "policy", 1)]
    stale = [_item("pib", 1, "Cabinet clears bill", "policy", 47)]
    assert score_event(fresh, now=NOW)[0] > score_event(stale, now=NOW)[0]


def test_single_outlet_no_anchor_penalty():
    lonely = [_item("reddit_india", 3, "unverified rumor", "", 1)]
    f = extract_features(lonely, now=NOW)
    assert f.signal_only is True
    assert score_features(f) == 0.0


def test_score_never_negative():
    trash = [
        _item("reddit_india", 3, "viral meme", "netizens trolls outrage backlash slams spat", 1)
    ]
    assert score_event(trash, now=NOW)[0] >= 0.0
