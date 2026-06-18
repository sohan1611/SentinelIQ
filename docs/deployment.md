# Deployment — Render (backend + Postgres) + Vercel (frontend)

Deployment shape is fixed by ADR-012: Vercel (frontend, native Next.js build) + Render
(backend + managed Postgres), **$0/month**, **single instance** (ADR-008). This doc is
the step-by-step playbook for the one-time setup. Per ADR-012, creating the Render/Vercel
projects, connecting the GitHub repo, and entering secrets are **owner-in-the-loop
actions** — Claude Code does not perform these.

## Live deployment (Phase 20, 2026-06-18)

| Service | URL |
|---|---|
| Backend (Render) | `https://sentineliq-y27m.onrender.com` |
| Frontend (Vercel) | `https://sentineliq-sohanmandal1611-7709s-projects.vercel.app` |

Health check verified: `{"status":"ok","database":"ok"}`.

**CORS requirement:** Render env var `FRONTEND_URL` must be set to the exact Vercel URL
above (no trailing slash). Update it whenever the Vercel domain changes.

Note: `sentineliq.vercel.app` is taken by another user. The project was renamed from
"frontend" to "sentineliq" — the stable URL above is the cleanest available under
the `.vercel.app` subdomain namespace without a custom domain.

## Local dry-run (already verified, Phase 10 Step 5)

Before following the steps below, the following were verified locally and require no
external accounts:

- `alembic upgrade head --sql` (offline mode, no DB connection) generates the full DDL for
  the `0001 -> 0002 -> 0003 (head)` chain — all 8 baseline tables (`users`, `companies`,
  `financial_data`, `analysis_results`, `red_flags`, `reports`, `watchlist`,
  `narrative_snapshots`), then `analysis_runs` (migration `0002`), then
  `ALTER TABLE analysis_runs ADD COLUMN counted ...` (migration `0003`). The chain is
  linear and the generated SQL is well-formed standard Postgres DDL. A live run against an
  actual Postgres instance was not possible in this sandbox (no Docker daemon, no native
  Postgres install available) — the start command in step 2 below runs
  `alembic upgrade head` for real on first deploy, and the post-deploy checklist (step 4)
  confirms it succeeded via `/health`.
- `frontend`: `npm run build` succeeds — production build, type checking, and static page
  generation all pass for all 16 routes.
- `backend/Dockerfile` already exists and matches Render's expected shape (`pip install -r
  requirements.txt`, `CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`) —
  Render can build the backend from this directly, or via its native Python runtime using
  the build/start commands below.
- `backend/app/database.py` has no `create_all` — schema is Alembic-only (ADR-012's
  "migrations gate deploys" requirement).
- `/health` (Phase 10 Step 2) is unauthenticated and checks DB connectivity — use it as
  Render's health check path.

## 1. Render — managed Postgres

1. New "PostgreSQL" instance, free tier (1GB).
2. Copy the connection string Render provides (currently labeled "Internal Database URL"
   in Render's dashboard). It will start with `postgresql://` or `postgres://`.
3. **Rewrite the scheme** before using it as `DATABASE_URL` — regardless of what Render
   calls the field or how it formats the URL, this app's `asyncpg` driver requires the
   scheme to be `postgresql+asyncpg://`:
   ```
   postgresql+asyncpg://USER:PASSWORD@HOST/DBNAME
   ```

## 2. Render — backend web service

- Root directory: `backend`
- Runtime: Python 3 (Dockerfile or native — either works; Dockerfile is already present)
- Build command: `pip install -r requirements.txt`
- Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  — running the migration before `uvicorn` starts ensures the schema is current on every
  deploy (ADR-012 "migrations gate deploys"); safe to repeat (Alembic no-ops if already at
  `head`).
- Health check path: `/health`
- Environment variables:

  | Key | Value |
  |---|---|
  | `DATABASE_URL` | the rewritten `postgresql+asyncpg://...` URL from step 1 |
  | `GEMINI_API_KEY` | your Gemini API key |
  | `SECRET_KEY` | a random string, 32+ chars (e.g. `openssl rand -hex 32`) |
  | `FRONTEND_URL` | the Vercel deployment URL, e.g. `https://sentineliq.vercel.app` (must match exactly — used as the sole CORS `allow_origins` entry) |
  | `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` (optional — this is the default) |

## 3. Vercel — frontend

1. New project, root directory `frontend`. Framework preset (Next.js) is auto-detected;
   default build command (`next build`) is unchanged.
2. Environment variable:

  | Key | Value |
  |---|---|
  | `NEXT_PUBLIC_API_URL` | the Render backend URL, e.g. `https://sentineliq-api.onrender.com` (no trailing slash — `lib/api/client.ts` appends `/api/v1`) |

## 4. Post-deploy verification checklist

- `curl https://<render-url>/health` -> `{"status": "ok", "database": "ok"}`
- Register a user via the deployed frontend, log in, run an analysis for a real ticker
  end-to-end, confirm the report renders.
- Confirm no CORS errors in the browser console (`FRONTEND_URL` must match the Vercel
  origin exactly, including `https://` and no trailing slash).

## Free-tier caveats (already mitigated, noted for ops awareness)

- Render free web services spin down after ~15 min idle; the next request triggers a cold
  start. The Step 3 reaper (`backend/app/tasks/reaper.py`) marks any analysis stuck in
  `running:*` for >10 minutes as `status = "error"` so a spin-down mid-analysis surfaces
  as "Analysis was interrupted. Please retry." instead of hanging forever.
- Render free Postgres instances expire after 90 days unless upgraded — out of scope for
  this phase, note for a future ops pass.
