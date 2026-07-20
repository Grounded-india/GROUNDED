"""Pluggable LLM backend for the generative agents.

Two backends, chosen the same way Layer 2 chooses its embedding backend:

  * ``AnthropicBackend`` - real Claude calls (used when ANTHROPIC_API_KEY is set)
  * ``LocalBackend``     - a marker for offline/deterministic mode; the agents
                           branch on ``backend.is_local`` and synthesize output
                           with plain Python instead of calling out.

Backend selection is read from the environment (``LLM_BACKEND`` =
auto|anthropic|local, ``GROUNDED_LLM_MODEL``) plus the existing
``settings.anthropic_api_key`` - no edits to the shared config module.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Protocol, runtime_checkable

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-3-5-sonnet-latest"

# OpenAI-compatible providers used by the Layer 3 crew. Both NVIDIA NIM and
# Google Gemini expose an OpenAI-shaped /chat/completions endpoint, so a single
# client class drives both - only base_url / key / model differ.
NEMOTRON_BASE_URL = "https://integrate.api.nvidia.com/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_NEMOTRON_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


@runtime_checkable
class LLMBackend(Protocol):
    name: str
    is_local: bool

    def complete(
        self, *, system: str, user: str, max_tokens: int = 1500, temperature: float = 0.2
    ) -> str: ...


class LocalBackend:
    """Offline marker backend. Agents handle ``is_local`` directly and never
    call :meth:`complete`, keeping the offline path fully deterministic."""

    name = "local"
    is_local = True

    def complete(
        self, *, system: str, user: str, max_tokens: int = 1500, temperature: float = 0.2
    ) -> str:
        raise RuntimeError(
            "LocalBackend.complete() should never be called - agents must branch "
            "on backend.is_local and synthesize output locally."
        )


class AnthropicBackend:
    """Thin wrapper over the Anthropic Messages API."""

    name = "anthropic"
    is_local = False

    def __init__(self, api_key: str, model: str | None = None) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.environ.get("GROUNDED_LLM_MODEL", DEFAULT_MODEL)

    def complete(
        self, *, system: str, user: str, max_tokens: int = 1500, temperature: float = 0.2
    ) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ]
        return "".join(parts).strip()


class OpenAICompatibleBackend:
    """Backend for any OpenAI-compatible chat endpoint (NVIDIA NIM, Gemini).

    ``name`` doubles as the provider label recorded in the audit trace
    (e.g. "nemotron", "gemini").
    """

    is_local = False

    def __init__(self, *, name: str, base_url: str, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.name = name
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def complete(
        self, *, system: str, user: str, max_tokens: int = 1500, temperature: float = 0.2
    ) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()


def _has_real_key(key: str) -> bool:
    key = (key or "").strip()
    return bool(key) and "..." not in key


def env_value(name: str) -> str:
    """Read a config value from the real environment, falling back to .env.

    pydantic-settings loads .env into ``settings`` but does not populate
    ``os.environ``, so keys the crew needs (NVIDIA_API_KEY, GEMINI_API_KEY, model
    overrides) are read here without touching the shared config module.
    """
    val = os.environ.get(name)
    if val:
        return val
    try:
        from dotenv import dotenv_values

        return (dotenv_values(".env").get(name) or "").strip()
    except Exception:  # pragma: no cover - dotenv always available as a dep
        return ""


def make_nemotron() -> LLMBackend | None:
    """NVIDIA NIM (Nemotron) backend, or None if no key is configured."""
    key = env_value("NVIDIA_API_KEY")
    if not _has_real_key(key):
        return None
    model = env_value("NEMOTRON_MODEL") or DEFAULT_NEMOTRON_MODEL
    return OpenAICompatibleBackend(
        name="nemotron", base_url=NEMOTRON_BASE_URL, api_key=key, model=model
    )


def make_gemini() -> LLMBackend | None:
    """Google Gemini backend, or None if no key is configured."""
    key = env_value("GEMINI_API_KEY")
    if not _has_real_key(key):
        return None
    model = env_value("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    return OpenAICompatibleBackend(
        name="gemini", base_url=GEMINI_BASE_URL, api_key=key, model=model
    )


def get_backend(prefer: str | None = None) -> LLMBackend:
    """Return the configured backend. Falls back to local when no key is set."""
    from grounded.config import settings

    choice = (prefer or os.environ.get("LLM_BACKEND", "auto")).lower()
    key = settings.anthropic_api_key
    has_key = _has_real_key(key)

    if choice == "local":
        return LocalBackend()
    if choice == "anthropic":
        if not has_key:
            raise RuntimeError(
                "LLM_BACKEND=anthropic but ANTHROPIC_API_KEY is missing/placeholder."
            )
        return AnthropicBackend(key)
    # auto
    if has_key:
        return AnthropicBackend(key)
    log.info("no ANTHROPIC_API_KEY found - using local offline agent backend")
    return LocalBackend()


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> Any:
    """Pull the first JSON value out of an LLM response.

    Tolerates markdown code fences and surrounding prose, which models emit even
    when told not to. Raises ``ValueError`` if nothing parseable is found.
    """
    if not text or not text.strip():
        raise ValueError("empty LLM response")

    fenced = _JSON_FENCE.search(text)
    candidate = fenced.group(1).strip() if fenced else text.strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    start = next((i for i, ch in enumerate(candidate) if ch in "[{"), None)
    if start is None:
        raise ValueError(f"no JSON found in response: {text[:200]!r}")

    open_ch = candidate[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(candidate)):
        ch = candidate[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(candidate[start : i + 1])

    raise ValueError("unterminated JSON in LLM response")
