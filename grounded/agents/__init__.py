"""
Layer 3 - Multi-Agent Story Building (core IP).

A five-agent crew turns one *selected* event (Layer 2 output) into a grounded
story package:

    Fact Extractor      -> pull atomic, verifiable claims from source material
    Primary Verifier    -> mark tier-1 backing + independent corroboration
    Context Agent       -> add grounded background (why this matters)
    Perspective Agent   -> steel-man the real debate sides
    Editor / Auditor    -> deterministic gate: drop ungrounded claims, assemble

Design split that makes this auditable and hard to game:
  * GENERATION (extraction, context, perspective) is done by an LLM backend,
    with a deterministic offline fallback so the whole crew runs without an API
    key (mirrors the local embedding backend in Layer 2).
  * ENFORCEMENT (grounding to real source ids, verification rules, the editor
    approval gate) is plain Python - it is unit-tested and a model cannot talk
    its way past it.

This package is intentionally self-contained: it only *reads* the shared
config/db/models and never edits Layer 1/2 modules, so it can be developed in
parallel without merge conflicts. Run it with ``python -m grounded.agents``.
"""

from grounded.agents.crew import build_story
from grounded.agents.runner import build_stories

__all__ = ["build_story", "build_stories"]
