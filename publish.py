#!/usr/bin/env python3
"""Publish today's GROUNDED edition into the reader site.

What this does
--------------
1. Renders every approved story into one Markdown newspaper:
     GROUNDED/output/edition-YYYY-MM-DD.md
2. Copies that file into the sibling frontend repo so The Grounded Times
   can pick it up without any manual step:
     ../grounded-page/content/editions/edition-YYYY-MM-DD.md

The frontend watches that folder (``npm run dev:pipeline`` / ``npm run pipeline``)
and lays the edition out by importance on its own. Dropping the file is the
only action needed to publish.

Usage
-----
    python publish.py                  # approved stories only → both repos
    python publish.py --all            # include rejected stories too
    python publish.py --no-site        # write output/ only, skip the site copy
    python publish.py --out PATH       # custom destination for the Markdown

Env
---
    OUTPUT_DIR                 Where to write the edition (default: ./output)
    GROUNDED_PAGE_DIR          Override path to the grounded-page repo
                               (default: ../grounded-page next to this repo)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _default_site_dir() -> Path:
    """Sibling ``grounded-page`` repo, overridable via GROUNDED_PAGE_DIR."""
    import os

    override = os.environ.get("GROUNDED_PAGE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (_repo_root().parent / "grounded-page").resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render today's edition and push it into grounded-page.",
    )
    parser.add_argument(
        "--all",
        dest="include_all",
        action="store_true",
        help="Include rejected stories (default: approved only).",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=None,
        help="Custom path for the edition Markdown (default: OUTPUT_DIR/edition-<date>.md).",
    )
    parser.add_argument(
        "--no-site",
        action="store_true",
        help="Skip copying into the grounded-page content/editions folder.",
    )
    parser.add_argument(
        "--site",
        dest="site_dir",
        default=None,
        help="Override path to the grounded-page repo.",
    )
    args = parser.parse_args(argv)

    # Import after argv parse so ``--help`` works without DB/config.
    from grounded.agents.edition import render_edition
    from grounded.config import settings

    md = render_edition(approved_only=not args.include_all)
    if not md or not md.strip():
        print("publish: nothing to write — no stories rendered.", file=sys.stderr)
        return 1

    if args.out_path:
        out_path = Path(args.out_path).expanduser().resolve()
    else:
        out_dir = Path(settings.output_dir)
        if not out_dir.is_absolute():
            out_dir = (_repo_root() / out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"edition-{datetime.now():%Y-%m-%d}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"publish: wrote {out_path}")

    if args.no_site:
        return 0

    site_root = Path(args.site_dir).expanduser().resolve() if args.site_dir else _default_site_dir()
    dest_dir = site_root / "content" / "editions"
    if not site_root.is_dir():
        print(
            f"publish: grounded-page not found at {site_root}\n"
            "         set GROUNDED_PAGE_DIR or pass --site /path/to/grounded-page\n"
            "         (edition was still written to output/; sync later with "
            "`npm run sync:editions` in grounded-page)",
            file=sys.stderr,
        )
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / out_path.name
    shutil.copy2(out_path, dest)
    print(f"publish: copied → {dest}")
    print(
        "publish: done. If grounded-page is running `npm run dev:pipeline`, "
        "refresh the browser — the new edition is live."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
