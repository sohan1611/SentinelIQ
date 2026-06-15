# PROJECT STATUS — SentinelIQ
**Prepared by:** Claude Code (Sonnet), acting as Lead Implementation Engineer
**Prepared for:** Opus (Chief Architect review)
**Date:** 2026-06-13
**Purpose:** Read-only snapshot of the current repository state, for roadmap planning. No code was changed while producing this document.

**Repo:** `https://github.com/sohan1611/SentinelIQ`, branch `main`. 12 commits total (all dated 2026-06-12/13). Working tree is clean except an untracked `.claude/launch.json` (local dev-server config, harmless).

---

# 1. Project Overview

## What SentinelIQ is

SentinelIQ is an **AI-powered corporate fraud early-warning platform**. A user enters a company name or stock ticker; the system runs **five independent forensic analyses** and produces a **Corporate Integrity Score (0–100)** plus an AI-generated, analyst-style report explaining every finding in plain language.

**Core USP:** instead of predicting stock prices, it answers *"Can this company be trusted?"*

**Target users:** equity analysts, independent investors, auditors, risk officers. This is an **institutional product**, not a consumer app.

## Vision / Five Analyses → One Score

The "five independent analyses" map to six weighted scoring categories (weights must sum to 1.0):

| Category | Weight | Backend module |
|---|---|---|
| Financial (Revenue Quality + Debt Stress, averaged) | 0.30 | `forensics/revenue_quality.py` + `forensics/debt_analysis.py` |
| Cash Flow Integrity | 0.20 | `forensics/cashflow_integrity.py` |
| Governance Risk | 0.15 | `governance/governance_scorer.py` (AI/Gemini-driven) |
| Earnings Quality | 0.15 | `forensics/earnings_quality.py` |
| Narrative Consistency | 0.10 | `narrative/consistency_engine.py` (AI/Gemini-driven) |
| News Sentiment | 0.10 | `services/news_aggregator.py` |

Risk bands: 0–20 SEVERE, 21–40 HIGH, 41–60 MODERATE, 61–80 LOW, 81–100 STRONG INTEGRITY.

> **Note:** the "financial = avg(revenue, debt)" combination and the overall weight→module mapping above is *implemented correctly* but is **not written down anywhere** — `docs/scoring-methodology.md` is an empty placeholder. See Section 5 (Technical Debt).

## Architecture

```
┌─────────────────┐      JWT-authenticated REST       ┌──────────────────┐
│ Next.js 14       │ ───────────────────────────────▶ │ FastAPI (async)   │
│ (App Router, TS) │ ◀─────────────────────────────── │ + SQLAlchemy/PG   │
└─────────────────┘                                    └──────────────────┘
                                                              │   │   │
                                                  ┌───────────┘   │   └─────────────┐
                                                  ▼                ▼                 ▼
                                          yfinance (financials) feedparser (news) Gemini 1.5 Flash
                                                                                  (governance/narrative/report AI)
```

- **Frontend:** Next.js 14 App Router, TypeScript (`strict: true`), Tailwind CSS, Chart.js (`react-chartjs-2`).
- **Backend:** FastAPI, Python 3.11+, async SQLAlchemy 2.0 + asyncpg, Alembic.
- **AI:** Google Gemini 1.5 Flash (free tier, 1,500 req/day), prompts loaded from `.txt` files.
- **Auth:** JWT (python-jose) + bcrypt.
- **Caching:** in-memory Python dict, no Redis (keeps hosting at $0/month).
- **Hosting target:** Vercel (frontend), Render free tier (backend + Postgres).

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router) | TypeScript |
| Styling | Tailwind CSS | Custom color config |
| Charts | Chart.js / react-chartjs-2 | Custom styled |
| Backend | FastAPI (Python 3.11+) | Async, asyncpg |
| Database | PostgreSQL | SQLAlchemy ORM (async) |
| Migrations | Alembic | Configured but **never run** — see §4 |
| AI | Google Gemini 1.5 Flash | Free tier |
| Finance Data | yfinance | via `asyncio.to_thread` |
| News | feedparser (RSS) | 3 feeds per ticker |
| Auth | JWT + bcrypt | python-jose + bcrypt |
| Caching | In-memory dict | No Redis |
| Frontend host | Vercel | not yet deployed |
| Backend host | Render | not yet deployed |

## Local Environment Readiness

