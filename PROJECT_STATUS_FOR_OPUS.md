# PROJECT STATUS — SentinelIQ

**Prepared by:** Claude Code (Sonnet), Lead Implementation Engineer
**Prepared for:** Opus (Chief Architect review)
**Date:** 2026-06-15
**Supersedes:** the 2026-06-13 snapshot of this document, which predates all work described
below and is now fully stale (it described the company-analysis tabs B6–B10 as "100% mock"
and the narrative/Stage-6 pipeline as broken — both are now fixed and verified).
**Purpose:** Phases 1–8 of the roadmap in `OPUS_ARCHITECTURAL_REVIEW.md` §6/§7 are complete.
This document re-verifies each phase against its original success criteria **at the
source-code level** (re-read this session, not taken on faith from commit messages),
surfaces deviations and open items for your review, and requests your ruling on Phase 9
onward.

For project background, tech stack, and design-system rules, see `CLAUDE.md` — unchanged
and still authoritative; not repeated here.

**Repo:** `https://github.com/sohan1611/SentinelIQ`, branch `main`, 21 commits total.
Working tree clean.

---

## 0. Headline

Per your own framing in §2 of `OPUS_ARCHITECTURAL_REVIEW.md`: *"(a) make the core honest
(Phase 3) and verified (Phase 4), (b) make it visible (Phases 2, 6, 7, 8), (c) make it an
analyst workflow (Phase 9 — history, drill-down, ⌘K), then (d) make it proactive and
defensible (Horizon 2)."*

**Stages (a) and (b) are both fully complete**, along with the foundational Phases 1 and 5:

| # | Phase | Commit | Status |
|---|---|---|---|
| 1 | Shell Hardening (route guard + UI foundations) | `e1aef878` | ✅ Complete |
| 2 | Wire Company Overview Tab | `36580d51` | ✅ Complete |
| 3 | Honest, Reproducible Scoring Pipeline | `bbb092f4` | ✅ Complete |
| 4 | Forensic Test Harness + Backtests + CI | `1c193813` | ✅ Complete |
| 5 | AnalysisRun + Alembic Baseline + Error Envelope | `4e968b0c` | ✅ Complete |
| 6 | Wire Financials Tab + Forensic Charts | `58ab07b8` | ✅ Complete |
| 7 | Wire Governance + Narrative Tabs | `63029f0b` | ✅ Complete |
| 8 | Wire Report Tab + Markdown + Exports | `88e99b8c` | ✅ Complete |

All 6 critical defects from §1.2 (C-1 through C-6) are resolved. Every "Status: Broken /
Fully mock" item flagged in the 2026-06-13 snapshot for the company-analysis tabs and the
narrative/Stage-6 pipeline is now real and verified.

