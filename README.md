# Grounded — An Autonomous, Fact-Driven News Channel

An autonomous, multi-agent AI news operation for India. Every claim is tied to a primary source, the importance ranker deliberately downweights outrage over evidence, and the pipeline is **auditable at every layer**. Ships as a daily newsletter / digital newspaper — cited articles, inline sources, no video.

## Documentation

- **[docs/README.md](docs/README.md)** — full vision, architecture (the five layers), design commitments, tech stack, and phased milestones.
- **[docs/progress.md](docs/progress.md)** — running build log: what's actually implemented and how to run it (Layers 1, 2, 2.5, and 3).

## The pipeline at a glance

```
[1] Source Ingestion
       ↓
[2] Event Clustering + Importance Ranking
       ↓
[3] Multi-Agent Story Building        ← core IP
       ↓
[4] Article + Edition Assembly        (not yet built)
       ↓
[5] Publishing                        (not yet built)
```

Layer 3 is a five-agent crew (Fact Extractor → Primary Source Verifier → Context → Perspective → Editor / Auditor). Generation runs on **Nemotron**; enforcement (verification + editing) runs on **Gemini** but can only ever make a story _stricter_ — the un-gameable core is plain, unit-tested Python. See [docs/README.md](docs/README.md#3-multi-agent-story-building-core-ip) for details, including the detail-level half-truth check and debate mode.

## Quick start

Requires Docker (Postgres + pgvector) and Python 3.12+.

```bash
# 1. start Postgres
docker compose -f infra/docker-compose.yml up -d

# 2. set up the environment
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env            # then add keys as needed

# 3. Layer 1 — ingest raw items from all sources
grounded ingest

# 4. Layer 2 — embed → cluster → rank → scrape
grounded pipeline

# 5. Layer 3 — run the five-agent crew on selected events
#    offline (deterministic floor only, no semantic fidelity check):
python -m grounded.agents build --limit 5
#    with models (enables the detail-level fidelity check):
pip install openai                          # not yet in pyproject.toml
#    add NVIDIA_API_KEY and GEMINI_API_KEY to .env
python -m grounded.agents build --limit 5
```

See [docs/progress.md](docs/progress.md) for the full command reference, live-run results, and known limitations.
