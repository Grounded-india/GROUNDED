"""Bottom-of-pipeline edition translation.

Takes the finished English edition markdown and produces a natural-sounding
edition in each target language, written to
``OUTPUT_DIR/edition-<date>.<lang>.md`` alongside the English one (and copied
into grounded-page by the caller).

Design notes:

* **Translate the rendered file, not the DB.** The edition is the final
  artefact — headlines, deks, reporter prose, captions and the footer all live
  in one place. Translating it keeps every downstream step (images, coherence,
  dedup) untouched.

* **Chunked per story.** One LLM call for the whole edition would blow the
  output cap and degrade quality by the tenth story. Each story is translated
  on its own; oversized stories are split further at paragraph boundaries.

* **URLs are never sent to the model.** Every markdown link target, image src
  and bare URL is swapped for a ``%%n%%`` placeholder before the call and
  restored after. A translated chunk that comes back missing a placeholder is
  retried once, then falls back to the untranslated original — a readable
  English paragraph beats a broken image or a mangled citation link.

* **The table of contents is rebuilt, not translated.** Translating the TOC
  independently of the headings would desync the ``#anchor`` slugs. Instead the
  TOC is regenerated from the *translated* ``## N. Headline`` lines using the
  same slug function the renderer uses, so in-page links keep working.

Failure isolation matches the rest of the pipeline: any per-chunk error leaves
that chunk in English and the run continues. A language that fails entirely is
logged and skipped; the English edition is never touched.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
from pathlib import Path

from grounded.agents.edition import _slug
from grounded.agents.llm import env_value, extract_json, make_gemini

log = logging.getLogger(__name__)

# Target languages: code -> (English name, endonym). The endonym is used in the
# "this is a translation" notice so the page reads native from the first line.
LANGUAGES: dict[str, tuple[str, str]] = {
    "hi": ("Hindi", "हिन्दी"),
    "kn": ("Kannada", "ಕನ್ನಡ"),
    "ta": ("Tamil", "தமிழ்"),
    "te": ("Telugu", "తెలుగు"),
    "bn": ("Bengali", "বাংলা"),
    "mr": ("Marathi", "मराठी"),
    "ml": ("Malayalam", "മലയാളം"),
    "gu": ("Gujarati", "ગુજરાતી"),
    "pa": ("Punjabi", "ਪੰਜਾਬੀ"),
    "ur": ("Urdu", "اردو"),
}

# Languages produced when nothing is passed on the CLI. Each language costs
# roughly (stories + 3) LLM calls, so widen this deliberately — via
# EDITION_LANGUAGES=hi,kn,mr,te,bn or `publish --lang bn`.
DEFAULT_LANGUAGES = ("hi", "kn", "mr", "te")

# Gemini free tier caps at 15 requests/minute per model — same throttle the
# coherence pass uses.
_INTER_CALL_SLEEP_SECONDS = 4.5

# Max characters of markdown sent in one call. Indic scripts tokenize far less
# efficiently than English, so a 4.5k-char English chunk can still approach the
# output cap in Devanagari/Kannada.
_MAX_CHUNK_CHARS = 4500
_MAX_TOKENS = 8000

_SYSTEM = (
    "You are a senior newspaper translator. You translate a daily news edition "
    "from English into {language} ({endonym}) for readers in India.\n"
    "\n"
    "Translate for MEANING, not word-for-word. The result must read like it was "
    "written by a {language} journalist for a {language} newspaper — natural "
    "register, natural sentence rhythm, idiomatic phrasing. Never produce stiff, "
    "literal, machine-sounding prose.\n"
    "\n"
    "REGISTER — write the way a mainstream {language} newspaper or news channel "
    "actually writes TODAY. Do NOT write in a pure, literary, Sanskritised or "
    "otherwise 'shuddh' form of the language.\n"
    "- Keep the everyday English loanwords {language} speakers genuinely use in "
    "speech and in print — police, court, report, minister, committee, protest, "
    "social media, video, platform, account, survey, bill, and so on — "
    "transliterated into {language} script.\n"
    "- Never hunt for an archaic, coined or textbook-only 'native equivalent' "
    "that an ordinary reader would stumble over or find comical.\n"
    "- Test: if an educated speaker discussing this news over chai would say the "
    "English word, use the English word.\n"
    "\n"
    "ACCURACY IS ABSOLUTE. This is factual news. Do not add, drop, soften, "
    "sharpen or reinterpret any fact, number, date, quantity, name or "
    "attribution. Do not add commentary. If a sentence hedges ('reportedly', "
    "'single-source', 'unverified'), carry that hedge over exactly.\n"
    "\n"
    "MARKDOWN — the input is markdown. Reproduce its structure EXACTLY:\n"
    "- Keep every heading level (#, ##, ###) and its numbering.\n"
    "- Keep every list marker, blockquote (>), bold/italic marker, and blank "
    "line. Keep <sub> and </sub> tags verbatim.\n"
    "- Keep every ![alt](...) image and [text](...) link in place. Translate the "
    "visible text and alt text; NEVER touch what is inside the parentheses.\n"
    "- Tokens that look like %%0%%, %%1%%, %%2%% are protected URLs. Reproduce "
    "each one character-for-character, exactly once, in the same position. Never "
    "translate, renumber, reformat, drop or invent them.\n"
    "\n"
    "NAMES — keep proper nouns for outlets, agencies, companies, people and "
    "places in their original Latin spelling unless {language} has a genuinely "
    "standard native form that a reader would expect (e.g. country and major "
    "city names). Source credits like 'The Hindu', 'PTI', 'Reuters', 'PIB' stay "
    "as they are. Acronyms stay as they are.\n"
    "- Never mix scripts inside a single name or word. A person's name is either "
    "fully in {language} script or fully in Latin script — never half of each.\n"
    "- Be consistent: once you render a name a certain way, use that same form "
    "everywhere else in the text.\n"
    "- Write all numbers, dates and figures in Western Arabic numerals (0-9), "
    "not in {language} script numerals.\n"
    "\n"
    "Output ONLY the translated markdown. No preamble, no explanation, no code "
    "fence."
)

_SHELL_SYSTEM = (
    "You translate the masthead and short UI labels of a news edition into "
    "{language} ({endonym}). Keep them short and natural — these are chrome, not "
    "prose.\n"
    "Use the everyday newspaper register {language} readers actually see in "
    "print, NOT a pure/literary/Sanskritised form. Where the common word is an "
    "English loanword (e.g. 'report'), use it transliterated into {language} "
    "script rather than an archaic native coinage.\n"
    "Write numbers and dates in Western Arabic numerals (0-9), not in "
    "{language}-script numerals, so they match the story bodies.\n"
    "Respond only with JSON."
)

# Unicode ranges each target language is allowed to write in, on top of Latin,
# digits and shared punctuation. Used to catch a rare failure mode seen in
# testing: the model splices a character from an unrelated script into the
# middle of a word (a Georgian letter inside a Kannada word), which renders as
# an obvious garbage glyph.
_SCRIPT_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "hi": ((0x0900, 0x097F),),
    "mr": ((0x0900, 0x097F),),
    "kn": ((0x0C80, 0x0CFF),),
    "te": ((0x0C00, 0x0C7F),),
    "ta": ((0x0B80, 0x0BFF),),
    "bn": ((0x0980, 0x09FF),),
    "ml": ((0x0D00, 0x0D7F),),
    "gu": ((0x0A80, 0x0AFF),),
    "pa": ((0x0A00, 0x0A7F),),
    "ur": ((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)),
}

# Script-neutral ranges every language may use: Latin + Latin Extended, combining
# diacriticals, general punctuation (— · … “”), currency, and letterlike symbols.
_NEUTRAL_RANGES: tuple[tuple[int, int], ...] = (
    (0x0000, 0x036F),
    (0x2000, 0x206F),
    (0x20A0, 0x20CF),
    (0x2100, 0x214F),
    (0x2190, 0x21FF),
    (0x2500, 0x27BF),
    (0xFE00, 0xFE0F),
)

# Anything inside a markdown link/image target, plus bare URLs. Protected from
# the model so a translation can never corrupt an image path or a citation.
_LINK_TARGET = re.compile(r"(?<=\]\()([^)\n]+)(?=\))")
_BARE_URL = re.compile(r"https?://[^\s)\]<>]+")
_PLACEHOLDER = re.compile(r"%%(\d+)%%")

_HEADING = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
_TOC_LINE = re.compile(r"^(\d+)\.\s+\[(.+)\]\(#([^)]*)\)\s+—\s+_(.+?)_\s*$")


def _protect_urls(md: str) -> tuple[str, list[str]]:
    """Swap every URL for a %%n%% token. Returns (masked_md, urls)."""
    urls: list[str] = []

    def _take(match: re.Match[str]) -> str:
        urls.append(match.group(0))
        return f"%%{len(urls) - 1}%%"

    masked = _LINK_TARGET.sub(_take, md)
    masked = _BARE_URL.sub(_take, masked)
    return masked, urls


def _restore_urls(md: str, urls: list[str]) -> str:
    def _put(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return urls[idx] if 0 <= idx < len(urls) else match.group(0)

    return _PLACEHOLDER.sub(_put, md)


def _placeholders_intact(masked: str, translated: str) -> bool:
    """True when the model returned every protected token exactly once."""
    return sorted(_PLACEHOLDER.findall(masked)) == sorted(
        _PLACEHOLDER.findall(translated)
    )


def _in_ranges(ch: str, ranges: tuple[tuple[int, int], ...]) -> bool:
    o = ord(ch)
    return any(lo <= o <= hi for lo, hi in ranges)


def _foreign_chars(text: str, lang: str) -> set[str]:
    """Characters belonging to neither Latin/punctuation nor ``lang``'s script."""
    allowed = _SCRIPT_RANGES.get(lang)
    if not allowed:
        return set()
    return {
        ch
        for ch in text
        if not _in_ranges(ch, _NEUTRAL_RANGES) and not _in_ranges(ch, allowed)
    }


