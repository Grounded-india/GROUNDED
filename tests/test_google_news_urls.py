"""Google News wrappers must resolve to the publisher, and the G logo must not ship."""

from __future__ import annotations

from pathlib import Path

from grounded.pipeline.images import (
    extract_image_candidates,
    image_data_url,
    vision_image_ref,
)
from grounded.pipeline.scrape import _resolve_url

_WRAPPER = "https://news.google.com/rss/articles/CBMi-example"
_PUBLISHER = "https://www.thehindu.com/news/example-story"
_LOGO = (
    "https://lh3.googleusercontent.com/"
    "J6_coFbogxhRI9iM864NL_liGXvsQp2AupsKei7z0cNNfDvGUmWUy20nuUhkREQyrpY4bEeIBuc=s0-w300"
)
_PHOTO = "https://cdn.example.com/photos/minister.jpg"


def test_resolve_url_accepts_success_key(monkeypatch):
    def fake(url, interval=None, timeout=None):
        assert url == _WRAPPER
        return {"success": True, "decoded_url": _PUBLISHER}

    monkeypatch.setattr("grounded.pipeline.scrape.gnewsdecoder", fake)
    assert _resolve_url(_WRAPPER) == _PUBLISHER


def test_resolve_url_accepts_legacy_status_key(monkeypatch):
    def fake(url, interval=None, timeout=None):
        raise TypeError("0.1.x has no timeout")

    def legacy(url, interval=None):
        return {"status": True, "decoded_url": _PUBLISHER}

    calls = {"n": 0}

    def routed(url, interval=None, timeout=None):
        calls["n"] += 1
        if timeout is not None:
            return fake(url, interval=interval, timeout=timeout)
        return legacy(url, interval=interval)

    monkeypatch.setattr("grounded.pipeline.scrape.gnewsdecoder", routed)
    assert _resolve_url(_WRAPPER) == _PUBLISHER
    assert calls["n"] == 2


def test_resolve_url_keeps_wrapper_when_decode_fails(monkeypatch):
    def fake(url, interval=None, timeout=None):
        return {"success": False, "message": "rate limited"}

    monkeypatch.setattr("grounded.pipeline.scrape.gnewsdecoder", fake)
    assert _resolve_url(_WRAPPER) == _WRAPPER


def test_resolve_url_ignores_decode_that_stays_on_google(monkeypatch):
    def fake(url, interval=None, timeout=None):
        return {"success": True, "decoded_url": "https://news.google.com/articles/still-wrapped"}

    monkeypatch.setattr("grounded.pipeline.scrape.gnewsdecoder", fake)
    assert _resolve_url(_WRAPPER) == _WRAPPER


def test_resolve_url_leaves_publisher_urls_alone(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("decoder should not run")

    monkeypatch.setattr("grounded.pipeline.scrape.gnewsdecoder", boom)
    assert _resolve_url(_PUBLISHER) == _PUBLISHER


def test_google_news_page_yields_no_images():
    html = f'<html><head><meta property="og:image" content="{_LOGO}"></head></html>'
    assert extract_image_candidates(_WRAPPER, html, credit="Google News") == []


def test_publisher_page_drops_google_logo_and_keeps_photo():
    html = f"""
    <html><head>
      <meta property="og:image" content="{_LOGO}">
    </head><body>
      <img src="{_PHOTO}" width="800" height="500" alt="The minister speaking">
    </body></html>
    """
    found = extract_image_candidates(_PUBLISHER, html, credit="The Hindu")
    urls = [c.url for c in found]
    assert _PHOTO in urls
    assert all(_LOGO not in u for u in urls)


def test_logo_only_page_yields_no_images():
    html = f'<html><head><meta property="og:image" content="{_LOGO}"></head></html>'
    assert extract_image_candidates(_PUBLISHER, html, credit="The Hindu") == []


def test_vision_uses_local_file_not_logo_hotlink(tmp_path: Path):
    photo = tmp_path / "story-0.jpg"
    photo.write_bytes(b"\xff\xd8\xff\xd9")
    row = {
        "local_path": photo.name,
        "source_url": _LOGO,
    }
    ref = vision_image_ref(row, tmp_path)
    assert ref is not None
    assert ref.startswith("data:image/jpeg;base64,")
    assert image_data_url(photo) == ref


def test_vision_refuses_logo_when_no_local_file(tmp_path: Path):
    row = {"local_path": "", "source_url": _LOGO}
    assert vision_image_ref(row, tmp_path) is None
