"""Shared HTTP client. Feeds tend to reject default python UAs (Reddit especially)."""

import httpx

# Real-looking UA. Reddit's RSS specifically rejects default python-httpx UA.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; GroundedNewsBot/0.1; "
    "+https://github.com/example/grounded)"
)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def make_client(user_agent: str | None = None) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": user_agent or DEFAULT_USER_AGENT},
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )
