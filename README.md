# Grounded — An Autonomous, Fact-Driven News Channel

> Working name. Feel free to rename.

An autonomous, multi-agent AI news operation for India. Every claim tied to a primary source. No human editor's bias in the daily loop. Publishes as a **daily newsletter / digital newspaper** — cited articles, inline sources, no video.

---

## The Idea

Indian news is heavily narrative-driven. Different outlets present incompatible versions of the same event, and audiences get news filtered by ideology rather than by importance or evidence.

**Grounded** is an attempt at the opposite: a system that selects stories by policy/legal impact rather than outrage, grounds every claim in primary sources (government documents, court judgments, official statistics, wire services), and — critically — is **auditable at every layer**. If a broadcast looks biased, you can trace which layer failed and see exactly which sources were consulted.

**What it is not:**
- Not a video/TV news channel (video adds cost and complexity without helping the core "cited facts" mission).
- Not a "one big LLM writes a news article" pipeline (unauditable; hallucination-prone).

**What it is:**
- A multi-agent pipeline where each agent has one narrow job.
- A **daily newsletter + digital newspaper** — cited articles with inline source links, a front page of top stories, section pages, an email edition.
- A system whose importance ranker deliberately downweights outrage cycles, celebrity noise, and single-source viral claims.
- A system where **social media is topic radar, never truth signal.**

---

## Core Design Commitments

| Commitment | Why |
|---|---|
| **Text-first: newsletter + digital newspaper** | Cited claims live naturally in text; drops video cost and complexity |
| **Two source tiers: primary/wire = truth ground, social = topic radar** | Prevents capture by coordinated social-media campaigns |
| **Steel-manned perspectives, not false balance** | If evidence is one-sided, say so; only 50/50 genuine policy tradeoffs |
| **Every claim must have a citation** | The Editor agent drops uncited claims rather than softening them |
| **English first, Hindi as phase-2 track** | Ship the English pipeline before splitting effort |
| **Daily edition cadence** | One auto-produced daily edition (front page + section pages + email newsletter); not hourly, not real-time |

---

## Architecture — Five Layers

```
[1] Source Ingestion
       ↓
[2] Event Clustering + Importance Ranking
       ↓
[3] Multi-Agent Story Building        ← core IP
       ↓
[4] Article + Edition Assembly
       ↓
[5] Publishing (web newspaper + email newsletter)
```

**Current focus: Layers 1, 2, 3.** They output a format-agnostic story package (claims + citations + context + perspectives + editorial approval). Layers 4 and 5 are just presentation.

### 1. Source Ingestion

Two tiers of input; every item stored raw with `source_url`, `source_tier`, `fetched_at`, `content`. No editorial touch.

**Truth ground (primary sources — high trust):**
- PIB India press releases (RSS)
- MEA, MHA, MoF, other ministry releases
- Supreme Court + High Court judgments (Indian Kanoon)
- RBI notifications, MoSPI statistics, ECI announcements, CAG reports
- Parliament proceedings (PRS India, Sansad TV transcripts)
- Gazette notifications

**Signal layer (topic radar — low trust):**
- Wire services: Reuters, AP, AFP (public feeds); PTI/ANI (public feeds)
- Google News RSS (broad topic sweep)
- Reddit RSS: `r/india`, `r/indianews`, `r/IndiaSpeaks`, `r/geopolitics`
- Twitter/X: start with Nitter/RSSHub mirrors; upgrade to paid API only if needed
- YouTube auto-captions from major outlet channels

### 2. Event Clustering + Importance Ranking

- **Clustering** — embed each raw item, cluster items about the same event across sources (cosine similarity + time-window is sufficient for v1)
- **Importance ranker** scores each event by:
  - Policy / legal impact — does this change law, spending, or rights?
  - Reach — how many people materially affected?
  - Primary-source anchoring — is there an official document behind it?
  - Corroboration count — how many independent sources?
- Deliberately **downweights** outrage cycles, celebrity, unverified virals, single-outlet stories with no primary source. This is what makes the ranker resistant to being gamed.
- Top ~5 events per day advance to Layer 3.

### 3. Multi-Agent Story Building (core IP)

For each event, a five-agent crew runs sequentially. Each agent has a single narrow responsibility. Every output is grounded to source URLs — if a claim can't be tied to a citation, it's dropped, not softened.

| Agent | Job | Output |
|---|---|---|
| **Fact Extractor** | Pull verifiable claims from raw source material | `[{claim, source_urls[]}]` |
| **Primary Source Verifier** | Cross-check each claim against official docs; flag anything only reported by one wire | Verified + flagged claims |
| **Context Agent** | Add historical / policy background — *why this matters, what led here* | Context section with citations |
| **Perspective Agent** | Identify real debate sides, steel-man each. If evidence is overwhelming, say so; if it's a genuine tradeoff, present both at real weight | Debate section |
| **Editor / Hallucination Auditor** | Final pass against source material; any unsupported claim is cut | Approved story package or rejection |

Auditability is the whole point: if a broadcast looks wrong, you can trace **which layer** failed.

### 4. Article + Edition Assembly

Takes each approved story package → generates the article, then bundles the day's articles into a daily edition:
- **Article** — headline, dek, body in markdown; every claim keyed to a citation index; explicit "what's contested" section where relevant; inline source links
- **Daily edition** — front page (top ~5 stories) + section pages (Politics / Economy / Courts / Policy)
- **Newsletter export** — same edition rendered as an email-safe HTML digest

### 5. Publishing

