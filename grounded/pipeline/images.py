"""Image enrichment for the daily edition.

Runs after stories are built + deduped, before the edition is rendered. For each
approved story it:

1. Re-fetches the article HTML for every cited source (raw HTML is not kept in the
   DB — ``scrape.py`` stores trafilatura text only — so we have to re-request).
2. Extracts candidate ``<img>`` tags and scores them by size, position, caption
   presence, and alt-text length.
3. If nothing usable comes back, falls back to a Google-News search on the
   headline and pulls images from the top-ranking articles.
4. Downloads the top 1-3 chosen images to ``output/images/<date>/`` for the
   hybrid hotlink+local-cache display, and persists everything to a new
   ``story_images`` table.

Copyright posture: we hotlink the source image URL and cite the outlet the
image came from (mirroring how every news aggregator handles this). The local
copy is a backup only, in case the source drops the file.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from bs4 import BeautifulSoup

from grounded.db import cursor
from grounded.ingest._http import make_client
from grounded.ingest._rss import fetch_feed
from grounded.ingest.google_news import build_query_url
from grounded.models import SourceTier
from grounded.pipeline.scrape import _is_paywalled, _resolve_url

log = logging.getLogger(__name__)

# Per-host politeness for the image-fetch phase. Shorter than the scrape phase
# because we're only pulling image binaries, not HTML.
_MIN_INTERVAL_PER_HOST_SECONDS = 1.0
_PER_URL_TIMEOUT_SECONDS = 20.0

# How many images to keep per story after scoring.
_MIN_PER_STORY = 1
_MAX_PER_STORY = 3

# Reject images smaller than this in either dimension (when we can tell).
_MIN_WIDTH = 300
_MIN_HEIGHT = 200

# Substrings in image URLs that almost always indicate a non-content asset.
_URL_BLOCKLIST = (
    "/logo", "logo.", "logo-", "-logo",
    "/favicon", "favicon.",
    "/icon", "-icon.", "sprite",
    "/ad-", "/ads/", "adserver", "doubleclick",
    "1x1.", "pixel.", "beacon",
    "avatar",
    "/subscribe", "/paywall",
)

# Fallback-search image blocklist for domains that block hotlinking or serve junk.
_HOST_BLOCKLIST = frozenset({
    "lookaside.fbsbx.com", "scontent.fbcdn.net",  # Facebook CDN, blocks hotlinks
    "pbs.twimg.com",                              # X CDN, unreliable
})


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS story_images (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id      UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    source_url    TEXT NOT NULL,
    local_path    TEXT,
    caption       TEXT,
    credit        TEXT,
    article_url   TEXT,
    ordinal       INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS story_images_story_idx
    ON story_images (story_id, ordinal);
"""


