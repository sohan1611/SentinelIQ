# SentinelIQ — Project Memory for Claude Code

This file gives Claude Code complete context about the SentinelIQ project.
Read this entire file before taking any action. Do not ask for context
that is already here.

---

## Constitution & Governance Documents (read before every phase)

SentinelIQ is governed by **four** documents. Before starting any new development
phase, read all four before making any architectural or UI change:

1. **CLAUDE.md** (this file) — operational constitution: rules, formulas, conventions, design system.
2. **PROJECT_STATUS_FOR_OPUS.md** — current-state ground truth: what exists, what's broken, what's mock.
3. **OPUS_ARCHITECTURAL_REVIEW.md** — the phased roadmap and ordered execution plan.
4. **ARCHITECTURAL_DECISIONS.md** — the CTO's ruling book: the *why*, with binding decisions and rejected alternatives.

Working model: **Opus is Chief Architect** (reviews, rules, prioritizes); **Sonnet is Lead
Implementation Engineer** (implements, tests, deploys). On **"Start new phase,"** execute
ONLY the next authorized phase, complete it fully, write a completion report, and STOP.

Follow these documents unless explicitly overruled by the owner. Decisions in
`ARCHITECTURAL_DECISIONS.md` are binding for the subjects they cover; this file (`CLAUDE.md`)
is authoritative for concrete rules/formulas/conventions; the owner overrides both.
Amendments are explicit and dated — never silent behavioral changes inside a feature commit.

> **Phase 3 amendment (2026-06-14):** ADR-005/006's scoring changes have landed — weight
> renormalization replaces neutral-50 fill, and `narrative` is temporarily excluded from
> the weight vector pending a real transcript pipeline. See "Fraud Score Weights" under
> Forensics Engine — Algorithms for the current rules, and Error Handling rule 2a for how
> this interacts with the existing per-module 50.0 fallback.

> **Phase 9 amendment (2026-06-15):** Governance scoring no longer treats empty/thin news
> coverage as a clean "100" — `GovernanceScorer.analyze` returns `50.0` with a
> `low_confidence` marker when `news_text` is below `MIN_NEWS_TEXT_LENGTH` (40 characters),
> and the Gemini call is skipped entirely. See "Analysis Pipeline — 7 Stages" Stage 3 and
> Error Handling rule 2b for the full rule and its threshold.

