# Automated daily publishing (GitHub Actions)

The **Daily publish** workflow (`.github/workflows/daily-publish.yml`) runs the full
backend pipeline and pushes the resulting newspaper to the frontend repo.

## What it does

1. Starts Postgres (pgvector) in CI
2. Runs `python publish.py --no-site` (wipe → ingest → embed → cluster → rank → scrape → crew → dedup → coherence → images → edition)
3. Copies `output/edition-YYYY-MM-DD.md` and `output/images/YYYY-MM-DD/` into `grounded-page`
4. Commits and pushes to `Grounded-india/grounded-page` on `main`
5. Vercel (if connected to `grounded-page`) redeploys the live site automatically

## Schedule

- **09:00 IST every day** (`30 3 * * *` UTC)
- **Manual run:** GitHub → Actions → *Daily publish* → *Run workflow*

## Required secrets (GROUNDED repo)

Add these under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `VOYAGE_API_KEY` | Layer 2 embeddings |
| `NVIDIA_API_KEY` | Nemotron (fact/context/debate/reporter) |
| `GEMINI_API_KEY` | Verifier, editor, coherence, image verify |
| `GROUNDPAGE_DEPLOY_TOKEN` | PAT with **contents:write** on `Grounded-india/grounded-page` |

### Creating `GROUNDPAGE_DEPLOY_TOKEN`

1. GitHub → Settings → Developer settings → Personal access tokens (fine-grained)
2. Repository access: **Only** `Grounded-india/grounded-page`
3. Permissions: **Contents → Read and write**
4. Copy the token into GROUNDED repo secret `GROUNDPAGE_DEPLOY_TOKEN`

## Local equivalent

```bash
python publish.py --no-site
python scripts/push_to_frontend.py --site ../grounded-page --source-dir output
```

Or use `python publish.py` without `--no-site` to copy locally (no git push).

## Runtime

A full publish can take **1–3 hours** in CI (LLM calls for ~20 stories). The job
timeout is set to 360 minutes.
