"""grounded — command-line entry point."""

from __future__ import annotations

import atexit
import logging
import sys

import click

from grounded.config import settings
from grounded.db import close_pool

# Importing sources triggers registration into the ingest registry.
import grounded.ingest.sources  # noqa: F401
from grounded.ingest.base import all_sources, get_source, store_raw_items
from grounded.models import SourceTier

atexit.register(close_pool)


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Cosmetic: psycopg-pool worker threads sometimes don't hit their 5s
    # shutdown deadline at process exit. Not actionable for CLI use.
    logging.getLogger("psycopg.pool").setLevel(logging.ERROR)


@click.group()
def cli() -> None:
    """Grounded — autonomous, fact-driven news pipeline."""
    _setup_logging()


@cli.command("sources")
def cmd_sources() -> None:
    """List registered ingest sources."""
    rows = [(s.name, s.tier.name, type(s).__name__) for s in all_sources()]
    if not rows:
        click.echo("No sources registered.")
        return
    width = max(len(name) for name, _, _ in rows)
    click.echo(f"{'NAME':<{width}}  TIER      KIND")
    click.echo("-" * (width + 22))
    for name, tier, kind in rows:
        click.echo(f"{name:<{width}}  {tier:<8}  {kind}")


@cli.command("ingest")
@click.option("--source", "source_name", default=None, help="Run only this source.")
@click.option(
    "--tier",
    type=click.IntRange(1, 3),
    default=None,
    help="Run only sources at this tier (1=primary, 2=wire, 3=signal).",
)
def cmd_ingest(source_name: str | None, tier: int | None) -> None:
    """Fetch from sources and store raw items."""
    if source_name:
        src = get_source(source_name)
        if src is None:
            click.echo(f"Unknown source: {source_name}", err=True)
            sys.exit(1)
        sources = [src]
    elif tier is not None:
        sources = [s for s in all_sources() if int(s.tier) == tier]
        if not sources:
            click.echo(f"No sources at tier {tier}", err=True)
            sys.exit(1)
    else:
        sources = all_sources()

    total_inserted = 0
    total_skipped = 0
    for src in sources:
        try:
            items = list(src.fetch())
        except Exception as e:
            click.echo(f"  [{src.name}] fetch error: {e}", err=True)
            continue

        if not items:
            click.echo(f"  [{src.name}] 0 items")
            continue

        inserted, skipped = store_raw_items(items)
        total_inserted += inserted
        total_skipped += skipped
        click.echo(
            f"  [{src.name}] fetched={len(items)} inserted={inserted} skipped={skipped}"
        )

    click.echo("")
    click.echo(f"Total: {total_inserted} inserted, {total_skipped} skipped (already in DB).")


@cli.command("status")
def cmd_status() -> None:
    """Show ingest DB stats: item counts by source and tier."""
    from grounded.db import cursor

    with cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM raw_items")
        total = cur.fetchone()["n"]
        click.echo(f"Total raw items: {total}")
        click.echo("")

        cur.execute(
            """
            SELECT source_tier, COUNT(*) AS n
            FROM raw_items
            GROUP BY source_tier
            ORDER BY source_tier
            """
        )
        click.echo("By tier:")
        for row in cur.fetchall():
            tier_name = SourceTier(row["source_tier"]).name
            click.echo(f"  tier {row['source_tier']} ({tier_name}): {row['n']}")
        click.echo("")

        cur.execute(
            """
            SELECT source_name, source_tier, COUNT(*) AS n,
                   MAX(fetched_at) AS last_fetched
            FROM raw_items
            GROUP BY source_name, source_tier
            ORDER BY source_tier, source_name
            """
        )
        rows = cur.fetchall()
        if not rows:
            return
        width = max(len(r["source_name"]) for r in rows)
        click.echo(f"{'SOURCE':<{width}}  TIER  COUNT  LAST FETCHED")
        click.echo("-" * (width + 40))
        for row in rows:
            click.echo(
                f"{row['source_name']:<{width}}  "
                f"{row['source_tier']:<4}  "
                f"{row['n']:<5}  "
                f"{row['last_fetched'].strftime('%Y-%m-%d %H:%M:%S')}"
            )


@cli.command("recent")
@click.option("--limit", default=10, help="How many recent items to show.")
@click.option("--source", "source_name", default=None, help="Filter by source.")
def cmd_recent(limit: int, source_name: str | None) -> None:
    """Show the most recently fetched raw items."""
    from grounded.db import cursor

    query = """
        SELECT source_name, source_tier, title, source_url, fetched_at
        FROM raw_items
        {where}
        ORDER BY fetched_at DESC
        LIMIT %s
    """
    params: tuple = ()
    where = ""
    if source_name:
        where = "WHERE source_name = %s"
        params = (source_name,)
    params = params + (limit,)

    with cursor() as cur:
        cur.execute(query.format(where=where), params)
        for row in cur.fetchall():
            tier = SourceTier(row["source_tier"]).name
            title = (row["title"] or "(no title)")[:80]
            click.echo(f"[{row['source_name']}/{tier}] {title}")
            click.echo(f"  {row['source_url']}")
            click.echo("")


if __name__ == "__main__":
    cli()
