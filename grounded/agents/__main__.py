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


def _default_site_dir() -> "Path":
    """Sibling ``grounded-page`` repo, overridable via GROUNDED_PAGE_DIR."""
    import os
    from pathlib import Path

    override = os.environ.get("GROUNDED_PAGE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "grounded-page").resolve()


def _copy_edition_to_site(out_path: "Path", site_dir: "Path | None") -> None:
    from pathlib import Path

    from grounded.handoff import sync_edition_bundle

    site_root = Path(site_dir).expanduser().resolve() if site_dir else _default_site_dir()
    if not site_root.is_dir():
        click.echo(
            f"[publish] grounded-page not found at {site_root}\n"
            "          set GROUNDED_PAGE_DIR or pass --site /path/to/grounded-page\n"
            "          (edition was still written to output/)",
            err=True,
        )
        return
    synced = sync_edition_bundle(edition_file=out_path, site_root=site_root)
    click.echo(f"[publish] copied → {synced['markdown']}")
    if synced["images"]:
        click.echo(f"[publish] copied → {synced['images']}")


@cli.command("enrich")
@click.option(
    "--date",
    "edition_date",
    default=None,
    help="Edition date in YYYY-MM-DD (defaults to today). Only used to name the "
    "output file and the image-cache folder — the DB state is not filtered by date.",
)
@click.option(
    "--out",
    "out_path",
    default=None,
    help="Output file path (defaults to OUTPUT_DIR/edition-<date>.md).",
)
@click.option(
    "--no-site",
    is_flag=True,
    help="Skip copying the enriched edition into grounded-page.",
)
@click.option(
    "--site",
    "site_dir",
    default=None,
    help="Override path to the grounded-page repo.",
)
@click.option(
    "--skip-fetch",
    is_flag=True,
    help="Skip the image fetch/extract step (use existing story_images rows).",
)
@click.option(
    "--skip-verify",
    is_flag=True,
    help="Skip the Gemini vision verify + dedup pass over story_images.",
)
def cmd_enrich(
    edition_date: str | None,
    out_path: str | None,
    no_site: bool,
    site_dir: str | None,
    skip_fetch: bool,
    skip_verify: bool,
) -> None:
    """Run the image-enrichment pass on the currently-approved stories and
    re-render the edition file. Does not wipe the DB or rebuild stories."""
    from datetime import datetime
    from pathlib import Path

    from grounded.agents.edition import render_edition
    from grounded.config import settings
    from grounded.pipeline.images import (
        enrich_stories_with_images,
        verify_and_dedup_images,
    )

    if edition_date is None:
        edition_date = datetime.now().strftime("%Y-%m-%d")

    out_dir = Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not skip_fetch:
        click.echo(f"[enrich] fetching images for approved stories (date={edition_date})...")
        ires = enrich_stories_with_images(out_dir, edition_date)
        click.echo(
            f"  images: {ires['with_images']}/{ires['stories']} stories "
            f"({ires['primary_hits']} primary, {ires['fallback_hits']} fallback)"
        )
    else:
        click.echo("[enrich] skip-fetch: using existing story_images rows")

    if not skip_verify:
        click.echo("[enrich] Gemini vision verify + dedup + recaption...")
        vres = verify_and_dedup_images()
        click.echo(
            f"  verify: reviewed {vres['checked']} image(s) across {vres['stories']} stor(y/ies); "
            f"dropped {vres['dropped_irrelevant']} irrelevant + {vres['dropped_duplicate']} duplicate; "
            f"recaptioned {vres['recaptioned']}; errors {vres['errors']}"
        )
    else:
        click.echo("[enrich] skip-verify: not running LLM check")

    click.echo("[enrich] rendering edition...")
    md = render_edition(approved_only=True)
    if out_path is None:
        out_path = str(out_dir / f"edition-{edition_date}.md")
    Path(out_path).write_text(md, encoding="utf-8")
    click.echo(f"[enrich] wrote {out_path}")

    if not no_site:
        site = Path(site_dir).expanduser().resolve() if site_dir else None
        _copy_edition_to_site(Path(out_path), site)


@cli.command("coherence")
@click.option(
    "--date",
    "edition_date",
    default=None,
    help="Edition date in YYYY-MM-DD (defaults to today). Used only to name "
    "the output file; the DB state is not filtered by date.",
)
@click.option(
    "--out",
    "out_path",
    default=None,
    help="Output file path (defaults to OUTPUT_DIR/edition-<date>.md).",
)
@click.option(
    "--no-render",
    is_flag=True,
    help="Skip re-rendering the edition file (only mutate the DB).",
)
@click.option(
    "--no-site",
    is_flag=True,
    help="Skip copying the edition into grounded-page.",
)
@click.option(
    "--site",
    "site_dir",
    default=None,
    help="Override path to the grounded-page repo.",
)
def cmd_coherence(
    edition_date: str | None,
    out_path: str | None,
    no_render: bool,
    no_site: bool,
    site_dir: str | None,
) -> None:
    """Run the coherence check + repair pass over currently-approved stories
    and re-render the edition file. Does not wipe the DB or rebuild stories."""
    from datetime import datetime
    from pathlib import Path

    from grounded.agents.coherence import check_and_repair_coherence
    from grounded.agents.edition import render_edition
    from grounded.config import settings

    if edition_date is None:
        edition_date = datetime.now().strftime("%Y-%m-%d")

    out_dir = Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    click.echo("[coherence] checking headline/dek vs body for every approved story...")
    cres = check_and_repair_coherence()
    click.echo(
        f"  coherence: {cres['coherent']}/{cres['stories']} coherent, "
        f"{cres['rewritten']} rewritten, {cres['dropped']} dropped, "
        f"{cres['errors']} error(s)"
    )

    if no_render:
        return

    click.echo("[coherence] rendering edition...")
    md = render_edition(approved_only=True)
    if out_path is None:
        out_path = str(out_dir / f"edition-{edition_date}.md")
    Path(out_path).write_text(md, encoding="utf-8")
    click.echo(f"[coherence] wrote {out_path}")

    if not no_site:
        site = Path(site_dir).expanduser().resolve() if site_dir else None
        _copy_edition_to_site(Path(out_path), site)


@cli.command("publish")
@click.option("--skip-wipe", is_flag=True, help="Don't wipe DB before running (useful for testing).")
@click.option("--limit", default=None, type=int, help="Override pipeline top_n.")
@click.option("--no-site", is_flag=True, help="Skip copying the edition into grounded-page.")
@click.option("--site", "site_dir", default=None, help="Override path to the grounded-page repo.")
def cmd_publish(skip_wipe: bool, limit: int | None, no_site: bool, site_dir: str | None) -> None:
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

    # 4. BUILD + DEDUP with top-up loop.
    #
    # Publish target: at least ``min_final_stories`` approved stories in the
    # final edition. If build+dedup leaves fewer, promote the next best-scoring
    # candidate events and repeat scrape+build+dedup. Bounded to 3 top-up
    # passes so a genuinely thin news day doesn't stall the pipeline.
    from grounded.agents.deduper import dedupe_stories
    from grounded.pipeline.importance import promote_next_candidates

    target = settings.min_final_stories
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

    click.echo("[publish] dedup pass...")
    dres = dedupe_stories()
    click.echo(
        f"  dedup: {dres['pairs_checked']} pair(s) checked, "
        f"{dres['dropped']} stor(y/ies) dropped"
    )

    def _approved_count() -> int:
        with cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM stories WHERE editor_approved = TRUE")
            return int(cur.fetchone()["c"])

    for attempt in range(1, 4):
        approved_now = _approved_count()
        if approved_now >= target:
            click.echo(
                f"[publish] approved={approved_now} >= target={target}; done topping up"
            )
            break
        deficit = target - approved_now
        # Overshoot the deficit — some new stories will be rejected by the
        # editor or dropped by dedup. Cap so we don't runaway on a thin day.
        batch = min(max(deficit * 2, 5), 15)
        click.echo(
            f"[publish] top-up pass {attempt}: approved={approved_now} < {target}; "
            f"promoting {batch} more candidate event(s)..."
        )
        promoted = promote_next_candidates(batch)
        if not promoted:
            click.echo("  no more eligible candidates; stopping top-up")
            break

        click.echo("[publish] scrape (top-up)...")
        sres = scrape_selected_events()
        click.echo(
            f"  scraped {sres['scraped']}, empty {sres['empty']}, "
            f"failed {sres['failed']} (of {sres['pending']} pending)"
        )
        click.echo("[publish] build (top-up)...")
        # Pass limit=batch so this pass only processes the freshly-promoted
        # events. Without the limit, any SELECTED events without a story row
        # (e.g. from prior failures) would be re-attempted every top-up pass
        # and the candidate count would snowball.
        bres = build_stories(limit=batch)
        click.echo(
            f"  built {bres['built']}: {bres['approved']} approved, "
            f"{bres['rejected']} rejected, {bres['skipped']} skipped, "
            f"{bres.get('failed', 0)} failed"
        )
        click.echo("[publish] dedup (top-up)...")
        dres = dedupe_stories()
        click.echo(
            f"  dedup: {dres['pairs_checked']} pair(s) checked, "
            f"{dres['dropped']} stor(y/ies) dropped"
        )
    else:
        click.echo(
            f"[publish] top-up cap reached (3 passes); approved={_approved_count()}"
        )

    # 6b. COHERENCE — catch stories where the headline no longer describes
    # the body (Layer-2 clustering can merge two events; the reporter writes
    # from one, the title comes from the other). Rewrites where possible,
    # drops where the body itself is a mix. Runs BEFORE image enrichment so
    # the image verify step gets the corrected headlines.
    click.echo("[publish] coherence check...")
    from grounded.agents.coherence import check_and_repair_coherence
    cres = check_and_repair_coherence()
    click.echo(
        f"  coherence: {cres['coherent']}/{cres['stories']} coherent, "
        f"{cres['rewritten']} rewritten, {cres['dropped']} dropped, "
        f"{cres['errors']} error(s)"
    )

    # 6c. IMAGES — re-fetch every cited article's HTML, extract 1-3 images
    # per story (article-body scoping, cross-story dedup, junk blocklist),
    # then run the Gemini vision pass to verify relevance, drop visual
    # duplicates, and rewrite captions grounded in the body.
    click.echo("[publish] fetching images for approved stories...")
    from grounded.pipeline.images import (
        enrich_stories_with_images,
        verify_and_dedup_images,
    )
    edition_date_str = datetime.now().strftime("%Y-%m-%d")
    ires = enrich_stories_with_images(out_dir, edition_date_str)
    click.echo(
        f"  images: {ires['with_images']}/{ires['stories']} stories "
        f"({ires['primary_hits']} primary, {ires['fallback_hits']} fallback)"
    )
    click.echo("[publish] Gemini vision verify + dedup + recaption...")
    vres = verify_and_dedup_images()
    click.echo(
        f"  verify: reviewed {vres['checked']} image(s) across {vres['stories']} stor(y/ies); "
        f"dropped {vres['dropped_irrelevant']} irrelevant + {vres['dropped_duplicate']} duplicate; "
        f"recaptioned {vres['recaptioned']}; errors {vres['errors']}"
    )

    # 7. EDITION.
    click.echo("[publish] rendering edition...")
    md = render_edition(approved_only=True)
    out_path = out_dir / f"edition-{datetime.now():%Y-%m-%d}.md"
    out_path.write_text(md, encoding="utf-8")
    elapsed_min = (time.monotonic() - t0) / 60
    click.echo(f"[publish] wrote {out_path} (total {elapsed_min:.1f} min)")

    if not no_site:
        site = Path(site_dir).expanduser().resolve() if site_dir else None
        _copy_edition_to_site(out_path, site)


if __name__ == "__main__":
    cli()
