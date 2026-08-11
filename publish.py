"""One-shot daily publish for Grounded.

Runs the full pipeline end-to-end:

    wipe -> ingest -> embed -> cluster -> rank -> scrape ->
    build (crew) -> dedup -> top-up loop ->
    coherence check (headline/dek match body?) ->
    image fetch + Gemini vision verify (relevance, dedup, recaption) ->
    render edition -> copy to grounded-page ->
    translate into Indian languages (Gemini) -> copy to grounded-page

Run:
    python publish.py                 # full fresh publish + copy to grounded-page
    python publish.py --skip-wipe     # keep existing DB contents
    python publish.py --limit 30      # override top-N
    python publish.py --no-site       # skip copy into ../grounded-page
    python publish.py --no-translate  # English only
    python publish.py --lang hi --lang bn   # override target languages

Output:
    ./output/edition-YYYY-MM-DD.md
    ./output/images/YYYY-MM-DD/*                        (downloaded photo backups)
    ./output/editions/YYYY-MM-DD/edition-YYYY-MM-DD.en.md
    ./output/editions/YYYY-MM-DD/edition-YYYY-MM-DD.<lang>.md
                                     (hi, kn, mr, te by default)
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