def _split_paragraphs(md: str, budget: int = _MAX_CHUNK_CHARS) -> list[str]:
    """Break a long block into <=budget-char pieces at blank-line boundaries."""
    if len(md) <= budget:
        return [md]
    out: list[str] = []
    current: list[str] = []
    size = 0
    for para in md.split("\n\n"):
        if current and size + len(para) + 2 > budget:
            out.append("\n\n".join(current))
            current, size = [], 0
        current.append(para)
        size += len(para) + 2
    if current:
        out.append("\n\n".join(current))
    return out


_MAX_ATTEMPTS = 3


def _translate_block(backend, md: str, lang: str, language: str, endonym: str) -> str:
    """Translate one markdown block, URL-safe. Falls back to English on failure.

    Two quality gates per attempt:

    * **Placeholders** — a chunk that lost or mangled a ``%%n%%`` URL token is
      rejected outright; after the last attempt the English original is kept,
      because a readable English paragraph beats a broken image or a dead
      citation link.
    * **Script purity** — a chunk carrying characters from an unrelated script
      is retried, but never thrown away: if every attempt has some, the cleanest
      one is used. A stray glyph is a far smaller defect than an untranslated
      paragraph.
    """
    if not md.strip():
        return md

    system = _SYSTEM.format(language=language, endonym=endonym)
    pieces: list[str] = []
    for piece in _split_paragraphs(md):
        masked, urls = _protect_urls(piece)
        translated = ""
        best: tuple[int, str] | None = None  # (stray count, candidate)

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                raw = backend.complete(
                    system=system,
                    user=masked,
                    max_tokens=_MAX_TOKENS,
                    temperature=0.3,
                )
            except Exception as e:
                log.warning("[%s] translate call failed (try %d): %s", lang, attempt, e)
                time.sleep(_INTER_CALL_SLEEP_SECONDS)
                continue

            candidate = _strip_fence(raw)
            if not candidate or not _placeholders_intact(masked, candidate):
                log.warning("[%s] chunk lost a URL token (try %d)", lang, attempt)
                time.sleep(_INTER_CALL_SLEEP_SECONDS)
                continue

            stray = _foreign_chars(candidate, lang)
            if not stray:
                translated = candidate
                break

            if best is None or len(stray) < best[0]:
                best = (len(stray), candidate)
            log.warning(
                "[%s] chunk has stray characters %s (try %d)",
                lang, "".join(sorted(stray))[:20], attempt,
            )
            time.sleep(_INTER_CALL_SLEEP_SECONDS)

        if not translated and best is not None:
            log.warning("[%s] accepting cleanest chunk (%d stray char(s))", lang, best[0])
            translated = best[1]

        if translated:
            pieces.append(_restore_urls(translated, urls))
        else:
            log.warning("[%s] keeping a block in English after %d tries", lang, _MAX_ATTEMPTS)
            pieces.append(piece)
        time.sleep(_INTER_CALL_SLEEP_SECONDS)

    return "\n\n".join(pieces)