def ensure_schema() -> None:
    with cursor() as cur:
        cur.execute(_SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ImageCandidate:
    url: str
    caption: str
    credit: str
    article_url: str
    score: float
    width: int | None = None
    height: int | None = None


# ---------------------------------------------------------------------------
# HTML → image candidates
# ---------------------------------------------------------------------------

def _parse_dim(val: str | None) -> int | None:
    if not val:
        return None
    m = re.match(r"(\d+)", str(val).strip())
    return int(m.group(1)) if m else None


def _url_is_junk(url: str) -> bool:
    if not url or url.startswith("data:"):
        return True
    lower = url.lower()
    for bad in _URL_BLOCKLIST:
        if bad in lower:
            return True
    host = urlparse(url).hostname or ""
    if host.lower() in _HOST_BLOCKLIST:
        return True
    return False


def _normalize_image_url(url: str) -> str:
    """Return a dedup key that treats size/quality variants of the same image
    as one. Publishers serve the same photo at many URLs: ``photo.jpg``,
    ``photo.jpg?w=1024``, ``photo.jpg?resize=450,253``, ``photo.jpg?quality=80``.
    A plain URL-string dedup misses these. We strip the query string entirely
    (all image CDNs use it for resize/quality/format, not for identity),
    lower-case the host, and drop trailing slashes."""
    try:
        p = urlparse(url)
    except Exception:
        return url.lower()
    host = (p.hostname or "").lower()
    port = f":{p.port}" if p.port else ""
    path = p.path.rstrip("/")
    return f"{p.scheme.lower()}://{host}{port}{path}"


def _pick_from_srcset(srcset: str) -> str | None:
    """Pick the largest URL from a srcset attribute."""
    best_url = None
    best_w = -1
    for chunk in srcset.split(","):
        parts = chunk.strip().split()
        if not parts:
            continue
        url = parts[0]
        w = 0
        if len(parts) > 1 and parts[1].endswith("w"):
            try:
                w = int(parts[1][:-1])
            except ValueError:
                w = 0
        if w > best_w:
            best_w = w
            best_url = url
    return best_url


def _closest_caption(img_tag) -> str:
    """Pull a caption from figure/figcaption or img alt/title, in that order."""
    fig = img_tag.find_parent("figure")
    if fig is not None:
        cap = fig.find("figcaption")
        if cap is not None:
            text = cap.get_text(" ", strip=True)
            if text:
                return text[:300]
    alt = (img_tag.get("alt") or "").strip()
    if alt:
        return alt[:300]
    title = (img_tag.get("title") or "").strip()
    if title:
        return title[:300]
    return ""


def extract_image_candidates(
    article_url: str, html: str, credit: str
) -> list[ImageCandidate]:
    """Parse an article HTML and return scored image candidates."""
    soup = BeautifulSoup(html, "lxml")

    # First, prefer og:image / twitter:image — these are the publisher's own
    # editorially-selected lead image for the article. Almost always safe.
    lead: ImageCandidate | None = None
    for prop in ("og:image", "og:image:secure_url", "twitter:image"):
        meta = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if meta and meta.get("content"):
            url = urljoin(article_url, meta["content"].strip())
            if not _url_is_junk(url):
                lead = ImageCandidate(
                    url=url,
                    caption=_og_caption(soup),
                    credit=credit,
                    article_url=article_url,
                    score=100.0,  # og:image beats body-scraped candidates
                )
                break

    candidates: list[ImageCandidate] = []
    if lead is not None:
        candidates.append(lead)

    for idx, img in enumerate(soup.find_all("img")):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or img.get("data-lazy-src")
            or ""
        ).strip()
        srcset = img.get("srcset") or img.get("data-srcset")
        if srcset:
            picked = _pick_from_srcset(srcset)
            if picked:
                src = picked

        if not src:
            continue
        url = urljoin(article_url, src)
        if _url_is_junk(url):
            continue

        w = _parse_dim(img.get("width"))
        h = _parse_dim(img.get("height"))
        if w is not None and w < _MIN_WIDTH:
            continue
        if h is not None and h < _MIN_HEIGHT:
            continue

        # Score: earlier in doc = more likely lead. Bigger = better.
        # Caption/alt presence is a strong positive.
        score = 10.0
        score -= min(idx, 20) * 0.3          # position penalty
        score += (w or 0) * 0.001            # size bonus (small weight)
        score += (h or 0) * 0.001
        caption = _closest_caption(img)
        if caption:
            score += 3.0 + min(len(caption), 100) * 0.02

        # Skip duplicates of the lead image.
        if lead is not None and url == lead.url:
            if caption and not lead.caption:
                lead.caption = caption
            continue

        candidates.append(
            ImageCandidate(
                url=url,
                caption=caption,
                credit=credit,
                article_url=article_url,
                score=score,
                width=w,
                height=h,
            )
        )

    return candidates


def _og_caption(soup) -> str:
    for prop in ("og:description", "twitter:description"):
        meta = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if meta and meta.get("content"):
            return meta["content"].strip()[:300]
    return ""


# ---------------------------------------------------------------------------
# HTTP fetching (article HTML + image binary)
# ---------------------------------------------------------------------------

class _HostThrottle:
    def __init__(self) -> None:
        self._last: dict[str, float] = defaultdict(lambda: 0.0)

    def wait(self, host: str) -> None:
        gap = _MIN_INTERVAL_PER_HOST_SECONDS - (time.monotonic() - self._last[host])
        if gap > 0:
            time.sleep(gap)
        self._last[host] = time.monotonic()


