"""One-shot daily publish for Grounded.

Wipes the DB, runs the full pipeline, builds all stories, renders the daily
edition markdown, and (by default) copies it into the sibling reader site.

Run:
    python publish.py                 # full fresh publish + copy to grounded-page
    python publish.py --skip-wipe     # keep existing DB contents
    python publish.py --limit 30      # override top-N
    python publish.py --no-site       # skip copy into ../grounded-page

Output: ./output/edition-YYYY-MM-DD.md
"""

from __future__ import annotations

import sys

from grounded.agents.__main__ import cli


def main() -> None:
    # Force the `publish` subcommand + forward any remaining args (e.g. --limit).
    sys.argv = [sys.argv[0], "publish", *sys.argv[1:]]
    cli()


if __name__ == "__main__":
    main()
