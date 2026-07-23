"""Layer 3 CLI, runnable as ``python -m grounded.agents``.

Kept separate from the shared ``grounded.cli`` module so Layer 3 can be built in
parallel without merge conflicts. Once things settle, a ``grounded story``
subcommand can delegate here.
"""

from __future__ import annotations

import logging
from uuid import UUID

import click

# Importing sources triggers registration into the ingest registry.
# Required for `publish` and any other command that iterates the registry.
import grounded.ingest.sources  # noqa: F401
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


@cli.command("edition")
@click.option("--all", "include_all", is_flag=True, help="Include rejected stories too.")
@click.option("--out", "out_path", default=None, help="Output file (default OUTPUT_DIR/edition-<date>.md).")
@click.option("--print", "to_stdout", is_flag=True, help="Print to stdout instead of writing a file.")
def cmd_edition(include_all: bool, out_path: str | None, to_stdout: bool) -> None:
    """Render all stories into one clean, single-page markdown newspaper."""
    from datetime import datetime
    from pathlib import Path

    from grounded.agents.edition import render_edition
    from grounded.config import settings

    md = render_edition(approved_only=not include_all)
    if to_stdout:
        click.echo(md)
        return
    if out_path is None:
        out_dir = Path(settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"edition-{datetime.now():%Y-%m-%d}.md")
    Path(out_path).write_text(md, encoding="utf-8")
    click.echo(f"wrote {out_path}")


@cli.command("publish")
@click.option("--skip-wipe", is_flag=True, help="Don't wipe DB before running (useful for testing).")
@click.option("--limit", default=None, type=int, help="Override pipeline top_n.")
def cmd_publish(skip_wipe: bool, limit: int | None) -> None:
    """One-shot daily publish: wipe -> ingest -> pipeline -> build -> edition."""
    import time
    from datetime import datetime
    from pathlib import Path

    from grounded.agents.edition import render_edition
    from grounded.agents.runner import build_stories
    from grounded.config import settings
    from grounded.db import cursor
    from grounded.ingest.base import all_sources, store_raw_items
    from grounded.pipeline.clustering import build_events
    from grounded.pipeline.embed import embed_pending
    from grounded.pipeline.importance import rank_events
    from grounded.pipeline.scrape import scrape_selected_events

    t0 = time.monotonic()

    # 1. WIPE.
    if not skip_wipe:
        click.echo("[publish] wiping DB...")
        with cursor() as cur:
            cur.execute(
                "TRUNCATE raw_items, events, event_items, stories, claims, "
                "claim_sources CASCADE"
            )

    # 2. INGEST.
    click.echo("[publish] ingest...")
    total_i = total_s = 0
    for src in all_sources():
        try:
            items = list(src.fetch())
        except Exception as e:
            click.echo(f"  [{src.name}] fetch error: {e}", err=True)
            continue
        if not items:
            continue
        ins, sk = store_raw_items(items)
        total_i += ins
        total_s += sk
    click.echo(f"  {total_i} inserted, {total_s} skipped")

    out_dir = Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 3. PIPELINE (embed + cluster + rank + scrape).
    click.echo("[publish] embed...")
    n_emb = embed_pending()
    click.echo(f"  embedded {n_emb} item(s)")

    click.echo("[publish] cluster...")
    n_ev = build_events()
    click.echo(f"  created {n_ev} event(s)")

    click.echo("[publish] rank...")
    rres = rank_events(top_n=limit)
    click.echo(
        f"  scored {rres['scored']}, selected {rres['selected']}, "
        f"demoted {rres['demoted']}"
    )

    click.echo("[publish] scrape...")
    sres = scrape_selected_events()
    click.echo(
        f"  scraped {sres['scraped']}, empty {sres['empty']}, "
        f"failed {sres['failed']} (of {sres['pending']} pending)"
    )

    # 4. BUILD stories for all selected events.
    click.echo("[publish] building stories (crew)...")
    total_top = limit if limit is not None else settings.select_top_n
    bres = build_stories(limit=total_top)
    models = ", ".join(f"{r}={n}" for r, n in bres["models"].items())
    click.echo(f"  models: {models}")
    click.echo(
        f"  built {bres['built']} story(ies) from {bres['candidates']} candidate(s): "
        f"{bres['approved']} approved, {bres['rejected']} rejected, "
        f"{bres['skipped']} skipped, {bres.get('failed', 0)} failed"
    )

    # 6.5. DEDUP — catch stories that are the same real-world event framed
    #      differently, drop the lower-ranked duplicate so the reader doesn't
    #      see "the same thing in different clothes" twice in one edition.
    click.echo("[publish] dedup pass...")
    from grounded.agents.deduper import dedupe_stories
    dres = dedupe_stories()
    click.echo(
        f"  dedup: {dres['pairs_checked']} pair(s) checked, "
        f"{dres['dropped']} stor(y/ies) dropped"
    )

    # 7. EDITION.
    click.echo("[publish] rendering edition...")
    md = render_edition(approved_only=True)
    out_path = out_dir / f"edition-{datetime.now():%Y-%m-%d}.md"
    out_path.write_text(md, encoding="utf-8")
    elapsed_min = (time.monotonic() - t0) / 60
    click.echo(f"[publish] wrote {out_path} (total {elapsed_min:.1f} min)")


if __name__ == "__main__":
    cli()