def _fetch_html(client: httpx.Client, url: str, throttle: _HostThrottle) -> str:
    host = (urlparse(url).hostname or "").lower()
    if _is_paywalled(host):
        return ""
    throttle.wait(host)
    try:
        resp = client.get(url, timeout=_PER_URL_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        log.info("image-html fetch failed for %s: %s", url, e)
        return ""
    ctype = resp.headers.get("content-type", "").lower()
    if "html" not in ctype and "xml" not in ctype:
        return ""
    return resp.text


def _download_image(
    client: httpx.Client, url: str, dest: Path, throttle: _HostThrottle
) -> bool:
    host = (urlparse(url).hostname or "").lower()
    throttle.wait(host)
    try:
        resp = client.get(url, timeout=_PER_URL_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        log.info("image download failed for %s: %s", url, e)
        return False
    ctype = resp.headers.get("content-type", "").lower()
    if "image" not in ctype:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return True


# ---------------------------------------------------------------------------
# DB access
# ---------------------------------------------------------------------------

def _load_approved_stories() -> list[dict]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.event_id, s.headline
            FROM stories s
            WHERE s.editor_approved = TRUE
            ORDER BY s.created_at DESC
            """
        )
        return list(cur.fetchall())


def _load_story_sources(story_id: UUID) -> list[dict]:
    """Every raw_item cited by this story (via claims → claim_sources)."""
    with cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT r.id, r.source_name, r.source_url
            FROM raw_items r
            JOIN claim_sources cs ON cs.raw_item_id = r.id
            JOIN claims c ON c.id = cs.claim_id
            WHERE c.story_id = %s
              AND r.source_tier <= 2
            """,
            (story_id,),
        )
        return list(cur.fetchall())


def _clear_existing_images(story_id: UUID) -> None:
    with cursor() as cur:
        cur.execute("DELETE FROM story_images WHERE story_id = %s", (story_id,))


def _persist_images(story_id: UUID, chosen: list[tuple[ImageCandidate, str | None]]) -> None:
    if not chosen:
        return
    with cursor() as cur:
        for i, (cand, local_path) in enumerate(chosen):
            cur.execute(
                """
                INSERT INTO story_images
                    (story_id, source_url, local_path, caption, credit,
                     article_url, ordinal)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    story_id,
                    cand.url,
                    local_path,
                    cand.caption or None,
                    cand.credit or None,
                    cand.article_url or None,
                    i,
                ),
            )


# ---------------------------------------------------------------------------
# Fallback: Google News search on the headline
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "as",
    "by", "over", "with", "amid", "after", "before", "into", "from",
}


def _headline_query(headline: str) -> str:
    """Distil a headline into a short, high-signal search query."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]{1,}", headline)
    kept = [w for w in words if w.lower() not in _STOPWORDS]
    return " ".join(kept[:8]).strip() or headline.strip()


def _fallback_search_candidates(
    client: httpx.Client, headline: str, throttle: _HostThrottle
) -> list[ImageCandidate]:
    query = _headline_query(headline)
    if not query:
        return []
    feed_url = build_query_url(query, when="7d")
    log.info("[image-fallback] search: %s", query)
    try:
        items = list(
            fetch_feed(
                feed_url,
                source_name="image-fallback",
                source_tier=SourceTier.WIRE,
                max_entries=5,
            )
        )
    except Exception as e:
        log.info("[image-fallback] rss fetch failed: %s", e)
        return []

    all_cands: list[ImageCandidate] = []
    for item in items[:5]:
        real_url = _resolve_url(item.source_url)
        host = (urlparse(real_url).hostname or "").lower()
        if _is_paywalled(host):
            continue
        html = _fetch_html(client, real_url, throttle)
        if not html:
            continue
        credit = _outlet_from_host(host)
        cands = extract_image_candidates(real_url, html, credit=credit)
        if cands:
            all_cands.extend(cands[:2])  # keep top 2 per fallback article
        if len(all_cands) >= 6:
            break
    return all_cands


def _outlet_from_host(host: str) -> str:
    """Best-effort human name for the outlet, from the URL host."""
    host = host.lower().removeprefix("www.").removeprefix("m.")
    parts = host.split(".")
    if len(parts) >= 2:
        return parts[0].replace("-", " ").title()
    return host or "source"


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def _hash_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:12]


def _ext_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"):
        if path.endswith(ext):
            return ext
    return ".jpg"


