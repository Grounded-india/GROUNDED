"""
Layer 2 — importance ranking.

Scores each event on the axes the product cares about and deliberately
downweights the axes that make mainstream feeds gameable.

Scored up:
  * Primary-source anchoring — is there an official document/wire behind it?
    This is the single biggest lever.
  * Policy / legal impact — does it touch law, spending, or rights?
  * Corroboration — how many *independent* sources (distinct outlets), not
    how many raw items, so spamming one outlet can't inflate a story.
  * Recency.

Scored down:
  * Outrage / celebrity / virality language.
  * Signal-only events (tier-3 only): social is topic radar, never truth
    signal — such events do not advance to Layer 3 at all.
  * Single-outlet stories with no primary/wire anchor.

The scoring is a pure function of extracted features so it is fully
deterministic and unit-testable. :func:`rank_events` is the DB wrapper.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from grounded.config import settings
from grounded.db import cursor
from grounded.models import EventStatus, SourceTier

log = logging.getLogger(__name__)


# Keywords that indicate real policy / legal / fiscal impact (law, spending,
# rights). Matched case-insensitively as substrings of title+content.
POLICY_IMPACT_KEYWORDS: tuple[str, ...] = (
    "supreme court", "high court", "verdict", "judgment", "judgement", "ruling",
    "bill", "ordinance", "amendment", "act ", "legislation", "parliament",
    "lok sabha", "rajya sabha", "cabinet", "ministry", "gazette", "notification",
    "policy", "regulation", "regulatory", "guidelines", "mandate", "sanction",
    "tax", "gst", "budget", "fiscal", "tariff", "subsidy", "scheme", "allocation",
    "rbi", "repo rate", "monetary policy", "sebi", "reserve bank",
    "election commission", "reservation", "rights", "constitution",
    "petition", "fine", "penalty",
)

# Language typical of outrage cycles, celebrity noise, and unverified virality.
DOWNWEIGHT_KEYWORDS: tuple[str, ...] = (
    "viral", "goes viral", "netizens", "trolls", "trolled", "slams", "slammed",
    "backlash", "outrage", "twitter reacts", "internet reacts", "fans", "meme",
    "bollywood", "box office", "trailer", "teaser", "actor", "actress",
    "celebrity", "star kid", "wedding", "dating", "girlfriend", "boyfriend",
    "instagram", "reels", "controversy erupts", "war of words", "spat",
    "shocking", "you won't believe", "sensational", "gossip",
)


@dataclass
class ItemView:
    """Minimal view of a raw_item needed for scoring."""

    source_name: str
    source_tier: int
    title: str | None = None
    content: str = ""
    timestamp: datetime | None = None


@dataclass
class EventFeatures:
    num_items: int
    distinct_sources: int
    tier1_sources: int
    tier2_sources: int
    has_tier1: bool
    has_tier2: bool
    signal_only: bool
    policy_impact_hits: int
    downweight_hits: int
    recency_hours: float
    matched_policy_keywords: list[str] = field(default_factory=list)
    matched_downweight_keywords: list[str] = field(default_factory=list)

    @property
    def tier_1_anchor(self) -> bool:
        """Backed by at least one primary or wire source."""
        return self.has_tier1 or self.has_tier2


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Return the distinct keywords present in ``text`` (already lowercased)."""
    return [kw for kw in keywords if kw in text]


