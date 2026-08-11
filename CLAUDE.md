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
> (rendered as `AI Model: gemini-2.5-flash` / `Source: Recent news coverage`, guarded on
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

> **Model hotfix (2026-06-18):** `gemini-2.0-flash` has zero free-tier quota on the
> project API key (confirmed 429 RESOURCE_EXHAUSTED). `DEFAULT_MODEL_ID` changed from
> `"gemini-2.0-flash"` to `"gemini-2.5-flash"` — confirmed working live (200 OK,
> text response received). CLAUDE.md tech stack table, Phase 3 amendment `model_id` pin,
> and Phase 11 Step 2 amendment UI display string updated to match.

> **Phase 22 amendment (2026-06-18):** Legal pages + methodology transparency layer.
> Four new public routes (no auth required, under `(marketing)` layout):
> - `frontend/app/(marketing)/terms/page.tsx` → `/terms` — Terms of Service (9 sections:
>   what it is, no investment advice, not an accusation, data sources, permitted use,
>   free-tier limits, liability, changes, contact). Owner must review wording before
>   opening to external users.
> - `frontend/app/(marketing)/privacy/page.tsx` → `/privacy` — Privacy Policy (9 sections:
>   overview, what's collected, what's not collected, third-party services, retention,
>   rights, security, changes, contact). No analytics, no tracking cookies, no payment data.
> - `frontend/app/(marketing)/methodology/page.tsx` → `/methodology` — Scoring Methodology
>   (7 sections: module table, weight vector, renormalization rule, confidence tiers,
>   all 4 forensic module formulas, AI modules, narrative exclusion rationale). All formulas
>   taken directly from the live implementation.
> - `frontend/app/(marketing)/data-sources/page.tsx` → `/data-sources` — Data Sources
>   (5 sections: yfinance/restated limitation with amber callout, RSS feeds, Gemini
>   grounding check, what's not used, summary table). Fulfills ADR-005 #7 ("Honest
>   Provenance") in the product UI.
>
> **Company layout disclaimer** (`frontend/app/(app)/company/[ticker]/layout.tsx`) now
> includes four links below the "Algorithmic screening signal only" text:
> "How scores are calculated" → `/methodology`, "Data sources" → `/data-sources`,
> "Terms" → `/terms`, "Privacy" → `/privacy`.
>
> **Footer** (`frontend/components/layout/Footer.tsx`): `#methodology` anchor updated to
> `/methodology` (now links to the real page instead of a landing-page anchor).
>
> **Analytics decision (Step 4):** no third-party analytics — confirmed by owner.
> Privacy Policy section 3 ("What we do not collect") reflects this accurately.

> **Phases 23-30 amendment (2026-06-20):** Honesty hardening, data-fetch resilience,
> report reliability, auth/prompt security, UI error states, and a technical-debt sweep
> (Phases 23-28) all landed as previously-described commits. Phase 29 (Smoke Test
> Harness) and Phase 30 (Deployment) are the ones worth recording in detail here, since
> both surfaced real defects no static check could have caught.
>
> **Phase 29 — first live run, two real bugs found and fixed.** Running
> `backend/scripts/smoke_test.py` against the real Neon DB + Gemini key for the first
> time (previously blocked on founder-supplied credentials) surfaced:
> 1. Every analysis got stuck in `running:Generating report...` forever. Root cause:
>    `analysis_worker.py`'s final commit block (`company.last_analyzed = datetime.now(
>    timezone.utc)`) assigned a tz-*aware* datetime into a naive `TIMESTAMP WITHOUT TIME
>    ZONE` column, outside the per-stage try/except, so the whole function aborted with
>    no fallback. A side effect of Phase 18's `datetime.utcnow()` migration — every other
>    call site got the companion `.replace(tzinfo=None)`, this one didn't. Fixed (both
>    this site and the `NarrativeSnapshot(fetched_at=...)` site below).
> 2. The narrative stage failed on every run: `_stage_narrative` spread the snapshot dict
>    from `ConsistencyEngine.analyze()` (`**s`) directly into `NarrativeSnapshot(...)`,
>    but Phase 14's grounding gate had added a `source_quote` key with no matching ORM
>    column. Caught by the per-stage isolation (fell back to narrative=50.0, contained),
>    but meant narrative never actually computed a real score. Fixed by constructing the
>    model from named fields instead of a blind spread; `source_quote` is still preserved
>    in `module_details.narrative.snapshots` (the JSON audit trail), just not passed to
>    the ORM model.
>
> A live UPST run after the fix surfaced a real, grounded governance flag (an actual
> securities-fraud lawsuit, verbatim-quoted source) — confirming Phase 14's grounding
> contract works correctly on a true positive, not just in tests.
>
> **Phase 30 — deployment was already live (since 2026-06-18, an earlier "Phase 20"
> session this doc never recorded), but had four real, live defects:**
> 1. Vercel's Deployment Protection ("Standard Protection") was blocking all public
>    access — the live frontend returned a bare 401 to every visitor. Owner disabled it
>    (Vercel → Settings → Deployment Protection → Require Log In → off).
> 2. `sentineliq-ai.vercel.app` — a manually-set `vercel alias`, not an auto-tracking
>    project Domain — had drifted to a pre-Phase-23 deployment and was serving a false
>    marketing claim ("earnings call transcripts") Phase 23 had already removed from the
>    real site. Re-pointed; documented the staleness mechanism in `docs/deployment.md`.
> 3. Render's `FRONTEND_URL` was set to that same fragile alias. Owner changed it to the
>    canonical auto-tracking domain (`sentineliq-sohanmandal1611-7709s-projects.vercel.app`),
>    permanently closing the staleness gap rather than requiring manual re-aliasing after
>    every future deploy.
> 4. `GET /health` had no `HEAD` handler. UptimeRobot's monitor (set up this session)
>    defaults to HEAD requests for HTTP(s) checks; every one got a bare 405, which
>    UptimeRobot correctly read as "down" — even though the service was healthy and
>    answering every real (GET) request the whole time. Fixed by stacking
>    `@router.head("/health")` on the same handler (`backend/app/api/health.py`) so HEAD
>    gets the identical real DB-connectivity check, just without a body (ASGI strips the
>    body for HEAD automatically). This was the actual cause of every "stuck-analysis
>    reaper"-style outage UptimeRobot reported this session — the backend never crashed.
>
> **Monitoring is now live**: UptimeRobot checks both `/health` (backend) and the
> frontend every 5 minutes. **`docs/deployment.md`** records the canonical URL, the
> Render service id, and the vanity-alias gotcha.

> **Phase 47 amendment (2026-06-24):** E-4, watchlist monitoring/alerting — closes the
> gap between "passive bookmark list" and the product's own "early warning" promise.
> Four steps, all landed together.
>
> **Step 1 — alert detector.** New `WatchlistAlert` model/table (`backend/app/models/
> watchlist_alert.py`, migration `0009`): `user_id`, `company_id`, `analysis_id`,
> `previous_score`/`new_score`, `previous_risk`/`new_risk`, `is_read`, `created_at`.
> `analysis_worker.py`'s `_generate_watchlist_alerts(ctx)` runs at the end of **every**
> completed analysis (user- or system-triggered) — own try/except, never threatens a
> pipeline that just finished. Trigger rule: **band-crossing only**, via
> `FraudScorer.classify_risk()` on the previous-vs-new `integrity_score` — a same-band
> point swing (e.g. 85→82, both "strong") does not alert. No prior completed analysis,
> or either score `None`, is "nothing to compare" and is silently skipped, not an error.
> One `WatchlistAlert` row is written per user watching the company (companies can have
> multiple watchers).
>
> **Step 2 — scheduled refresher (the "monitoring" half).** Step 1 alone only fires
> opportunistically, whenever *any* analysis happens to complete. `backend/app/tasks/
> watchlist_refresher.py`'s `watchlist_refresher_loop()` (started in `main.py`'s
> `lifespan`, same pattern as the reaper) is what makes this autonomous:
> `find_due_companies()` selects companies that are on **at least one** user's watchlist
> and are either never-analyzed or past `STALE_AFTER_HOURS` (24) old, capped at
> `MAX_REFRESHES_PER_TICK` (3) per tick (`REFRESH_INTERVAL_SECONDS` = 3600) so a large
> watchlist backlog drains gradually instead of bursting yfinance/Gemini all at once —
> deliberately conservative given the live yfinance rate-limiting already observed
> (Phase 43) and the shared `GEMINI_DAILY_BUDGET=200`/day ceiling this loop draws from
> like any other caller. `trigger_refresh()` creates a `pending` `AnalysisResult` and
> calls `run_full_analysis()` directly — **no `AnalysisRun` row is logged**; that table
> meters user-initiated free-tier quota (ADR-007/013), and a scheduled tick has no
> acting user.
>
> **Step 3 — API.** `GET /alerts` returns `{alerts, unread_count}` for the current user,
> newest first, capped at `ALERTS_LIMIT` (50); `unread_count` is a **separate**,
> unscoped-by-limit query — a nav badge must reflect every unread alert, not just the
> page returned by the capped list. `POST /alerts/{id}/read` 404s if the alert is
> missing **or owned by a different user** (the real security boundary — ownership, not
> just existence).
>
> **Step 4 — frontend.** New `/alerts` page (`frontend/app/(app)/alerts/page.tsx`),
> `useAlerts` hook, Sidebar nav entry rendered as `Alerts (N)` when `N > 0` (plain text
> in parens, same convention as the watchlist page's `Compare Selected (N)` — no icons,
> design rule #4/#9). Clicking through to the company page marks the alert read as a
> side effect. **Not added to `BottomTabBar.tsx`** (mobile bottom nav) — its 4 slots
> (Home/Search/Watchlist/Settings) were a deliberate, already-settled mobile layout
> decision; mobile users can still reach `/alerts` via the URL, just not from the tab
> bar. A 5th-slot decision wasn't in this phase's scope and is left for the owner.

> **Phase 48 amendment (2026-06-24):** A-1, stop sharing one long-lived DB session
> across the whole pipeline. `run_full_analysis`'s 7-stage loop, plus Phase 47's new
> post-loop alert step, had all been threading a single `AsyncSession` through every
> stage, each calling `commit()`/`rollback()` on it — and `rollback()` expires every
> object in that session's identity map, including the shared `company`/`analysis` ORM
> objects. A later stage reading either after an earlier stage's rollback would hit an
> expired attribute, which `AsyncSession` (unlike sync `Session`) cannot silently
> lazy-reload — a latent hazard, not reproduced live (no local Postgres connection to
> observe it against), but traced precisely through the code and SQLAlchemy's documented
> rollback semantics.
>
> **Fix:** `run_full_analysis`'s loop now opens a fresh `AsyncSessionLocal()` per stage
> iteration, re-fetching `company`/`analysis` fresh each time, before calling
> `stage.fn(ctx)` — `StageContext.session`/`company`/`analysis` are reassigned every
> iteration rather than fixed once for the whole run (the dataclass fields are now
> `Optional`, default `None`, for the brief window before the loop's first iteration
> sets them). **None of the 7 `_stage_*` function bodies changed** — the hazard lived in
> the orchestrator sharing one session, not in any stage's own logic, so the fix is
> entirely in the loop. The final status/`last_analyzed` write and
> `_generate_watchlist_alerts` (now taking plain `analysis_id`/`company_id` instead of a
> `StageContext`) each get their own fresh session too, for the same reason.
>
> Verified via the existing integration suite (output-unchanged across all prior
> scenarios) plus one new test purpose-built for this property:
> `test_stage_failure_does_not_leak_session_into_next_stage` runs a 2-stage list where
> stage 1 raises unconditionally (no internal try/except, simulating a bug that escapes
> a stage's own handling) and confirms stage 2 still receives a distinct, valid
> session/company/analysis.

> **Phase 50 amendment (2026-06-24):** E-5, data retention & incident response policy
> (documentation only, no code). **`docs/data-retention-incident-response.md`** is new —
> a table-by-table retention statement (confirmed by inspection: the only `DELETE` in the
> entire backend is the user-initiated watchlist-removal endpoint; every other table
> grows indefinitely), the actual manual process behind the Privacy Policy's existing
> "30 days" account-deletion promise (no self-service tool exists; scoped to
> user-identifying tables only, never the company-scoped `analysis_results`/`red_flags`/
> `reports`/`financial_data`), an incident-response table for the six realistic failure
> modes this system is actually built to handle, and a plainly-stated vendor
> concentration section (yfinance is still primary, not replaced, by the EDGAR as-filed
> hedge; Gemini has no failover provider at all). Written for what this project actually
> is — a single-owner, pre-revenue project — not as an enterprise SOC-2 document
> claiming a posture it doesn't have.

> **Phase 51 amendment (2026-06-24):** U-4, accessibility pass on the custom gauge/
> bars/charts. Audited the actual current state first rather than trust the backlog's
> "never audited" framing — `IntegrityGauge` already had solid ARIA (`role="meter"`,
> `aria-valuetext`, respects `prefers-reduced-motion`) and needed no change. Three real
> gaps found and fixed, all purely additive (no visible design change):
>
> 1. **`ChartFrame`** (the shared wrapper under all 5 Chart.js components —
>    `CashFlowChart`, `DebtTrendChart`, `IntegrityScoreTrendChart`, `NarrativeTrendChart`,
>    `RevenueQualityChart`) rendered a bare `<canvas>` with zero accessible alternative.
>    New optional `accessibleTable` prop renders a visually-hidden (`sr-only`) `<table>`
>    alongside the canvas — one column per dataset (`ChartFrameAccessibleSeries[]`,
>    generalized for both 1-dataset and 2-dataset charts), reusing each chart's own
>    existing tick-formatter function rather than introducing new formatting logic. The
>    visual canvas wrapper gets `aria-hidden="true"` whenever a table is supplied.
> 2. **`ModuleScoreCard`**'s risk tier was conveyed only via the card's left-border
>    color, with no text equivalent anywhere (unlike `ModuleScoreBadge` in the same
>    file, which already renders a `Badge` with the risk label). Fixed with a single
>    `sr-only` span stating the risk label immediately before the score number — no
>    visible change.
> 3. **`RedFlagTimeline`** (custom HTML, not Chart.js) had real text content but no
>    semantic list structure, and severity was conveyed only by dot/tick color with no
>    text anywhere. The events container is now a `<ul role="list">` (the explicit
>    `role` is defensive — some browser/AT combinations drop the implicit list
>    semantics once `list-style: none` is applied via CSS); each event is an `<li>`
>    carrying one `aria-label` summarizing severity + label + year as a single
>    coherent announcement, with the inner decorative pieces marked `aria-hidden` to
>    avoid double-announcing the same text — the same "labeled wrapper + hidden
>    decorative children" pattern `IntegrityGauge` already used.
>
> No code changes beyond these three components; verification was `tsc`/`next build`
> plus careful manual review of every edited file — all three live behind the app's
> auth wall with no mock-data fixture available locally, so the actual rendered
> accessibility tree could not be checked live in this environment (noted explicitly
> rather than implied otherwise).

> **Phase 52 amendment (2026-06-25):** U-5 Step 1, frontend test infrastructure —
> previously zero test files, zero test tooling, confirmed by inspection before
> building anything. Chose **Vitest + React Testing Library + jsdom** over Jest: no
> existing investment in either, and Vitest is faster (esbuild-based) with better
> Next.js 15/ESM support for a clean setup. `frontend/vitest.config.ts` mirrors
> `tsconfig.json`'s `@/*` path alias exactly; `frontend/vitest.setup.ts` wires up
> `@testing-library/jest-dom` matchers. New `npm test` (`vitest run`, used in CI) and
> `npm run test:watch` scripts.
>
> First real suite (not a placeholder): `frontend/lib/utils/formatDate.test.ts`,
> chosen because `formatDate`/`formatRelativeTime` have a **documented bug history**
> (Phase 28's naive-UTC-timestamp misparse fix) — testing it locks the fix against
> silent regression. The regression test pins `process.env.TZ` to a fixed, non-DST,
> clearly-offset zone (`"Etc/GMT+5"`) directly in the test file (the only way to
> control timezone identically on Windows-local dev and Linux CI) — pinning to plain
> UTC would make the original bug invisible, since the offset would be zero.
> `formatRelativeTime`'s tests use `vi.setSystemTime()` to pin "now," avoiding
> real-clock flakiness on minute/hour/day boundary assertions. 17/17 passing.
>
> `.github/workflows/ci.yml` gained a new `frontend-test` job, deliberately separate
> from the existing `test` job — branch protection requires `test` by name, and that
> job must never gain a second name it could start depending on. No `paths:` filter,
> same rationale the existing job already documents for itself.
>
> **Disclosed, not silently absorbed:** `npm install` surfaced `npm audit` findings
> (3 moderate, 1 high, 1 critical) — traced to a single root cause, `esbuild`'s known
> dev-server-only advisory (GHSA-67mh-4wv8-2f99: a local website can read responses
> from a running dev server), propagating through Vite into Vitest's dependency tree.
> The only fix path is a major `vitest` v2→v4 bump (`isSemVerMajor: true`) with no
> tests yet validated against the new major version — deliberately not forced into the
> very first commit that introduces testing at all. Real-world exposure here is
> low: this is a dev-only dependency never shipped in `next build`'s output, and the
> exploitable surface (`vitest`'s interactive watch mode) is never used in CI (which
> always runs the one-shot `vitest run`). Revisit the v4 upgrade as its own deliberate
> step once there's more suite coverage to validate against it.
>
> **Follow-up (2026-06-25):** Dependabot opened the exact fix as two duplicate PRs
> (`@vitejs/plugin-react` 4→6, `vitest` 2→4). Tested directly rather than merged
> blind: checked out the PR branch, ran the full suite (17/17 still passing — same
> count, same assertions), `tsc --noEmit`, `next build`, and `next lint`, all clean;
> `npm audit` dropped to 0 vulnerabilities. Merged the verified one, closed the
> duplicate with an explanation rather than leaving a stale, never-actionable PR
> open.

> **Phase 53 amendment (2026-06-25):** E-2 free scaffolding — real token revocation.
> `POST /auth/logout` previously only cleared the cookie client-side; it decoded the
> JWT solely for audit logging and never invalidated it server-side, so a
> copied/leaked token kept working for its full remaining lifetime even after the
> legitimate user "logged out." `create_access_token` now embeds a `jti` claim
> (`backend/app/api/v1/routes/auth.py`); `logout` inserts it into a new
> `revoked_tokens` table (`backend/app/models/revoked_token.py`, migration `0010`)
> via `INSERT ... ON CONFLICT DO NOTHING` (jti is the primary key, so a repeated
> logout call with the same token stays idempotent — the existing contract
> `logout` already had); `get_current_user` (`backend/app/api/deps.py`) now checks
> the blocklist before trusting an otherwise-valid signature/exp, raising the same
> 401 used for every other auth failure.
>
> **Bounded without a new background loop.** `expires_at` mirrors the revoked
> token's own `exp` — once that passes, `jose.jwt.decode` already rejects the
> token regardless of the blocklist, so a row only needs to outlive the token's
> natural lifetime. `logout` opportunistically deletes any already-expired
> blocklist rows in the same transaction as every new revocation, rather than
> adding a third always-on asyncio loop alongside the reaper and watchlist
> refresher.
>
> **Scope explicitly excludes refresh tokens** — that's a separate, larger change
> (new endpoint, new cookie strategy, frontend silent-refresh logic) than closing
> the "logout doesn't actually revoke" gap. Not scheduled; revisit only if the
> 60-minute access-token lifetime itself becomes a problem.

> **Phase 54 amendment (2026-06-30):** S-3 — gate analysis-output read endpoints
> behind auth. An architecture-review pass found that every endpoint revealing
> analysis value was fully public while only `POST /analysis/run` (the
> compute-triggering, quota-metered endpoint) was gated — anyone could read a full
> fraud-analysis report for free; only generating a *new* one cost anything. A
> related issue: `GET /company/{ticker}` performed an unauthenticated database
> write (creates a `Company` row via a live `yfinance` call on cache miss) — a real
> cost vector given the project's hard $7-8/month budget ceiling. The owner was
> asked directly (require login / keep public / public-but-rate-limited) and chose
> **require login**.
>
> Seven routes now require `current_user: User = Depends(get_current_user)`,
> replicating the exact pattern `POST /analysis/run` already used — no new auth
> logic, purely wiring the existing dependency onto more routes:
> `GET /analysis/compare`, `GET /analysis/{id}/status`,
> `GET /analysis/company/{ticker}`, `GET /analysis/company/{ticker}/history`,
> `GET /report/company/{ticker}`, `GET /company/{ticker}`, `GET /company/search`.
> `GET /health` stays deliberately public (Render's spin-down probe); no
> CSV/export endpoints exist anywhere in the backend, so this is the complete
> scope. See "API Routes Reference" below for the per-route table.
>
> **No frontend changes** — `frontend/lib/api/client.ts`'s shared `apiRequest()`
> already sets `credentials: "include"` on every fetch, so the `sentineliq_token`
> httpOnly cookie was already sent on every one of these calls before this phase;
> gating the backend only closes the gap where someone bypasses the frontend
> entirely and hits the routes directly with no credentials. Background tasks
> (`watchlist_refresher.py`, `analysis_worker.py`, `reaper.py`) are unaffected —
> none make HTTP calls to these routes, all operate on `AsyncSession`/ORM directly.
>
> New `backend/tests/integration/test_protected_routes_require_auth.py` exercises
> the real ASGI app via `TestClient` (parametrized over all 7 routes, asserting
> 401), since the existing per-route unit tests only prove the Python function
> works when called directly, not that the dependency is wired onto the live
> route. Confirmed via this test that a 401 from `get_current_user` is still
> wrapped by the global error envelope (Phase 5c) — `{"error": {"code":
> "UNAUTHORIZED", "message": "Could not validate credentials"}}` — not a bare
> `detail` string, regardless of which route triggers it.

> **Phase 59 amendment (2026-08-04):** idle-compute reduction — the Neon free tier's
> 100 CU-hour monthly allowance was fully exhausted (110.33 CU-hrs, compute cut off).
> Root cause was **not** analysis traffic: the backend touched the database more often
> than Neon's 5-minute scale-to-zero window, continuously, so compute **never idled** —
> 0.25 CU × 730 h ≈ 182 CU-hrs/month against a 100 CU-hr allowance, exhausted around
> day 16. Two independent causes, each sufficient on its own (fixing only one would have
> saved nothing):
> 1. `reaper.py`'s `reaper_loop` ran a DB `UPDATE` every **120 s**.
> 2. `GET/HEAD /health` ran `SELECT 1` on **every** probe — and it is polled by
>    UptimeRobot (~5 min, Phase 30) *and* on Render's own health-check schedule, which
>    cannot be disabled.
>
> **`/health` is now a shallow liveness probe that makes no database call at all**,
> returning `{"status": "ok", "reaper": {...}}`. The `"database"` key was deliberately
> dropped rather than left reporting a check no longer performed. The deep check moved
> to a new **`GET/HEAD /health/db`** → `{"status": "ok", "database": "ok"}`, preserving
> the identical 503 `SERVICE_UNAVAILABLE` error envelope; it is for manual/occasional
> diagnosis and must never be used as a polling target. Both routes keep the stacked
> `@router.get` + `@router.head` decorators — HEAD is load-bearing (Phase 30's outage
> was a bare 405 to UptimeRobot's HEAD probes) — and both stay unauthenticated.
>
> `REAPER_INTERVAL_SECONDS` 120 → **1800** (30 min): the old cadence bought nothing,
> since `STUCK_ANALYSIS_THRESHOLD_MINUTES` (10) means a row isn't reapable for 10
> minutes anyway. Worst-case detection becomes ~40 min; the immediate startup pass is
> unchanged, so restart recovery is unaffected. `REFRESH_INTERVAL_SECONDS` 3600 →
> **21600** (6 h) — 4 ticks/day × `MAX_REFRESHES_PER_TICK` (3) still comfortably serves
> the unchanged 24-hour `STALE_AFTER_HOURS` target.
>
> Locked by `backend/tests/unit/test_health_endpoint.py`, which asserts `/health` takes
> no `db` parameter and — via `TestClient` with a `get_db` override that raises — that
> `/health` still returns 200 when the database is entirely unavailable. That test fails
> the moment anyone re-adds a DB call to `/health`, which is precisely how this outage
> happened. Verified live: `/health` registers with **0** dependencies, `/health/db`
> with 1.

> **Phase 60 amendment (2026-08-04):** safe mode + on-demand reaping — finishes what
> Phase 59 started. Phase 59 left ~30 CU-hrs/month of pure *idle* reaper polling; this
> removes it and adds an emergency kill switch for when the DB quota is exhausted.
>
> **On-demand reaping.** `reaper.py` gains `maybe_reap_stuck_analyses(session)`, called
> from `GET /analysis/{id}/status` — the one endpoint where a stuck row is actually
> observed. The insight: **a stuck analysis only matters when someone looks at it**, and
> doing the work during real traffic is free because the database is already awake, whereas
> timer polling wakes it purely to find nothing. Guarded by an in-process throttle,
> `REAP_MIN_INTERVAL_SECONDS = 60` — load-bearing, because the frontend polls that endpoint
> every 3 seconds and an unthrottled reap would issue an `UPDATE` per poll. The call is
> wrapped in `try/except` and logs a warning on failure: an opportunistic optimisation
> riding on a read path must never be able to break the read (covered by
> `test_get_analysis_status_survives_a_failing_ondemand_reap`). It runs **before** the row
> is fetched, so the status served already reflects the reap. A successful on-demand reap
> also updates `_last_run_at`/`_last_reaped_count` — with the timer loop disabled those are
> the only updates those fields would get, and `/health` would otherwise report the reaper
> permanently stale.
>
> **Safe mode.** `ENABLE_REAPER_LOOP` and `ENABLE_WATCHLIST_REFRESHER` (both
> `bool = True` in `config.py`, env-overridable) gate `asyncio.create_task` in `main.py`'s
> `lifespan`, which now collects started tasks in a list and cancels only those. Setting
> both to `false` yields **zero background database traffic** while the API stays fully
> functional — the intended posture when the Neon compute quota is exhausted or near its
> limit. Each disabled loop logs a startup warning naming the flag, so a silent loop is
> never a mystery. `get_reaper_status()` gains `loop_enabled` and forces `stale = False`
> when the loop is disabled: a deliberately-disabled loop is not "stale," and reporting it
> as such would be a permanent false alarm on `/health` in safe mode. Both flags default
> to `True`, so existing deployments are unchanged — safe mode is opt-in.
>
> **Test-isolation note worth remembering.** Wiring the reap into the status route broke
> `test_health_endpoint.py` in full-suite runs only (it passed in isolation).
> `test_analysis_status_endpoint.py` passes an `AsyncMock` session, so the real reap stored
> `session.execute(...).rowcount` — a `Mock`, not an `int` — into the module-level
> `_last_reaped_count`, which then leaked for the rest of the session and made `/health`
> unserialisable. Fixed with an autouse fixture neutralising the reap in those tests
> (they cover stage-text mapping, not reaping). The lesson: module-level mutable state
> written from a request path is a test-pollution vector, and order-dependent failures
> hide from single-file runs.

> **Phase 61 amendment (2026-08-04):** the financial forensics were silently dead — and
> had been for the entire recorded history of the database. Found by finally running the
> core loop end-to-end (`backend/scripts/smoke_test.py AAPL`) rather than trusting the
> test suite.
>
> **Symptom.** Every analysis returned `financial`, `cashflow`, and `earnings` as `None`
> ("stage failed"), leaving `integrity_score` computed from only `governance` + `news` —
> **2 of 5 modules, 27.8% of the weight vector** (the three dead modules carry
> 0.3333 + 0.2222 + 0.1667 = **0.7222**). Confirmed against stored data: **59 of 63**
> completed analyses have `financial_score IS NULL` and `confidence = "low"` — 23/23 in
> June 2026, 36/36 in July, and every August run before this fix.
>
> **Root cause.** `yfinance==0.2.40` (pinned mid-2024) can no longer parse Yahoo's current
> API. Raw calls fail with `AttributeError: 'str' object has no attribute 'name'` on
> `.info`, return an empty `(0, 0)` frame for `.income_stmt`, and report **AAPL** as
> "possibly delisted". This is a library-vs-API incompatibility, **not** the yfinance
> rate-limiting seen in Phase 43 — there is no 429 involved. `yahoo_finance.py`'s own
> error handling correctly converted the failure into `FINANCIAL_DATA_UNAVAILABLE`, and
> `analysis_worker.py`'s per-stage isolation correctly degraded to `None` scores, so
> nothing ever crashed. **The pipeline was working exactly as designed; the data source
> underneath it was not.**
>
> **Fix.** `yfinance==0.2.40` → `yfinance==1.5.2`. **No code change was required** —
> `yahoo_finance.py` works unchanged against the new major version (verified live:
> `fetch_company_info` and `fetch_financials` both succeed, returning 5 real periods).
> `pip check` is clean and the pinned `numpy`/`pandas` versions are unaffected.
>
> **Verified impact** on a real AAPL run, before → after:
> `financial` FAILED → 100.0, `cashflow` FAILED → 100.0, `earnings` FAILED → 75.0,
> `integrity_score` 80.3 → **90.4**, `confidence` **low → high**. Full suite: 280 passed.
>
> **Why no test caught this, and what that means.** Every backend test mocks yfinance —
> correctly, since CI must stay free and offline — so no unit or integration test can
> detect that the live data source has broken. This class of failure is only observable by
> running the real loop. The honesty architecture (ADR-005's "absence ≠ neutral"
> renormalization plus the confidence tier) meant the product never *lied* about it: every
> affected analysis was correctly labelled `low` confidence. It quietly under-delivered
> instead of silently fabricating — which is the intended failure mode, but it also meant
> nobody noticed for months. **Treat `smoke_test.py` as a periodic obligation, not a
> one-off**; a stored `confidence` distribution skewed to `low` is the cheapest existing
> signal that an upstream feed has died.
>
> **Data note.** The 59 pre-fix analyses are not wrong, but they are *thin* — scores built
> on governance + news only. They should be re-run before any of them is treated as a real
> assessment.

> **Phase 62 amendment (2026-08-11):** an invisible BOM in a Vercel env var broke every
> API call on the deployed site. Registration and login failed with the generic message
> **"Request failed"**, and **no request ever reached the backend**.
>
> **Root cause.** `NEXT_PUBLIC_API_URL` in Vercel had a leading UTF-8 BOM (U+FEFF) —
> the signature of pasting a value copied out of a UTF-8-with-BOM file (PowerShell
> `Out-File` and Notepad both produce these). The deployed bundle contained
> `"".concat("﻿https://sentineliq-y27m.onrender.com", "/api/v1")`. Because that
> string does not begin with a scheme, `fetch()` treated the URL as **relative** and
> resolved it against the frontend origin — the observed request was
> `https://<frontend>/%EF%BB%BFhttps:/sentineliq-y27m.onrender.com/api/v1/auth/register`
> → Vercel's HTML **404**.
>
> **Why the symptom was so uninformative.** `client.ts` builds its thrown message as
> `message || response.statusText || "Request failed"`. The HTML 404 body isn't JSON, so
> no message could be extracted; `statusText` is **always `""` on HTTP/2** (which both
> Vercel and Render serve). Both fell through to the literal fallback. The register page
> compounds it: it shows `err.message` for an `ApiError` but
> `"Something went wrong. Please try again."` for a thrown network/CORS error — so the
> exact wording was the only clue distinguishing "a real HTTP error arrived with an
> unparseable body" from "the request never completed."
>
> **Fix.** `resolveApiBaseUrl()` in `frontend/lib/api/client.ts` — a pure, exported,
> unit-tested helper that strips BOM/zero-width characters (U+FEFF, U+200B/C/D),
> whitespace, surrounding quotes, and trailing slashes, falling back to
> `http://localhost:8000` when empty. It is deliberately pure (the env value is passed in
> rather than read inside) so the exact production input is testable, and it
> `console.error`s — rather than throws — when the cleaned value still isn't absolute, since
> a module-load throw would white-screen the entire app. Locked by
> `frontend/lib/api/client.test.ts`, whose BOM case reproduces the production value.
>
> **Diagnostic lesson.** This was invisible to every static check: the value *looked*
> correct in the Vercel dashboard, the bundle *did* contain the right hostname (my own
> grep for `onrender.com` found it and I wrongly cleared the config), and a hand-typed
> `fetch()` to the same URL worked perfectly. Only reading the **actual request URL** in
> the browser's network log exposed the `%EF%BB%BF` prefix. When a frontend reports a
> generic failure, read the real outbound request before trusting configuration.
>
> **Two unrelated findings surfaced during this investigation, NOT fixed here:**
> 1. `POST /auth/register` enforces **no server-side minimum password length** — a
>    1-character password was accepted with `200`. The 8-character rule exists only in the
>    frontend, so it is trivially bypassed by calling the API directly.
> 2. The `rate_limit("register", 5)` dependency **did not trigger** across 7 rapid requests
>    from one browser. Consistent with the concern already documented in `client_ip()`:
>    the rightmost `X-Forwarded-For` entry may vary per request behind Render/Cloudflare,
>    scattering one caller across many buckets and making the limiter ineffective.

> **Phase 63 amendment (2026-08-11):** closes the two auth defects recorded in the Phase 62
> amendment. Both were found empirically against the **live** backend, not by inspection.
>
> **Server-side password policy.** `POST /auth/register` accepted a **one-character**
> password and returned `200`, creating a real user — the 8-character rule existed only in
> the frontend form and was bypassed by any direct API call. `UserCreate` now enforces it
> in the schema via a Pydantic v2 `field_validator`: `MIN_PASSWORD_LENGTH = 8` and
> `MAX_PASSWORD_BYTES = 72`. The upper bound is not cosmetic — this project calls `bcrypt`
> directly (not passlib), and modern bcrypt **raises** on inputs over 72 bytes, so a long
> password was an unhandled **500**; it is now a clean 422. The cap is measured in **bytes,
> not characters**, because multi-byte UTF-8 (emoji, accents) reaches it sooner than a
> character count suggests. Length only — no complexity rules, matching what the UI
> promises. Validation failures flow through the existing global handler, so the route
> body is unchanged.
>
> **Rate limiter now identifies the real caller.** `rate_limit("register", 5)` did **not**
> trigger across 7 rapid requests from one browser. Root cause: `client_ip()` used the
> rightmost `X-Forwarded-For` entry, which is not stable per client on this deployment.
> Confirmed live that **Cloudflare fronts Render** (`Server: cloudflare`, `CF-RAY`,
> `cf-cache-status`, alongside Render's `rndr-id`), so the resolution order is now
> **`CF-Connecting-IP` → `True-Client-IP` → rightmost `X-Forwarded-For` → peer address**.
> Cloudflare sets and *overwrites* `CF-Connecting-IP` on every request, so it is both
> stable per client and un-spoofable — unlike the leftmost XFF entry, which remains
> untrusted for the reasons H-2 already documented. Present-but-empty headers fall through
> to the next source, and the existing log line now records which source was used.
>
> Locked by a regression test asserting that two requests with the **same**
> `CF-Connecting-IP` but **different** `X-Forwarded-For` values share one bucket — the
> exact production failure, where a single caller was scattered across buckets and never
> limited. Backend suite: 289 passed.

> **Phase 64 amendment (2026-08-11):** two live-visible defects, both found by driving the
> deployed app in a browser and cross-checking the production database — not by reading
> code or running tests.
>
> **The narrative module compared a date with itself.** The live Narrative tab printed
> *"Significant tone shift between 2026-08-10 and 2026-08-10 (Score diff: 0.85)"* and a
> red **15/100 SEVERE RISK** card. `ConsistencyEngine.analyze` sorted snapshots by `period`
> and compared every consecutive pair without checking the periods actually differed — so
> two journalists' same-day headlines registered as a management narrative contradiction.
> The loop now skips same-period pairs; when every pair is same-period the existing
> `if not contradiction_scores` path returns the neutral `50.0` instead of a fabricated
> severe score. Thresholds, the score formula, and the grounding gate are unchanged.
> This is a display-only correction — narrative remains zero-weighted (ADR-006), so no
> Integrity Score changes.
>
> **The trend chart silently omitted the analysis you just ran.** Confirmed live: with the
> database already holding a `2026-08-11` run, the chart's newest point was `2026-08-09`;
> a manual reload made it appear. `useAnalysisHistory` fetched inside a `useEffect` keyed
> only on `[ticker]`, and completing an analysis does not change the ticker. The hook now
> takes an optional `refreshKey` (the Overview page passes `analysis?.id`), so a
> newly-completed analysis — which has a new id — retriggers the fetch.
>
> **The pattern worth internalising.** Phases 61, 62 and 64 were all found the same way:
> by exercising the real product, never by the test suite. The suite mocks every external
> and every one of these bugs lived precisely in what mocks replace — a dead upstream feed,
> an env var, and real-world data shape (headlines clustering on one day). **Static green
> is not evidence the product works.** The cheapest standing signal remains the stored
> `confidence` distribution: a run of `low` means an upstream module is silently returning
> `None`.

> **Phase 65 amendment (2026-08-11):** signal-integrity monitoring — makes a silently
> degrading pipeline observable. This is the architectural answer to Phase 61: the three
> financial forensic modules were dead for **two months** (59 of 63 stored analyses had
> `financial_score IS NULL` and `confidence = "low"`) while the product kept publishing
> scores about real, named companies, and **nothing surfaced it**.
>
> **Why nothing caught it.** Every backend test mocks the external feeds — correctly, since
> CI must stay free and offline — so no test *can* detect that a live source has died. The
> pipeline's own resilience then hid the damage: per-stage isolation degraded failed modules
> to `None` and ADR-005's renormalization honestly re-weighted the survivors. The product
> never lied; it correctly labelled every affected run `low` confidence. That signal existed
> the whole time, unread in the database.
>
> **`backend/app/services/pipeline_health.py`** turns it into an observable one.
> `record_analysis_outcome(scores, confidence)` is called from `_stage_score_persist`
> **after** its commit succeeds, inside its own try/except so an observability bug can never
> fail an analysis that is already computed and persisted. `get_pipeline_status()` reports,
> over a bounded ring buffer of the last `MAX_TRACKED_ANALYSES` (50) runs:
> `degraded_pct`, a per-module `module_failures` tally, the `confidence` distribution, and
> `signal_degraded` — true only once `MIN_SAMPLE_FOR_DEGRADED` (3) runs have been seen and
> `degraded_pct >= 50`, so a single post-restart failure can't raise a false alarm.
>
> Only the five `BASE_WEIGHTS` modules count; **`narrative` is excluded** because it is
> zero-weighted (ADR-006), so its absence is not a signal outage. A module is "missing" only
> when absent or `None` — a real computed `50.0` is not missing, per ADR-005's
> "absence ≠ neutral".
>
> **Deliberately in-process and database-free**, surfaced on the already-polled `/health`.
> Querying the DB here would keep Neon's free-tier compute from ever idling — the exact
> failure Phase 59 fixed — so this adds no query, no loop, and no timer. Like the `reaper`
> field, `pipeline` **never** changes `/health`'s status code: conflating a dead data feed
> with "the API is down" would recreate the Phase 30 false-alarm outage. State resets on
> restart, an accepted trade (the reaper status and rate limiter already work this way).
>
> **Verified by replaying the real outage**: recording three analyses with
> `financial`/`cashflow`/`earnings` `None` yields `signal_degraded: true` and
> `module_failures` of 3/3/3 against 0 for `governance`/`news` — pinpointing *which* feed
> died, not merely that something is wrong. Backend suite: 299 passed.

> **Phase 66 amendment (2026-08-11):** the narrative module now reads **management's own
> words** instead of press coverage. It was the last dishonest signal in the product: it is
> meant to detect whether a company's own story changes over time, but it consumed Google
> News headlines — journalists' mood, not corporate narrative. Live consequence, observed
> on the deployed site: with two headlines published the same day it printed
> *"Significant tone shift between 2026-08-10 and 2026-08-10"* and a red 15/100 SEVERE RISK
> card. Phase 64 stopped same-period pairs from counting; this phase fixes the input.
>
> `_stage_narrative` now tries `sec_edgar.fetch_management_statements()` — the free,
> keyless 10-K/10-Q **MD&A** extractor built and left unwired in Phase 58 — taking
> `NARRATIVE_EDGAR_FILING_LIMIT` (3) recent filings. Quarterly filings carry genuinely
> distinct `reportDate`s, so the comparison is finally temporal. Verified live: AAPL and KO
> each return 3 statements across **3 distinct quarters**.
>
> **News headlines remain a real fallback**, not a formality: EDGAR has no coverage for
> foreign private issuers (20-F filers) or non-XBRL filers. The EDGAR call sits in its own
> `try/except` so an EDGAR outage degrades to news rather than failing the stage; if both
> sources yield <2 statements the pre-existing neutral `50.0` behaviour is unchanged.
>
> **Cost control.** `ConsistencyEngine` makes one Gemini call *per statement*, and MD&A
> excerpts run to thousands of characters against a ~100-character headline.
> `NARRATIVE_MAX_STATEMENT_CHARS` (4000) truncates each statement at the call site, where
> the cost decision is visible, and *before* the engine — so each `source_quote` is grounded
> against exactly the text the model saw. Truncation builds **new** dicts rather than
> mutating the service's return value, because `fetch_management_statements` caches for 7
> days and in-place mutation would poison every later read.
>
> **Honesty.** `module_details.narrative.source` records which source was actually used
> (`"edgar_mdna"` / `"news_headlines"` / `"none"`), defaulted so pre-existing rows still
> validate. The Narrative tab reads it and adapts its heading and description — it would
> otherwise keep telling users the score is "derived from recent headlines" while showing
> MD&A analysis, which is exactly the kind of quiet overclaim this project exists to avoid.
>
> **Narrative remains ZERO-WEIGHTED.** `BASE_WEIGHTS` is untouched. ADR-006 step 2 requires
> the signal to be validated on real output before any weight is restored, and that is the
> owner's call — this phase makes the module honest, not weighted. Backend 304 passed
> (was 299); frontend 135 passed, tsc clean, build succeeds.
>
> **Known limitation carried forward from Phase 58:** MD&A extraction is heuristic. KO's
> excerpts came back at 377–640 characters versus AAPL's full 8000, because the
> "last occurrence of the heading" rule can start mid-section. Robust extraction needs the
> filing's DOM heading structure, not flattened text. Worth revisiting before narrative is
> ever re-weighted.

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

**Mandatory pre-merge check for any PR not opened by the owner (Dependabot, or any other
bot/non-owner contributor):** before running `gh pr merge --squash`, re-author that PR's
branch to the owner's identity first — `git commit --amend --author="sohan1611
<sohanmandal1611@gmail.com>"` (or `git rebase`/interactive amend for multi-commit
branches), then force-push that **feature/bot branch** (never `main` — bot branches
carry no protection rule, so this needs no settings change and no admin bypass). Only
*then* squash-merge. GitHub's squash-merge preserves the original commits' author when a
PR has a single author — it does NOT default to whoever clicks merge — so an
un-re-authored Dependabot PR lands on `main` already attributed to `dependabot[bot]`,
which then shows up in the repo's Contributors graph. Re-authoring before merge avoids
ever needing to touch `main`'s branch protection or force-push to `main` at all.

*(Background: on 2026-06-30, exactly this happened — PR #30, a Dependabot dependency
bump, was squash-merged without re-authoring first, landing `dependabot[bot]` on `main`
as a contributor. Fixed via `git filter-repo` rewriting just that one commit's
author/committer fields (content-verified byte-identical via diff against a backup
branch), then a one-time owner-performed force-push to `main` after the owner — not
Claude — temporarily loosened `main`'s "allow force pushes" and "do not allow bypassing
the above settings" protections, immediately re-locking both afterward. Verified clean
via the actual GitHub Contributors API (`gh api repos/{owner}/{repo}/contributors`), not
the cached UI widget. This rule's pre-merge step exists so this never has to be
repeated.)*

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
| AI | Google Gemini 2.5 Flash | Free tier: 1,500 req/day |
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
run at `temperature=0` with a pinned `model_id` (`gemini-2.5-flash`), with prompts and raw
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
GET    /health                      shallow liveness + reaper status, NO DB call, no auth
GET    /health/db                   deep DB connectivity probe, no auth — manual use only,
                                    never a polling target (Phase 59)

POST   /auth/register              create user, return JWT
POST   /auth/login                 OAuth2 form, return JWT
GET    /auth/me                    current user profile

GET    /company/search?q=          ILIKE search, max 10 results — auth required
GET    /company/{ticker}           company metadata, creates if new — auth required

POST   /analysis/run                       check free limit, trigger background task
GET    /analysis/{id}/status               status + stage + elapsed (polled every 3s) — auth required
GET    /analysis/company/{ticker}          latest completed result + red flags — auth required
GET    /analysis/company/{ticker}/history  score history, oldest first, for trend chart — auth required
GET    /analysis/compare?tickers=          up to 5 tickers, side-by-side latest results — auth required

GET    /report/company/{ticker}    markdown report content — auth required

GET    /watchlist                  user's list with latest scores
POST   /watchlist                  add company (409 if duplicate)
DELETE /watchlist/{ticker}         remove company

GET    /alerts                     user's risk-band-change alerts + unread_count
POST   /alerts/{id}/read           mark one alert read (404 if not owned)
```

All routes not marked "no auth" above already required `get_current_user`
(`backend/app/api/deps.py`) before Phase 54 except the seven now explicitly marked
"— auth required" — see the Phase 54 amendment under "Constitution & Governance
Documents" for why and what changed.

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

## Database Models (14 total)

Original 8, plus 6 added across later phases (list corrected here as of Phase 47 —
it had drifted out of date across Phases 5/38/41/45/46 without this header being fixed):

```
User              id, email, hashed_pw, full_name, tier, created_at, is_active,
                  org_id, role  [Phase 46]
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
AnalysisRun       id, user_id, company_id, analysis_result_id, run_at, counted
                  [Phase 5 / ADR-007, counted column Phase 10 / ADR-013]
EdgarFinancialFact id, company_id, concept, period_start, period_end, value,
                  accession_number, form_type, filed_date  [Phase 41 / H-4]
AuditLog          id, user_id, action, detail (JSON), ip_address, created_at
                  [Phase 38 / F6]
GeminiDailyBudget date (PK), count  [Phase 45 / A-4]
Organization      id, name, created_at  [Phase 46 / E-1]
WatchlistAlert    id, user_id, company_id, analysis_id, previous_score, new_score,
                  previous_risk, new_risk, is_read, created_at  [Phase 47 / E-4]
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
