"""Copy a rendered edition bundle into the frontend repo layout.

Contract (shared with grounded-page/scripts/sync-editions.mjs):
  - ``edition-YYYY-MM-DD.md`` → ``content/editions/``
  - ``images/YYYY-MM-DD/*``   → ``public/images/YYYY-MM-DD/``
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

EDITION_RE = re.compile(r"^edition-(\d{4}-\d{2}-\d{2})\.md$")


def edition_date_from_path(path: Path) -> str:
    match = EDITION_RE.match(path.name)
    if not match:
        raise ValueError(f"not an edition file: {path.name}")
    return match.group(1)


def sync_edition_bundle(*, edition_file: Path, site_root: Path) -> dict[str, Path | None]:
    """Copy edition markdown and its image folder into a frontend repo checkout."""
    edition_file = edition_file.resolve()
    site_root = site_root.resolve()
    if not edition_file.is_file():
        raise FileNotFoundError(edition_file)

    date = edition_date_from_path(edition_file)

    dest_md = site_root / "content" / "editions" / edition_file.name
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(edition_file, dest_md)

    dest_images: Path | None = None
    src_images = edition_file.parent / "images" / date
    if src_images.is_dir():
        dest_images = site_root / "public" / "images" / date
        dest_images.parent.mkdir(parents=True, exist_ok=True)
        if dest_images.exists():
            shutil.rmtree(dest_images)
        shutil.copytree(src_images, dest_images)

    return {"markdown": dest_md, "images": dest_images}