def extract_features(items: list[ItemView], now: datetime | None = None) -> EventFeatures:
    if not items:
        raise ValueError("cannot extract features from an empty event")
    now = now or datetime.now(UTC)

    distinct_sources = {it.source_name for it in items}
    tier1 = {it.source_name for it in items if int(it.source_tier) == SourceTier.PRIMARY}
    tier2 = {it.source_name for it in items if int(it.source_tier) == SourceTier.WIRE}
    has_tier1 = bool(tier1)
    has_tier2 = bool(tier2)
    signal_only = all(int(it.source_tier) == SourceTier.SIGNAL for it in items)

    combined = " \n ".join(
        f"{it.title or ''} {it.content or ''}" for it in items
    ).lower()
    policy = _count_keyword_hits(combined, POLICY_IMPACT_KEYWORDS)
    downweight = _count_keyword_hits(combined, DOWNWEIGHT_KEYWORDS)

    timestamps = [_as_utc(it.timestamp) for it in items if it.timestamp is not None]
    last_seen = max(timestamps) if timestamps else now
    recency_hours = max(0.0, (now - last_seen).total_seconds() / 3600.0)

    return EventFeatures(
        num_items=len(items),
        distinct_sources=len(distinct_sources),
        tier1_sources=len(tier1),
        tier2_sources=len(tier2),
        has_tier1=has_tier1,
        has_tier2=has_tier2,
        signal_only=signal_only,
        policy_impact_hits=len(policy),
        downweight_hits=len(downweight),
        recency_hours=recency_hours,
        matched_policy_keywords=policy,
        matched_downweight_keywords=downweight,
    )


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def score_features(f: EventFeatures, recency_window_hours: float = 48.0) -> float:
    """
    Turn features into a single importance score (>= 0). Higher = more important.

    Weights are intentionally hand-tuned and transparent so a broadcast can be
    audited: you can point at exactly why an event ranked where it did.
    """
    score = 0.0

    # Primary-source anchoring — the dominant term.
    if f.has_tier1:
        score += 4.0
    elif f.has_tier2:
        score += 2.0

    # Independent corroboration (distinct outlets), with diminishing returns.
    score += min(f.distinct_sources, 6) * 0.6
    # Extra weight for multiple independent primary sources.
    score += min(f.tier1_sources, 4) * 0.5

    # Policy / legal / fiscal impact.
    score += min(f.policy_impact_hits, 5) * 0.5

    # Recency: linear decay to zero across the window.
    score += max(0.0, 1.0 - f.recency_hours / recency_window_hours)

    # --- downweights: what makes the ranker resistant to being gamed ---
    score -= min(f.downweight_hits, 6) * 0.7

    # Social-only: topic radar, never truth signal.
    if f.signal_only:
        score -= 3.0

    # Single outlet with no primary/wire anchor.
    if f.distinct_sources == 1 and not f.tier_1_anchor:
        score -= 1.0

    return max(0.0, score)


def score_event(items: list[ItemView], now: datetime | None = None) -> tuple[float, EventFeatures]:
    features = extract_features(items, now=now)
    return score_features(features), features


def _load_candidate_events() -> dict:
    """Return {event_id: [ItemView, ...]} for all candidate events."""
    with cursor() as cur:
        cur.execute(
            """
            SELECT e.id AS event_id,
                   r.source_name,
                   r.source_tier,
                   r.title,
                   r.content,
                   COALESCE(r.published_at, r.fetched_at) AS ts
            FROM events e
            JOIN event_items ei ON ei.event_id = e.id
            JOIN raw_items r    ON r.id = ei.raw_item_id
            WHERE e.status = %s
            ORDER BY e.id
            """,
            (EventStatus.CANDIDATE,),
        )
        rows = cur.fetchall()

    events: dict = {}
    for r in rows:
        events.setdefault(r["event_id"], []).append(
            ItemView(
                source_name=r["source_name"],
                source_tier=int(r["source_tier"]),
                title=r["title"],
                content=r["content"] or "",
                timestamp=r["ts"],
            )
        )
    return events


def rank_events(top_n: int | None = None, now: datetime | None = None) -> dict:
    """
    Score every candidate event, persist scores, and promote the top events to
    ``selected`` so Layer 3 can pick them up.

    Only events with a primary/wire anchor are eligible for selection —
    social-only events never advance. Returns a small summary dict.
    """
    top_n = settings.select_top_n if top_n is None else top_n
    now = now or datetime.now(UTC)

    events = _load_candidate_events()
    if not events:
        log.info("no candidate events to rank")
        return {"scored": 0, "selected": 0}

    scored: list[tuple[object, float, EventFeatures]] = []
    with cursor() as cur:
        for event_id, items in events.items():
            score, features = score_event(items, now=now)
            cur.execute(
                "UPDATE events SET importance_score = %s, tier_1_anchor = %s WHERE id = %s",
                (score, features.tier_1_anchor, event_id),
            )
            scored.append((event_id, score, features))

    eligible = [
        (eid, score) for (eid, score, feat) in scored if feat.tier_1_anchor and score > 0
    ]
    eligible.sort(key=lambda x: x[1], reverse=True)
    selected_ids = [eid for eid, _ in eligible[:top_n]]

    if selected_ids:
        with cursor() as cur:
            cur.execute(
                "UPDATE events SET status = %s WHERE id = ANY(%s)",
                (EventStatus.SELECTED, selected_ids),
            )

    log.info("scored %d events, selected %d", len(scored), len(selected_ids))
    return {"scored": len(scored), "selected": len(selected_ids)}
