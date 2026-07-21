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
from typing import Any

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

# Ground-reality events: protests, incidents, resignations, court verdicts,
# etc. Scored equal to policy keywords so multi-source non-government stories
# can rank alongside government press releases instead of always losing to
# them. Matched case-insensitively as substrings of title+content.
GROUND_REALITY_KEYWORDS: tuple[str, ...] = (
    "protest", "march", "rally", "strike", "shutdown", "blockade", "bandh",
    "clash", "violence", "riot", "lathi", "teargas", "water cannon",
    "arrest", "detained", "custody", "remand", "chargesheet", "fir ",
    "killed", "injured", "dead", "casualties", "victim", "died", "death toll",
    "resignation", "resigned", "dismissed", "sacked", "suspended",
    "inquiry", "probe", "investigation", "scandal", "allegation", "accused",
    "verdict", "acquittal", "conviction", "guilty", "sentenced",
    "explosion", "attack", "assault", "raid", "seized",
)

# India-relevance signal. The whole product is India-focused, so this is a
# large lever applied as a SWING (positive if the event is about India,
# negative if it clearly is not). Matched case-insensitively as substrings
# of title+content. If your ingest fans out globally later, tune weights.
INDIA_KEYWORDS: tuple[str, ...] = (
    "india", "indian", "bharat", "hindustan",
    "delhi", "new delhi", "mumbai", "bengaluru", "bangalore", "chennai",
    "kolkata", "hyderabad", "pune", "ahmedabad", "lucknow", "jaipur",
    "modi", "narendra modi", "rahul gandhi", "amit shah", "kejriwal",
    "yogi", "mamata", "stalin", "sonia gandhi", "priyanka gandhi",
    "parliament", "lok sabha", "rajya sabha", "sansad", "monsoon session",
    "bjp", "congress", "aap", "tmc", "dmk", "aiadmk", "shiv sena", "ncp",
    "supreme court of india", "high court", "cji", "chief justice of india",
    "rbi", "reserve bank of india", "sebi", "pib", "prs india",
    "niti aayog", "aadhaar", "gst", "cbi", " ed ", "nia", "cag",
    "kashmir", "ladakh", "manipur", "punjab", "tamil nadu", "karnataka",
    "kerala", "maharashtra", "gujarat", "uttar pradesh", "bihar",
    "west bengal", "odisha", "assam", "andhra pradesh", "telangana",
    "rajasthan", "madhya pradesh", "haryana", "himachal", "uttarakhand",
    "jharkhand", "chhattisgarh", "goa", "sikkim", "nagaland", "meghalaya",
    "arunachal pradesh", "tripura", "mizoram",
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
    ground_reality_hits: int
    india_hits: int
    downweight_hits: int
    recency_hours: float
    matched_policy_keywords: list[str] = field(default_factory=list)
    matched_ground_reality_keywords: list[str] = field(default_factory=list)
    matched_india_keywords: list[str] = field(default_factory=list)
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
    ground_reality = _count_keyword_hits(combined, GROUND_REALITY_KEYWORDS)
    india = _count_keyword_hits(combined, INDIA_KEYWORDS)
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
        ground_reality_hits=len(ground_reality),
        india_hits=len(india),
        downweight_hits=len(downweight),
        recency_hours=recency_hours,
        matched_policy_keywords=policy,
        matched_ground_reality_keywords=ground_reality,
        matched_india_keywords=india,
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

    # Primary-source anchoring. Kept as a positive signal but no longer
    # dominant — a lone government press release should not outrank a
    # well-corroborated cross-source ground-reality story.
    if f.has_tier1:
        score += 2.5
    elif f.has_tier2:
        score += 1.5

    # Independent corroboration (distinct outlets), with diminishing returns.
    # This is the strongest signal for ground-reality events that governments
    # do not announce but multiple wires and social feeds report.
    score += min(f.distinct_sources, 8) * 0.9
    # Extra weight for multiple independent primary sources.
    score += min(f.tier1_sources, 4) * 0.5
    # Same treatment for multiple independent wire sources.
    score += min(f.tier2_sources, 4) * 0.5

    # Policy / legal / fiscal impact.
    score += min(f.policy_impact_hits, 5) * 0.5
    # Ground-reality impact (protests, arrests, verdicts, resignations, etc.).
    score += min(f.ground_reality_hits, 5) * 0.5

    # India relevance — the whole product is India-focused. This is a large
    # lever comparable to tier-1 anchoring, applied as a SWING not a bonus:
    #   >= 3 India mentions → strong positive
    #   0 India mentions   → strong negative
    # A story with zero India mentions has to be extraordinarily well-
    # corroborated to stay in the top selection.
    if f.india_hits >= 3:
        score += 3.0
    elif f.india_hits == 0:
        score -= 4.0

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


def _load_rankable_events() -> dict:
    """
    Return {event_id: [ItemView, ...]} for every re-rankable event.

    Both ``candidate`` and ``selected`` events are rankable so each run can
    re-select from the full pool (and demote stale selections). ``published``
    and ``rejected`` are terminal, Layer-3-owned states and are left untouched.
    """
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
            WHERE e.status IN (%s, %s)
            ORDER BY e.id
            """,
            (EventStatus.CANDIDATE, EventStatus.SELECTED),
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


def select_event_ids(
    scored: list[tuple[Any, float, EventFeatures]], top_n: int
) -> list[Any]:
    """
    Pick the ids of the top ``top_n`` events eligible for Layer 3.

    Eligible = primary/wire-anchored with a positive score; social-only events
    never advance. Pure function of its inputs so it is deterministic and
    unit-testable without a DB. Ties break toward the lower id for stability.
    """
    eligible = [
        (eid, score) for (eid, score, feat) in scored if feat.tier_1_anchor and score > 0
    ]
    eligible.sort(key=lambda x: (-x[1], str(x[0])))
    return [eid for eid, _ in eligible[:top_n]]


def rank_events(top_n: int | None = None, now: datetime | None = None) -> dict:
    """
    Score every re-rankable event, persist scores, and re-select the top events
    as ``selected`` for Layer 3.

    Idempotent: each run recomputes scores over the full candidate+selected pool
    and re-selects from scratch, demoting any previously-selected event that no
    longer makes the cut back to ``candidate``. Running it twice in a row yields
    the same selection (modulo recency drift) — selections never accumulate.

    Only events with a primary/wire anchor are eligible; social-only events
    never advance. Returns a small summary dict.
    """
    top_n = settings.select_top_n if top_n is None else top_n
    now = now or datetime.now(UTC)

    events = _load_rankable_events()
    if not events:
        log.info("no rankable events")
        return {"scored": 0, "selected": 0, "demoted": 0}

    scored: list[tuple[Any, float, EventFeatures]] = []
    with cursor() as cur:
        for event_id, items in events.items():
            score, features = score_event(items, now=now)
            cur.execute(
                "UPDATE events SET importance_score = %s, tier_1_anchor = %s WHERE id = %s",
                (score, features.tier_1_anchor, event_id),
            )
            scored.append((event_id, score, features))

    selected_ids = select_event_ids(scored, top_n)
    selected_set = set(selected_ids)
    demote_ids = [eid for eid, _, _ in scored if eid not in selected_set]

    demoted = 0
    with cursor() as cur:
        if selected_ids:
            cur.execute(
                "UPDATE events SET status = %s WHERE id = ANY(%s)",
                (EventStatus.SELECTED, selected_ids),
            )
        if demote_ids:
            # Only rows actually leaving 'selected' count as demotions, so a
            # steady-state re-run reports 0 churn.
            cur.execute(
                "UPDATE events SET status = %s WHERE id = ANY(%s) AND status = %s",
                (EventStatus.CANDIDATE, demote_ids, EventStatus.SELECTED),
            )
            demoted = cur.rowcount

    log.info(
        "scored %d events, selected %d, demoted %d",
        len(scored),
        len(selected_ids),
        demoted,
    )
    return {"scored": len(scored), "selected": len(selected_ids), "demoted": demoted}
