"""Layer 3 CLI, runnable as ``python -m grounded.agents``.

Kept separate from the shared ``grounded.cli`` module so Layer 3 can be built in
parallel without merge conflicts. Once things settle, a ``grounded story``
subcommand can delegate here.
"""

from __future__ import annotations

import logging
from uuid import UUID

import click

from grounded.agents.runner import build_stories


def _setup_logging() -> None:
    from grounded.config import settings

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("psycopg.pool").setLevel(logging.ERROR)
    # httpx logs one line per LLM request; keep it so slow calls are visible.
    logging.getLogger("httpx").setLevel(logging.INFO)


@click.group()
def cli() -> None:
    """Layer 3 - multi-agent story building."""
    _setup_logging()


@cli.command("build")
@click.option("--force", is_flag=True, help="Rebuild stories even if one already exists.")
@click.option("--limit", default=None, type=int, help="Max events to process.")
@click.option("--event-id", default=None, help="Only build this event (UUID).")
def cmd_build(force: bool, limit: int | None, event_id: str | None) -> None:
    """Run the agent crew over selected events and persist stories."""
    eid = UUID(event_id) if event_id else None
    result = build_stories(force=force, limit=limit, event_id=eid)
    models = ", ".join(f"{role}={name}" for role, name in result["models"].items())
    click.echo(f"models: {models}")
    click.echo(
        f"built {result['built']} story(ies) from {result['candidates']} candidate(s): "
        f"{result['approved']} approved ({result['debates']} as debate), "
        f"{result['rejected']} rejected, {result['skipped']} skipped, "
        f"{result.get('failed', 0)} failed."
    )


@cli.command("list")
@click.option("--limit", default=15, help="How many stories to show.")
@click.option("--approved/--all", "approved_only", default=False, help="Only approved stories.")
def cmd_list(limit: int, approved_only: bool) -> None:
    """List built stories, newest first."""
    from grounded.db import cursor

    where = "WHERE editor_approved" if approved_only else ""
    with cursor() as cur:
        cur.execute(
            f"""
            SELECT s.headline, s.editor_approved, s.editor_notes,
                   (SELECT COUNT(*) FROM claims c WHERE c.story_id = s.id) AS n_claims
            FROM stories s
            {where}
            ORDER BY s.created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    if not rows:
        click.echo("No stories.")
        return
    for r in rows:
        mark = "OK " if r["editor_approved"] else "REJ"
        click.echo(f"[{mark}] claims={r['n_claims']:<3} {(r['headline'] or '(untitled)')[:80]}")
        if not r["editor_approved"]:
            click.echo(f"       notes: {r['editor_notes']}")


@cli.command("show")
@click.argument("event_id")
def cmd_show(event_id: str) -> None:
    """Print the full markdown body of a story by its event id."""
    from grounded.db import cursor

    with cursor() as cur:
        cur.execute(
            "SELECT headline, editor_approved, editor_notes, body_markdown "
            "FROM stories WHERE event_id = %s",
            (UUID(event_id),),
        )
        row = cur.fetchone()
    if not row:
        click.echo("No story for that event id.")
        return
    status = "APPROVED" if row["editor_approved"] else "REJECTED"
    click.echo(f"# [{status}] {row['editor_notes']}\n")
    click.echo(row["body_markdown"] or "(empty)")


if __name__ == "__main__":
    cli()