_REPAIR_SYSTEM = (
    "You are a {language} ({endonym}) copy editor. Each WORD below appears in "
    "the given {language} CONTEXT but was garbled by a translation model: it "
    "contains characters from some other script. Work out from the context what "
    "the word must mean and write it correctly.\n"
    "Every character of your answer must be {language} script, Latin, digits or "
    "punctuation — never any third script. Keep attached punctuation such as ':' "
    "as given. Respond only with JSON."
)

# A whitespace-delimited token, used to find the words that need repair.
_WORD = re.compile(r"\S+")
_REPAIR_BATCH = 20
_REPAIR_ROUNDS = 2
_REPAIR_CONTEXT_CHARS = 90


def _normalize_digits(md: str) -> str:
    """Fold script-native digits (०-९, ೦-೯, ౦-౯ …) down to ASCII 0-9.

    The prompt asks for Western Arabic numerals so figures match the English
    edition, but the model drifts — Marathi came back with ``६०,000``, i.e.
    Devanagari and ASCII digits inside a single number. This is a pure
    character mapping, so it is fixed deterministically rather than by asking
    the model again. URLs and citations are unaffected: they are restored from
    the ASCII English original and can never contain a native digit.
    """
    out = []
    for ch in md:
        if ch.isdigit() and not ch.isascii():
            try:
                out.append(str(unicodedata.decimal(ch)))
                continue
            except (TypeError, ValueError):
                pass
        out.append(ch)
    return "".join(out)