**Per the original roadmap, Phase 9 ("Analyst Workflow Layer: ⌘K + Score History + Evidence
Drill-down") is next** — both of its hard dependencies (Phase 3 ✅, Phase 5 ✅) are
satisfied. Section 4 asks you to confirm or revise this given what Phases 1–8 actually
produced.

---

## 1. Phase-by-Phase Verification

(re-verified this session by reading source files directly — file paths below)

### Phase 1 — Shell Hardening · `e1aef878`
**Objective:** route guard at the `(app)` layout level (ADR-009); build the missing UI
primitives the rest of the roadmap depends on.

Delivered, verified:
- `frontend/app/(app)/layout.tsx` — redirects to `/login` when `!isLoading && !user`, no
  pre-resolution flash (renders an empty `bg-canvas` shell while loading).
- `components/ui/{Input,Modal,Tooltip}.tsx` — real implementations (forward-ref `Input`
  with error/hint, portal-based `Modal` with Escape/overlay dismiss, `Tooltip` with 200ms
  delay).
- `components/ui/DataTable.tsx`, `components/charts/ChartFrame.tsx` — new shared
  primitives, both consumed by the Phase 6/7/8 chart and table work.
- `contexts/ToastContext.tsx` — now matches MR-1 exactly: `translateX` enter (not
  `translateY`), 3000ms auto-dismiss, `MAX_TOASTS = 3`. Wired into real flows (watchlist
  add/remove, auth errors).
- `lib/theme/tokens.ts` — design-system colors and chart theme exported as a JS object,
  consumed directly by Chart.js components (not via Tailwind classes) — this was the "one
  concrete technical UI debt" item from §3.3.
- `npx tsc --noEmit` — clean.

Deviations: none found.

### Phase 2 — Wire Company Overview Tab · `36580d51`
**Objective:** integrity gauge, 6 component scores, red flags all sourced from
`useCompanyData().analysis`; honest empty state.

Delivered, verified:
- `app/(app)/company/[ticker]/page.tsx` — gauge, all 6 component scores, and `red_flags`
  all read from the real `AnalysisResultWithFlags`. No hardcoded `componentScores` /
  `redFlags` / `moduleData` arrays remain.
- Honest "not yet analyzed" empty state with a "Run Analysis" CTA, live-polled stage text
  during a run, error display on failure.
- Period-count context line ("Based on N reporting period(s)...") computed from
  `module_details`.

Deviations:
- `module_details.confidence` ("low"/"medium"/"high", added in Phase 3) is computed and
  persisted but **not yet rendered** anywhere in the Overview tab. See Open Items §3.

### Phase 3 — Honest, Reproducible Scoring Pipeline · `bbb092f4`
**Objective:** ADR-004/005/006/010 — deterministic AI, no-dilution renormalization,
confidence tiers, uniform stage-isolated pipeline.

Delivered, verified:
- `core/scoring/fraud_scorer.py` — `BASE_WEIGHTS` dict matches CLAUDE.md's Phase 3
  amendment exactly (financial 0.3333 / cashflow 0.2222 / governance 0.1667 / earnings
  0.1667 / news 0.1111, narrative absent, sum = 1.0). `compute_integrity_score(scores,
  period_count)` renormalizes over modules whose value `is not None` and returns
  `(integrity_score, confidence)`. Confidence-tier thresholds match the documented rule
  exactly (≤2 → low; 5-of-5 and ≥3 periods → high; else medium).
- `tasks/analysis_worker.py` — rewritten as a `STAGES` list of isolated stage functions,
  each in its own try/except with a neutral fallback; orchestrator never sets
  `status="failed"` — every started analysis ends `"complete"`. News fetch (stage 5) and
  score persistence (stage 6) are now separate steps, so a news-fetch failure can't discard
  computed forensic scores. Stage 7 (report) always runs.
- `core/ai/gemini_client.py` — score-bearing calls default to `temperature=0.0`;
  `generate_content_with_provenance` / `generate_json_with_provenance` return
  `{text/result, prompt, model_id, raw_response}`; 429/quota errors get 3-attempt
  exponential backoff.
- `core/narrative/consistency_engine.py` — `analyze()` now returns a 4-tuple
  `(narrative_score, snapshots, contradictions, provenance)`, fed real multi-period
  statements via the new `news_aggregator.fetch_news_statements()` (was a single
  hardcoded mock statement).
- `core/governance/governance_scorer.py` — `analyze()` now returns a 3-tuple `(score,
  flags, provenance)`.
- `module_details` now includes `confidence`, `narrative.provenance`,
  `narrative.statements_used`, `governance.provenance` — all confirmed present and
  exercised by `tests/unit/test_analysis_schemas.py`.

Deviations from the original plan (both *resolutions*, not gaps):
- The original Phase 3 plan explicitly deferred `NarrativeSnapshot.fetched_at`
  (documented as "pre-existing gap, not fixed in this phase"). It **was** fixed during
  execution — the column is now populated.
- CLAUDE.md's "Analysis Pipeline — 7 Stages" section was updated to match the new stage
  loop, beyond the plan's original minimum of just amending the scoring-weights section.

### Phase 4 — Forensic Test Harness + Backtests + CI · `1c193813`
**Objective:** ADR-011 — deterministic unit tests for all 4 forensic modules +
fraud_scorer, pipeline integration test, ≥1 historical backtest, CI.

Delivered, verified:
- `backend/tests/` — 14 test files, **70 tests collected successfully** via `pytest
  --collect-only`. Covers all 4 forensic modules, `fraud_scorer`
  (renormalization/confidence-tier cases), `forensics_runner`, the error envelope, the
  `AnalysisRun` model, the Alembic migration chain, free-tier query logic, and analysis
  schemas.
- `backend/tests/integration/test_analysis_pipeline.py` — 2 tests exercising the full
  stage loop against an in-memory session; confirms `module_details` wiring, provenance
  round-trip, and per-stage failure resilience (ADR-010/011).
- `backend/scripts/backtest_wirecard.py` (7,209 bytes) and
  `backend/scripts/backtest_enron.py` (6,961 bytes) — real, populated backtests against
  known fraud cases.
- `.github/workflows/ci.yml` — runs on push/PR to `main` for backend paths, Python 3.12,
  installs `requirements.txt`, runs `pytest`.

Deviations / open item:
- Two **0-byte leftover files** exist at repo-root `scripts/backtest_{enron,wirecard}.py`
  (dated 2026-06-12, pre-Phase-1 scaffolding) — same filenames as the real, populated ones
  now at `backend/scripts/`. Dead duplicates. See Open Items §3.

### Phase 5 — AnalysisRun + Alembic Baseline + Error Envelope · `4e968b0c`
**Objective:** ADR-007 — user-scoped `AnalysisRun` audit/metering table; ADR-006/C-6 —
real Alembic migrations, retire `create_all`; global `{"error":{"code","message"}}`
envelope.

Delivered, verified:
- `app/models/analysis_run.py` — `AnalysisRun(id, user_id, company_id, analysis_result_id,
  run_at)` with a composite `(user_id, run_at)` index.
- `api/v1/routes/analysis.py` — free-tier count now queries `AnalysisRun` by `user_id` +
  calendar month (5/month limit enforced); a cache-hit still logs an `AnalysisRun` row (no
  recompute needed to count against quota).
- `backend/alembic/versions/0001_baseline_schema.py` (170 lines, all 8 original tables)
  and `0002_add_analysis_runs.py` (45 lines, `analysis_runs` table) — both real and
  non-empty. `tests/unit/test_alembic_migrations.py` confirms a single linear head.
- `app/main.py` — `Base.metadata.create_all` removed (schema is Alembic-managed); global
  handlers for `HTTPException`, `RequestValidationError`, and unhandled `Exception` all
  normalize to `{"error":{"code":str,"message":str}}` with a status-code→error-code map
  (400→BAD_REQUEST, ..., 422→VALIDATION_ERROR, unmapped→HTTP_ERROR; 500s never leak
  internals).
- Route files (`watchlist.py`, `report.py`, `analysis.py`) raise `HTTPException(status_code,
  detail="...")` with plain-string details — the global handler wraps these into the
  envelope shape uniformly, so the contract holds API-wide without every route needing to
  construct the dict by hand.

Deviations: none found.

### Phase 6 — Wire Financials Tab + Forensic Charts · `58ab07b8`
**Objective:** `RevenueQualityChart`, `CashFlowChart`, `DebtTrendChart` built on
`ChartFrame`, fed by `module_details.{revenue,cashflow,debt}`.

Delivered, verified:
- All three chart components exist with real content, use the shared `ChartFrame`
  wrapper, and read typed data from `module_details`.
- `CashFlowChart` maps the Sloan accrual ratio to the CLAUDE.md score bands and colors
  each bar via `getScoreColor()`.
- `app/(app)/company/[ticker]/financials/page.tsx` extracts `divergences`, `recv_ratios`,
  `accrual_ratios`, `debt_metrics` from `module_details` and passes them straight to the
  chart components — no inline hardcoded Chart.js datasets remain.
- Each chart has its own empty/short-history state (uses an `alignByPeriod` utility to pad
  gaps when periods are missing).

Deviations: none found.

### Phase 7 — Wire Governance + Narrative Tabs · `63029f0b`
**Objective:** `GovernanceChecklist` from `red_flags` (`flag_type==="governance"`);
narrative tab from `module_details.narrative.snapshots` with honest partial states.

Delivered, verified:
- `components/modules/GovernanceChecklist.tsx` — real component; maps red flags to
  checklist rows with severity badges and dates; has its own empty state.
- `app/(app)/company/[ticker]/governance/page.tsx` — filters `analysis.red_flags` by
  `flag_type === "governance"`, honest empty/no-flags states, reuses the Phase 2 "not yet
  analyzed" CTA pattern.
- `app/(app)/company/[ticker]/narrative/page.tsx` — reads
  `module_details.narrative.snapshots`; **three** distinct states handled explicitly: 0
  snapshots ("no recent statements"), 1 snapshot ("not enough to compare"), 2+
  (side-by-side comparison + contradiction alerts + `NarrativeTrendChart`). Shows
  `narrative_score` with an explicit disclaimer that it does not currently affect the
  integrity score (correctly reflecting Phase 3's renormalization).

Deviations:
- `components/charts/RiskRadar.tsx` is a 1-byte empty stub and is not imported anywhere.
  Phase 7's original scope said "RiskRadar if used" — it wasn't needed for the
  governance/narrative wiring as built. See Open Items §3.

### Phase 8 — Wire Report Tab + Markdown + Exports · `88e99b8c`
**Objective:** render the AI-generated report as formatted markdown; wire watchlist add;
PDF/CSV export.

Delivered (this session, implemented directly):
- `components/modules/ReportSection.tsx` — full `react-markdown` + `remark-gfm` renderer
  with custom components for every CLAUDE.md typographic rule (section-label + heading
  pairs, IBM Plex Mono via `font-mono` on `<code>`, hairline-divider tables, no zebra
  striping).
- `lib/hooks/useReport.ts` — fetches `GET /report/company/{ticker}`, treats 404 as "no
  report yet" (not an error).
- `app/(app)/company/[ticker]/report/page.tsx` — rewritten to render real report content
  via `ReportSection`, with an honest "not generated yet" state.
- `lib/hooks/useAddToWatchlist.ts` (extracted, reused) — wires the report page's "Add to
  Watchlist" action to the real API with toast feedback (success / 409-already-exists /
  error), consistent with Phase 1's toast wiring.
- Export: PDF via `window.print()` (print-stylesheet-driven), CSV export util for
  forensic time-series data.
- Build verified clean.

Deviations: none found.

---

## 2. ADR & Minor-Ruling Compliance Snapshot

| ADR / MR | Subject | Status |
|---|---|---|
| ADR-001 | Premium institutional platform (north star) | No violations observed across Phases 1–8 |
| ADR-002 | Forensic-Editorial UI identity | ✅ design tokens, solid risk colors, no gradients/shadows, `ChartFrame`/`DataTable` primitives all in place |
| ADR-003 | Light mode only | ✅ no dark-mode code introduced |
| ADR-004 | Deterministic/Explainable/Auditable AI | ✅ `temperature=0` + provenance confirmed for governance & narrative (Phase 3) |
| ADR-005 | Scoring philosophy (renormalize, confidence tier, news minor) | ✅ for renormalization/confidence-tier/news-weight. **`docs/data-sources.md`** (principle #7) — not verified this session |
| ADR-006 | Narrative strategy (news-derived now, transcripts Horizon 2) | ✅ `fetch_news_statements`, narrative excluded from `BASE_WEIGHTS` |
| ADR-007 | `AnalysisRun` data model | ✅ confirmed (Phase 5) |
| ADR-008 | In-memory cache, single-instance | Unchanged — no Redis/queue introduced, still correct as documented |
| ADR-009 | Route protection at layout level | ✅ confirmed (Phase 1) |
| ADR-010 | Uniform stage isolation | ✅ confirmed (Phase 3) |
| ADR-011 | Testing as credibility requirement | ✅ 70 tests + 2 backtests + CI (Phase 4) |
| ADR-012 | Deployment shape / $0/month | Phase 5 prereq ✅ done; Phase 11 itself not started |
| MR-1 | ToastContext spec conformance | ✅ confirmed (Phase 1) |
| MR-2 | Dead stubs deleted, not carried | Original "8 empty backend stubs" not re-checked this session; **2 new dead-code items found** below, candidates for Phase 10 |
| MR-3 | Honest "not yet available" auth stub pages | Phase 10 scope, not started |

---

## 3. Open Items Surfaced During Verification

1. **Two 0-byte dead files**: `scripts/backtest_enron.py` and `scripts/backtest_wirecard.py`
   (repo root, dated 2026-06-12) duplicate the names of the real, populated Phase 4
   backtests now at `backend/scripts/backtest_{enron,wirecard}.py`. Safe to delete.
   *(Phase 10 candidate.)*
2. **Dead branch**: `frontend/app/(app)/company/[ticker]/page.tsx` still checks
   `analysisStatus?.status === "failed"`. Phase 3 retired that status server-side
   (`analysis_worker.py` always ends `"complete"`), so this branch is now unreachable.
   Harmless but should be removed for clarity. *(Phase 10 candidate.)*
3. **Empty stub**: `frontend/components/charts/RiskRadar.tsx` (1 byte), unreferenced
   anywhere. Either delete or scope into a future phase if a radar visualization is still
   wanted. *(Phase 10 candidate.)*
4. **Confidence tier not surfaced in UI**: `module_details.confidence` (Phase 3, ADR-005
   #5) is computed and persisted but not shown on the Overview tab. This seems like a
   natural fit for Phase 9's "evidence drill-down" framing (showing *why* to trust — or
   not trust — a given score) rather than a standalone Phase 2 patch.
5. **`docs/data-sources.md`** (ADR-005 principle #7) — not checked this session; worth a
   quick look before Phase 9 if evidence drill-down will reference data
   provenance/recency.

None of these are blocking — all are small, well-scoped, and most map naturally onto
Phase 10 ("Settings Actions + Auth Honesty + Dead-Code Sweep") as already planned.

---

## 4. Request for Opus

Phases 1–8 — the entire "make it honest, verified, and visible" arc — are done and
verified at the code level. Before Sonnet starts the next phase, please:

1. **Review Phases 1–8** above for any architectural drift from your original intent — in
   particular, the Phase 3 deviations (`NarrativeSnapshot.fetched_at` fixed early;
   CLAUDE.md pipeline-stages section updated beyond the minimum) and the Phase 2
   confidence-tier display gap (item 4 in §3).
2. **Confirm or revise Phase 9.** Per §6/§7 of `OPUS_ARCHITECTURAL_REVIEW.md`, Phase 9
   ("Analyst Workflow Layer: ⌘K + Score History + Evidence Drill-down") is next — both
   hard dependencies (Phase 3, Phase 5) are satisfied. Given Phases 1–8's actual shape
   (especially the now-rich `module_details` provenance/confidence data from Phase 3, and
   the chart/table primitives from Phase 1/6), does Phase 9's scope still look right, or
   should it be adjusted?
3. **Sequencing of Phase 10 vs. 9 vs. 11.** Open Items §3 gives Phase 10
   ("Settings/Auth-honesty/Dead-code sweep") a short, concrete punch list right now.
   Should Phase 10 move *before* Phase 9 (quick cleanup first), stay after, or get folded
   into Phase 9 opportunistically?
4. **Horizon 2 candidates.** With stage (b) ("make it visible") fully done, are any
   Horizon 2 items — portfolio monitoring/alerting, sector-relative benchmarking, the
   transcript/SEC narrative pipeline — worth pulling forward in priority, or does the
   original (c)→(d) sequencing (Phase 9 first, Horizon 2 after Phase 11) still hold?
