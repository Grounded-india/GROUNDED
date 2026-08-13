# Automated daily publishing (GitHub Actions)

The **Daily publish** workflow (`.github/workflows/daily-publish.yml`) runs the full
backend pipeline and pushes the resulting newspaper to the frontend repo.

## What it does

Two jobs, so translation cannot eat the English paper's 6-hour GitHub cap:

1. **`publish`** — Postgres, then `python publish.py --no-site --no-translate`
   (wipe → ingest → embed → cluster → rank → scrape → crew → dedup →
   coherence → images → English edition). Pushes `edition-YYYY-MM-DD.md` +
   images to `grounded-page` and uploads an artifact.
2. **`translate`** — starts only after `publish` succeeds. Downloads the
   artifact, runs `python -m grounded.agents translate`, pushes `hi`/`kn`/`mr`/`te`
   files if they land. `continue-on-error: true`: a Gemini failure leaves
   yesterday's English edition live.

Local `python publish.py` still translates by default. Skip with `--no-translate`.

## Schedule

- **12:00 IST every day** (`30 6 * * *` UTC)
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

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. **Repository access:** Only **`Grounded-india/grounded-page`**
3. **Permissions:** **Contents → Read and write** (required — Actions/Workflows alone will **not** work)
4. Generate, copy once, add as secret `GROUNDPAGE_DEPLOY_TOKEN` on the **GROUNDED** repo

If push fails with `Permission denied to <your-username>`, the token is missing **Contents** write or the secret name is wrong.

## Local equivalent

```bash
python publish.py --no-site --no-translate
python scripts/push_to_frontend.py --site ../grounded-page --source-dir output
# optional, after the English file exists:
python -m grounded.agents translate --date YYYY-MM-DD --site ../grounded-page
```

Or use `python publish.py` without `--no-site` to copy locally (includes
translation unless you pass `--no-translate`).

## Runtime

English crew can take **4–6 hours** in CI (Nemotron calls for ~20 stories plus
top-up). That job's timeout is 360 minutes — GitHub-hosted max. Translation
gets its own 180-minute job afterwards.
