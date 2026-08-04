"""Tests for edition handoff into the frontend repo layout."""

from __future__ import annotations

from pathlib import Path

import pytest

from grounded.handoff import edition_date_from_path, sync_edition_bundle


def test_edition_date_from_path():
    assert edition_date_from_path(Path("edition-2026-08-04.md")) == "2026-08-04"


def test_edition_date_from_path_rejects_bad_name():
    with pytest.raises(ValueError):
        edition_date_from_path(Path("not-an-edition.md"))


def test_sync_edition_bundle_copies_md_and_images(tmp_path: Path):
    out = tmp_path / "output"
    site = tmp_path / "site"
    date = "2026-08-04"
    edition = out / f"edition-{date}.md"
    img_dir = out / "images" / date
    img_dir.mkdir(parents=True)
    edition.write_text("# Edition\n", encoding="utf-8")
    (img_dir / "photo.jpg").write_bytes(b"jpeg")

    synced = sync_edition_bundle(edition_file=edition, site_root=site)

    assert synced["markdown"] == site / "content" / "editions" / edition.name
    assert synced["markdown"].read_text(encoding="utf-8") == "# Edition\n"
    assert synced["images"] == site / "public" / "images" / date
    assert (synced["images"] / "photo.jpg").read_bytes() == b"jpeg"
