# Architecture

## Component map

```
Browser
  └─ Next.js 14 (Vercel)
       └─ REST API calls → FastAPI (Render free tier)
                              ├─ PostgreSQL (Render free tier, 1 GB)
                              │    └─ Alembic migrations (3 files, 9 tables)
                              ├─ yfinance (Yahoo Finance) — financial statements
                              ├─ feedparser (Google News RSS etc.) — news headlines
                              └─ Google Gemini 2.5 Flash — governance + narrative scoring + report
```

## Request flow for a full analysis

1. `POST /api/v1/analysis/run` — auth check, free-tier quota check, cache check
2. If no cached result: create `AnalysisResult(status="pending")`, schedule background task
3. Background task (`analysis_worker.py`) runs 7 stages in sequence:
   - **Stage 1 — financials:** fetch yfinance data, persist `FinancialData` rows
   - **Stage 2 — forensics:** run 4 forensic modules, persist `RedFlag` rows
   - **Stage 3 — governance:** fetch news text, call Gemini, persist governance events as `RedFlag` rows
   - **Stage 4 — narrative:** fetch 5 news headlines, call Gemini per headline, persist `NarrativeSnapshot` rows
   - **Stage 5 — news sentiment:** keyword sentiment over RSS feeds
   - **Stage 6 — score persist:** renormalized weighted average → `AnalysisResult` scores + `module_details`
   - **Stage 7 — report:** call Gemini, persist `Report`
4. `GET /api/v1/analysis/{id}/status` polled by frontend every 3s

Each stage has its own `try/except`; a failed stage falls back to `None` (excluded from the weighted average) or `50.0` (neutral, for narrative/news). The pipeline always reaches `status="complete"` — it never aborts.

## Key architectural decisions (ADRs)

| ADR | Decision |
|---|---|
| ADR-004 | Score-bearing AI calls run at `temperature=0` with pinned `model_id`; prompt + raw response persisted in `module_details.{governance,narrative}.provenance` |
| ADR-005/006 | Narrative score excluded from the weight vector until a real transcript pipeline exists; the 5 remaining modules are renormalized to sum to 1.0 |
| ADR-007 | Every user-triggered analysis logs an `AnalysisRun` row for the audit trail, regardless of cache hit |
| ADR-008 | No Redis, no multi-instance job queue — single-process in-memory cache (keeps hosting at $0) |
| ADR-010 | Pipeline never aborts on a single stage failure; `status="failed"` is retired |
| ADR-012 | `/health` is unauthenticated so Render can probe DB connectivity on free-tier restart |
| ADR-013 | `AnalysisRun.counted=false` on cache-hit re-opens; only fresh computations consume the 5/month free-tier quota |

Full ADR text: `ARCHITECTURAL_DECISIONS.md`.

## Database schema (9 tables)

`users`, `companies`, `financial_data`, `analysis_results`, `red_flags`, `reports`, `watchlist`, `narrative_snapshots`, `analysis_runs`.

Schema is authoritative in `backend/alembic/versions/` (3 migrations). `docker-compose.yml` provides a local PostgreSQL instance for development; run `alembic upgrade head` to initialize it.

## Scoring formula

```
integrity_score = sum(BASE_WEIGHTS[k] * scores[k] for available k)
                / sum(BASE_WEIGHTS[k] for available k)

BASE_WEIGHTS = { financial: 0.3333, cashflow: 0.2222,
                 governance: 0.1667, earnings: 0.1667, news: 0.1111 }
```

A module with `None` (stage failure) is excluded from both numerator and denominator — the remaining modules are renormalized automatically. See `docs/scoring-methodology.md` for the per-module algorithms.
