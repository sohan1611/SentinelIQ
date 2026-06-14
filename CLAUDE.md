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
| AI | Google Gemini 1.5 Flash | Free tier: 1,500 req/day |
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
run at `temperature=0` with a pinned `model_id` (`gemini-1.5-flash`), with prompts and raw
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
  → governance_scorer.analyze(news_text) — temperature=0, returns
    (score, flags, provenance)
  → Save governance events as RedFlag records (flag_type="governance")
  → module_details.governance.provenance ← provenance
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

```
POST   /auth/register              create user, return JWT
POST   /auth/login                 OAuth2 form, return JWT
GET    /auth/me                    current user profile

GET    /company/search?q=          ILIKE search, max 10 results
GET    /company/{ticker}           company metadata, creates if new

POST   /analysis/run               check free limit, trigger background task
GET    /analysis/{id}/status       status + stage + elapsed (polled every 3s)
GET    /analysis/company/{ticker}  latest completed result + red flags

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
  Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  Set all env vars in Render dashboard

Database → Render PostgreSQL (free tier, 1GB)
  Copy the connection string to DATABASE_URL
```

---

## How to Work on This Project

When I ask you to work on SentinelIQ:
1. Read this file first — all context is here
2. Check the relevant file before editing it
3. Follow the design system rules strictly — no approximations
4. Run the dev servers and test before marking anything done
5. Never expose API keys in code or logs
6. If a design decision is not in this file, ask before inventing one