def enrich_stories_with_images(
    output_root: Path,
    edition_date: str,
) -> dict:
    """Main entry. Populate story_images for every approved story.

    ``output_root`` is the folder that already contains ``edition-<date>.md``
    (usually ``settings.output_dir``). Images are cached to
    ``<output_root>/images/<edition_date>/<story-uuid>-<n><ext>``.
    """
    ensure_schema()
    stories = _load_approved_stories()
    if not stories:
        log.info("no approved stories to enrich")
        return {"stories": 0, "with_images": 0, "primary_hits": 0, "fallback_hits": 0}

    image_dir = output_root / "images" / edition_date
    log.info("enriching %d stor(y/ies) → %s", len(stories), image_dir)

    throttle = _HostThrottle()
    primary_hits = 0
    fallback_hits = 0
    with_images = 0

    with make_client() as client:
        for story in stories:
            story_id = story["id"]
            headline = story["headline"] or ""
            sources = _load_story_sources(story_id)

            all_candidates: list[ImageCandidate] = []
            for src in sources:
                real_url = _resolve_url(src["source_url"])
                html = _fetch_html(client, real_url, throttle)
                if not html:
                    continue
                credit = _humanize_source(src["source_name"])
                cands = extract_image_candidates(real_url, html, credit=credit)
                all_candidates.extend(cands)

            source_of = "primary"
            if not all_candidates:
                fallback = _fallback_search_candidates(client, headline, throttle)
                if fallback:
                    all_candidates = fallback
                    source_of = "fallback"

            all_candidates.sort(key=lambda c: c.score, reverse=True)
            # Deduplicate by NORMALIZED URL so /photo.jpg and /photo.jpg?w=1024
            # count as one image (they are, at different sizes).
            seen: set[str] = set()
            unique: list[ImageCandidate] = []
            for c in all_candidates:
                key = _normalize_image_url(c.url)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(c)
                if len(unique) >= _MAX_PER_STORY:
                    break

            if not unique:
                log.info("no images found for story %s (%s)", story_id, headline[:60])
                _clear_existing_images(story_id)
                continue

            chosen: list[tuple[ImageCandidate, str | None]] = []
            for i, cand in enumerate(unique):
                dest = image_dir / f"{story_id}-{i}-{_hash_url(cand.url)}{_ext_from_url(cand.url)}"
                ok = _download_image(client, cand.url, dest, throttle)
                # Store POSIX-style path so the markdown renders correctly on
                # web (grounded-page) and on non-Windows CI. Windows still reads
                # forward-slash paths fine when the file is served/opened.
                local_path = dest.relative_to(output_root).as_posix() if ok else None
                chosen.append((cand, local_path))

            _clear_existing_images(story_id)
            _persist_images(story_id, chosen)
            with_images += 1
            if source_of == "primary":
                primary_hits += 1
            else:
                fallback_hits += 1
            log.info(
                "story %s: %d image(s) via %s",
                headline[:60], len(chosen), source_of,
            )

            # Safety: guarantee at least MIN_PER_STORY isn't violated when we
            # actually found something.
            if len(chosen) < _MIN_PER_STORY:
                log.warning("only %d image(s) for story %s", len(chosen), headline[:60])

    return {
        "stories": len(stories),
        "with_images": with_images,
        "primary_hits": primary_hits,
        "fallback_hits": fallback_hits,
    }


# Same shortlist edition.py uses. Kept local to avoid an import cycle with the
# renderer, and to let images.py be used standalone.
_ACRONYMS = {"ap", "pib", "rbi", "sci", "prs", "un", "us", "usa", "gst", "cjp", "rss"}


def _humanize_source(name: str) -> str:
    parts = [p for p in (name or "").replace("-", "_").split("_") if p]
    if not parts:
        return name or "source"
    return " ".join(p.upper() if p.lower() in _ACRONYMS else p.capitalize() for p in parts)


# ---------------------------------------------------------------------------
# Reader — used by the renderer
# ---------------------------------------------------------------------------

