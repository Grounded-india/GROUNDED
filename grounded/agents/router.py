"""Per-agent model routing for the Layer 3 crew.

Each agent role is assigned to a provider (per the product spec):

    fact_extractor  -> nemotron        (NVIDIA NIM)
    verifier        -> gemini          (Google Gemini 2.5)
    context         -> nemotron
    perspective     -> nemotron        (runs as a multi-agent debate)
    editor          -> gemini

If the provider's API key is missing (or ``force_local`` / ``LLM_BACKEND=local``),
that role transparently falls back to the deterministic offline ``LocalBackend``
so the whole crew still runs without any keys. A single ``LLMBackend`` can also
be wrapped to force every role onto one model (used by tests and single-model
runs).
"""

from __future__ import annotations

import os

from grounded.agents.llm import (
    LLMBackend,
    LocalBackend,
    make_gemini,
    make_nemotron,
)

ROLE_PROVIDER: dict[str, str] = {
    "fact_extractor": "nemotron",
    "verifier": "gemini",
    "context": "nemotron",
    "perspective": "nemotron",
    "editor": "gemini",
}

_PROVIDER_FACTORY = {
    "nemotron": make_nemotron,
    "gemini": make_gemini,
}


class ModelRouter:
    """Resolves each agent role to a backend, caching provider clients."""

    def __init__(self, force_local: bool | None = None) -> None:
        if force_local is None:
            force_local = os.environ.get("LLM_BACKEND", "").lower() == "local"
        self.force_local = force_local
        self._cache: dict[str, LLMBackend] = {}

    def _provider(self, provider: str) -> LLMBackend:
        if provider in self._cache:
            return self._cache[provider]
        backend: LLMBackend | None = None
        if not self.force_local:
            factory = _PROVIDER_FACTORY.get(provider)
            if factory is not None:
                backend = factory()
        backend = backend or LocalBackend()
        self._cache[provider] = backend
        return backend

    def for_role(self, role: str) -> LLMBackend:
        return self._provider(ROLE_PROVIDER.get(role, "nemotron"))

    def summary(self) -> dict[str, str]:
        """Which concrete backend each role resolved to (for the audit trace)."""
        return {role: self.for_role(role).name for role in ROLE_PROVIDER}


class SingleBackendRouter:
    """Force every role onto one backend (single-model runs and tests)."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self.force_local = getattr(backend, "is_local", False)

    def for_role(self, role: str) -> LLMBackend:
        return self._backend

    def summary(self) -> dict[str, str]:
        return {role: self._backend.name for role in ROLE_PROVIDER}


Router = ModelRouter | SingleBackendRouter


def as_router(obj: object | None) -> Router:
    """Coerce ``None`` / an ``LLMBackend`` / a router into a router.

    * ``None``            -> default ``ModelRouter`` (keys from env, local fallback)
    * an ``LLMBackend``   -> ``SingleBackendRouter`` (that backend for every role)
    * a router            -> returned unchanged
    """
    if obj is None:
        return ModelRouter()
    if isinstance(obj, (ModelRouter, SingleBackendRouter)):
        return obj
    if hasattr(obj, "for_role"):
        return obj  # duck-typed router
    if hasattr(obj, "is_local") and hasattr(obj, "complete"):
        return SingleBackendRouter(obj)  # an LLMBackend
    raise TypeError(f"cannot coerce {type(obj)!r} into a model router")