- Digital newspaper (web) — `/edition/YYYY-MM-DD` front page + `/story/[slug]` pages + section indices
- Email newsletter — daily send to subscribers (mailing service TBD; Resend / Buttondown / Listmonk are candidates)
- Archive + search
- RSS feed

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend / agents / ingest | **Python** | Best ecosystem for ingestion, embeddings, agent orchestration |
| Agent LLM | **Claude (Anthropic SDK)** — Sonnet 4.6 for reasoning, Haiku 4.5 for extraction | Cost/quality balance, strong at citation-grounded output |
| Database | **Postgres + pgvector** | Raw items, events, stories, claims, sources; pgvector for clustering |
| Frontend (phase 2) | **Next.js (App Router)** | Digital newspaper site |
| Email delivery (phase 2) | **Resend** or **Buttondown** | Simple transactional/newsletter APIs |
| Orchestration | **cron + Postgres queue** for v1 | Simple; Prefect later if we outgrow it |
| Deploy | **Railway** or **Fly.io** (Python + Postgres) | Cheap, sane defaults |

**Budget expectation** (daily edition, ~5 stories/day):
- LLM: ~$3–10/day (agent chain across 5 stories)
- Everything else: negligible for v1
- **Total: ~$50–150/month during regular operation**

---

## Phased Milestones

### Phase 0 — Layers 1–3 working end-to-end (current focus)

Prove the core pipeline on real data, output as markdown (no site yet).
- **Layer 1**: ingest workers for PIB (primary) + a wire feed + Reddit RSS (signal), storing raw items to Postgres
- **Layer 2**: embed items, cluster into events, importance-rank
- **Layer 3**: run the 5-agent crew (Fact Extractor → Primary Verifier → Context → Perspective → Editor) on top events
- **Output**: approved story packages saved as markdown files locally

**Done when**: `grounded run-daily` command ingests today's news, clusters it, produces 3–5 fact-grounded markdown articles with inline citations, and the Editor has correctly rejected at least one hallucinated/uncited claim in test cases.

### Phase 1 — Newspaper website + newsletter

- Next.js digital newspaper site (front page, section pages, story pages)
- Daily edition assembly (Layer 4)
- Email newsletter delivery (Resend / Buttondown)
- Cron scheduler for daily autonomous operation
- Runs for 7 consecutive days unattended

### Phase 2 — Trust + reach

- Hindi track (translated articles + Hindi newsletter)
- Public "correction log" — machine-readable record of any post-publish corrections
- Twitter/X paid API for real-time breaking events (optional)
- Subscriber accounts + preference-based section subscriptions

---

## Repository Layout

```
grounded/                           # Python package (Layers 1–3)
  __init__.py
  cli.py                            # `grounded` command entry point
  config.py                         # Env / settings loading
  db.py                             # Postgres connection + query helpers
  models.py                         # Pydantic models: RawItem, Event, Story, Claim

  ingest/                           # Layer 1
    __init__.py
    base.py                         # Shared fetch + dedup + store utilities
    pib.py                          # PIB India press releases (primary)
    reuters.py                      # Reuters India (wire)
    reddit.py                       # Reddit RSS: r/india, r/indianews, etc.
    # (more sources added incrementally)

  pipeline/                         # Layer 2
    __init__.py
    embed.py                        # Generate embeddings for raw items
    clustering.py                   # Cluster items into events
    importance.py                   # Score + rank events

  agents/                           # Layer 3
    __init__.py
    base.py                         # Shared prompting + citation-check utils
    fact_extractor.py
    primary_verifier.py
    context_agent.py
    perspective_agent.py
    editor.py
    crew.py                         # Sequential agent runner for one event

db/
  schema.sql                        # raw_items, events, stories, claims, ...
  migrations/                       # Future schema changes

infra/
  docker-compose.yml                # Local dev: postgres + pgvector

apps/site/                          # Next.js digital newspaper (Phase 1)
  # deferred until Layers 1–3 are working

pyproject.toml
.env.example                        # ANTHROPIC_API_KEY, DATABASE_URL
```

---

## Verification & Trust Tests

- **End-to-end smoke test** — inject a synthetic event with known source URLs, run the full pipeline, verify a published story page appears with correct citations linked and video embedded.
- **Fact-check test** — seed a story with a claim that contradicts its source. The Editor agent must catch it before publish; assert the story is rejected.
- **Bias resistance test** — run the same event twice with different narrative-leaning source pools. Final published article must be substantially the same. Large divergence = a layer is leaking bias.
- **Source-tier test** — assert no claim from a Tier-2 (social) source appears in the final output without Tier-1 (primary/wire) corroboration.
- **Daily unattended test** — after Phase 1, run for a full week without intervention. Manually review each day. Failure rate < 1 story per 7 days is the bar.

---

## Risks & Open Questions

- **Hallucination is existential.** The Editor agent is the single most important component. Budget significant time on its evaluation harness.
- **Legal — wire service ToS.** Scraping PTI/ANI likely violates ToS. Stick to freely-licensed primary sources + Reuters/AP public wires + Google News RSS for v1; budget for licensed feeds later.
- **Copyright — b-roll footage.** Need a CC-0 / licensed pool. Can't scrape arbitrary YouTube clips. Consider Pexels/Unsplash video + auto-generated stock cards for v1.
- **Social media capture risk.** Even as topic radar, social signals can be gamed by coordinated inauthentic behavior. Importance ranker must weight primary-source anchoring heavily.
- **Cost curve.** 5 stories/day is manageable. Hourly bulletins or multi-language roughly scales linearly. Model this before phase 2.
- **Editorial responsibility.** An autonomous news publisher is legally still a publisher. Consider incorporating and having an "editor of record" (someone legally responsible for site content) before serious traffic — not a blocker for MVP.

---

## Status

Pre-code. Architecture and phase plan agreed. Deciding between:
1. **Phase 0 first** — get one manually-picked story through the full pipeline for a fast "wow it works" moment.
2. **Scaffold first** — set up the repo, database, and Next.js site so the pipeline has a home to grow into.
