"""Copy a rendered edition bundle into the frontend repo layout.

Contract (shared with grounded-page/scripts/sync-editions.mjs):
  - ``edition-YYYY-MM-DD.md`` → ``content/editions/``
  - ``images/YYYY-MM-DD/*``   → ``public/images/YYYY-MM-DD/``
  - ``editions/YYYY-MM-DD/*.md`` → ``content/editions/YYYY-MM-DD/``
    (optional multilingual bundle from the translate pass; skipped when absent)
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
    """Copy edition markdown, images, and any translation folder into a site checkout.

    English flat-file + images behavior is unchanged. If
    ``<output>/editions/<date>/`` exists (written by the translate pass), its
    ``*.md`` files are also copied to ``content/editions/<date>/``. Missing
    translations are a no-op so CI and English-only publishes keep working.
    """
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

    dest_translations: Path | None = None
    src_translations = edition_file.parent / "editions" / date
    if src_translations.is_dir() and any(src_translations.glob("*.md")):
        dest_translations = site_root / "content" / "editions" / date
        dest_translations.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_translations.glob("*.md")):
            shutil.copy2(f, dest_translations / f.name)

    return {
        "markdown": dest_md,
        "images": dest_images,
        "translations": dest_translations,
    }