- `backend/.env`, `backend/.env.example`, `.env.example` (root), `frontend/.env.local` — **all present**.
- `backend/.venv/` — present (dependencies installed).
- `frontend/node_modules/` — present (dependencies installed).
- The repo therefore **can be run locally right now** (`npm run dev` + `uvicorn ...`) assuming a local Postgres instance matches `backend/.env`'s `DATABASE_URL` and a valid `GEMINI_API_KEY` is set.
- `docker-compose.yml` exists and references a `backend/Dockerfile` (present) and a `frontend/Dockerfile` (**missing** — `docker-compose up` will fail on the frontend service as currently written; README's "Run via Docker" instructions are not yet accurate).

## Important Design Decisions Inherited (from CLAUDE.md, verified still true in code)

1. **No Redis** — in-memory cache only ✅ (`backend/app/services/cache.py`).
2. **No separate `GovernanceEvent` model** — governance events are `RedFlag` rows with `flag_type="governance"` ✅ verified in `governance_scorer.py` + `analysis_worker.py`.
3. **No social login** ✅ — only email/password in `auth.py`/login/register pages.
4. **No icons in navigation, text labels only, all breakpoints** ✅ verified in `Sidebar.tsx`, `BottomTabBar.tsx`, `Navbar.tsx`.
5. **No dark mode** ✅ — no dark-mode classes/contexts found.
6. **Risk gauge = solid arc color (not gradient)** ✅ `IntegrityGauge.tsx`.
7. **Active nav/tab = 2px underline** ✅ company layout tabs, settings tabs.
8. **"✓" success state is a text character** ✅ used in `layout.tsx` analysis-complete bar.
9. **"Show"/"Hide" password toggle is text** ✅ `settings/page.tsx`, login/register pages.
10. **Error messages are text only** ✅ throughout.
11. **Skeleton loaders only, no spinners** ✅ `Skeleton.tsx` used everywhere loading states exist.
12. **Button loading state shows "..."** ✅ `Button.tsx`.
13. **Governance events are RedFlag records** ✅ (duplicate of #2, both confirmed).
14. **Free tier: 5 analyses/month** — *intended*, but **the enforcement logic is broken** — see §4 Critical.

---

# 2. Features Inventory

## A. Frontend — Public & Auth Pages

### A1. Landing / Marketing Page
- **Description:** Public homepage — hero, trust strip, feature strip, "How It Works" score-scale legend, 4 hardcoded case-study tiles (Enron 28, Wirecard 22, Satyam 31, Luckin 19), second CTA.
- **Status:** Completed (static by design — marketing copy doesn't need backend wiring).
- **Files:** `frontend/app/(marketing)/page.tsx` (260 lines), uses real `SearchBar`/`Badge` components.
- **Dependencies:** none.
- **Known issues:** none.

### A2. Authentication — Login & Register
- **Description:** Email/password login and registration forms.
- **Status:** Completed.
- **Files:** `frontend/app/(auth)/login/page.tsx` (132 lines), `frontend/app/(auth)/register/page.tsx` (231 lines). Wired in commit `10970221`.
- **Dependencies:** `lib/api/auth.ts`, `contexts/AuthContext.tsx`, backend `POST /auth/login` (OAuth2 form), `POST /auth/register`.
- **Known issues:** none found at the page level. (See A19/E1 for the cross-cutting "no route guard" issue this feeds into.)

### A3. Authentication — Forgot Password
- **Description:** "Enter email to receive reset link" flow with a confirmation screen.
- **Status:** Broken / Fully mock.
- **Files:** `frontend/app/(auth)/forgot-password/page.tsx` (115 lines).
- **Dependencies:** none currently wired — there is **no backend password-reset endpoint** and no corresponding `lib/api/auth.ts` function.
- **Known issues:** `handleSubmit` only does `e.preventDefault(); setIsSent(true)` — no API call is made, so users would believe an email was sent when nothing happened. Page also still contains leftover **dev-only "state toggle" debug buttons** ("Default"/"Sent") that must not ship to production.

### A4. Authentication — Verify Email
- **Description:** Email-verification landing page with verifying/success/invalid states.
- **Status:** Broken / Fully mock.
- **Files:** `frontend/app/(auth)/verify-email/page.tsx` (81 lines).
- **Dependencies:** none currently wired — no backend email-verification endpoint, no token parsing from the URL.
- **Known issues:** State is driven entirely by local `useState`, defaulting to `"verifying"` forever in practice (nothing transitions it). Leftover **dev-only "state toggle" debug buttons** (Verifying/Success/Invalid) present. "Resend Verification Email" button has no `onClick` handler.

## B. Frontend — Core Application Pages

### B1. Dashboard
- **Description:** Authenticated home — quick search, watchlist summary table/cards, and a client-derived "Recent Reports" section (top 3 watchlist items by `last_analyzed`).
- **Status:** Completed.
- **Files:** `frontend/app/(app)/dashboard/page.tsx` (195 lines). Wired in commit `e9885a12`.
- **Dependencies:** `useWatchlist`, `SearchBar`, `CompanyCard`, `lib/utils/{formatNumber,riskLabel,scoreColor,formatDate}`.
- **Known issues:** "Recent Reports" is a client-side derivation, not a real backend endpoint — acceptable per an inline code comment ("the backend has no user-scoped recent-reports endpoint"), but worth a real endpoint if usage patterns demand it later.

### B2. Search
- **Description:** Company search page — debounced live search via `SearchBar`, results table, plus a ticker-pattern heuristic that offers "Investigate {TICKER} directly →" even for tickers not yet in the local DB.
- **Status:** Completed.
- **Files:** `frontend/app/(app)/search/page.tsx` (156 lines). Wired in commit `e9885a12`.
- **Dependencies:** `lib/api/company.ts` (`searchCompanies`), `useSearchParams` (wrapped in `<Suspense>` per Next.js 14 requirement).
- **Known issues:** none.

### B3. Watchlist
- **Description:** List of companies the user is tracking, with score, risk badge, last-analyzed, and remove action; desktop table + mobile `CompanyCard` list.
- **Status:** Completed.
- **Files:** `frontend/app/(app)/watchlist/page.tsx` (150 lines, new file), `frontend/components/shared/CompanyCard.tsx` (extended). Built in commit `160fd635`.
- **Dependencies:** `useWatchlist` (`lib/hooks/useWatchlist.ts`), `lib/api/watchlist.ts`.
- **Known issues:** none.

### B4. Settings
- **Description:** Account/Notifications/Plan/API tabs.
- **Status:** Partially Completed.
- **Files:** `frontend/app/(app)/settings/page.tsx` (285 lines). Last touched in commit `7ac009c1`.
- **Dependencies:** `useAuth` (`contexts/AuthContext.tsx`).
- **Known issues:**
  - **Account tab:** Full Name / Work Email fields correctly display real `user.full_name` / `user.email` via `useAuth`, but the **"Save Changes" button has no handler** — nothing is persisted. "Update Password" button also has no handler, and there is **no backend endpoint for changing password**. "Delete Account" button has no handler and no backend endpoint.
  - **Notifications tab:** four toggles are pure local `useState` — not persisted, no backend model/endpoint for notification preferences.
  - **Plan tab:** correctly shows the real `user.tier` via `useAuth`, but both "Upgrade to Pro" buttons have no handler (no billing integration exists, which is expected at this stage, but should be a clearly-labeled stub).
  - **API tab:** static "available on Pro plan" message — fine as-is.

### B5. Company Workspace Shell (header, tabs, "Run Analysis")
- **Description:** Shared layout for all `/company/[ticker]/*` pages — company name/sector/exchange header, "Last analyzed" date, "Run Analysis" button, live analysis-status bar (polls every 3s), and the Overview/Financials/Governance/Narrative/Report tab strip with animated underline.
- **Status:** Completed.
- **Files:** `frontend/app/(app)/company/[ticker]/layout.tsx` (199 lines). Wired in commit `866258cc` (this session).
- **Dependencies:** `useCompanyData`, `useAnalysis`, `Skeleton`, `Button`, `formatDate`.
- **Known issues:** Only the layout's *own* `useCompanyData` is refetched when an analysis completes (via `onComplete`) — this updates the header's "Last analyzed" date, but **child tab pages do not automatically refresh** their own data when an analysis finishes while the user is on that tab. Documented limitation, deferred by design (not over-engineered with shared/context state). Also: a harmless redundant ternary `${isReport ? 'mb-8' : 'mb-8'}` remains (cosmetic, no functional impact).

### B6. Company — Overview Tab
- **Description:** Should show the Corporate Integrity Score gauge, 5 component scores, red-flag timeline, and module score cards for the *currently selected* company.
- **Status:** Broken / Fully mock (this is the core product surface and it is currently 100% fake data).
- **Files:** `frontend/app/(app)/company/[ticker]/page.tsx` (191 lines).
- **Dependencies (intended but unused):** `useCompanyData` → `analysis.module_details`, `analysis.red_flags`, `AnalysisResultWithFlags` (all already defined in `types/analysis.ts` and returned by the backend).
- **Known issues:** Every data point is a hardcoded literal: `componentScores` (5-item array: Financial Quality 42, Cash Flow Integrity 31, Governance Risk 28, Earnings Quality 18, Narrative Consistency 55), `redFlags` (6-item array), `moduleData` (4-item array), and `<IntegrityScoreGauge score={22} lastAnalyzed="June 9, 2025">`. "Export PDF" and "Add to Watchlist" buttons have no handlers. This is **Phase D2** in the roadmap (§6).

### B7. Company — Financials Tab
- **Description:** Should show Revenue vs. OCF growth divergence, Cash Flow (Net Income vs. OCF), and Debt-to-Revenue trend charts derived from `module_details`.
- **Status:** Broken / Fully mock.
- **Files:** `frontend/app/(app)/company/[ticker]/financials/page.tsx` (220 lines).
- **Dependencies (intended but unused):** `module_details.revenue.divergences`, `module_details.revenue.recv_ratios`, `module_details.cashflow.accrual_ratios`, `module_details.debt.debt_metrics` (all typed and present in `types/analysis.ts`); the empty `RevenueQualityChart`, `CashFlowChart`, `DebtTrendChart` components.
- **Known issues:** All three charts (`revenueChartData`, `cashFlowChartData`, `debtStressChartData`) are built inline with hardcoded 12-quarter / 4-year datasets directly via `<Line>`/`<Bar>` from `react-chartjs-2`, duplicating logic that should live in the (currently empty) chart components. All scores/badges/narrative text are hardcoded strings.

### B8. Company — Governance Tab
- **Description:** Should show a governance checklist (CFO stability, auditor continuity, board independence, etc.) and a governance event log, derived from `RedFlag` rows with `flag_type="governance"`.
- **Status:** Broken / Fully mock.
- **Files:** `frontend/app/(app)/company/[ticker]/governance/page.tsx` (100 lines).
- **Dependencies (intended but unused):** `analysis.red_flags` filtered by `flag_type === "governance"`; the empty `GovernanceChecklist` component.
- **Known issues:** `checklist` (6-item array) and `eventLog` (6-item table, hardcoded) are static. Each event-log row's "SOURCE" column links to `href="#"` (dead link). Score "28/100" and risk badge are hardcoded.

### B9. Company — Narrative Tab
- **Description:** Should show a "confidence over time" chart and side-by-side management-statement comparisons with contradiction alerts, derived from `NarrativeSnapshot` records.
- **Status:** Broken / Fully mock — **and even if wired, the backend currently has almost nothing real to show** (see D4/Narrative Consistency Engine).
- **Files:** `frontend/app/(app)/company/[ticker]/narrative/page.tsx` (153 lines).
- **Dependencies (intended but unused):** `module_details.narrative.snapshots` (`NarrativeSnapshotData[]`, typed and present); the real, implemented `NarrativeComparison` component (already used here, but with hardcoded props); the empty `RiskRadar` component.
- **Known issues:** `chartData` (12-quarter "Confidence Score %" line, hardcoded `[88,86,85,80,82,75,60,45,55,30,25,15]`) and three `NarrativeComparison` instances all use hardcoded quotes/contradiction text. Two manually-positioned absolute-div chart annotations ("Guidance withdrawn", "Audit review") are also hardcoded. Score "55/100" hardcoded.

### B10. Company — Report Tab
- **Description:** Should render the AI-generated markdown analyst report (`Report.content`) produced by Gemini in Stage 7 of the pipeline.
- **Status:** Broken / Fully mock.
- **Files:** `frontend/app/(app)/company/[ticker]/report/page.tsx` (150 lines).
- **Dependencies (intended but unused):** `lib/api/report.ts`'s `getReport(ticker)` (exists, 7 lines, **never called anywhere in the app**); `types/report.ts`'s `Report.content` (markdown string); the empty `ReportSection` component; a markdown renderer (not yet a dependency — none installed).
- **Known issues:** Entire report ("Wirecard AG", "Generated June 9, 2025", "Analysis #2891", score "22/100", and 5 full prose sections) is hardcoded. "Share Report" and "Export PDF" buttons have no handlers. `RecommendationBox` (real, implemented component) is used but with a hardcoded `body` string.

### B11. Error / 404 Pages
- **Description:** Generic 500-style error boundary and 404 not-found page.
- **Status:** Completed.
- **Files:** `frontend/app/error.tsx` (52 lines), `frontend/app/not-found.tsx` (38 lines).
- **Dependencies:** Next.js error-boundary conventions (`reset()` prop).
- **Known issues:** `not-found.tsx`'s "Back" link uses `href="javascript:history.back()"` — works, but is a legacy/non-idiomatic pattern; a `router.back()` `onClick` would be cleaner. Cosmetic only.

### B12. Design System Reference Page
- **Description:** Dev-only visual catalog of every UI primitive/module/chart in various states (loading, error, populated) — used for design QA.
- **Status:** Completed (dev-only scaffolding, not part of the product).
- **Files:** `frontend/app/(app)/design-system/page.tsx` (251 lines).
- **Dependencies:** nearly every component in `components/`.
- **Known issues:** Sits inside the authenticated `(app)` route group and the Sidebar — should probably be excluded from the production nav/build before launch (Low Priority, §4).

## C. Frontend — Infrastructure & Shared Code

### C1. API Client Layer
- **Description:** Central `fetch` wrapper + per-resource API modules.
- **Status:** Completed.
- **Files:** `frontend/lib/api/{client.ts (79), auth.ts (17), company.ts (10), analysis.ts (17), watchlist.ts (19), report.ts (7)}`.
- **Dependencies:** `NEXT_PUBLIC_API_URL` env var (falls back to `http://localhost:8000`), `types/api.ts` (`ApiError`).
- **Known issues:** `client.ts` correctly implements `Authorization: Bearer <token>` injection (token in `localStorage["sentineliq_token"]`), JSON/form-encoding auto-detection, and unwraps both FastAPI's default `{"detail": "..."}` and the documented `{"detail": {"error": {"code","message"}}}` shapes — this client-side leniency is currently *masking* the backend's error-envelope inconsistency (see §4 Critical). `report.ts`'s `getReport` is unused (B10).

### C2. Auth Context & Session Management
- **Description:** `useAuth()` — current user, login/register/logout, JWT persistence.
- **Status:** Completed, but with a security/UX gap.
- **Files:** `frontend/contexts/AuthContext.tsx` (63 lines).
- **Dependencies:** `lib/api/auth.ts`, `lib/api/client.ts` token helpers.
- **Known issues:** **No route protection exists.** There is no `middleware.ts` and `app/(app)/layout.tsx` does not check `user`/`isLoading` or redirect to `/login`. Any unauthenticated visitor can load `/dashboard`, `/search`, `/watchlist`, `/settings`, `/company/[ticker]` directly — pages will show API-driven error/empty states (401s) rather than redirecting. For an "institutional product," this is a notable gap (§4 Critical).

### C3. Toast Notification System
- **Description:** Stacked toast notifications for user feedback (success/info).
- **Status:** Partially Completed — built but unused, and deviates from spec.
- **Files:** `frontend/contexts/ToastContext.tsx` (103 lines), mounted in `app/(app)/layout.tsx`.
- **Dependencies:** none external.
- **Known issues:** `useToast()` has **zero call sites** anywhere in `app/` or `components/` — no toast ever fires (watchlist add/remove, login, analysis-complete all lack feedback). Additionally, the implementation **deviates from CLAUDE.md's animation spec**: both enter and exit use `translateY` (spec: enter should be `translateX`), auto-dismiss is 4000ms (spec: 3000ms), and there is no "max 3 stacked" cap (code comment acknowledges the translateX deviation).

### C4. Layout Shell & Navigation
- **Description:** App chrome — sidebar/bottom-tab navigation, marketing nav/footer, search bar, route-transition animation.
- **Status:** Completed.
- **Files:** `AppShell.tsx` (16), `Sidebar.tsx` (95), `BottomTabBar.tsx` (37), `Navbar.tsx` (33), `Footer.tsx` (33), `SearchBar.tsx` (187), `PageTransition.tsx` (40) — all in `frontend/components/layout/`.
- **Dependencies:** `useAuth`, `usePathname`, `useDebounce` + `searchCompanies` (SearchBar live dropdown).
- **Known issues:** none — confirmed "no icons in nav" compliance (Sidebar/BottomTabBar/Navbar are text-only). `b75f0247` also removed two dead empty route stubs: `(marketing)/about/page.tsx` and `api/[...proxy]/route.ts`.

### C5. Chart Component Library
- **Description:** Reusable chart components for the company-analysis tabs.
- **Status:** Partially Completed (2 of 6 implemented).
- **Files:** `frontend/components/charts/`:
  - `IntegrityGauge.tsx` (157 lines) — **Completed**. `IntegrityScoreGauge({score, lastAnalyzed, loading, startAnimation})`, animated SVG arc + solid risk-band colors, internal `getRiskDetails(score)`.
  - `RedFlagTimeline.tsx` (61 lines) — **Completed**. `RedFlagTimeline({events: TimelineEvent[]})`.
  - `CashFlowChart.tsx`, `RevenueQualityChart.tsx`, `DebtTrendChart.tsx`, `RiskRadar.tsx` — **Planned (0-byte stubs)**.
- **Dependencies:** Chart.js / react-chartjs-2 (for the 4 stubs, once built).
- **Known issues:** the 4 stub components are the reason B7/B9 reimplement chart logic inline.

### C6. Module Component Library
- **Description:** Reusable "card"-style modules for displaying scores, flags, recommendations, and report sections.
- **Status:** Partially Completed (4 of 7 implemented).
- **Files:** `frontend/components/modules/`:
  - `ScoreCard.tsx` (63) — **Completed**. `ModuleScoreCard({label, score, summary, href, loading})`.
  - `RedFlagItem.tsx` (48) — **Completed**. `RedFlagItem({severity, date, description, type, loading})`, exports `Severity` type.
  - `NarrativeComparison.tsx` (60) — **Completed**. `NarrativeComparison({left, right, contradictionAlert, alertSeverity})`.
  - `RecommendationBox.tsx` (28) — **Completed**. `RecommendationBox({variant, body})`.
  - `FraudScoreBanner.tsx`, `GovernanceChecklist.tsx`, `ReportSection.tsx` — **Planned (0-byte stubs)**.
- **Dependencies:** `Badge`.
- **Known issues:** the 3 stubs are the reason B8/B10 reimplement their layouts inline.

### C7. Shared / UI Component Library
- **Description:** Base primitives (buttons, badges, cards, inputs, modals, tooltips, skeletons) and shared widgets (`CompanyCard`, error boundary, loading state).
- **Status:** Partially Completed.
- **Files:** `frontend/components/ui/{Badge.tsx, Button.tsx (38), Card.tsx (15), Separator.tsx (20), Skeleton.tsx (16)}` — **Completed**; `Input.tsx`, `Modal.tsx`, `Tooltip.tsx` — **Planned (0-byte stubs)**. `frontend/components/shared/CompanyCard.tsx` (108 lines) — **Completed** (score-change flash animation, used in Dashboard/Watchlist); `ErrorBoundary.tsx`, `LoadingState.tsx` — **Planned (0-byte stubs)**.
- **Dependencies:** none beyond Tailwind.
- **Known issues:** `frontend/package.json` lists `lucide-react` as a dependency, but no nav/icon usage was found anywhere that would require it (CLAUDE.md prohibits nav icons) — possibly an unused dependency left over from scaffolding (Low Priority cleanup candidate).

### C8. Hooks, Utils & Constants
- **Description:** Data-fetching hooks and small formatting/constant helpers.
- **Status:** Completed.
- **Files:**
  - `frontend/lib/hooks/{useAnalysis.ts (69), useCompanyData.ts (66), useDebounce.ts (12), useWatchlist.ts (55)}`
  - `frontend/hooks/useStaggeredReveal.ts` (root-level, separate from `lib/hooks/` — used by Overview tab)
  - `frontend/lib/utils/{formatDate.ts (27), formatNumber.ts (15), riskLabel.ts (12), scoreColor.ts (10)}`
  - `frontend/lib/constants/{routes.ts (16), riskThresholds.ts (38)}`
  - `frontend/types/{analysis.ts (111), api.ts (11), company.ts (9), report.ts (8), user.ts (24), watchlist.ts (8)}`
- **Dependencies:** none.
- **Known issues:** `riskThresholds.ts`'s color constants match CLAUDE.md's design-system hex values exactly, including two extra UI-state keys (`analyzing`, `flagged`) not in the original spec table — harmless additions.

## D. Backend — Forensics, Scoring & AI Engine

### D1. Forensics Engine (Modules A–D + Runner)
- **Description:** The four quantitative forensic modules (Revenue Quality, Cash Flow Integrity, Earnings Quality, Debt Stress) plus the runner that executes all four and aggregates red flags.
- **Status:** Completed — matches CLAUDE.md formulas/weights/thresholds, including the Sloan Accrual Ratio, divergence/recv-ratio logic, margin-delta/CV logic, and debt-to-revenue/interest-coverage logic.
- **Files:** `backend/app/core/forensics/{base.py (19), revenue_quality.py (85), cashflow_integrity.py (65), earnings_quality.py (70), debt_analysis.py (68), forensics_runner.py (29)}`.
- **Dependencies:** `FinancialData` model (multi-period records from `yahoo_finance.py`).
- **Known issues:** only minor, defensible boundary-condition interpretations (`>=` vs `>` at exact threshold values) and two red-flag conditions that add an extra revenue-growth gate not literally specified in CLAUDE.md (tightens false positives, doesn't violate intent). All error-handling rules (skip-on-None, neutral-50.0-if-all-None, never crash) are followed.

### D2. Fraud / Risk Scoring
- **Description:** Combines all module scores into the final Integrity Score and classifies the risk band.
- **Status:** Completed (but co-located with dead sibling files — see Technical Debt).
- **Files:** `backend/app/core/scoring/fraud_scorer.py` (18 lines) — `compute_integrity_score()` (weights sum to exactly 1.0, `.get(key, 50.0)` neutral fallback ✅) and `classify_risk()` (0–20/21–40/41–60/61–80/81–100 bands ✅).
- **Dependencies:** scores dict from `analysis_worker.py`.
- **Known issues:** `risk_classifier.py` and `weights.py` are both **0-byte empty files**, unimported anywhere — all their intended logic already lives in `fraud_scorer.py`. Dead code (§5).

### D3. Governance Scoring Module
- **Description:** AI-driven analysis of recent news headlines to detect governance red flags (CFO/CEO resignation, auditor change, director resignation, SEC inquiry, shareholder lawsuit, restatement).
- **Status:** Completed.
- **Files:** `backend/app/core/governance/governance_scorer.py` (42 lines) + `backend/app/core/ai/prompts/governance_prompt.txt` (16 lines).
- **Dependencies:** `services/news_aggregator.py` (`fetch_news_text`), `core/ai/gemini_client.py`.
- **Known issues:** On Gemini failure, correctly returns `(50.0, [])` (neutral, no flags) ✅. Two sibling files `governance/board_analysis.py` and `governance/exec_turnover.py` are **0-byte empty stubs** — unused, likely represent un-built deeper governance analysis (Planned).

### D4. Narrative Consistency Engine
- **Description:** AI-driven analysis comparing management statements across periods; sentiment deltas > 0.6 become contradiction red flags.
- **Status:** Completed as code, but **effectively non-functional at runtime** (see Known issues — this is the most important single finding in this report).
- **Files:** `backend/app/core/narrative/consistency_engine.py` (60 lines) + `backend/app/core/ai/prompts/narrative_prompt.txt` (10 lines).
- **Dependencies:** statements list passed in by `analysis_worker.py` Stage 5; `core/ai/gemini_client.py`.
- **Known issues:**
  - The engine itself correctly implements: per-statement Gemini calls with graceful skip-on-failure, `score_delta > 0.6` → contradiction RedFlag (severity `high` if `>0.8` else `moderate`), and `(50.0, snapshots, [])` neutral fallback if fewer than 2 snapshots succeed — **all matches CLAUDE.md**.
  - **However**, `analysis_worker.py` (Stage 5, lines ~119–123) feeds it a **hardcoded single statement**:
    ```python
    # We mock management statements from news_text for this prototype
    # In real app, we'd fetch transcripts
    statements = [
        {"period": "Current", "text": "We see strong growth ahead despite headwinds.", "source": "News"}
    ]
    ```
    With only one statement, `len(snapshots) < 2` is always true, so **`narrative_score` is always exactly `50.0` and zero contradictions are ever detected** — for *every* company, on every analysis run. One of the "five independent forensic analyses" the product advertises does not actually run.
  - Three related sibling modules are **0-byte empty stubs**: `narrative/sentiment_scorer.py`, `narrative/statement_extractor.py`, `narrative/transcript_parser.py`, plus `services/transcript_fetcher.py` and `services/sec_scraper.py` — these look like the intended (unbuilt) real data path for this module.

### D5. AI Report Generation
- **Description:** Generates the final analyst-style markdown report via Gemini, using all scores + red flags + narrative contradictions.
- **Status:** Completed.
- **Files:** `backend/app/core/ai/{gemini_client.py (39), report_generator.py (54)}` + `backend/app/core/ai/prompts/report_prompt.txt` (31 lines).
- **Dependencies:** `FraudScorer.classify_risk()`, all module scores, `RedFlag` list.
- **Known issues:** none — `gemini-1.5-flash` model, prompt loaded via `Path(__file__).parent / "prompts" / "..."` + `.format(**kwargs)` exactly per CLAUDE.md convention, Gemini failure → static fallback string (not a crash). Report quality will obviously be limited by D4's effectively-stub narrative input.

### D6. Analysis Pipeline Orchestrator (7-Stage Worker)
- **Description:** The background task that runs all 7 stages described in CLAUDE.md for a single ticker, persists results, and updates `AnalysisResult`/`Report`/`RedFlag`/`NarrativeSnapshot`/`Company.last_analyzed`.
- **Status:** Completed, with two notable rule deviations.
- **Files:** `backend/app/tasks/analysis_worker.py` (206 lines / 205 of content).
- **Dependencies:** every module in D1–D5 + `services/yahoo_finance.py` + `services/news_aggregator.py`.
- **Known issues:**
  1. **Stage 6 violates "pipeline never aborts on single-stage failure"**: its `except` block sets `analysis.status = "failed"` and **returns early, skipping Stage 7 entirely**. A transient Gemini/news error during Stage 6 means the user gets **no report at all** instead of a degraded one. All other stages (1, 2/3, 4, 5, 7) correctly isolate failures with neutral fallbacks and continue.
  2. Stage 5's hardcoded mock statement — see D4.
  3. `backend/app/tasks/data_refresh.py` is a **0-byte empty stub** — presumably intended for periodic background refresh of cached company data, not built.

## E. Backend — Platform

### E1. Authentication & Authorization
- **Description:** Register/login/me endpoints, JWT issuance/validation, password hashing.
- **Status:** Completed, with a misleading dead-code detail.
- **Files:** `backend/app/api/v1/routes/auth.py`, `backend/app/api/deps.py` (1362 bytes).
- **Dependencies:** `python-jose`, `bcrypt`, `User` model.
- **Known issues:** `deps.py` line ~26 builds `token_data = TokenData(email=user_id) # Using sub as ID usually...` — `TokenData.email` is actually populated with the user's UUID, and `token_data` itself is **never used** (the real lookup uses `user_id` directly on the next line). Functionally correct, but confusing dead code. Also: `backend/app/api/v1/deps.py` is a **separate 0-byte empty file**, a dead duplicate of the real `backend/app/api/deps.py`.

### E2. Database Models & Schemas
- **Description:** SQLAlchemy ORM models (8, per CLAUDE.md) and Pydantic request/response schemas.
- **Status:** Models Completed (8/8); Schemas Partially Completed.
- **Files:** `backend/app/models/{user,company,financial_data,analysis_result,red_flag,report,watchlist,narrative_snapshot}.py` (all present, all UUID PKs); `backend/app/schemas/{user,company,analysis,report,watchlist}.py`.
- **Dependencies:** async SQLAlchemy, `database.py`.
- **Known issues:**
  - All 8 models match CLAUDE.md's field lists. `WatchlistItem` correctly has the `UniqueConstraint('user_id','company_id')`.
  - **Missing schemas**: `FinancialData` (no schema at all — not currently exposed via any route, low impact) and `NarrativeSnapshot` (no schema at all — needed for B9/D4 once narrative is fixed and wired to the frontend).
  - `RedFlagResponse` lives inside `schemas/analysis.py` rather than its own `red_flag.py` — organizational nit, not a bug.

### E3. API Routes / REST Layer
- **Description:** All 12 routes from CLAUDE.md's API reference, across 5 route modules.
- **Status:** Partially Completed — 11/12 routes exist and function, but with real bugs.
- **Files:** `backend/app/api/v1/routes/{auth,company,analysis,report,watchlist}.py`, `backend/app/api/v1/router.py`.
- **Dependencies:** all of D1–D6, E1, E2.
- **Known issues:**
  - **`POST /analysis/run` free-tier limit is structurally broken**: it counts "analyses run this month" by joining `AnalysisResult` to `WatchlistItem` on `company_id` — but `AnalysisResult` has **no `user_id` column**, so this either undercounts (analyses on companies not in the user's watchlist are invisible) or overcounts (other users' analyses on a company in *this* user's watchlist count against them). The code itself contains a comment acknowledging this. The "5 analyses/month free tier" — a core monetization mechanic — does not work as intended.
  - **Error envelope inconsistency**: CLAUDE.md mandates `{"error": {"code": str, "message": str}}` for *all* errors. Only `POST /analysis/run` uses this shape; every other endpoint raises plain-string `HTTPException(detail=...)`, which FastAPI serializes as `{"detail": "..."}`. (The frontend's `client.ts` happens to handle both shapes, so this is currently invisible to end users — but it's a contract violation any other API consumer would hit.)
  - `GET /analysis/company/{ticker}` only returns a result if `status == "complete"` — matches a literal reading of "latest completed result," but means a `"failed"` analysis (see D6 issue #1) leaves the user with a 404 and no visibility into what happened.
  - All other routes (register/login/me, company search/get, report, watchlist CRUD) verified correct against the spec (ILIKE search capped at 10, auto-create company on GET, 409 on duplicate watchlist add, etc.).

### E4. Database Migrations (Alembic)
- **Description:** Schema migration tooling.
- **Status:** Broken / Planned — scaffolding complete, zero migrations exist.
- **Files:** `backend/alembic.ini`, `backend/alembic/env.py` (correctly configured: async engine, imports all 8 models onto `Base.metadata`). `backend/alembic/versions/` is **completely empty**.
- **Dependencies:** all 8 models (E2), `DATABASE_URL`.
- **Known issues:** Despite commit `56830563`'s message ("...add migrations"), **no Alembic revision files exist**. Currently, `backend/app/main.py`'s startup `lifespan` handler calls `Base.metadata.create_all` directly — this is how tables actually get created today, completely bypassing Alembic. The first real migration will need to be generated against an *already-existing* schema (via `alembic stamp head` + careful autogenerate, or a hand-written baseline) — this is a **deployment blocker** for Render Postgres (§4 Critical).

### E5. Caching Layer
- **Description:** In-memory TTL cache for company info/financials/news/analysis.
- **Status:** Completed.
- **Files:** `backend/app/services/cache.py` (20 lines) — simple `dict` with lazy expiry.
- **Dependencies:** none.
- **Known issues:** Confirmed TTLs in use: `company:{ticker}:info` 24h (`yahoo_finance.py`), `company:{ticker}:financials` 12h (`yahoo_finance.py`), `company:{ticker}:news` 2h (`news_aggregator.py`) — all match CLAUDE.md. The documented `company:{ticker}:analysis` 6h TTL was **not found** being set anywhere (not in the 3 service files, nor observed in `analysis_worker.py`) — either it's intentionally absent (analysis results are persisted to Postgres so caching may be redundant) or it's a small gap. Process-local dict won't share state across multiple backend workers/replicas if the deployment ever scales beyond one instance (acceptable for the documented $0/Render-free-tier plan).

### E6. External Data Services (Yahoo Finance, News RSS)
- **Description:** Fetches company info/financials (yfinance) and news headlines/sentiment (feedparser, 3 RSS feeds).
- **Status:** Completed.
- **Files:** `backend/app/services/{yahoo_finance.py (101), news_aggregator.py (88)}`.
- **Dependencies:** `yfinance`, `feedparser`, `pandas`, `cache.py`.
- **Known issues:** Two minor code-smells (not bugs): in both files, a module (`pandas` in `yahoo_finance.py`, `time` in `news_aggregator.py`) is imported *after* its first use inside a closure — works correctly due to Python's late name binding, but should be moved to top-of-file for clarity. Bad-ticker handling correctly raises HTTP 404 per CLAUDE.md's error rules.

### E7. Backend Test Suite
- **Description:** Unit + integration tests for forensics, scoring, narrative engine, and the full pipeline.
- **Status:** Planned — all stubs, zero coverage.
- **Files:** `backend/tests/integration/test_analysis_pipeline.py`, `backend/tests/unit/{test_fraud_scorer.py, test_narrative_engine.py, test_revenue_quality.py}` — **all 0 bytes**, no `__init__.py`/`conftest.py`. `pytest` would collect 0 tests.
- **Dependencies:** would need all of D1–D6.
- **Known issues:** Every "Completed" status in this document is based on static reading of the code, not test execution — there is no automated safety net for any future change.

## F. Project-Level Infrastructure

### F1. Deployment Infrastructure
- **Description:** Docker Compose (local), Vercel (frontend), Render (backend + Postgres).
- **Status:** Planned / Not started.
- **Files:** `docker-compose.yml` (root), `backend/Dockerfile` (present), `frontend/Dockerfile` (**missing**).
- **Dependencies:** E4 (migrations must exist before a real deploy), all env vars from CLAUDE.md.
- **Known issues:** `docker-compose.yml` declares a `frontend` service with `build.context: ./frontend`, but `frontend/Dockerfile` does not exist — `docker-compose up -d` will fail as-is, contradicting the README's documented "Run via Docker" quickstart. Neither Vercel nor Render projects appear to be connected/configured yet (no config files like `vercel.json` or `render.yaml` found).

### F2. Documentation
- **Description:** Architecture/methodology/API/data-source docs, plus SQL schema reference.
- **Status:** Planned — all placeholders.
- **Files:** `docs/{architecture.md, scoring-methodology.md, api-reference.md, data-sources.md}` and `database/{schema.sql, migrations/001..006_*.sql}` — **all 0 bytes** (7+4 = 11 files total). `README.md` (57 lines) is real and accurate about high-level structure, but its Docker instructions are currently broken (F1).
- **Dependencies:** none.
- **Known issues:** `CLAUDE.md` is currently the *only* source of truth for algorithms/scoring/architecture. Fine for Claude Code sessions, but a gap for any human contributor or for `docs/scoring-methodology.md` specifically — which is exactly where the "financial = avg(revenue, debt)" mapping (Section 1) should be documented.

### F3. Dev / Backtest Scripts
- **Description:** Scripts intended to seed dev data and backtest the scoring model against known historical fraud cases (Enron, Wirecard).
- **Status:** Planned — all placeholders.
- **Files:** `scripts/{backtest_enron.py, backtest_wirecard.py, deploy.sh, seed_dev_data.py}` — **all 0 bytes**.
- **Dependencies:** D1–D6 (backtests), E2 (seed data).
- **Known issues:** none beyond being unbuilt. `backtest_wirecard.py` in particular would be a strong validation of the whole forensics engine given the landing page already references Wirecard as a case study.

## G. Items From the User's Example List Not Present in SentinelIQ

The task description's example feature list included "Multi-Agent System," "Executive Coach," and "Simulations." A full search of `CLAUDE.md` and the codebase found **no trace of any of these** — they do not appear to be part of SentinelIQ's actual scope:

- **Multi-Agent System** — N/A. SentinelIQ uses a single sequential 7-stage pipeline (D6) with discrete forensic/AI modules, not a multi-agent architecture. Nothing resembling agent orchestration, message-passing between AI agents, or an agent framework exists.
- **Executive Coach** — N/A. No feature, route, component, or prompt file with this name or concept exists.
- **Simulations** — N/A. No simulation engine, scenario modeling, or "what-if" feature exists. (`scripts/backtest_*.py` are the closest concept — historical backtesting — but these are 0-byte placeholders, see F3.)

Flagging these explicitly so Opus knows they were checked for and are confirmed absent, not accidentally skipped.

---

# 3. Work Completed Since Takeover

This covers commits from `b3bf1fb3` (the commit that added `CLAUDE.md` — the explicit handover marker) through `866258cc` (the most recent commit, completed this session). Everything before `b3bf1fb3` is treated as the inherited Antigravity baseline (Section 1).

### 1. `b3bf1fb3` — docs: add CLAUDE.md project memory for Claude Code
- **Purpose:** Record the complete inherited state (architecture, design system, algorithms, decisions) as a persistent reference for all future Claude Code sessions.
- **Files modified:** `CLAUDE.md` (new, 540 lines).
- **Result:** Established the single source of truth this report is built against.
- **Fully completed:** Yes.

### 2. `10970221` — feat(frontend): wire login and register pages to real auth API
- **Purpose:** Replace mock login/register forms with real `POST /auth/login` / `POST /auth/register` calls.
- **Files modified:** `frontend/app/(auth)/login/page.tsx` (44 changed lines), `frontend/app/(auth)/register/page.tsx` (171 changed lines).
- **Result:** Both pages now call `lib/api/auth.ts` via `AuthContext`, persist the JWT, and redirect on success. Confirmed Completed by this session's audit.
- **Fully completed:** Yes (for these two pages — forgot-password/verify-email were *not* in scope and remain mock, A3/A4).

### 3. `e9885a12` — feat(frontend): wire dashboard and search to real API
- **Purpose:** Replace mock dashboard/search pages with real watchlist/company-search data.
- **Files modified:** `frontend/app/(app)/dashboard/page.tsx` (264 changed lines), `frontend/app/(app)/search/page.tsx` (158 changed lines), `frontend/components/layout/SearchBar.tsx` (141 changed lines), `frontend/components/shared/CompanyCard.tsx` (6 changed lines).
- **Result:** Dashboard now driven by `useWatchlist`; Search now driven by `searchCompanies` + debounced `SearchBar` with ticker-pattern fallback. Confirmed Completed by this session's audit.
- **Fully completed:** Yes.

### 4. `b75f0247` — fix(frontend): wire sidebar/bottom nav to real auth, remove dead routes
- **Purpose:** Make navigation reflect the real authenticated user and sign-out correctly; remove unused scaffold routes.
- **Files modified:** `frontend/components/layout/{Sidebar.tsx (30 changed), BottomTabBar.tsx (9 changed)}`; removed `frontend/app/(marketing)/about/page.tsx` and `frontend/app/api/[...proxy]/route.ts` (both were 0-byte stubs).
- **Result:** Sidebar shows real user email/initials and a working "Sign Out" (clears token, redirects to `/login`). Confirmed Completed by this session's audit.
- **Fully completed:** Yes.

### 5. `160fd635` — feat(frontend): build out watchlist page wired to real API
- **Purpose:** Build the previously-stubbed Watchlist page against real data.
- **Files modified:** `frontend/app/(app)/watchlist/page.tsx` (new, 150 lines), `frontend/components/shared/CompanyCard.tsx` (18 changed lines).
- **Result:** Full desktop table + mobile card list, loading/error/empty states, remove-with-confirmation. Confirmed Completed by this session's audit (full file read).
- **Fully completed:** Yes.

### 6. `7ac009c1` — fix(frontend): wire settings Account/Plan tabs to real user data
- **Purpose:** Make Settings' Account and Plan tabs reflect the real logged-in user.
- **Files modified:** `frontend/app/(app)/settings/page.tsx` (46 changed lines).
- **Result:** Account tab now shows real `full_name`/`email`; Plan tab shows real `tier`. Confirmed by this session's audit (full file read).
- **Fully completed:** Partially — the *display* wiring is done, but the tab's *action* buttons (Save Changes, Update Password, Delete Account, notification toggles, Upgrade to Pro) remain non-functional no-ops (see B4). This was evidently out of scope for this specific commit, which targeted only "Account/Plan tabs" data display.

### 7. `866258cc` — feat(frontend): wire company layout header to real data and live analysis status (this session)
- **Purpose:** Replace the hardcoded "Wirecard AG" header and a fully-fake 60-second analysis simulation with real `useCompanyData`/`useAnalysis` hooks and a real "Run Analysis" trigger.
- **Files modified:** `frontend/app/(app)/company/[ticker]/layout.tsx` (89 insertions, 74 deletions).
- **Result:** Header now shows real company name/ticker/sector/exchange/last-analyzed (with skeleton loading + error states); a real "Run Analysis" button triggers `POST /analysis/run` and polls status every 3s via `GET /analysis/{id}/status`; status bar shows live stage text, elapsed `mm:ss`, and a 3-second auto-dismissing completion/failure message. Verified via `next build` (successful) and live preview against `/company/AAPL` (no backend running — confirmed correct error-path behavior: "Failed to load company data," "Failed to start analysis.").
- **Fully completed:** Yes, for the layout/header scope. Explicitly *did not* touch the 5 child tab pages (B6–B10), which remain fully mock — that is the natural next phase (D2 in §6).

---

# 4. Pending Tasks

### Critical
*(build failures, runtime errors, broken features, security issues — these undermine the product's core promises or block deployment)*

1. **Narrative Consistency analysis is silently non-functional** (D4/D6#2). `analysis_worker.py` Stage 5 hardcodes a single mock statement, so `narrative_score` is *always* exactly `50.0` and contradiction-flag detection never fires for any company. One of the "five independent forensic analyses" central to the product's pitch does not actually run. **Needs an architectural decision** (see §7) before it can be fixed properly — not a one-line patch.
2. **Pipeline Stage 6 aborts the entire analysis on failure** (D6#1), violating CLAUDE.md's explicit "pipeline never aborts on a single-stage failure" rule. A transient Gemini/news error means the user gets `status: "failed"` and **zero report**, when a degraded report (with `news_score = 50.0`) should still be possible.
3. **Free-tier 5/month limit is structurally broken** (E3). `AnalysisResult` has no `user_id`; the current join-through-`WatchlistItem` logic both under- and over-counts. This is a monetization-critical bug — the freemium gate does not gate correctly.
4. **No Alembic migrations exist** (E4). `alembic/versions/` is empty; schema is created ad-hoc via `Base.metadata.create_all` on app startup. This blocks any clean deploy to Render Postgres and means future schema changes have no migration path.
5. **No route protection on authenticated pages** (C2). `/dashboard`, `/search`, `/watchlist`, `/settings`, `/company/[ticker]/*` are all reachable without a JWT — no redirect to `/login`. Security/UX gap for an institutional product.
6. **`frontend/Dockerfile` is missing** (F1), so `docker-compose up -d` — the README's documented quickstart — currently fails on the frontend service.

### High Priority
*(important unfinished features, architectural improvements)*

7. **All 5 company-analysis tabs (Overview, Financials, Governance, Narrative, Report) are 100% mock data** (B6–B10) — this is the entire visible product surface for the core USP (Integrity Score + AI report). Backend already computes and stores everything needed (`AnalysisResult.module_details`, `red_flags`, `Report.content`); only the frontend wiring is missing. This is **Phase D2+** in §6 — deferred pending this report's review, the natural highest-value next step.
8. **Error envelope inconsistency across API routes** (E3) — only `POST /analysis/run` returns the documented `{"error":{"code","message"}}`; everything else returns FastAPI's default `{"detail": "..."}`. Currently masked by frontend leniency, but a contract violation.
9. **Settings page action buttons are all no-ops** (B4): Save Changes, Update Password, Delete Account, notification toggles, Upgrade to Pro — no backend endpoints exist for any of these.
10. **8 backend "Planned" stub modules** with no implementation: `governance/{board_analysis,exec_turnover}.py`, `narrative/{sentiment_scorer,statement_extractor,transcript_parser}.py`, `services/{transcript_fetcher,sec_scraper}.py`, `tasks/data_refresh.py`. These look like the intended real data path for D3/D4 — needs an architectural call on whether to build or delete (§7).
11. **12 frontend component stubs are empty** (C5/C6/C7): `CashFlowChart`, `RevenueQualityChart`, `DebtTrendChart`, `RiskRadar`, `FraudScoreBanner`, `GovernanceChecklist`, `ReportSection`, `ErrorBoundary`, `LoadingState`, `Input`, `Modal`, `Tooltip` — currently the analysis-tab pages reimplement this logic inline instead.
12. **`getReport()` / `Report.content` markdown is never rendered** (B10) — no markdown-rendering dependency installed yet.
13. **ToastContext is fully built but has zero consumers** (C3) — no user-facing feedback for any action.

### Medium Priority
*(refactoring, UI improvements, performance optimizations)*

14. Forgot-password and verify-email pages are fully mock with leftover dev-only "state toggle" debug buttons (A3/A4) — must be removed/replaced before production.
15. Toast animation/timing deviates from CLAUDE.md spec (translateY both directions instead of translateX-enter; 4000ms not 3000ms; no max-3 cap) (C3).
16. Dead/duplicate backend files: `api/v1/deps.py` (0 bytes, dupe of real `api/deps.py`), `api/middleware/{auth.py,rate_limit.py}` (0 bytes, no `__init__.py`, unused) (E1).
17. Dead scoring stubs `risk_classifier.py` / `weights.py` (0 bytes, logic lives in `fraud_scorer.py`) (D2).
18. `passlib[bcrypt]` listed in CLAUDE.md but absent from `requirements.txt` (code uses raw `bcrypt`, which works) — doc/dependency drift (E1).
19. Minor import-ordering code smells in `yahoo_finance.py` / `news_aggregator.py` (E6) — works, but fragile.
20. No-op buttons: Overview's "Export PDF"/"Add to Watchlist" (B6), Report's "Share Report"/"Export PDF" (B10), Governance's dead `href="#"` source links (B8).
21. `deps.py`'s misleading unused `token_data`/`TokenData(email=user_id)` (E1) — clean up or comment accurately.
22. Possibly-unused `lucide-react` dependency in `frontend/package.json` (C7) — verify and remove if truly unused.

### Low Priority
*(nice-to-have features)*

23. `database/`, `docs/`, `scripts/` — 11 zero-byte placeholder files from the initial scaffold (F2/F3). Either populate (especially `docs/scoring-methodology.md`, which has real content to document — see Section 1) or remove.
24. `design-system` page (B12) — fine for now, but should be excluded from production nav/build before launch.
25. Documented 6-hour `company:{ticker}:analysis` cache TTL (CLAUDE.md) was not found implemented anywhere (E5) — confirm intentional or add it.
26. Cosmetic: redundant `${isReport ? 'mb-8' : 'mb-8'}` ternary in `company/[ticker]/layout.tsx` (B5); `not-found.tsx`'s `javascript:history.back()` link (B11).

---

# 5. Technical Debt

- **Dead code (≈20 files / locations):** `risk_classifier.py`, `weights.py`, `api/v1/deps.py`, `api/middleware/{auth,rate_limit}.py`, 8 backend "Planned" stub modules (D3/D4/E6/D6), 12 empty frontend component stubs (C5–C7), unused `ToastContext`, possibly-unused `lucide-react`. None of this is *harmful* today, but it inflates the codebase and makes "is this implemented?" a non-trivial question — exactly the gap this report exists to close.
- **Duplicate logic:** `financials/governance/narrative/report` pages each reimplement chart/list/section rendering inline because the corresponding shared components (`RevenueQualityChart`, `CashFlowChart`, `DebtTrendChart`, `GovernanceChecklist`, `ReportSection`, `RiskRadar`) are empty stubs. Once those are built, the inline copies need consolidating — otherwise there will be two parallel implementations to maintain.
- **Scalability:** the in-memory `cache.py` dict is process-local. Fine for a single Render free-tier instance (the documented $0/month plan), but would silently stop working as a shared cache if the backend ever runs >1 worker/replica — each instance would re-fetch from yfinance/Gemini/RSS independently, multiplying calls against rate-limited external APIs.
- **Coupling:** `analysis_worker.py` is a single ~200-line function directly instantiating and sequencing `ForensicsRunner`, `GovernanceScorer`, `ConsistencyEngine`, `FraudScorer`, `ReportGenerator`, plus raw DB writes for 4 different models across 7 stages. No stage-level abstraction or dependency injection — understanding or testing one stage requires reading the whole function. This is the file most in need of architectural attention if E7 (tests) is ever prioritized.
- **Missing documentation:** `docs/architecture.md`, `docs/scoring-methodology.md`, `docs/api-reference.md`, `docs/data-sources.md` are all empty. `CLAUDE.md` is the *only* current source of truth — appropriate for Claude Code, but a real gap for the scoring-methodology nuances this report surfaced (e.g., "financial = avg(revenue, debt)") which exist only in code, nowhere in prose.
- **Architectural weakness — no per-user analysis tracking:** `AnalysisResult` has no `user_id` and there's no `AnalysisRun`/usage-log table. The free-tier limit (E3#3) **cannot** be correctly implemented without a schema change. This is the single highest-leverage architectural decision pending (see §7).
- **Zero automated tests** (E7): every status in this report comes from static reading, not execution. Any future refactor — especially of `analysis_worker.py` — carries real regression risk with no safety net.
- **No CI/CD pipeline:** no GitHub Actions config found. The "$0/month" plan doesn't yet account for free CI (GitHub Actions has a generous free tier for public/private repos and would cost nothing).
- **Alembic configured but unused** (E4): the *first* real migration will need to be generated against a database whose schema was created by `create_all`, not by Alembic — requires either `alembic stamp head` against a baseline migration, or careful handling to avoid autogenerate trying to recreate everything from scratch.

---

# 6. Suggested Roadmap

Each phase below is scoped to be **small, independently completable, and safe to stop after** — per the standing instruction, only ONE phase will be executed per "Start new phase" command, in whatever order Opus approves (the numbering below is a suggested default order, not a hard dependency chain except where noted).

---

### Phase D2 — Wire Company Overview Tab to Real Analysis Data
- **Goal:** Replace B6's hardcoded `componentScores`/`redFlags`/`moduleData`/gauge score with real data from `useCompanyData`'s `analysis` (`AnalysisResultWithFlags`).
- **Scope:** `frontend/app/(app)/company/[ticker]/page.tsx` only. Map `analysis.{financial,cashflow,governance,earnings,narrative,news}_score` → the 5 `componentScores`; `analysis.red_flags` → `RedFlagItem`/`RedFlagTimeline`; `analysis.integrity_score` → `IntegrityScoreGauge`. Handle the "not yet analyzed" (`analysis === null`) state with an empty/CTA state.
- **Estimated effort:** Small (1 file, established hooks already exist).
- **Risks:** Low — read-only consumption of already-typed, already-returned data. Main risk is UI/empty-state polish (what does Overview look like for a never-analyzed company?).
- **Dependencies:** None — `useCompanyData` and all needed types already exist and were verified this session.

### Phase D3 — Wire Company Financials Tab + Build Missing Chart Components
- **Goal:** Replace B7's hardcoded charts with real data, and build the 3 empty chart components (`RevenueQualityChart`, `CashFlowChart`, `DebtTrendChart`) so the page consumes them instead of inline Chart.js.
- **Scope:** `frontend/app/(app)/company/[ticker]/financials/page.tsx` + 3 new chart components in `frontend/components/charts/`. Data source: `analysis.module_details.{revenue,cashflow,debt}`.
- **Estimated effort:** Medium (3 new components + 1 page rewrite).
- **Risks:** Medium — first real use of `module_details`'s nested point-arrays; need to handle short history (e.g., a company with only 1–2 periods of data) and empty arrays gracefully.
- **Dependencies:** None (independent of D2, but same pattern — doing D2 first is recommended for familiarity).

### Phase D4 — Wire Company Governance Tab + Build GovernanceChecklist
- **Goal:** Replace B8's hardcoded checklist/event-log with `analysis.red_flags` filtered by `flag_type === "governance"`, and build the empty `GovernanceChecklist` component.
- **Scope:** `frontend/app/(app)/company/[ticker]/governance/page.tsx` + `frontend/components/modules/GovernanceChecklist.tsx`.
- **Estimated effort:** Small–Medium.
- **Risks:** Low–Medium — the "checklist" (CFO Stability, Auditor Continuity, etc.) is a fixed set of indicators, but real `RedFlag` data is a variable-length list of events; needs a sensible mapping from "events that occurred" to "checklist pass/fail," which may need a small product decision (could be deferred to a follow-up "design the checklist mapping" mini-task within this phase).
- **Dependencies:** None.

### Phase D5 — Wire Company Narrative Tab (Frontend-Only, Within Current Backend Limits)
- **Goal:** Replace B9's hardcoded chart/comparisons with real `analysis.module_details.narrative.snapshots`, accepting that — until Critical #1 is fixed — there will usually be 0–1 snapshots and a flat `narrative_score = 50`.
- **Scope:** `frontend/app/(app)/company/[ticker]/narrative/page.tsx`. Design an honest "limited narrative data available" empty/partial state rather than faking a 12-quarter trend from 1 data point.
- **Estimated effort:** Small.
- **Risks:** Low technically, but **product-risk**: this phase will visibly expose Critical #1 (the page will look sparse/empty for every company) — recommend doing **Phase E1 (pipeline fixes) before or alongside D5** so this tab has something real to show. Flagged as a dependency below.
- **Dependencies:** Best done *after* Phase E1, otherwise the "fixed" page will look broken/empty.

### Phase D6 — Wire Company Report Tab + Markdown Rendering
- **Goal:** Replace B10's hardcoded prose with `getReport(ticker)` → `Report.content`, rendered as markdown; build the empty `ReportSection` component for layout structure.
- **Scope:** `frontend/app/(app)/company/[ticker]/report/page.tsx` + `frontend/components/modules/ReportSection.tsx`. Add a markdown-rendering dependency (e.g. `react-markdown`) — first new frontend dependency, call this out explicitly when executing.
- **Estimated effort:** Small–Medium (new dependency + markdown styling to match the design system's typography rules).
- **Risks:** Medium — markdown output from Gemini needs to render correctly within CLAUDE.md's strict typography rules (Inter body, IBM Plex Mono for numbers, no prohibited styles); may need custom renderers for headings/lists.
- **Dependencies:** None (independent), but more satisfying after D2/D5 since the report references the same scores/flags.

### Phase E1 — Fix Analysis Pipeline Stage 5 & Stage 6 (Backend)
- **Goal:** Fix Critical #1 (narrative input is hardcoded) and Critical #2 (Stage 6 aborts pipeline).
- **Scope:** `backend/app/tasks/analysis_worker.py` only, for Stage 6 (wrap in proper try/except with neutral fallback like other stages, matching the "never abort" rule). For Stage 5, the *minimal* fix is feeding it real multi-period input — **this needs an architectural decision first** (§7): is "real input" (a) recent news headlines split into multiple "statements" (cheap, uses existing `news_aggregator.fetch_news_text`), or (b) building out `transcript_fetcher.py`/`statement_extractor.py` for real earnings-call transcripts (bigger, new external dependency)? Recommend scoping this phase to **option (a)** — a same-day fix using existing data sources — and treating (b) as a separate future phase if Opus wants deeper narrative analysis.
- **Estimated effort:** Small (Stage 6) + Small–Medium (Stage 5, option a).
- **Risks:** Medium — touches the core pipeline; needs careful manual testing against a real ticker (no automated tests exist, E7).
- **Dependencies:** None, but should land **before D5** (see above).

### Phase E2 — Fix Free-Tier Limit Logic + Standardize Error Envelope (Backend)
- **Goal:** Fix Critical #3 (free-tier counting) and High #8 (error envelope consistency).
- **Scope:** Likely requires a small migration: add `user_id` to `AnalysisResult` (or a new lightweight `AnalysisRun(user_id, company_id, run_at)` log table) — **architectural decision needed** (§7) on which shape. Then fix `POST /analysis/run`'s count query, and wrap all route exception handlers in the documented `{"error":{"code","message"}}` shape (likely via a shared FastAPI exception handler rather than per-route changes).
- **Estimated effort:** Medium (schema decision + migration + multi-file route changes).
- **Risks:** Medium — schema change affects E3 (Alembic baseline); recommend sequencing this **before or together with E3** so the baseline migration includes the new column/table from the start.
- **Dependencies:** Architectural decision (§7); ideally sequenced with E3.

### Phase E3 — Generate Alembic Baseline Migration
- **Goal:** Fix Critical #4. Produce a working `alembic upgrade head` against a fresh database, matching the 8 (or 9, if E2's schema change lands first) current models.
- **Scope:** `backend/alembic/versions/` (new baseline revision file). Verify against both a fresh DB (clean `upgrade head`) and the current dev DB (via `alembic stamp head` if tables already exist from `create_all`). Optionally remove/guard the `create_all` call in `main.py`'s lifespan once Alembic is the source of truth.
- **Estimated effort:** Small–Medium.
- **Risks:** Medium — migration tooling mistakes can be hard to undo on a real database; do this against a disposable local Postgres first.
- **Dependencies:** Best done **after E2** if E2's schema change is approved, to avoid a second migration immediately after the first.

### Phase F1 — Wire Settings Page Actions (Frontend + small Backend additions)
- **Goal:** Fix High #9. Make "Save Changes" (name/email — email likely stays read-only per existing "contact support" copy), "Update Password," and notification toggles actually persist.
- **Scope:** `frontend/app/(app)/settings/page.tsx` + new backend endpoint(s) (e.g. `PATCH /auth/me`, `POST /auth/change-password`) + possibly a small `notification_prefs` JSON column on `User`. "Delete Account" and "Upgrade to Pro" can remain explicit stubs (e.g. a "Contact us" link) — full account deletion and billing are bigger scope and not implied as urgent by CLAUDE.md.
- **Estimated effort:** Medium (new endpoints + frontend forms + possible migration).
- **Risks:** Low–Medium. If a `notification_prefs` column is added, sequence with E3 (migrations).
- **Dependencies:** None strictly, but touches migrations — consider after E3.

### Phase F2 — Auth Route Guard + Toast Integration
- **Goal:** Fix Critical #5 (no route protection) and High #13 (unused toast system).
- **Scope:** Add a guard in `frontend/app/(app)/layout.tsx` (redirect to `/login` if `!isLoading && !user`). Wire `useToast()` into 3–5 key actions (watchlist add/remove success/error, "Run Analysis" started/failed, settings save) — and while there, fix C3's spec deviations (translateX enter, 3000ms, max-3 cap).
- **Estimated effort:** Small.
- **Risks:** Low. Mainly needs care around the loading-state flash (don't redirect before `useAuth`'s initial `getMe()` resolves).
- **Dependencies:** None.

### Phase G1 — Dead Code Cleanup Sweep
- **Goal:** Remove or resolve the dead-code items in §5: `risk_classifier.py`, `weights.py`, `api/v1/deps.py`, `api/middleware/*`, possibly-unused `lucide-react`, the 8 backend "Planned" stubs (delete *or* convert to tracked TODOs depending on §7's decision), redundant ternary in `layout.tsx`, `not-found.tsx` link pattern.
- **Scope:** Many small deletions/edits across both frontend and backend — no behavior change.
- **Estimated effort:** Small (mechanical, but touches many files — good "cooldown" phase between bigger ones).
- **Risks:** Very low — purely subtractive/cosmetic, easy to verify via `next build` + `uvicorn` startup.
- **Dependencies:** Should happen **after** D3/D4/E1's decisions on the 8 backend stubs (don't delete something Opus decides to build).

### Phase F3 — Auth Pages: Forgot Password & Verify Email
- **Goal:** Fix Medium #14. Either build real password-reset/email-verification flows (new backend endpoints + email-sending — likely out of scope for a $0/month plan unless using a free transactional-email tier) or explicitly redesign these pages as "not yet available" states and remove the dev-toggle debug buttons.
- **Scope:** `frontend/app/(auth)/{forgot-password,verify-email}/page.tsx` (+ backend, if building real flows).
- **Estimated effort:** Small (if redesigning as honest "not available" stubs) to Large (if building real email flows).
- **Risks:** Low for the small option; recommend the small option unless Opus flags email verification as a priority.
- **Dependencies:** None.

### Phase H1 — Deployment Dry-Run
- **Goal:** Fix Critical #6 (missing `frontend/Dockerfile`) and execute CLAUDE.md's deployment plan: Vercel (frontend) + Render (backend + Postgres), with `alembic upgrade head` run against the Render database.
- **Scope:** Add `frontend/Dockerfile` (or confirm Vercel doesn't need it and fix `docker-compose.yml`/README instead); first Render + Vercel deploys; verify all env vars; smoke-test `POST /analysis/run` end-to-end against a real ticker in production.
- **Estimated effort:** Medium (mostly configuration and waiting on free-tier build times, not code).
- **Risks:** Medium — first time touching real external infrastructure (shared/visible state). Should be done with explicit user confirmation at each external step (creating Render/Vercel projects, connecting GitHub, setting secrets) per this session's safety guidelines.
- **Dependencies:** **Must come after E3** (working migrations) — deploying with `create_all`-only schema management to a managed Postgres is the kind of thing that's hard to walk back later.

---

# 7. Instructions for Opus

**Current state of SentinelIQ:** The backend's analytical core is in much better shape than the frontend's presentation of it. All four quantitative forensic modules (Revenue Quality, Cash Flow Integrity, Earnings Quality, Debt Stress), the fraud scorer, the Gemini integration, the governance scorer, and the 7-stage pipeline orchestrator are implemented and closely match the CLAUDE.md spec — verified line-by-line this session. The platform layer (auth, models, 8/8 DB tables, API client, dashboard, search, watchlist, login/register, navigation) is real and wired. **The gap is almost entirely in the 5 company-analysis tabs** (Overview/Financials/Governance/Narrative/Report) — the actual screens that deliver the product's core promise (Integrity Score + AI report) are still 100% hardcoded mockups, even though the backend already computes and stores everything they need.

**Biggest risks, in order:**
1. **The Narrative module is a silent no-op** (Critical #1) — for every analysis, one of the "five independent forensic analyses" simply returns a flat neutral 50 with no real contradiction detection. This is a *correctness* risk to the product's core claim, not just a missing feature, and it's currently invisible (no error, no log warning beyond a code comment) — exactly the kind of thing that should be fixed before more UI is built on top of it (hence D5's dependency on E1).
2. **Free-tier enforcement is broken at the schema level** (Critical #3) — a monetization mechanic that doesn't work, requiring a schema decision (below) before it can be properly fixed.
3. **Zero migrations + zero tests** (Critical #4, E7) — the project is one schema change or one refactor away from a "works on my machine, breaks in prod" incident, with no automated way to catch it.
4. **Pipeline Stage 6 abort-on-failure** (Critical #2) — turns a transient AI/news hiccup into a total analysis failure with no report, undermining the "Gemini failure always returns 50.0 (neutral) — never crashes" guarantee CLAUDE.md promises for the *rest* of the pipeline.

**Most important next steps:** Phase D2 (Overview tab) is the recommended starting point — it's pure frontend, strictly additive/read-only against data the backend already returns, has zero migration/architecture dependencies, and directly demonstrates the core USP for the first time. Phase E1 (pipeline fixes) is the next-highest priority and should land before D5 (Narrative tab) so that tab isn't built against data that's known to always be flat/empty.

**Areas requiring architectural review before implementation phases proceed:**
1. **Per-user analysis tracking** (feeds E2 and the free-tier fix): should `AnalysisResult` gain a `user_id` column directly, or should there be a separate `AnalysisRun(user_id, company_id, analysis_id, run_at)` log table? This decision shapes the Alembic baseline (E3) and ideally should be made *once*, before E3 runs, rather than as a follow-up migration.
2. **Scope of the Narrative fix** (feeds E1 and D5): is the goal a same-day "use existing news headlines as multiple statements" fix (cheap, ships fast, still somewhat shallow), or should this be the trigger to build out the 5 currently-empty narrative/governance-adjacent stub modules (`transcript_fetcher.py`, `statement_extractor.py`, `sentiment_scorer.py`, `transcript_parser.py`, `sec_scraper.py`) for a deeper, transcript-based analysis? This is a scope/timeline call, not an implementation detail.
3. **ToastContext spec deviations** (C3): formally decide whether to bring the implementation in line with CLAUDE.md's exact animation spec (translateX enter, 3000ms, max-3 cap), or update CLAUDE.md to match the simpler existing implementation — small either way, but it's a "spec vs. code" conflict that should be resolved deliberately rather than by whichever gets touched first.
4. **Deployment shape** (H1): confirm the Vercel/Render plan from CLAUDE.md is still current before Phase H1, since it involves creating real external accounts/projects and will need explicit user confirmation at each step per this session's operating rules.

---

**End of report. Per the standing instruction: STOPPING here. Awaiting Opus's review and roadmap approval before any further code changes. On "Start new phase," I will re-read Opus's recommendations, execute exactly one approved phase from §6 (or as amended by Opus), produce a completion report, and stop again.**