def _context_for(md: str, word: str) -> str:
    """The sentence fragment around a word, so the repairer can infer meaning."""
    i = md.find(word)
    if i < 0:
        return ""
    start = max(0, i - _REPAIR_CONTEXT_CHARS)
    end = i + len(word) + _REPAIR_CONTEXT_CHARS
    return md[start:end].replace("\n", " ").strip()


def _repair_stray_scripts(
    backend, md: str, lang: str, language: str, endonym: str
) -> str:
    """Second-pass fix for words carrying characters from an unrelated script.

    Even after per-chunk retries a handful of words survive with a foreign
    glyph spliced in (``ಸೌजन्य:`` — Kannada with Devanagari inside). Re-running
    a whole chunk to fix one word is wasteful, so the damaged words are
    collected and repaired in batches of one LLM call each.

    URLs are masked for the duration, and any replacement that is still impure
    (or that touches a placeholder) is discarded — the word simply keeps its
    original form.
    """
    if lang not in _SCRIPT_RANGES:
        return md

    masked, urls = _protect_urls(md)
    bad = sorted(
        {w for w in _WORD.findall(masked) if _foreign_chars(w, lang) and "%%" not in w}
    )
    if not bad:
        return md

    log.info("[%s] repairing %d word(s) with mixed scripts", lang, len(bad))
    system = _REPAIR_SYSTEM.format(language=language, endonym=endonym)
    fixes: dict[str, str] = {}
    pending = bad

    # The model is itself unreliable about script discipline — it sometimes
    # "corrects" a word into yet another wrong script. Every proposal is
    # validated, and whatever it fails to fix is simply retried once more.
    for _ in range(_REPAIR_ROUNDS):
        if not pending:
            break
        for i in range(0, len(pending), _REPAIR_BATCH):
            batch = pending[i : i + _REPAIR_BATCH]
            items = [
                {"word": w, "context": _context_for(masked, w)} for w in batch
            ]
            try:
                raw = backend.complete(
                    system=system,
                    user=(
                        'Return JSON: {"fixes": {"<word>": "<corrected word>", ...}}'
                        "\n\n" + json.dumps(items, ensure_ascii=False, indent=1)
                    ),
                    max_tokens=1500,
                    temperature=0.0,
                    json_mode=True,
                )
                data = extract_json(raw)
            except Exception as e:
                log.warning("[%s] repair batch failed: %s", lang, e)
                time.sleep(_INTER_CALL_SLEEP_SECONDS)
                continue

            pairs = data.get("fixes") if isinstance(data, dict) else None
            if isinstance(pairs, dict):
                for original, fixed in pairs.items():
                    fixed = str(fixed or "").strip()
                    if (
                        original in batch
                        and fixed
                        and fixed != original
                        and "%%" not in fixed
                        and not _foreign_chars(fixed, lang)
                    ):
                        fixes[original] = fixed
            time.sleep(_INTER_CALL_SLEEP_SECONDS)
        pending = [w for w in pending if w not in fixes]

    if not fixes:
        log.warning("[%s] repair pass fixed nothing (%d word(s) left)", lang, len(bad))
        return md

    # Longest-first so a short word is never substituted inside a longer one.
    for original in sorted(fixes, key=len, reverse=True):
        masked = masked.replace(original, fixes[original])
    log.info("[%s] repaired %d/%d word(s)", lang, len(fixes), len(bad))
    return _restore_urls(masked, urls)


