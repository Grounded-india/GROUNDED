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
# The 49B "super" reliably follows the "respond only with JSON" instruction and
# produces clean, parseable output. Smaller/faster nano models (e.g.
# nemotron-3-nano-30b) ignore JSON mode on complex prompts and emit reasoning
# prose + numbered lists instead, which cannot be parsed - so we default to super
# for correctness. It is slower (~80-130s/call on the free tier); json_mode keeps
# it from rambling to the token cap. Override with NEMOTRON_MODEL if you have a
# faster endpoint or want to trade quality for speed.
DEFAULT_NEMOTRON_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
# NOTE: gemini-2.5-flash is retired for new API keys (returns 404). The *-lite
# aliases are the reliably-callable, current flash tier on the free plan. Bump to
# gemini-flash-latest / gemini-2.5-pro via GEMINI_MODEL if your quota allows it.
DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"

# Per-request wall-clock cap so a slow/hung provider can't freeze a run forever.
# The super model's fact-extraction call legitimately takes ~135s on the free
# tier, so this sits comfortably above that to avoid aborting real work; a truly
# hung request still aborts here and the SDK retries (with backoff) to ride out
# transient 429/503/5xx blips. Override via LLM_TIMEOUT.
DEFAULT_TIMEOUT = 240.0
DEFAULT_MAX_RETRIES = 4


@runtime_checkable
class LLMBackend(Protocol):
    name: str
    is_local: bool

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str: ...


class LocalBackend:
    """Offline marker backend. Agents handle ``is_local`` directly and never
    call :meth:`complete`, keeping the offline path fully deterministic."""

    name = "local"
    is_local = True

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        json_mode: bool = False,
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
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        # Anthropic has no response_format flag; json_mode is a no-op here (the
        # default router does not use this backend).
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

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        system_prefix: str = "",
        extra_body: dict[str, Any] | None = None,
    ) -> None:
        from openai import OpenAI

        self.name = name
        self.model = model
        # Prepended to every system prompt. Used to switch Nemotron reasoning off
        # ("detailed thinking off") so it returns clean JSON fast instead of
        # emitting a long <think> block that blows the timeout.
        self.system_prefix = system_prefix
        # Provider-specific params forwarded to chat.completions.create via
        # extra_body. Used by NVIDIA Nemotron 3 reasoning variants (550B, 340B,
        # 120B) which read {"chat_template_kwargs": {"enable_thinking": bool}}
        # and {"reasoning_budget": int}. Older models ignore unknown fields.
        self.extra_body = extra_body or None
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        if self.system_prefix:
            system = f"{self.system_prefix}{system}"
        # JSON mode forces valid, self-terminating JSON: the model stops when the
        # object closes instead of rambling to the token cap (which produced
        # truncated / half-prose output on small models). Only pass it when the
        # caller actually expects JSON.
        kwargs: dict[str, Any] = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
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


def _timeout() -> float:
    try:
        return float(env_value("LLM_TIMEOUT") or DEFAULT_TIMEOUT)
    except ValueError:
        return DEFAULT_TIMEOUT


def make_nemotron() -> LLMBackend | None:
    """NVIDIA NIM (Nemotron) backend, or None if no key is configured.

    Reasoning control (Nemotron models reason by default, which is slow and eats
    output tokens):

    * ``NEMOTRON_THINKING=on``  -> allow reasoning, budget = NEMOTRON_REASONING_BUDGET
      (default 8192). Best debate quality, ~2-4x wall clock per call.
    * default / ``off``         -> disable reasoning. Fast, clean answers.

    Two mechanisms are set simultaneously so the switch works across model
    families:
      - ``system_prefix="detailed thinking off\\n"`` for the 49B ``super`` model
        (text-prompt convention).
      - ``extra_body={"chat_template_kwargs":{"enable_thinking": bool}, ...}``
        for Nemotron 3 reasoning variants (550B, 340B, 120B).
    """
    key = env_value("NVIDIA_API_KEY")
    if not _has_real_key(key):
        return None
    model = env_value("NEMOTRON_MODEL") or DEFAULT_NEMOTRON_MODEL
    thinking_on = env_value("NEMOTRON_THINKING").lower() == "on"
    try:
        reasoning_budget = int(env_value("NEMOTRON_REASONING_BUDGET") or 8192)
    except ValueError:
        reasoning_budget = 8192

    extra_body: dict[str, Any] = {
        "chat_template_kwargs": {"enable_thinking": thinking_on},
    }
    if thinking_on:
        extra_body["reasoning_budget"] = reasoning_budget

    return OpenAICompatibleBackend(
        name="nemotron",
        base_url=NEMOTRON_BASE_URL,
        api_key=key,
        model=model,
        timeout=_timeout(),
        system_prefix="" if thinking_on else "detailed thinking off\n",
        extra_body=extra_body,
    )


def make_gemini() -> LLMBackend | None:
    """Google Gemini backend, or None if no key is configured."""
    key = env_value("GEMINI_API_KEY")
    if not _has_real_key(key):
        return None
    model = env_value("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    return OpenAICompatibleBackend(
        name="gemini", base_url=GEMINI_BASE_URL, api_key=key, model=model, timeout=_timeout()
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
# Reasoning models (e.g. Nemotron-super) can wrap their answer in <think>...</think>
# whose free text may contain stray braces that confuse a brace-matching scan.
# Strip any such block (including an unterminated one) before looking for JSON.
_THINK_BLOCK = re.compile(r"<think\b[^>]*>.*?</think>", re.DOTALL | re.IGNORECASE)
_THINK_OPEN = re.compile(r"<think\b[^>]*>.*", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove reasoning-model <think>...</think> blocks (incl. an unterminated one)."""
    text = _THINK_BLOCK.sub("", text)
    return _THINK_OPEN.sub("", text)


def extract_json(text: str) -> Any:
    """Pull the first JSON value out of an LLM response.

    Tolerates markdown code fences, reasoning-model <think> blocks, and
    surrounding prose, which models emit even when told not to. Raises
    ``ValueError`` if nothing parseable is found.
    """
    if not text or not text.strip():
        raise ValueError("empty LLM response")

    text = strip_reasoning(text)
    if not text.strip():
        raise ValueError("LLM response was only a reasoning block, no JSON")

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