> **Phase 10 amendment (2026-06-16):** Per ADR-013 (Ruling A), `AnalysisRun` gained a
> `counted: bool` column (`server_default=true`, Alembic `0003`). `POST /analysis/run`
> sets `counted=False` on a cache-hit re-open (`is_cache_hit = analysis is not None`,
> captured before the cache-miss branch reassigns `analysis`) and `counted=True` on a
> fresh computation. `_free_tier_usage_query` now adds `AnalysisRun.counted.is_(True)` —
> only fresh computations consume the 5/month free-tier quota; cache-hit re-opens are
> still logged as `AnalysisRun` rows for the audit trail (ADR-007) but don't decrement it.
> The `FREE_TIER_MONTHLY_LIMIT = 5` value itself is unchanged.
>
> **Step 3 — stuck-analysis reaper + terminal `"error"` status.** `backend/app/tasks/reaper.py`
> runs an in-process `asyncio` loop (`reaper_loop`, started via `asyncio.create_task` in
> `main.py`'s `lifespan`, cancelled on shutdown) that calls `reap_stuck_analyses` immediately
> on startup and every `REAPER_INTERVAL_SECONDS` (120s) thereafter. It marks any
> `AnalysisResult` with `status LIKE 'running:%'` and `run_at` older than
> `STUCK_ANALYSIS_THRESHOLD_MINUTES` (10) as `status = "error"` — covering an in-process
> background task killed mid-analysis by a Render free-tier spin-down/restart (ADR-012).
> `"error"` is a **new terminal status** — it does NOT revive the retired `"failed"`
> status (ADR-010 / Phase 3's status retirement is unchanged; the dead `"failed"` branches
> in `get_analysis_status` and the frontend are left as-is, Phase 12 cleanup scope).
> `get_analysis_status` maps `status == "error"` → `stage = "Analysis interrupted"`.
> `frontend/lib/hooks/useAnalysis.ts` treats `"error"` as terminal alongside `"complete"`/
> `"failed"`, stops polling, and sets `error = "Analysis was interrupted. Please retry."` —
> the existing `analysisError ||` gates in `layout.tsx`'s status bar and `page.tsx`'s
> empty state render this with no further changes.
>
> **Step 4 — structured JSON logging + correlation ID.** `backend/app/logging_config.py`
> adds `JsonFormatter` (renders every log record as one JSON line: `timestamp`, `level`,
> `logger`, `message`, plus any `extra=` fields) and `CorrelationLoggerAdapter` (merges
> per-call `extra` with the adapter's bound context, unlike stdlib `LoggerAdapter` which
> overwrites it). `main.py` calls `configure_logging()` at import time, so every module's
> logger inherits the JSON formatter via root-logger propagation. In
> `run_full_analysis`, `log = CorrelationLoggerAdapter(logger, {"correlation_id":
> str(analysis_id), "ticker": company.ticker})` is built once and stored on
> `StageContext.log`; the orchestrator emits `log.info("stage started", extra={"stage":
> stage.name})` before each of the 7 stages and `log.info("analysis complete")` at the
> end, and every `_stage_*` failure log (`ctx.log.error(...)`) carries the same
> `correlation_id`/`ticker` plus its own `stage`. This lets a stuck analysis (Step 3's
> reaper target) be traced to its last-logged stage across Render's log stream.

> **Phase 11 amendment (2026-06-16):** Step 1 of the Analyst Workflow Layer adds
> `GET /analysis/company/{ticker}/history` (`backend/app/api/v1/routes/analysis.py`),
> returning up to `ANALYSIS_HISTORY_LIMIT` (24) `status == "complete"` `AnalysisResult`
> rows for a company as lightweight `AnalysisHistoryItem` objects (`id`, `run_at`, and the
> 7 score fields — `integrity_score` plus the 6 components — with `module_details` and
> `status` omitted). The DB query is newest-first (so the `LIMIT` keeps the most recent
> runs) and reversed before returning, so the response is chronological (oldest first) —
> ready to feed an x-axis directly. 404 if the ticker/company doesn't exist (matching
> `GET /company/{ticker}` and `GET /analysis/company/{ticker}`); `[]` (200) if the company
> exists but has no completed analyses yet — "history" is naturally zero-or-more, unlike
> the "latest analysis" endpoints which 404 on zero rows.
>
> Frontend: `IntegrityScoreTrendChart` (`frontend/components/charts/
> IntegrityScoreTrendChart.tsx`) is a new chart built on `ChartFrame` (same pattern as
> `DebtTrendChart`/`NarrativeTrendChart` — `baseChartOptions` + design tokens from
> `lib/theme/tokens.ts`), fed by the new `useAnalysisHistory` hook
> (`frontend/lib/hooks/useAnalysisHistory.ts`) and `getAnalysisHistory` API client fn
> (`frontend/lib/api/analysis.ts`). Unlike the percent-based forensic charts, its y-axis is
> fixed to `[0, 100]` (`options.scales.y.min/max`) since Integrity Score is always on that
> scale (see "Risk classification" bands above) — a fixed axis lets an analyst compare the
> line's position against those bands directly. It is wired into the Company Overview
> page's right column, between the module-score grid and the red-flag sections. Empty
> state (`history.length < 2` — a single point can't show a trend): "Run more analyses
> over time to see how this company's Integrity Score has changed." A loading skeleton
> (matching CLAUDE.md's "skeleton loaders only" rule) renders while the history fetch is
> in flight, so the empty state never flashes before real data arrives.

> **Phase 11 Step 2 amendment (2026-06-16):** "Evidence drill-down" (OPUS Phase 11 success
> criterion: "every flag traces to a source"), plus a schema bug fix it depends on.
>
> **Schema fix.** `backend/app/schemas/analysis.py`'s `NarrativeModuleDetails` and
> `GovernanceModuleDetails` were missing `tone_shifts: List[Dict[str, Any]] = []` and
> `low_confidence: bool = False`. Pydantic v2's default `extra="ignore"` silently dropped
> both fields from every `AnalysisResultResponse`, even though `analysis_worker.py`'s
> `_stage_score_persist` always writes `module_details.narrative.tone_shifts` and
> `module_details.governance.low_confidence`, and the frontend's Phase 9 UI
> (`governance/page.tsx`'s low-confidence disclaimer, `narrative/page.tsx`'s tone-shift
> contradiction alerts) was already built to consume them — both were silently dead.
> Adding the two fields is purely additive; `frontend/types/analysis.ts` already declared
> them.
>
> **Evidence drill-down.** `frontend/lib/utils/redFlag.ts` adds
> `getFlagEvidence(flag, moduleDetails) -> EvidenceRow[]`, mapping a `RedFlag`'s
> `flag_type` + `period` back to the `module_details` row(s) that produced it:
> `"revenue"` → `revenue.divergences`/`recv_ratios`; `"cash_flow"` → BOTH
> `cashflow.accrual_ratios` AND `debt.debt_metrics` (debt_analysis.py also emits
> `flag_type="cash_flow"`, so both series are checked for a matching `period`);
> `"earnings"` → `earnings.margins`/`net_incomes`; `"governance"` → `governance.provenance`
> (rendered as `AI Model: gemini-2.0-flash` / `Source: Recent news coverage`, guarded on
> `provenance?.model_id` — a governance flag only exists when that call succeeded).
> `frontend/components/modules/RedFlagItem.tsx` gained an optional `evidence?:
> EvidenceRow[]` prop: when non-empty, a text "Evidence"/"Hide" toggle (decision #9 — text,
> not an icon) expands a label/value panel below the flag row.
> `frontend/app/(app)/company/[ticker]/page.tsx`'s FLAG DETAILS list passes
> `evidence={getFlagEvidence(flag, analysis.module_details)}` to each `RedFlagItem`. Flags
> with no matching `module_details` row (older analyses, or pre-Phase-3 analyses with no
> `module_details` at all) render `evidence=[]` — no toggle, identical to the prior UI.

> **Phase 11 Step 4 amendment (2026-06-17):** ⌘K command palette + frontend query cache
> (cross-tab navigation reuses one fetch).
>
> **Query cache.** `frontend/contexts/CompanyContext.tsx` is a new React context that
> holds `{company, analysis, isLoading, error, refetch, analysisStatus, isRunning,
> analysisError, startAnalysis}`. `company/[ticker]/layout.tsx` calls `useCompanyData`
> and `useAnalysis` exactly once (as it did before) and wraps `<PageTransition>` with
> `<CompanyContext.Provider value={{...}}>`. All 5 child tabs (Overview `page.tsx`,
> `financials/`, `governance/`, `narrative/`, `report/`) now call `useCompanyContext()`
> instead of their own `useCompanyData(ticker)` calls — eliminating 5 duplicate API
> fetches and 1 duplicate polling instance. `report/page.tsx`'s `useReport(ticker,
> !!analysis)` call is unaffected (different endpoint, kept separate).
>
> **⌘K command palette.** `frontend/components/layout/CommandPalette.tsx` — triggered by
> `Cmd+K`/`Ctrl+K` global keydown listener in `frontend/app/(app)/layout.tsx`; shows
> debounced search via `searchCompanies()` (220ms debounce with `useDebounce`); keyboard
> navigation (↑/↓ arrow keys, Enter to navigate, Esc to close); static nav items
> (Dashboard, Search, Watchlist, Settings) when query is empty. Design: FFFFFF card,
> 1px E3DFD8 border, 8px radius, `translateY(-8px)→0` + opacity at 150ms ease-out —
> consistent with CLAUDE.md's search dropdown animation spec. Tickers rendered in IBM
> Plex Mono. No icons (design decision #4/#9 equivalents).

> **Phase 11 Step 3 amendment (2026-06-17):** M-1 (deep provenance) and M-5 (governance
> schema validation).
>
> **M-1 — Deep provenance.** `generate_content_with_provenance` in
> `backend/app/core/ai/gemini_client.py` previously set `raw_response = text` (the
> extracted `.text` string), losing `finish_reason`, safety ratings, and token counts.
> It now calls `model.generate_content(...)` directly via `_call_with_backoff`, captures
> the full response object, and passes it to `_extract_provenance_fields(response)` —
> a new defensive helper that returns `{"finish_reason", "safety_ratings",
> "prompt_token_count", "candidates_token_count"}` from the response or `{}` on any
> attribute error. `generate_json_with_provenance` is simplified to delegate through
> `generate_content_with_provenance` (was an independent path; now shares the same
> response-capture logic). `GenerationResult.raw_response` type changed from
> `str | None` to `dict | None`; `frontend/types/analysis.ts`'s
> `GovernanceProvenance.raw_response` updated to match (`GeminiRawResponse | null` —
> a new named interface with the four fields above). Nothing in the frontend reads
> `raw_response` beyond type checking, so no UI change.
>
> **M-5 — Governance JSON schema validation.** `GovernanceEvent` (Pydantic `BaseModel`)
> is now the validated gate for every governance event before scoring:
> `severity` is validated against `{"moderate","high","severe"}` (unknown values
> normalize to `"moderate"` with a warning — parseable-but-malformed responses still
> produce a deduction rather than a falsely clean score); `description` defaults to
> `"Governance event detected"` if empty. Non-dict events in the `events` list are
> skipped with a `logger.warning`. The scoring deduction table moves from inline
> `if/elif` branches to `_SEVERITY_DEDUCTIONS = {"moderate": 15, "high": 25,
> "severe": 35}`.

> **Phase 12 Step 5 amendment (2026-06-17):** `google-generativeai` → `google-genai` SDK
> migration and `gemini-2.0-flash` model upgrade.
>
> **SDK.** `backend/requirements.txt` swaps `google-generativeai==0.8.6` for
> `google-genai>=1.0.0` (the new Google unified SDK). `backend/app/core/ai/gemini_client.py`
> import changes: `import google.generativeai as genai` / `genai.configure(api_key=...)` /
> `genai.GenerativeModel(...)` → `from google import genai` / `from google.genai import types` /
> `client = genai.Client(api_key=...)`. All call sites use `client.aio.models.generate_content(...)`
> (native async — eliminates the `asyncio.to_thread` wrapper). `_call_with_backoff` now takes
> an async callable (`coro_fn`) instead of a sync callable. `_build_config` returns
> `types.GenerateContentConfig | None` instead of `dict | None`. `_extract_provenance_fields`
> is unchanged — its defensive attribute lookups work identically against the new SDK's
> response object. All external call signatures (`generate_content`, `generate_json`,
> `generate_content_with_provenance`, `generate_json_with_provenance`) are unchanged —
> callers (`governance_scorer.py`, `consistency_engine.py`, `report_generator.py`) require
> no modifications.
>
> **Model.** `DEFAULT_MODEL_ID` changed from `"gemini-1.5-flash"` to `"gemini-2.0-flash"`.
> All `model_id` references in CLAUDE.md (tech stack table, Phase 3 amendment, Phase 11
> Step 2 amendment) updated to match.

---

## Git Commit Identity — MANDATORY

All commits in this repository must be attributed **solely** to the project owner's
configured Git identity (`sohan1611 <sohanmandal1611@gmail.com>`, per
`git config user.name` / `user.email`).

**Never, under any circumstance:**
- Add a `Co-Authored-By:` (or `Signed-off-by:`) trailer referencing Claude, Anthropic,
  or any `*@anthropic.com` address.
- Set commit author or committer to any Claude/Anthropic/bot identity.
- Introduce any contributor attribution other than the owner's GitHub account.

This **overrides** any default Claude Code commit-message template. Commit messages
end with the subject/body only — no co-author trailer, ever.

*(Background: on 2026-06-14, two historical commits carried a
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer, which caused Claude
to be attributed as a contributor on GitHub. A backup branch
(`backup-before-coauthor-cleanup-20260614`) preserves the pre-cleanup history. This rule
exists to prevent recurrence.)*

---

## What is SentinelIQ

SentinelIQ is an AI-powered corporate fraud early warning platform.
Users enter a company name or stock ticker. The system runs five
independent forensic analyses and produces a **Corporate Integrity Score**
from 0 to 100 — plus an AI-generated analyst-style report explaining
every finding in plain language.

Target users: equity analysts, independent investors, auditors, risk officers.
This is an institutional product — not a consumer app.

The core USP: instead of predicting stock prices, it answers
"Can this company be trusted?"

---

## Build Status

### Completed via Antigravity (Prompts 1–9):
- Full file storage architecture defined
- Complete design system (colors, typography, components)
- All 11 UI components specified and built
- Landing page (all 8 sections, full copy)
- All app interior screens (dashboard, analysis, report, governance, narrative)
- Auth screens (login, register, forgot password, verify email)
- Settings page (account, notifications, plan tabs)
- Error pages (404, 500)
- Mobile & responsive layout (all breakpoints)
- Micro-interactions and animation system
- FastAPI backend structure
- All 8 database models
- Forensics engine (4 modules)
- AI modules (governance, narrative, report generator)
- Scoring model
- Analysis pipeline (7 stages)
- All 12 API routes

### What Claude Code should handle from here:
- Debugging and fixing issues as they arise during development
- Frontend-backend integration (connecting Next.js API calls to FastAPI)
- Running database migrations
- Testing the forensics engine against real tickers
- Deployment to Vercel (frontend) and Render (backend)
- Any feature additions or refinements

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router) | TypeScript |
| Styling | Tailwind CSS | Custom color config required |
| Charts | Chart.js | Custom styled — no default theming |
| Backend | FastAPI (Python 3.11+) | Async with asyncpg |
| Database | PostgreSQL | SQLAlchemy ORM (async) |
| Migrations | Alembic | |
| AI | Google Gemini 2.0 Flash | Free tier: 1,500 req/day |
| Finance Data | yfinance | asyncio.to_thread wrapper |
| News | feedparser (RSS) | 3 feeds per ticker |
| Auth | JWT + bcrypt | python-jose + passlib |
| Caching | In-memory Python dict | No Redis — stays free |
| Frontend host | Vercel | |
| Backend host | Render | Free tier |
| Estimated cost | $0/month | |

---

## Project File Structure

```
sentineliq/
├── CLAUDE.md                        ← this file
├── .env.example
├── docker-compose.yml
├── frontend/
│   ├── app/
│   │   ├── (marketing)/             public pages (no auth)
│   │   │   └── page.tsx             landing page
│   │   ├── (auth)/                  login, register, forgot-password, verify-email
│   │   └── (app)/                   protected pages (requires auth)
│   │       ├── layout.tsx           app shell — sidebar + content
│   │       ├── dashboard/page.tsx
│   │       ├── search/page.tsx
│   │       ├── company/[ticker]/
│   │       │   ├── page.tsx         overview tab
│   │       │   ├── financials/
│   │       │   ├── governance/
│   │       │   ├── narrative/
│   │       │   └── report/
│   │       ├── watchlist/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── ui/                      Button, Badge, Card, Input, Modal, Skeleton, Tooltip
│   │   ├── charts/                  IntegrityGauge, CashFlowChart, RevenueQualityChart,
│   │   │                            DebtTrendChart, RedFlagTimeline, RiskRadar
│   │   ├── modules/                 ScoreCard, FraudScoreBanner, RedFlagItem,
│   │   │                            NarrativeComparison, GovernanceChecklist,
│   │   │                            ReportSection, RecommendationBox
│   │   ├── layout/                  Navbar, AppShell, Sidebar, SearchBar, Footer
│   │   └── shared/                  CompanyCard, LoadingState, ErrorBoundary
│   ├── lib/
│   │   ├── api/                     client.ts, company.ts, analysis.ts, watchlist.ts
│   │   ├── hooks/                   useCompanyData, useAnalysis, useWatchlist, useDebounce,
│   │   │                            useStaggeredReveal
│   │   └── utils/                   scoreColor.ts, riskLabel.ts, formatDate.ts
│   ├── types/
│   └── public/
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── config.py                Pydantic Settings
    │   ├── database.py              async SQLAlchemy
    │   ├── api/v1/routes/           auth.py, company.py, analysis.py, report.py, watchlist.py
    │   ├── core/
    │   │   ├── forensics/           base.py, revenue_quality.py, cashflow_integrity.py,
    │   │   │                        earnings_quality.py, debt_analysis.py, forensics_runner.py
    │   │   ├── governance/          governance_scorer.py
    │   │   ├── narrative/           consistency_engine.py
    │   │   ├── scoring/             fraud_scorer.py, risk_classifier.py
    │   │   └── ai/                  gemini_client.py, report_generator.py,
    │   │                            prompts/ (report_prompt.txt, governance_prompt.txt,
    │   │                                     narrative_prompt.txt)
    │   ├── services/                yahoo_finance.py, news_aggregator.py, cache.py
    │   ├── models/                  user.py, company.py, financial_data.py,
    │   │                            analysis_result.py, red_flag.py, report.py,
    │   │                            watchlist.py, narrative_snapshot.py
    │   ├── schemas/                 matching Pydantic schemas for each model
    │   └── tasks/                   analysis_worker.py
    ├── alembic/
    ├── tests/
    └── requirements.txt
```

---

## Environment Variables

### Backend (backend/.env)
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sentineliq
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_minimum_32_chars
FRONTEND_URL=http://localhost:3000
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Frontend (frontend/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Development Commands

### Start everything locally:
```bash
# Terminal 1 — PostgreSQL (if not running as service)
# Mac: brew services start postgresql@15
# Windows: Start from Services panel

# Terminal 2 — Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm run dev
```

### Database:
```bash
cd backend
alembic upgrade head          # run all migrations
alembic revision --autogenerate -m "description"   # create new migration
```

### Install dependencies:
```bash
# Backend
cd backend && pip install -r requirements.txt --break-system-packages

# Frontend
cd frontend && npm install
```

---

## Design System — Non-Negotiable Rules

Claude Code must enforce these in all frontend work.

### Colors (exact hex — never approximate):
```
Canvas background:  #F6F4EF   warm off-white
Card surface:       #FFFFFF
Border:             #E3DFD8   warm light gray
Brand navy:         #1C3558
Primary text:       #1A1A18
Secondary text:     #7A786F
Muted text:         #B0ADA7
Skeleton:           #E8E5DF

Risk colors (solid, never gradient):
  Severe:    #6E1010
  High:      #B03028
  Moderate:  #C47A14
  Low:       #1C3558  (navy)
  Strong:    #1A6B3C

Risk tints (badge backgrounds):
  Severe:    #F5DADA
  High:      #FAE8E8
  Moderate:  #FDF2DC
  Low:       #E4F2EB
  Strong:    #D6EDE0
```

### Typography:
```
Headings (hero only): Playfair Display, weight 400
UI headings:          Inter, weight 500–600
Body:                 Inter, weight 400, 14–16px
ALL numbers/scores/tickers: IBM Plex Mono — no exceptions
Labels (all-caps):    Inter, 10–11px, uppercase, letter-spacing 0.07em
```

### Component rules:
- Card: `#FFFFFF bg, 1px #E3DFD8 border, 8px radius, NO box-shadow`
- Buttons: `6px radius, no gradients, no rounded-pill`
- Tables: `no zebra striping, hairline dividers only`
- Nav: `text labels only — no icons at any breakpoint`
- Risk gauge: `solid arc color per risk level — NOT gradient`
- Active tab: `2px #1C3558 underline — NOT pill or background fill`
- Section labels: `10px, uppercase, #7A786F, letter-spaced`

### Absolute prohibitions in the frontend:
- No gradient backgrounds
- No box-shadows on cards
- No AI illustrations, robot icons, neural network graphics
- No dark mode
- No spring/bounce animations
- No scroll-triggered animations
- No typewriter effects
- No hover card-lift (translateY on hover)
- No full-width colored hero banners

---

## Animation System

### CSS Variables (must be in globals.css):
```css
--duration-instant:   80ms;
--duration-fast:      150ms;
--duration-base:      220ms;
--duration-slow:      400ms;
--duration-deliberate:700ms;

--ease-out:  cubic-bezier(0.0, 0.0, 0.2, 1.0);
--ease-in:   cubic-bezier(0.4, 0.0, 1.0, 1.0);
--ease-base: cubic-bezier(0.4, 0.0, 0.2, 1.0);
```

### Key animations:
- **Integrity Gauge**: 700ms arc draw (stroke-dashoffset) + synced integer counter
- **Skeleton → content**: 40ms stagger per element, ease-out fade
- **Route transitions**: opacity only — 100ms out, 200ms in — sidebar stays static
- **Search dropdown**: translateY(-8px)→0 + opacity on appear (150ms ease-out)
- **Toasts**: translateX enter, translateY exit, 3000ms auto-dismiss, max 3 stacked
- **Score change flash**: #FAE8E8 (worse) / #E4F2EB (better), 400ms, one-shot

---

## Forensics Engine — Algorithms

### Module A: Revenue Quality (weight: 30%)
```
divergence = revenue_growth_rate - ocf_growth_rate
receivables_ratio = accounts_receivable / revenue

Scoring (start at 100):
  divergence > 0.15 per period:  -15
  divergence > 0.30 per period:  -25
  recv_ratio increase > 0.10/yr: -10

Red flags:
  divergence > 0.20 for 2+ consecutive periods → HIGH
  recv_ratio increases 3+ consecutive periods  → MODERATE
```

### Module B: Cash Flow Integrity (weight: 20%)
```
Sloan Accrual Ratio = (net_income - operating_cf) / total_assets

Score by ratio:
  < 0.05:  100
  0.05–0.10: 70
  0.10–0.15: 45
  > 0.15:   20

Red flags:
  net_income > 0 AND operating_cf < 0 same period → SEVERE
  accrual_ratio > 0.10 for 2+ years             → HIGH
```

### Module C: Earnings Quality (weight: 15%)
```
margin_delta = gross_margin_t - gross_margin_t-1
cv = coefficient_of_variation(net_income_growth_rates)

Scoring (start at 100):
  |margin_delta| > 0.08:  -20
  cv > 1.5:               -25

Red flags:
  margin_delta > 0.10:         → MODERATE
  net_income spike > 50% with no revenue match → HIGH
```

### Module D: Debt Stress (weight: included in financial)
```
debt_to_revenue = total_debt / revenue
interest_coverage = operating_cf / (total_debt * 0.05)

Scoring (start at 100):
  debt_to_revenue > 1.0:  -20
  debt_to_revenue > 2.0:  -20 (additional)
  debt growth > 30% YoY:  -15
  interest_coverage < 2.0: -20

Red flag:
  debt > 40% growth, revenue flat or declining → HIGH
```

### Fraud Score Weights — Phase 3 amendment (2026-06-14, ADR-005/006)

`narrative` is **temporarily excluded** from the weight vector. The current narrative
pipeline derives statements from news headlines, not management transcripts — until a
real transcript pipeline exists (Horizon 2), `narrative_score` is still computed and
displayed, but carries zero weight in `integrity_score`. The remaining 5 modules are
renormalized from their original weights (financial 0.30, cashflow 0.20, governance 0.15,
earnings 0.15, news 0.10 — summing to 0.90) by ×(1/0.9):

```python
# backend/app/core/scoring/fraud_scorer.py
BASE_WEIGHTS: dict[str, float] = {
    "financial":   0.3333,
    "cashflow":    0.2222,
    "governance":  0.1667,
    "earnings":    0.1667,
    "news":        0.1111,
}  # sum = 1.0000; narrative intentionally absent
```

**Renormalization rule ("no dilution by neutral fill"):**
```
available = { k: scores[k] for k in BASE_WEIGHTS if scores.get(k) is not None }
integrity_score = round(
    sum(BASE_WEIGHTS[k] * v for k, v in available.items())
    / sum(BASE_WEIGHTS[k] for k in available),
    1
)
```

**Absence ≠ neutral.** A module key that is `None` or missing from `scores` means its
stage produced **no real signal** (network/AI failure, zero financial periods, etc.) and
is dropped from both the numerator and denominator above — it is NOT filled with `50.0`.
A module that legitimately computed exactly `50.0` from real data is still "available" and
weighted normally. This None-vs-value distinction is produced by `analysis_worker.py`'s
per-stage fallbacks (see Analysis Pipeline below), not by `fraud_scorer.py` itself.

**Confidence tier.** `compute_integrity_score(scores, period_count)` returns
`(integrity_score, confidence)`. Given `available_count` = number of the 5 `BASE_WEIGHTS`
modules with real signal, and `period_count` = number of `FinancialData` periods fetched:
```
available_count <= 2                       → "low"
available_count == 5 AND period_count >= 3  → "high"
otherwise                                   → "medium"
```
These thresholds are Phase 3's initial cutoffs — tunable later without revisiting the
renormalization formula above. `confidence` is persisted at
`AnalysisResult.module_details.confidence`.

**AI provenance (ADR-004).** `governance` and `narrative` are score-bearing AI calls and
run at `temperature=0` with a pinned `model_id` (`gemini-2.0-flash`), with prompts and raw
responses persisted for auditability:
- `module_details.governance.provenance` → `{model_id, prompt, raw_response}`
- `module_details.narrative.provenance` → list of `{period, model_id, prompt, raw_response}`, one per statement
- `module_details.narrative.statements_used` → count of statements that produced a snapshot

**News** remains a minor signal (weight `0.1111` post-renormalization) and always has
SOME value — `fetch_news_sentiment` falls back to `50.0` on failure, unchanged from
before Phase 3.

### Risk classification:
```
0–20:   SEVERE RISK
21–40:  HIGH RISK
41–60:  MODERATE RISK
61–80:  LOW RISK
81–100: STRONG INTEGRITY
```

---

## Analysis Pipeline — 7 Stages

```
Stage 1: "Fetching financial data..."
  → yahoo_finance.fetch_financials(ticker)
  → Save FinancialData records

Stage 2: "Running financial forensics..."
  → forensics_runner.run_forensics(financial_data) — all 4 modules
  → Save RedFlag records from forensic modules
  → On failure or zero financial periods: financial/cashflow/earnings/debt = None
    (excluded + renormalized — see Fraud Score Weights)

Stage 3: "Evaluating governance indicators..."
  → news_aggregator.fetch_news_text(ticker)
  → If len(news_text.strip()) < MIN_NEWS_TEXT_LENGTH (40 chars): governance = 50.0,
    low_confidence = true, Gemini not called (Phase 9 — see Error Handling rule 2b)
  → Else governance_scorer.analyze(news_text) — temperature=0, returns
    (score, flags, provenance); provenance.low_confidence = true if this Gemini call fails
  → Save governance events as RedFlag records (flag_type="governance")
  → module_details.governance.{provenance, low_confidence} ← above
  → On failure: governance = None

Stage 4: "Processing narrative consistency..."
  → news_aggregator.fetch_news_statements(ticker, limit=5)
  → If < 2 statements: narrative = 50.0, Gemini not called
  → Else consistency_engine.analyze(statements) — temperature=0, returns
    (score, snapshots, contradictions, provenance)
  → Save NarrativeSnapshot records
  → Contradictions (score_delta > 0.6) saved as RedFlag records
  → module_details.narrative.{snapshots, statements_used, provenance} ← above
  → On failure: narrative = 50.0

Stage 5: "Computing Integrity Score..."
  → news_aggregator.fetch_news_sentiment()
  → On failure: news = 50.0

Stage 6: "Computing Integrity Score..."
  → fraud_scorer.compute_integrity_score(scores, period_count) → (integrity_score, confidence)
  → Pure computation + DB write, no network calls
  → Update AnalysisResult with all scores, confidence, and module_details

Stage 7: "Generating report..."
  → report_generator.generate_report(company, analysis, flags, snapshots)
  → Save Report record
  → Update Company.last_analyzed
  → Set AnalysisResult.status = "complete"
```

**Each stage wrapped in its own try/except, plus an outer per-stage safety net in the
orchestrator. Pipeline never aborts on a single stage failure — every started analysis
ends with status = "complete" (status = "failed" is retired). Governance/narrative
Gemini failures fall back to a neutral score — never crash.**

---

## API Routes Reference

All routes below are mounted under `/api/v1` except `/health`, which is
unauthenticated and unversioned (Render hits it directly to detect
free-tier spin-down/restart cycles — ADR-012).

```
GET    /health                      DB connectivity probe, no auth

POST   /auth/register              create user, return JWT
POST   /auth/login                 OAuth2 form, return JWT
GET    /auth/me                    current user profile

GET    /company/search?q=          ILIKE search, max 10 results
GET    /company/{ticker}           company metadata, creates if new

POST   /analysis/run                       check free limit, trigger background task
GET    /analysis/{id}/status               status + stage + elapsed (polled every 3s)
GET    /analysis/company/{ticker}          latest completed result + red flags
GET    /analysis/company/{ticker}/history  score history, oldest first, for trend chart

GET    /report/company/{ticker}    markdown report content

GET    /watchlist                  user's list with latest scores
POST   /watchlist                  add company (409 if duplicate)
DELETE /watchlist/{ticker}         remove company
```

---

## Error Handling Rules

1. All forensic modules: if a field is None, skip that period — never crash
2. If ALL periods have None for a required field: return score 50.0 (neutral)
2a. Rule 2 is a **module-internal** fallback (unchanged by Phase 3): it fires *inside* a
    forensic module when the module ran but had incomplete data, and that 50.0
    contributes to the module's own score like any other value. This is a different
    layer from the Phase 3 orchestrator-level renormalization in "Fraud Score Weights"
    above: if a module's entire stage fails, or there are zero `FinancialData` periods at
    all, `analysis_worker.py` records that module's score as `None` — excluded from
    `integrity_score` and renormalized, not diluted with 50.0. The two rules don't
    conflict; they answer different questions ("the module ran but the data was thin" vs.
    "the module produced nothing at all").
2b. **Empty governance ≠ 100 (Phase 9, 2026-06-15).** `GovernanceScorer.analyze` starts at
    `100.0` and only deducts points for detected events — if `news_text` is empty or
    near-empty, there is nothing to deduct and the module would otherwise report a
    falsely pristine `100.0`. Fix: before calling Gemini, if
    `len(news_text.strip()) < MIN_NEWS_TEXT_LENGTH` (40 chars — shorter than a single
    typical headline), return `50.0` with `low_confidence: True` in the provenance
    record, and skip the Gemini call entirely. The same `low_confidence: True` marker is
    set if Gemini *is* called but the call fails (`events is None`) — both are "no real
    signal" outcomes, distinct from a real review that found zero events
    (`low_confidence: False`, `score == 100.0`, a legitimate "checked, all clear").
    `low_confidence` is surfaced at `module_details.governance.low_confidence` and shown
    as a disclaimer on the governance tab. This does not change rule 3 below — it adds a
    pre-call short-circuit plus a confidence marker on top of it.
3. Gemini API failure: log error, return None to caller, caller returns 50.0
4. Bad ticker (yfinance returns nothing): raise HTTP 404
5. Free tier limit (≥5 analyses/month): return HTTP 403 code LIMIT_REACHED
6. All errors: `{ "error": { "code": str, "message": str } }` — never expose stack traces

---

## Caching Strategy (In-Memory Dict)

```python
TTLs:
  "company:{ticker}:info"       → 24 hours
  "company:{ticker}:financials" → 12 hours
  "company:{ticker}:news"       → 2 hours
  "company:{ticker}:analysis"   → 6 hours
```

Always check cache before any yfinance or Gemini call.

---

## Database Models (8 total)

```
User              id, email, hashed_pw, full_name, tier, created_at, is_active
Company           id, name, ticker, sector, exchange, last_analyzed
FinancialData     id, company_id, period, period_type, revenue, net_income,
                  operating_cf, free_cf, total_debt, total_assets,
                  accounts_recv, gross_margin, fetched_at
AnalysisResult    id, company_id, run_at, integrity_score, financial_score,
                  cashflow_score, governance_score, earnings_score,
                  narrative_score, news_score, module_details (JSON), status
RedFlag           id, analysis_id, company_id, flag_type, severity,
                  description, period, event_date
Report            id, company_id, analysis_id, content (Text), generated_at
WatchlistItem     id, user_id, company_id, added_at [unique: user_id+company_id]
NarrativeSnapshot id, company_id, period, statement_text, sentiment_label,
                  sentiment_score, source, fetched_at
```

---

## AI Prompt Files

All 3 prompt templates live as .txt files:
```
backend/app/core/ai/prompts/report_prompt.txt
backend/app/core/ai/prompts/governance_prompt.txt
backend/app/core/ai/prompts/narrative_prompt.txt
```

Load with `pathlib.Path(__file__).parent / "prompts" / "filename.txt"`
Inject variables with `.format(**kwargs)`.
Never hardcode prompts in Python files.

---

## Important Decisions Already Made

1. No Redis — in-memory cache only (keeps hosting cost at $0)
2. No separate GovernanceEvent model — governance events saved as RedFlag records
3. No social login (Google/GitHub) on auth screens
4. No icons in navigation — text labels only, all breakpoints
5. No dark mode — light only
6. Risk gauge uses solid arc color (not gradient)
7. Active nav/tab: 2px underline (not pill or background)
8. "✓" in success states is a text character, not SVG
9. "Show"/"Hide" password toggle is text, not an eye icon
10. Error messages are text only — no icons beside them
11. Loading states: skeleton loaders only — no spinners
12. Button loading state shows "..." — not a spinner
13. Governance events NOT stored in separate table — they are RedFlag records
14. Free tier: 5 analyses per calendar month per user

---

## Deployment Targets

```
Frontend → Vercel
  vercel --prod (from /frontend directory)
  Set env var: NEXT_PUBLIC_API_URL=https://api.sentineliq.io

Backend → Render
  Connect GitHub repo
  Build command: pip install -r requirements.txt
  Start command: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  Health check path: /health
  Set all env vars in Render dashboard

Database → Render PostgreSQL (free tier, 1GB)
  Copy the connection string, rewrite scheme to postgresql+asyncpg:// for DATABASE_URL
```

See `docs/deployment.md` for the full setup playbook (env var table, scheme-rewrite
gotcha, post-deploy verification checklist) and the Phase 10 Step 5 dry-run results
(offline `alembic upgrade head --sql` against the full 8-table baseline + `analysis_runs`
+ `counted`, and a clean `npm run build`). Per ADR-012, creating the Render/Vercel
projects, connecting GitHub, and setting secrets are owner-in-the-loop actions.

---

## How to Work on This Project

When I ask you to work on SentinelIQ:
1. Read this file first — all context is here
2. Check the relevant file before editing it
3. Follow the design system rules strictly — no approximations
4. Run the dev servers and test before marking anything done
5. Never expose API keys in code or logs
6. If a design decision is not in this file, ask before inventing one
