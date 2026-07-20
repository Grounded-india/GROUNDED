"""Unit tests for per-agent model routing (no network)."""

from __future__ import annotations

from grounded.agents.llm import LocalBackend
from grounded.agents.router import (
    ROLE_PROVIDER,
    ModelRouter,
    SingleBackendRouter,
    as_router,
)


def test_role_provider_mapping_matches_spec():
    assert ROLE_PROVIDER["fact_extractor"] == "nemotron"
    assert ROLE_PROVIDER["verifier"] == "gemini"
    assert ROLE_PROVIDER["context"] == "nemotron"
    assert ROLE_PROVIDER["perspective"] == "nemotron"
    assert ROLE_PROVIDER["editor"] == "gemini"


def test_force_local_routes_all_roles_to_local():
    router = ModelRouter(force_local=True)
    for role in ROLE_PROVIDER:
        assert router.for_role(role).is_local is True
    assert set(router.summary().values()) == {"local"}


def test_as_router_none_returns_model_router():
    assert isinstance(as_router(None), ModelRouter)


def test_as_router_wraps_single_backend():
    local = LocalBackend()
    router = as_router(local)
    assert isinstance(router, SingleBackendRouter)
    assert router.for_role("editor") is local
    assert set(router.summary().values()) == {"local"}


def test_as_router_passes_router_through():
    router = ModelRouter(force_local=True)
    assert as_router(router) is router
