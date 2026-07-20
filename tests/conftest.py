"""Shared pytest fixtures. Pure-logic tests need nothing here; the integration
tests use ``db_available`` to skip cleanly when Postgres isn't running."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def db_available() -> bool:
    try:
        from grounded.db import cursor

        with cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception as exc:  # pragma: no cover - depends on local env
        pytest.skip(f"Postgres not available: {exc}")
        return False