def load_story_images(story_id: UUID) -> list[dict]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT source_url, local_path, caption, credit, article_url, ordinal
            FROM story_images
            WHERE story_id = %s
            ORDER BY ordinal
            """,
            (story_id,),
        )
        return list(cur.fetchall())


# ---------------------------------------------------------------------------
# Gemini vision verify + dedup + recaption
# ---------------------------------------------------------------------------

# Sleep between Gemini calls to stay under the 15 req/min free-tier ceiling.
# ~20 stories with 2-3 images each is ~20 requests; 4.5s spacing keeps us safe.
_VERIFY_SLEEP_SECONDS = 4.5

# Body chars sent to the LLM alongside the images. Enough for the LLM to
# understand what the story is actually about (the opening lede + first few
# paragraphs) without paying for every extra token. This is the CRITICAL fix
# from the previous verify pass, which only saw the headline+dek and dropped
# body-relevant images that didn't match the (sometimes wrong) headline.
_VERIFY_BODY_CHARS = 2000


_IMAGE_VERIFY_SYSTEM = (
    "You are a photo editor for a fact-driven Indian news newsletter. You are "
    "shown a story (headline, dek, body) and a set of candidate images. For "
    "each image you must do three things:\n"
    "\n"
    "1. RELEVANCE — decide KEEP or DROP.\n"
    "   - KEEP if the image plausibly illustrates the story: same event, same "
    "person, same institution, same place, or the same theme (protest / court "
    "/ parliament / flood / stadium / market / etc). File photos and old "
    "photos of the right subject are fine. Judge relevance against the STORY "
    "BODY, not just the headline — the body is what the article actually "
    "reports on.\n"
    "   - DROP only if the image is clearly unrelated: a greeting card, a "
    "promo/download banner, a sidebar thumbnail, a person or subject not in "
    "the story at all. When unsure, KEEP.\n"
    "\n"
    "2. DUPLICATE DETECTION — for each image, if it is a VISUAL duplicate of "
    "another image in this set (same photo at a different size, near-identical "
    "framing, obvious stock re-use), record the id of the FIRST duplicate you "
    "see it match. Only one image per duplicate group should survive; the rest "
    "get DROP with `duplicate_of` set. If not a duplicate, `duplicate_of` is "
    "null.\n"
    "\n"
    "3. CAPTION — write one clean sentence (max 200 chars) that describes what "
    "the image actually shows AND ties it to the story. Do not invent names, "
    "dates, or events not visible or in the body. If the given caption is "
    "already clean and accurate, keep it.\n"
    "\n"
    "Respond only with JSON."
)


def _load_all_images_with_body() -> dict:
    """story_id -> {headline, dek, body_markdown, images: [row, ...]}."""
    with cursor() as cur:
        cur.execute(
            """
            SELECT si.id AS image_id, si.story_id, si.source_url, si.local_path,
                   si.caption, si.credit, si.article_url, si.ordinal,
                   s.headline, s.dek, s.body_markdown
            FROM story_images si
            JOIN stories s ON s.id = si.story_id
            WHERE s.editor_approved = TRUE
            ORDER BY si.story_id, si.ordinal
            """
        )
        rows = list(cur.fetchall())
    grouped: dict = {}
    for r in rows:
        bucket = grouped.setdefault(r["story_id"], {
            "headline": r["headline"] or "",
            "dek": r["dek"] or "",
            "body": r["body_markdown"] or "",
            "images": [],
        })
        bucket["images"].append(r)
    return grouped


def _vision_verify_gemini(
    backend, system: str, user_text: str, image_urls: list[str]
) -> str:
    """Multimodal Gemini call; bypasses text-only backend.complete."""
    content: list[dict] = [{"type": "text", "text": user_text}]
    for url in image_urls[:6]:  # bound the request
        if url:
            content.append({"type": "image_url", "image_url": {"url": url}})
    resp = backend._client.chat.completions.create(  # noqa: SLF001
        model=backend.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        max_tokens=2000,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return (resp.choices[0].message.content or "").strip()


def _apply_image_verdicts(image_rows: list[dict], verdicts: list[dict]) -> tuple[int, int, int]:
    """Delete DROPs and dupes; update captions on KEEPs. Returns
    (dropped_irrelevant, dropped_duplicate, recaptioned)."""
    by_id = {str(r["image_id"]): r for r in image_rows}
    to_delete: set[str] = set()
    caption_updates: list[tuple[str, str]] = []

    for v in verdicts:
        if not isinstance(v, dict):
            continue
        img_id = str(v.get("image_id") or "")
        if img_id not in by_id:
            continue
        verdict = str(v.get("verdict") or "").upper()
        dup_of = v.get("duplicate_of")
        if verdict == "DROP":
            to_delete.add(img_id)
            continue
        # KEEP: if marked as duplicate of another kept image, drop this too.
        if dup_of and str(dup_of) in by_id and str(dup_of) != img_id:
            to_delete.add(img_id)
            continue
        new_cap = (v.get("caption") or "").strip()[:400]
        if new_cap:
            caption_updates.append((new_cap, img_id))

    dropped_irrelevant = 0
    dropped_duplicate = 0
    for img_id in to_delete:
        # crude split: mark as duplicate if the LLM set duplicate_of
        v = next((x for x in verdicts if str(x.get("image_id") or "") == img_id), None)
        if v and v.get("duplicate_of"):
            dropped_duplicate += 1
        else:
            dropped_irrelevant += 1

    with cursor() as cur:
        if to_delete:
            cur.execute(
                "DELETE FROM story_images WHERE id::text = ANY(%s)",
                (list(to_delete),),
            )
        for cap, img_id in caption_updates:
            cur.execute(
                "UPDATE story_images SET caption = %s WHERE id::text = %s",
                (cap, img_id),
            )
        # Re-pack ordinals per story so gaps don't confuse the renderer.
        cur.execute(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (PARTITION BY story_id ORDER BY ordinal) - 1 AS new_ord
                FROM story_images
            )
            UPDATE story_images si
            SET ordinal = ranked.new_ord
            FROM ranked
            WHERE si.id = ranked.id AND si.ordinal <> ranked.new_ord
            """
        )
    return dropped_irrelevant, dropped_duplicate, len(caption_updates)


