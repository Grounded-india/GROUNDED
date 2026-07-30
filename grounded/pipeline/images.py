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
# These are sidebar / recirculation / greeting-graphic patterns that leaked
# through as "lead images" in the first 07-29 run — see task #55.
_URL_BLOCKLIST = (
    "/logo", "logo.", "logo-", "-logo",
    "/favicon", "favicon.",
    "/icon", "-icon.", "sprite",
    "/ad-", "/ads/", "adserver", "doubleclick",
    "1x1.", "pixel.", "beacon",
    "avatar",
    "/subscribe", "/paywall",
    # Recirculation / greeting cards / promo graphics — these are almost never
    # the actual news photo. Extend as new patterns are seen.
    "wishes", "greeting", "guru-purnima", "happy-",
    "download-app", "app-download",
    "readwhere", "loader.gif",
    "creativecommons", "licensebuttons",
    "youtube.com/vi/", "img.youtube.com",  # video thumbnails from embeds
    "scorecardresearch", "score-card",
    "cdn.publive.online/fit-in/1200x675/",  # publive placeholder banner
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


def _looks_like_url(text: str) -> bool:
    """A caption that is itself a URL means we grabbed the img src as alt text —
    a classic sidebar/hotlink-block giveaway. Reject those upstream."""
    s = (text or "").strip().lower()
    return s.startswith(("http://", "https://", "//")) or "images.indianexpress.com" in s


def _closest_caption(img_tag) -> str:
    """Pull a caption from figure/figcaption or img alt/title, in that order.
    Return "" for URL-shaped captions so they never render."""
    fig = img_tag.find_parent("figure")
    if fig is not None:
        cap = fig.find("figcaption")
        if cap is not None:
            text = cap.get_text(" ", strip=True)
            if text and not _looks_like_url(text):
                return text[:300]
    alt = (img_tag.get("alt") or "").strip()
    if alt and not _looks_like_url(alt):
        return alt[:300]
    title = (img_tag.get("title") or "").strip()
    if title and not _looks_like_url(title):
        return title[:300]
    return ""


# CSS selectors that identify the actual article body — where the real photos
# live. Everything outside these containers is sidebar/recirculation/related.
# Ordered by specificity; the first hit wins.
_ARTICLE_CONTAINER_SELECTORS = (
    "article",
    "main",
    '[role="main"]',
    '[itemprop="articleBody"]',
    ".article-body", ".story-body", ".story__body",
    ".entry-content", ".post-content",
    "#story-content", "#article-content",
)


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

    # Restrict the img walk to the article body if we can find one — otherwise
    # fall back to the whole document. This keeps sidebar / "you might also
    # like" / promo thumbnails out of the candidate pool.
    body_scope = None
    for sel in _ARTICLE_CONTAINER_SELECTORS:
        body_scope = soup.select_one(sel)
        if body_scope is not None:
            break
    scope = body_scope or soup
    in_body = body_scope is not None

    for idx, img in enumerate(scope.find_all("img")):
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
        # Caption/alt presence is a strong positive. Article-body scoping
        # earns a big base bonus so those beat any stray fall-back images.
        score = 10.0
        if in_body:
            score += 15.0
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
    # Cross-story dedup: any image URL reused across stories is almost always
    # a sidebar / "you might also like" / recirculation module thumbnail. Skip
    # it on the second and subsequent stories so it never appears twice.
    used_urls: set[str] = set()

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
            # Per-story dedup + cross-story dedup in one pass.
            seen_here: set[str] = set()
            unique: list[ImageCandidate] = []
            for c in all_candidates:
                if c.url in seen_here or c.url in used_urls:
                    continue
                seen_here.add(c.url)
                unique.append(c)
                if len(unique) >= _MAX_PER_STORY:
                    break
            # Record the URLs actually kept so future stories can't reuse them.
            for c in unique:
                used_urls.add(c.url)

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
# LLM verify + recaption pass (Gemini vision)
# ---------------------------------------------------------------------------

_VERIFY_SYSTEM = (
    "You are a photo editor for a fact-driven Indian news newsletter. For each "
    "image supplied, decide whether it is a RELEVANT illustration for the given "
    "story, and write a clean one-sentence caption grounded in what the image "
    "actually shows plus the story context.\n"
    "\n"
    "RELEVANCE RULES\n"
    "- KEEP if the image plausibly illustrates the story: the same event, the "
    "person named, the institution, the place, the theme (protest / court / "
    "parliament / flood / stadium / etc). File photos of the right subject are "
    "fine. Old photos of the right subject are fine.\n"
    "- DROP if the image is a greeting card, a promo/download banner, a "
    "sidebar/related-article thumbnail, a logo, a person or subject unrelated "
    "to the story, or generic stock unrelated to the topic.\n"
    "- When unsure, KEEP — a plausibly-relevant photo is better than none.\n"
    "\n"
    "CAPTION RULES\n"
    "- One sentence, factual, no hype, no adjectives that pick a side.\n"
    "- Describe what is actually visible AND connect it to the story where the "
    "sources allow. Do not invent names, dates, or events not visible or in the "
    "story context.\n"
    "- If the caption you were given is already clean and accurate, you may "
    "keep it. If it is a URL, empty, or misleading, rewrite it.\n"
    "- Max 200 characters. No trailing period required.\n"
    "\n"
    "Respond only with JSON."
)


def _load_all_images_by_story() -> dict[UUID, list[dict]]:
    """Fetch every story_images row grouped by story_id, joined with headline+dek."""
    with cursor() as cur:
        cur.execute(
            """
            SELECT si.id AS image_id, si.story_id, si.source_url, si.local_path,
                   si.caption, si.credit, si.article_url, si.ordinal,
                   s.headline, s.dek
            FROM story_images si
            JOIN stories s ON s.id = si.story_id
            WHERE s.editor_approved = TRUE
            ORDER BY si.story_id, si.ordinal
            """
        )
        rows = list(cur.fetchall())
    grouped: dict[UUID, list[dict]] = {}
    for r in rows:
        grouped.setdefault(r["story_id"], []).append(r)
    return grouped


def _apply_verdicts(
    verdicts: list[dict],
) -> tuple[int, int]:
    """Given LLM output [{image_id, verdict, caption}, ...], apply to DB.

    Returns (dropped, recaptioned) counts.
    """
    dropped = 0
    recaptioned = 0
    with cursor() as cur:
        for v in verdicts:
            image_id = v.get("image_id")
            if not image_id:
                continue
            verdict = str(v.get("verdict") or "").upper()
            if verdict == "DROP":
                cur.execute("DELETE FROM story_images WHERE id = %s", (image_id,))
                dropped += 1
            elif verdict == "KEEP":
                new_caption = (v.get("caption") or "").strip()[:400]
                if new_caption:
                    cur.execute(
                        "UPDATE story_images SET caption = %s WHERE id = %s",
                        (new_caption, image_id),
                    )
                    recaptioned += 1
    # Re-pack ordinal per story so gaps left by drops don't confuse the
    # renderer (which uses ordinal to pick "lead" = ordinal 0).
    with cursor() as cur:
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
            WHERE si.id = ranked.id
              AND si.ordinal <> ranked.new_ord
            """
        )
    return dropped, recaptioned


def verify_and_recaption_images() -> dict:
    """Vision-based final gate over story_images.

    For every approved story, send its images (as URLs) to Gemini along with
    the headline and dek. Gemini returns per-image KEEP/DROP + a clean
    one-sentence caption. Dropped rows are deleted, kept rows get their
    caption rewritten, and ordinals are compacted.

    Requires GEMINI_API_KEY. If Gemini is unavailable, returns a no-op summary.
    """
    from grounded.agents.llm import extract_json, make_gemini

    backend = make_gemini()
    if backend is None or getattr(backend, "is_local", False):
        log.warning("verify_and_recaption_images: no Gemini backend; skipping")
        return {"stories": 0, "images_checked": 0, "dropped": 0, "recaptioned": 0}

    grouped = _load_all_images_by_story()
    total_dropped = 0
    total_recaptioned = 0
    total_checked = 0

    for story_id, imgs in grouped.items():
        if not imgs:
            continue
        headline = imgs[0]["headline"] or ""
        dek = imgs[0]["dek"] or ""
        image_block = "\n".join(
            f"- id={r['image_id']}, url={r['source_url']}, "
            f"current_caption={r['caption'] or '(none)'}, "
            f"article={r['article_url'] or '(none)'}"
            for r in imgs
        )
        user = (
            f"STORY HEADLINE: {headline}\n"
            f"STORY DEK: {dek}\n\n"
            f"IMAGES TO REVIEW:\n{image_block}\n\n"
            'Return JSON: {"verdicts": [{"image_id": "<id>", "verdict": "KEEP" | "DROP", "caption": "<one-sentence caption if KEEP>"}]}'
        )
        try:
            raw = _vision_complete_gemini(backend, _VERIFY_SYSTEM, user, [r["source_url"] for r in imgs])
            data = extract_json(raw)
        except Exception as e:
            log.warning("image verify failed for story %s: %s", headline[:60], e)
            continue

        verdicts = data.get("verdicts") if isinstance(data, dict) else None
        if not isinstance(verdicts, list):
            log.warning("image verify: unexpected response shape for %s", headline[:60])
            continue

        # Coerce image_id strings back to UUIDs the DB layer expects.
        cleaned = []
        for v in verdicts:
            if not isinstance(v, dict):
                continue
            try:
                v["image_id"] = UUID(str(v.get("image_id")))
            except (ValueError, TypeError):
                continue
            cleaned.append(v)

        dropped, recaptioned = _apply_verdicts(cleaned)
        total_dropped += dropped
        total_recaptioned += recaptioned
        total_checked += len(imgs)
        log.info(
            "story %s: reviewed %d, dropped %d, recaptioned %d",
            headline[:60], len(imgs), dropped, recaptioned,
        )

    return {
        "stories": len(grouped),
        "images_checked": total_checked,
        "dropped": total_dropped,
        "recaptioned": total_recaptioned,
    }


def _vision_complete_gemini(
    backend, system: str, user_text: str, image_urls: list[str]
) -> str:
    """Send a multimodal request to the Gemini OpenAI-compatible endpoint.

    Bypasses ``OpenAICompatibleBackend.complete`` because it only supports
    text-in/text-out; the underlying OpenAI() client on the backend supports
    the multimodal message shape natively.
    """
    content: list[dict] = [{"type": "text", "text": user_text}]
    for url in image_urls[:6]:  # bound the request
        if not url:
            continue
        content.append({"type": "image_url", "image_url": {"url": url}})
    kwargs = {"response_format": {"type": "json_object"}}
    resp = backend._client.chat.completions.create(  # noqa: SLF001 — private access for vision
        model=backend.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        max_tokens=2000,
        temperature=0.1,
        **kwargs,
    )
    return (resp.choices[0].message.content or "").strip()