def _strip_fence(raw: str) -> str:
    """Models occasionally wrap the answer in ```markdown fences. Unwrap it."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _shell_strings(
    backend, language: str, endonym: str, date_text: str, count_text: str
) -> dict[str, str]:
    """Translate the masthead + the labels the renderer emits outside prose.

    The masthead is rebuilt from these strings rather than run through the
    prose translator: sent as free markdown, the model reads
    "# GROUNDED — Daily Edition" as branding and inconsistently leaves the whole
    header in English (it did for Kannada but not Hindi in testing). Asking for
    the fields explicitly makes the header deterministic across languages.
    """
    fallback = {
        "daily_edition": "Daily Edition",
        "tagline": "Autonomous, fact-grounded newsletter",
        "date": date_text,
        "count": count_text,
        "toc": "In this edition",
        "report": "report",
        "debate": "debate",
        "notice": f"{endonym} edition — machine-translated from the English original.",
    }
    try:
        raw = backend.complete(
            system=_SHELL_SYSTEM.format(language=language, endonym=endonym),
            user=(
                f"Translate each field into {language}. The brand name GROUNDED "
                "is not included here — do not add it.\n\n"
                'Return JSON: {"daily_edition": "<heading meaning Daily Edition>", '
                f'"tagline": "<{fallback["tagline"]}>", '
                f'"date": "<{date_text} — written naturally, as a newspaper dates itself>", '
                f'"count": "<{count_text} — written naturally>", '
                '"toc": "<heading meaning: In this edition>", '
                '"report": "<label for a straight news report>", '
                '"debate": "<label for a two-sided debate item>", '
                '"notice": "<one short sentence telling the reader this edition was '
                'automatically translated from the English original>"}'
            ),
            max_tokens=500,
            temperature=0.2,
            json_mode=True,
        )
        data = extract_json(raw)
        if isinstance(data, dict):
            return {k: (str(data.get(k) or "").strip() or v) for k, v in fallback.items()}
    except Exception as e:
        log.warning("[%s] masthead/label translation failed: %s", language, e)
    return fallback


# `*Autonomous, fact-grounded newsletter · Friday, 31 July 2026 · 20 stories*`
_SUBTITLE = re.compile(r"^\*(.+?)\s+·\s+(.+?)\s+·\s+(.+?)\*\s*$", re.MULTILINE)


def _parse_masthead(head: str) -> tuple[str, str]:
    """Pull (date_text, count_text) out of the rendered masthead subtitle."""
    m = _SUBTITLE.search(head)
    if not m:
        return "", ""
    return m.group(2).strip(), m.group(3).strip()


def _split_edition(md: str) -> tuple[str, list[str], str]:
    """Split the rendered edition into (head, story blocks, footer).

    ``_render_story`` prefixes every story with a ``---`` rule and the closing
    credit block sits behind one too, so the horizontal rules are a reliable
    seam. Returns an empty footer when the shape is unexpected.
    """
    parts = [p for p in re.split(r"\n---\n", md)]
    if len(parts) < 3:
        return md, [], ""
    head, *rest = parts
    footer = rest.pop() if rest and "Every claim above" in rest[-1] else ""
    return head, rest, footer


def _strip_toc(head: str) -> tuple[str, list[tuple[str, str]]]:
    """Remove the TOC list from the head block.

    Returns (head_without_list, [(headline, mode), ...]) so the list can be
    rebuilt from the translated headings afterwards.
    """
    kept: list[str] = []
    entries: list[tuple[str, str]] = []
    for line in head.splitlines():
        m = _TOC_LINE.match(line)
        if m:
            entries.append((m.group(2), m.group(4)))
            continue
        kept.append(line)
    return "\n".join(kept).rstrip() + "\n", entries


def _rebuild_toc(
    stories: list[str], modes: list[tuple[str, str]], ui: dict[str, str]
) -> list[str]:
    """Regenerate TOC lines from the translated story headings.

    Anchors are recomputed with the renderer's own slug function so they match
    the translated ``## N. Headline`` they point at.
    """
    lines: list[str] = []
    for i, block in enumerate(stories):
        m = _HEADING.search(block)
        if not m:
            continue
        num, headline = m.group(1), m.group(2)
        mode_en = modes[i][1].lower() if i < len(modes) else "report"
        mode = ui.get(mode_en, mode_en)
        anchor = _slug(f"{num}. {headline}")
        lines.append(f"{num}. [{headline}](#{anchor}) — _{mode}_")
    return lines


def translate_edition(md: str, lang: str) -> str:
    """Translate one rendered edition into ``lang``. Raises if unsupported."""
    if lang not in LANGUAGES:
        raise ValueError(f"unsupported language {lang!r}; known: {', '.join(LANGUAGES)}")
    language, endonym = LANGUAGES[lang]

    backend = make_gemini()
    if backend is None or getattr(backend, "is_local", False):
        raise RuntimeError("translation needs a Gemini backend (set GEMINI_API_KEY)")

    head, stories, footer = _split_edition(md)
    _, toc_entries = _strip_toc(head)
    date_text, count_text = _parse_masthead(head)

    ui = _shell_strings(backend, language, endonym, date_text, count_text)
    time.sleep(_INTER_CALL_SLEEP_SECONDS)

    log.info("[%s] translating %d stor(y/ies)...", lang, len(stories))
    out_stories: list[str] = []
    for i, block in enumerate(stories, 1):
        log.info("[%s] story %d/%d", lang, i, len(stories))
        out_stories.append(_translate_block(backend, block, lang, language, endonym))

    out_footer = (
        _translate_block(backend, footer, lang, language, endonym) if footer else ""
    )

    # Masthead is rebuilt, not translated — see _shell_strings.
    parts = [
        f"# GROUNDED — {ui['daily_edition']}",
        f"*{ui['tagline']} · {ui['date']} · {ui['count']}*",
        f"## {ui['toc']}",
    ]
    toc_lines = _rebuild_toc(out_stories, toc_entries, ui)
    if toc_lines:
        parts.append("\n".join(toc_lines))
    parts.append(f"<sub>*{ui['notice']}*</sub>")
    head_md = "\n\n".join(p for p in parts if p.strip())

    blocks = [head_md, *(b.strip() for b in out_stories)]
    if out_footer.strip():
        blocks.append(out_footer.strip())
    out = "\n\n---\n\n".join(blocks).strip() + "\n"

    # Final sweeps. Digit folding runs over the whole document at once so a
    # heading and the TOC anchor pointing at it stay identical.
    out = _repair_stray_scripts(backend, out, lang, language, endonym)
    return _normalize_digits(out)


def resolve_languages(cli_langs: tuple[str, ...] | list[str] | None) -> list[str]:
    """CLI flags win, then EDITION_LANGUAGES, then DEFAULT_LANGUAGES."""
    raw: list[str]
    if cli_langs:
        raw = list(cli_langs)
    else:
        env = env_value("EDITION_LANGUAGES")
        raw = [p.strip() for p in env.split(",")] if env else list(DEFAULT_LANGUAGES)

    out: list[str] = []
    for code in raw:
        code = code.strip().lower()
        if not code or code in ("en", *out):
            continue
        if code not in LANGUAGES:
            log.warning("unknown language %r — skipping (known: %s)", code, ", ".join(LANGUAGES))
            continue
        out.append(code)
    return out


_REL_TARGET = re.compile(r"(?<=\]\()([^)\n]+)(?=\))")


def _rehome_relative_paths(md: str, src: Path, dest_dir: Path) -> str:
    """Rewrite relative link/image targets for a file moving to ``dest_dir``.

    The renderer emits image paths relative to the edition file
    (``images/2026-08-03/x.jpg``). Translations live one level deeper, so those
    targets need a ``../`` prefix or every photo 404s. Absolute URLs and
    in-page ``#anchors`` are left alone.
    """
    src_dir = Path(src).parent.resolve()
    dest_dir = Path(dest_dir).resolve()
    if src_dir == dest_dir:
        return md

    def _fix(match: re.Match[str]) -> str:
        target = match.group(0).strip()
        if not target or target.startswith(("#", "/", "http://", "https://", "mailto:", "data:")):
            return match.group(0)
        rebased = os.path.relpath(src_dir / target, dest_dir)
        return rebased.replace(os.sep, "/")

    return _REL_TARGET.sub(_fix, md)


def translate_edition_file(
    src: Path,
    langs: list[str] | None = None,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Translate a rendered edition into every requested language.

    Output lands in one self-contained folder per edition — by default
    ``<output>/editions/<date>/`` — holding the English original alongside
    ``edition-<date>.<lang>.md`` for each language, so the whole multilingual
    edition can be shipped as a unit.

    One language failing never stops the others, and the English source file is
    never modified.
    """
    src = Path(src)
    md = src.read_text(encoding="utf-8")
    codes = langs if langs is not None else resolve_languages(None)

    # `edition-2026-08-03.md` -> folder `editions/2026-08-03/`
    stem = src.stem
    slug = stem.removeprefix("edition-") or stem
    dest_dir = Path(out_dir) if out_dir is not None else src.parent / "editions" / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    failed: list[str] = []

    # Drop the English original into the folder too, so it is self-contained.
    en_dest = dest_dir / f"{stem}.en.md"
    en_dest.write_text(_rehome_relative_paths(md, src, dest_dir), encoding="utf-8")
    written.append(en_dest)

    for code in codes:
        try:
            out_md = translate_edition(md, code)
        except Exception as e:
            log.error("translation to %s failed: %s", code, e)
            failed.append(code)
            continue
        dest = dest_dir / f"{stem}.{code}.md"
        dest.write_text(
            _rehome_relative_paths(out_md, src, dest_dir), encoding="utf-8"
        )
        written.append(dest)
        log.info("wrote %s", dest)

    return {
        "written": written,
        "failed": failed,
        "languages": codes,
        "dir": dest_dir,
    }
