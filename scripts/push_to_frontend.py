#!/usr/bin/env python3
"""Copy today's edition bundle into grounded-page and push to GitHub."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from grounded.handoff import sync_edition_bundle  # noqa: E402


def _run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Push an edition bundle to grounded-page.")
    parser.add_argument("--site", required=True, help="Path to grounded-page repo checkout")
    parser.add_argument("--source-dir", default="output", help="GROUNDED output directory")
    parser.add_argument("--date", default=None, help="Edition date YYYY-MM-DD (default: today)")
    parser.add_argument("--edition", default=None, help="Explicit path to edition markdown")
    parser.add_argument("--branch", default="main", help="Frontend branch to push")
    args = parser.parse_args(argv)

    date = args.date or datetime.now().strftime("%Y-%m-%d")
    edition = (
        Path(args.edition).expanduser().resolve()
        if args.edition
        else (Path(args.source_dir).expanduser().resolve() / f"edition-{date}.md")
    )
    site = Path(args.site).expanduser().resolve()

    if not edition.is_file():
        print(f"push_to_frontend: edition not found: {edition}", file=sys.stderr)
        return 1
    if not site.is_dir():
        print(f"push_to_frontend: site repo not found: {site}", file=sys.stderr)
        return 1

    synced = sync_edition_bundle(edition_file=edition, site_root=site)
    print(f"push_to_frontend: copied → {synced['markdown']}")
    if synced["images"]:
        print(f"push_to_frontend: copied → {synced['images']}")

    author_name = os.environ.get("GIT_AUTHOR_NAME", "GROUNDED Bot")
    author_email = os.environ.get("GIT_AUTHOR_EMAIL", "bot@grounded.india")
    _run(["git", "config", "user.name", author_name], cwd=site)
    _run(["git", "config", "user.email", author_email], cwd=site)

    add_paths = [str(synced["markdown"].relative_to(site))]
    if synced["images"]:
        add_paths.append(str(synced["images"].relative_to(site)))
    _run(["git", "add", *add_paths], cwd=site)

    diff = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=site)
    if diff.returncode == 0:
        print("push_to_frontend: no changes to commit")
        return 0

    _run(["git", "commit", "-m", f"chore: publish edition {date}"], cwd=site)
    _run(["git", "push", "origin", f"HEAD:{args.branch}"], cwd=site)
    print(f"push_to_frontend: pushed edition {date} to {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
