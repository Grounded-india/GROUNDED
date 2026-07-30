"""Shared date/time framing helpers used by editor, reporter, and debate prompts.

Every generation agent that produces reader-facing text (headline, dek, body,
debate turn) is now expected to be time-aware. This module gives them one
consistent way to know what "today" is and how the event's date relates to it.

The helpers are prompt-facing strings, not code that mutates the model output.
The model still decides whether to include a date in the headline — but with
these strings in its context it has the information to do so accurately.
"""

from __future__ import annotations

from datetime import UTC, datetime


def _to_local(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone()


def _pick_event_date(
    first_seen_at: datetime | None,
    earliest_source_published_at: datetime | None,
) -> datetime | None:
    """The date the event actually happened, best-effort.

    Prefers the earliest source publish time (that is the reporter's own timestamp
    on the event) and falls back to when our ingest first saw the event.
    """
    return _to_local(earliest_source_published_at or first_seen_at)


def build_time_context(
    first_seen_at: datetime | None,
    earliest_source_published_at: datetime | None,
    *,
    now: datetime | None = None,
) -> str:
    """Return a compact multi-line block for injection into a prompt.

    Example output::

        TIME CONTEXT
        TODAY IS Thursday, 30 July 2026.
        This event was first reported: Wednesday, 29 July 2026 (yesterday, ~14 hours ago).
        When you name a day in the headline or dek, use the relative day
        ("yesterday", "Wednesday"), and reserve the full absolute date for
        archive pieces (older than 7 days) or when the day of week alone would
        be ambiguous.
    """
    now = _to_local(now or datetime.now(UTC))
    event_at = _pick_event_date(first_seen_at, earliest_source_published_at)

    lines = ["TIME CONTEXT", f"TODAY IS {now:%A, %d %B %Y}."]

    if event_at is None:
        lines.append(
            "The event's date is unknown; do not invent one. Prefer present-tense "
            "framing without a date in the headline."
        )
    else:
        # Prefer calendar-day comparison over rolling 24-hour windows: a story
        # that landed at 4am today reads as "today", not "9 hours ago"; a story
        # from yesterday evening reads as "yesterday", not "today, earlier".
        cal_days = (now.date() - event_at.date()).days
        hours = int((now - event_at).total_seconds() // 3600)
        if hours < 0:
            # Source is timestamped in the future (rare — bad publisher clock).
            when = "future-stamped source (do not surface as 'today')"
        elif cal_days == 0:
            when = "today"
        elif cal_days == 1:
            when = "yesterday"
        elif 1 < cal_days <= 6:
            when = f"{event_at:%A} ({cal_days} days ago)"
        elif 6 < cal_days <= 30:
            when = f"{event_at:%d %B} ({cal_days} days ago)"
        else:
            when = f"{event_at:%d %B %Y} — archive piece ({cal_days} days ago)"

        lines.append(
            f"This event was first reported: {event_at:%A, %d %B %Y} ({when})."
        )

    lines.append(
        "Guidance: bake the timing into the headline or dek when the timing is "
        "load-bearing (a vote today, a protest yesterday, a court order on Monday). "
        "Use the relative day for events within the last week ('today', "
        "'yesterday', 'Monday'), and the absolute date for anything older or for "
        "archive material. Do NOT prepend a date if it does not add information "
        "(e.g. steady-state analysis pieces, ongoing situations). Never invent a "
        "date the sources do not give you."
    )
    return "\n".join(lines)