def verify_and_dedup_images() -> dict:
    """Vision-based pass over story_images: drop irrelevant, dedupe visual
    duplicates, rewrite captions. Requires GEMINI_API_KEY; no-op otherwise."""
    from grounded.agents.llm import extract_json, make_gemini

    backend = make_gemini()
    if backend is None or getattr(backend, "is_local", False):
        log.warning("verify_and_dedup_images: no Gemini backend; skipping")
        return {"stories": 0, "checked": 0, "dropped_irrelevant": 0,
                "dropped_duplicate": 0, "recaptioned": 0, "errors": 0}

    grouped = _load_all_images_with_body()
    total_checked = 0
    total_drop_irrelevant = 0
    total_drop_dupe = 0
    total_recap = 0
    errors = 0

    for idx, (story_id, bucket) in enumerate(grouped.items()):
        if idx > 0:
            time.sleep(_VERIFY_SLEEP_SECONDS)
        imgs = bucket["images"]
        if not imgs:
            continue
        image_block = "\n".join(
            f"- id={r['image_id']}, url={r['source_url']}, "
            f"current_caption={r['caption'] or '(none)'}"
            for r in imgs
        )
        user = (
            f"STORY HEADLINE: {bucket['headline']}\n"
            f"STORY DEK: {bucket['dek']}\n"
            f"STORY BODY (source of truth for relevance):\n"
            f"{bucket['body'][:_VERIFY_BODY_CHARS]}\n\n"
            f"IMAGES TO REVIEW:\n{image_block}\n\n"
            'Return JSON: {"verdicts": [{"image_id": "<id>", "verdict": "KEEP" | "DROP", "duplicate_of": "<other id or null>", "caption": "<one-sentence caption if KEEP>"}]}'
        )
        try:
            raw = _vision_verify_gemini(
                backend, _IMAGE_VERIFY_SYSTEM, user,
                [r["source_url"] for r in imgs],
            )
            data = extract_json(raw)
        except Exception as e:
            log.warning("image verify failed for %s: %s", bucket["headline"][:60], e)
            errors += 1
            continue

        verdicts = data.get("verdicts") if isinstance(data, dict) else None
        if not isinstance(verdicts, list):
            log.warning("image verify: unexpected response for %s", bucket["headline"][:60])
            errors += 1
            continue

        di, dd, rc = _apply_image_verdicts(imgs, verdicts)
        total_checked += len(imgs)
        total_drop_irrelevant += di
        total_drop_dupe += dd
        total_recap += rc
        log.info(
            "%s: reviewed %d, dropped %d irrelevant, %d dupe, recaptioned %d",
            bucket["headline"][:60], len(imgs), di, dd, rc,
        )

    return {
        "stories": len(grouped),
        "checked": total_checked,
        "dropped_irrelevant": total_drop_irrelevant,
        "dropped_duplicate": total_drop_dupe,
        "recaptioned": total_recap,
        "errors": errors,
    }
