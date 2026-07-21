"""Unit tests for the shared boilerplate / chrome text hygiene helpers."""

from __future__ import annotations

import pytest

from grounded.agents.cleaning import is_boilerplate, strip_boilerplate

BOILERPLATE = [
    "You are logged in Loading...",
    "Subscribe nowSubscribed with another email?",
    "Your active subscription(s) Account subscription benefits alongside Premium Stories",
    "Published - July 20, 2026 06:19 pm IST You are logged in Loading...",
    "Accept all cookies to continue",
    "All rights reserved.",
    "Please sign in to your account",
]

REAL = [
    "Four Indian nationals were killed in the attack on MV Golden Leo.",
    "The Bill amends the Supreme Court (Number of Judges) Act, 1956.",
    "The RBI cut the repo rate by 25 basis points on Monday.",
    "The government's new crop-insurance subscription policy covers 10 million farmers.",
]


@pytest.mark.parametrize("text", BOILERPLATE)
def test_flags_boilerplate(text):
    assert is_boilerplate(text) is True


@pytest.mark.parametrize("text", REAL)
def test_spares_real_reporting(text):
    assert is_boilerplate(text) is False


def test_strip_boilerplate_keeps_real_half_of_a_line():
    text = "You are logged in. The RBI cut the repo rate by 25 basis points."
    out = strip_boilerplate(text)
    assert "logged in" not in out.lower()
    assert "repo rate" in out


def test_strip_boilerplate_drops_chrome_lines():
    text = (
        "Subscribe now\n"
        "The cabinet cleared the manufacturing scheme on Monday.\n"
        "Your active subscription benefits await"
    )
    out = strip_boilerplate(text)
    assert "manufacturing scheme" in out
    assert "subscribe" not in out.lower()
    assert "subscription" not in out.lower()


def test_strip_boilerplate_drops_orphan_citation_lines():
    text = (
        "- Published - July 20, 2026 06:19 pm IST You are logged in Loading... (the_hindu)\n"
        "- Subscribe nowSubscribed with another email? (the_hindu)\n"
        "- Spain won the World Cup final on Sunday. (indian_express)"
    )
    out = strip_boilerplate(text)
    assert "(the_hindu)" not in out
    assert "won the World Cup final" in out
    assert "(indian_express)" in out


def test_strip_boilerplate_handles_empty():
    assert strip_boilerplate("") == ""
    assert strip_boilerplate(None) is None
