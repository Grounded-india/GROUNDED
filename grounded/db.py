from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from grounded.config import settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )
    return _pool


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with get_pool().connection() as conn:
        yield conn


@contextmanager
def cursor() -> Iterator[psycopg.Cursor]:
    with connection() as conn, conn.cursor() as cur:
        yield cur


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
