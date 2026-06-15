# SentinelIQ — Architectural Review & Roadmap
**Author:** Claude Opus, acting as Chief Architect / CTO / Product Strategist
**Audience:** Claude Sonnet (Lead Implementation Engineer), and the project owner
**Date:** 2026-06-14
**Inputs reviewed:** Sonnet's `PROJECT_STATUS_FOR_OPUS.md` (full), `CLAUDE.md` (the constitution), and a targeted re-read of the load-bearing source files (`analysis_worker.py`, `fraud_scorer.py`, `routes/analysis.py`, `gemini_client.py`, `(app)/layout.tsx`, `globals.css`) to verify the audit's most consequential claims before issuing rulings.

> **Status of this document:** This is a review and a plan, not code. No production files were modified. On a future **"Start new phase"** command, Sonnet executes exactly **one** phase from §6/§7, fully, then writes a completion report and stops.

---

## 0. Executive Summary & How I Read Sonnet's Audit

Sonnet's audit is **excellent** — thorough, honest, correctly prioritized at the file level, and it found every bug that matters. I verified its load-bearing claims against source and they hold. Where I add value is at the altitude Sonnet explicitly deferred to me: **resolving the open architectural decisions, reframing three findings that are more serious than they first appear, elevating one priority Sonnet under-weighted, and setting product/UI direction.**

**The one-sentence state of the project:** *SentinelIQ has a genuinely strong, spec-compliant quantitative forensic core wrapped in a single-company demo UI that is still 100% mock — but the score that core produces is not yet honest, not yet reproducible, not yet tested, and not yet metered correctly, and those four things matter more than wiring another screen.*

**Where I diverge from Sonnet's prioritization (the headlines):**

1. **The Stage 6 bug is worse than documented.** It's not just "the pipeline aborts." The `fetch_news_sentiment` **network call sits inside the same `try` block as the persistence of the already-computed forensic scores** (`analysis_worker.py:150–176`). A transient news/RSS hiccup therefore **throws away the revenue/cashflow/earnings/debt scores that already succeeded in Stage 2/3**, marks the whole run `failed`, and skips the report. The most expensive, most reliable work in the pipeline is gated behind its flakiest, cheapest call.

2. **The narrative stub doesn't just "return 50" — it actively poisons every score.** Because `fraud_scorer` blends a fixed `50.0 × 0.10` term into *every* company's Integrity Score (`fraud_scorer.py:8`), and narrative is *always* 50, **10% of every score in the product is a constant.** Combined with the weighting, ~35% of the headline number is currently weak AI/news signal and a third of *that* is literal noise pulling every company toward the middle. This is a **scoring-credibility** problem, not a missing-feature problem.

3. **The score is not reproducible.** `gemini_client.py` runs at Gemini's **default temperature (~1.0)** with no `generation_config` — so the governance score, narrative score, and report prose **change run-to-run for the same company**. For a tool whose entire pitch is "can this company be trusted with billion-dollar decisions," a score that won't reproduce is a foundational defect, not a polish item.

4. **Testing is a credibility issue, not a "Low priority" nice-to-have.** Sonnet correctly noted zero tests but ranked it low. I am elevating it: the forensic engine is **deterministic pure math with formulas written down in CLAUDE.md** — it is simultaneously the product's entire credibility *and* the single easiest thing in the codebase to test. You cannot sell "institutional-grade fraud detection" on an unverified scoring engine. This gets its own early phase plus CI.

5. **`frontend/Dockerfile` is not Critical.** Sonnet flagged it Critical #6. Vercel — the documented frontend host — **does not use a Dockerfile**; it builds Next.js natively. The missing file only breaks the local `docker-compose` convenience path. It's worth fixing for local parity, but it is **High at most**, not a deployment blocker. I'm downgrading it.

**The four decisions Sonnet escalated to me — resolved here, up front, because the roadmap depends on them:**

| # | Decision Sonnet deferred | My ruling | One-line rationale |
|---|---|---|---|
| 1 | Per-user analysis tracking: `user_id` on `AnalysisResult` **vs.** separate log table | **Separate `AnalysisRun` table.** `AnalysisResult` stays company-scoped. | Analysis is an expensive, **cacheable, shareable** artifact; *runs* are user-scoped metered events. Splitting them fixes the quota bug, avoids recomputing AAPL per user, and gives the **audit trail** institutional buyers require. |
| 2 | Narrative fix scope: cheap news-derived statements **vs.** build transcript pipeline | **Cheap news-derived statements now**, transcripts deferred to Horizon 2. **And** fix the scorer to renormalize, not dilute. | Ship an *honest* narrative signal this week using data we already fetch; don't block the core on an SEC/transcript scraper. |
| 3 | ToastContext: code-to-spec **vs.** spec-to-code | **Code conforms to CLAUDE.md** (translateX enter, 3000ms, max-3). | CLAUDE.md is the constitution. Code bends to it, not the reverse, unless we deliberately amend the constitution. |
| 4 | The 8 empty backend stubs + deployment shape | **Delete the stubs** in the cleanup phase; track their *intent* in this roadmap. Confirm Vercel/Render shape at deploy time with the owner. | Empty files are not a plan. The roadmap is the plan. Re-create a file when its feature is actually scheduled. |

One scoring change above (renormalize weights instead of blending in 50, and temporarily drop narrative from the weighting until it is real) is a **deliberate amendment to CLAUDE.md's scoring philosophy.** It must be made explicitly — updating CLAUDE.md in the same phase — not slipped in silently. CLAUDE.md currently says "return 50.0 (neutral)"; I am proposing we evolve that rule, with reasons, in §6 Phase 3.

---

# 1. Architectural Review

## 1.1 What is genuinely strong (do not touch)

- **The forensic engine (`core/forensics/`).** Four pure, well-separated modules + a runner, each matching CLAUDE.md's formulas (Sloan accrual ratio, revenue/OCF divergence, margin-delta/CV, debt-to-revenue/interest-coverage). Pure functions, no I/O, no hidden state. This is the best-engineered part of the system and the product's actual differentiator. **Protect it with tests; don't refactor it.**
- **Layering & externalized AI prompts.** Forensics / governance / narrative / scoring / AI / services are cleanly separated, and Gemini prompts live in `.txt` files loaded at runtime — exactly right, and rare discipline for a project this young.
- **Async-first stack, UUID primary keys.** FastAPI async + async SQLAlchemy + asyncpg is the correct modern choice. UUID PKs are the right institutional default (non-enumerable, mergeable, safe to expose).
- **The frontend hook layer.** `useCompanyData` / `useAnalysis` / `useWatchlist` are already wired and typed; the remaining tab work is mechanical consumption, not new plumbing.
- **The design constitution itself.** CLAUDE.md's design system is unusually mature and tasteful (see §3). Most projects this age have no design discipline; SentinelIQ has a strong, opinionated one. The `globals.css` foundation (timing/easing/font tokens, tabular-nums, reduced-motion, focus rings, **and an existing print stylesheet**) is already in place.

## 1.2 Critical correctness defects (the score is not yet trustworthy)

These are ordered by how directly they undermine the product's core claim.

### C-1 — The Integrity Score is diluted by a hardcoded constant (`fraud_scorer.py:8`, `analysis_worker.py:121`)
Narrative is always 50; the scorer always blends `50 × 0.10` in. Every score in the product carries a fixed 5-point pull toward the mean that represents *no information*. **Fix (Phase 3):** feed the narrative engine real multi-statement input from the news text we already fetch, **and** change the scorer to **renormalize weights across the modules that actually produced a signal** rather than substituting 50 for missing ones. A company with no narrative data should be scored on what *is* known, not muddied by a neutral guess. *(This amends CLAUDE.md's "return 50.0 neutral" rule — make the amendment explicit.)*

### C-2 — Stage 6 discards completed work on a flaky network call (`analysis_worker.py:147–176`)
As verified: the news fetch and the persistence of already-computed forensic scores share one `try`. A news hiccup → `status="failed"`, no scores saved, no report. **Fix (Phase 3):** give the news fetch its own try/fallback (neutral 50, like every other stage), then make **persistence a separate, near-infallible step**, and ensure Stage 7 always runs. This restores CLAUDE.md's promised "pipeline never aborts on a single-stage failure" invariant — which every stage *except* this one already honors.

### C-3 — The score is not reproducible (`gemini_client.py:10–17`)
Default Gemini temperature; same input → different governance/narrative scores and different report prose across runs. **Fix (Phase 3):** set `generation_config={"temperature": 0}`, and **persist the exact prompt, model id, and raw response into `module_details`** so any score is auditable and reproducible after the fact. Determinism + provenance is non-negotiable for a forensic product.

### C-4 — Free-tier metering is structurally broken (`routes/analysis.py:34–44`)
Verified: the count joins `AnalysisResult → WatchlistItem` because `AnalysisResult` has no `user_id` (the code's own comments agonize over this). It both under- and over-counts. **Fix (Phase 5):** the `AnalysisRun` table (Decision #1). Count runs by `user_id` + month. Clean, correct, and it doubles as the audit log.

### C-5 — No route protection (`(app)/layout.tsx` — verified: no auth check at all)
The authenticated shell is `ToastProvider > AppShell > PageTransition` with **zero** `useAuth`/redirect. Every protected route is reachable unauthenticated. **Fix (Phase 1):** guard the layout (redirect to `/login` once `!isLoading && !user`, with no auth-resolution flash).

### C-6 — No migrations; schema born from `create_all` (Alembic `versions/` empty)
Blocks any clean managed-Postgres deploy and leaves schema evolution with no path. **Fix (Phase 5):** generate a baseline migration (including `AnalysisRun`), `stamp` the existing dev DB, and retire `create_all` in production.

## 1.3 Reliability & scalability risks (architecture, not bugs)

- **In-process `BackgroundTasks` + Render free-tier spin-down = lost analyses.** Verified `background_tasks.add_task(run_full_analysis, …)`. There is no queue, no retry, no idempotency. Render's free tier **spins the instance down after ~15 min idle**; an analysis in flight during a restart is stuck at `pending`/`running:` **forever**, and the polling UI waits indefinitely. **Mitigation (Phase 11, cheap):** a startup "reaper" that marks any `running` analysis older than ~10 min as `failed`, plus a `/health` endpoint. **Long term (Horizon 2):** a real job queue — but that breaks the $0/month constraint, so defer deliberately.
- **Process-local cache is a hidden single-instance constraint.** `cache.py` and the background-task model *both* silently assume one instance. The moment a second replica exists, the cache stops sharing and job state fragments. This constraint should be **documented as an explicit architectural decision**, not discovered in production.
- **Gemini free-tier ceiling.** 1,500 req/day, and each analysis makes several Gemini calls (governance + per-statement narrative + report). Real-world ceiling is ~150–300 analyses/day **across all users**, with **no 429 backoff** in `gemini_client`. Fine for demo; a known wall for load. Add retry/backoff when narrative goes multi-statement (Phase 3).
- **`analysis_worker.py` coupling.** One ~200-line function instantiating six engines, sequencing seven stages, and doing raw writes for five models. Sonnet flagged this correctly. **My prescription:** when Phase 3 touches it, refactor to a **uniform stage loop** — a list of `(name, coroutine)` stages, each isolated by the *orchestrator's* try/except with a neutral fallback, accumulating into a shared context. This makes C-2 *structurally impossible to reintroduce*, makes each stage unit-testable, and is a smaller change than it sounds. Do it *as part of* the Phase 3 fix, not as a separate refactor.

## 1.4 Data-model & sourcing ceilings (honest limits, not MVP blockers)

- **`AnalysisResult` should stay company-scoped; add `AnalysisRun` for users.** (Decision #1.) This also makes the documented 6h analysis cache meaningful: a second user requesting AAPL within the TTL gets the cached `AnalysisResult` *and* a logged `AnalysisRun` (metered, no recompute).
- **`module_details` as schemaless JSON is acceptable — but validate it hard at the boundary.** The frontend tabs (Phases 2, 6, 7) will trust this shape. Pydantic schemas for `module_details` and `NarrativeSnapshot` (the two Sonnet found missing) must be rigorous so the UI can rely on them.
- **Point-in-time data is the deep ceiling.** yfinance returns *current* (often *restated*) figures — and restatements are exactly the fraud signal we hunt. Without as-of-filing-date data, the engine can be blind to the very manipulation it's designed to catch. This is a genuine credibility ceiling versus a Bloomberg/CapitalIQ-backed tool. **Not an MVP blocker — but state it honestly in `docs/data-sources.md` and never let marketing imply filing-grade provenance we don't have.**
- **No confidence/completeness signal.** A 2-period company and a 12-period company render the same authoritative gauge. False precision is how institutional users learn to distrust a tool. Surface a **data-completeness/confidence indicator** (compute in Phase 3, show in Phase 2).

## 1.5 Security & auth posture

JWT+bcrypt is fine for MVP, but the posture is **consumer-grade** and institutional buyers will eventually require more: no refresh tokens (hard 60-min logout — painful for an all-day terminal), no revocation, no RBAC (every user can do everything), no SSO/SAML/MFA, no auth audit logging. **None are MVP blockers**; all are predictable enterprise-sales requirements. Flag as Horizon 2; the `AnalysisRun` audit table (Phase 5) is the first foundation stone toward it.

---

# 2. Product Review — as a premium institutional intelligence platform

Judged against the bar the owner set (Bloomberg / Aladdin / Palantir / Goldman internal tools), here is the honest gap.

**What the product *is* today:** a single-company, one-shot scorer. Type a ticker → wait ~60s → read a score and an AI report. The quant core behind it is real and good. But the *workflow* around it is a demo, not an analyst's tool.

**What feels unfinished (beyond "the tabs are mock"):**
- **No investigation workflow.** Analysts don't run one score; they build a case. There is no saved investigation, no analyst notes/annotations, no dossier, no "flag this for review."
- **No export.** Institutional users *live in Excel and PDF.* The "Export PDF" button is a no-op and there is no CSV/XLSX export of the underlying forensic series. This is table stakes, not a feature.
- **No drill-down to evidence.** A red flag should link to the exact financial line items / news article that triggered it. Right now a flag is an assertion with no traceable provenance — the opposite of forensic.
- **No history, though the data exists.** Every run creates an `AnalysisResult`; the DB *already accumulates* a company's score over time. But the API only ever returns the latest. **Surfacing an integrity-score trend is high value at near-zero data cost** — it's already in the database.
- **Watchlist is a bookmark list, not a monitored portfolio.** No auto-rescore, no change alerts. The empty `tasks/data_refresh.py` stub shows someone *intended* this.

**The features premium users will expect (and the monetization path):**
1. **Portfolio monitoring + alerting** — "score all 47 names in my fund nightly; alert me when any score drops a band." This is the single highest-value institutional capability *and* the natural Pro/Enterprise tier. (Horizon 2.)
2. **Sector-relative benchmarking** — absolute thresholds misjudge a capital-intensive utility vs. a SaaS firm. "AAPL's accrual ratio vs. its sector" is how analysts actually think.
3. **Export & shareable reports** (Phase 8).
4. **Evidence drill-down & company score history** (Phase 9 — both cheap because the data already exists).
5. **Collaboration** (sharing, comments, assignment) and **RBAC/SSO** — enterprise-sales requirements. (Horizon 2.)

**The strategic read:** the order is (a) make the core **honest** (Phase 3) and **verified** (Phase 4), (b) make it **visible** (Phases 2, 6, 7, 8), (c) make it an **analyst workflow** (Phase 9 — history, drill-down, ⌘K), then (d) make it **proactive and defensible** (Horizon 2 — monitoring, alerts, audit, benchmarking). Don't build workflow on top of a score you can't yet trust or reproduce.

---

# 3. UI / UX Philosophy

The owner's brief and CLAUDE.md's design constitution are in violent agreement, so my job here is not to invent a language — it's to **affirm it, sharpen it, and name the one place the brief and the constitution must be reconciled.**

## 3.1 The core direction: "Forensic editorial," not "trading terminal"

The owner referenced Bloomberg's *black terminal*. **I recommend explicitly resisting that cliché.** SentinelIQ's product is *judgment rendered as a document* — "can this company be trusted?" — not a stream of real-time ticks. CLAUDE.md's **warm off-white canvas (#F6F4EF), navy, and serif/mono pairing** already points somewhere better and rarer: the world of the **Financial Times long-read, The Economist, a top-tier audit report, a private-bank dossier.** That warm, printed, editorial register reads as *old-money institutional* and *considered* — which is exactly the trust signal a forensic product wants. **It is more distinctive than another dark dashboard, and it is already half-built. Lean all the way in.**

> **The one reconciliation the owner must rule on:** CLAUDE.md's constitution says **"No dark mode."** The Bloomberg reference implies dark. These conflict. **My recommendation: stay light/warm** — it's the stronger, more differentiated choice and it's already the constitution. *If* a dark "terminal" theme is genuinely wanted later, treat it as a **deliberate constitutional amendment**, not a default — and even then, a *warm dark* (ink-on-charcoal, not neon-on-black). Until the owner says otherwise, Sonnet builds light only.

## 3.2 The system, element by element (all consistent with CLAUDE.md)

- **Typography.** Keep Playfair (hero serif) / Inter (UI) / IBM Plex Mono (**all** numbers — already enforced via tabular-nums in `globals.css`). *Add:* a documented **type scale** (it's the one foundation missing from `globals.css`), generous line-height for report prose, and strict tabular figures in every data column so numbers align vertically like a real financial table.
- **Color.** Affirm the warm palette and the **solid (never gradient) risk colors** — risk is categorical, and a glowing gauge would cheapen it. *Add:* a **muted, desaturated data-viz palette** derived from the risk colors + navy (FT-style, never neon), exposed as **JS-accessible tokens** (charts currently can't read Tailwind classes — see §3.3).
- **Spacing & density.** Resolve the one real tension: the editorial warmth that's perfect for the marketing page and the *report* is too airy for an analyst's *data tables*. **Reports breathe; data tables are dense.** Offer a **comfortable/compact density toggle** (Aladdin, Gmail, and Linear all do this) so power users can pack more rows per screen.
- **Tables.** This is where institutional credibility lives. Hairline dividers, no zebra (per constitution), right-aligned mono numerals, sortable headers, sticky header row, optional sparkline column. Build **one real `DataTable` primitive** and use it everywhere.
- **Charts.** FT-quality: muted fills, hairline gridlines, mono axis labels, restrained annotation, **no** 3D/glow/scroll-animation. The only motion is the existing 700ms gauge arc draw. Build **one `ChartFrame` wrapper** that enforces the theme so no page hand-rolls Chart.js again.
- **Navigation.** Text-only (per constitution) — affirmed. *Add* the single highest-leverage power-user feature: a **⌘K command palette** (jump to company, switch tab, run analysis) — pure Bloomberg-function-key / Palantir / Linear DNA, and it violates none of the constitution's prohibitions.
- **Forms / modals / interactions.** Restrained, fast, no bounce/spring, skeletons-not-spinners, "..." button loading — all per constitution. Build the three missing primitives (`Input`, `Modal`, `Tooltip`) to spec in Phase 1.

## 3.3 One concrete technical UI debt to fix early

`globals.css` defines timing/font/print tokens but **the color palette lives only in Tailwind classes** — so Chart.js (which needs raw hex in JS) currently can't share the design tokens, which is *why* the chart pages hardcode colors inline. Fix in Phase 1 by exposing the palette as CSS variables + a small JS theme object. This single change unblocks consistent, on-brand charts for Phases 2/6/7.

---

# 4. Design Inspirations (what to emulate, and why it matters)

| Inspiration | Emulate this | Why it matters for SentinelIQ |
|---|---|---|
| **Financial Times / The Economist** | Editorial typography, the warm printed canvas, beautiful *restrained* charts, the dignity of long-form analytical layout | This is the closest aesthetic match to the warm palette and to a *report* product. It's the house style for SentinelIQ's voice. |
| **BlackRock Aladdin** | Risk-*first* information hierarchy; **risk decomposition** (a headline number that visibly breaks into contributing factors) | Directly models the Overview tab: Integrity Score → its six weighted components → the flags beneath each. Teaches users to *trust by drilling down*. |
| **Palantir Foundry / Gotham** | Investigation workflow; **drill-down from conclusion to source evidence**; linked entities | The antidote to "AI asserts a flag." Every red flag should trace to the financial line / article that produced it (Phase 9). |
| **Bloomberg Terminal** | Information **density**, keyboard-first operation, mono numerals, the function-command model | Adopt density + the **⌘K command palette**. *Reject* the black background — take the ergonomics, not the skin. |
| **Stripe Dashboard / Linear** | Craft bar, ⌘K, keyboard nav, restraint, "built by people who care" polish | The *quality* benchmark for interactions — not the SaaS-gradient look (which the constitution rightly bans). |
| **Moody's / S&P CapitalIQ research notes** | The **rating + supporting-evidence document** structure | The mental model for the Report tab: a verdict, then the evidence that earns it. |

**The throughline:** take **density and keyboard ergonomics** from the terminals, **typography and chart restraint** from the editorial press, **risk-decomposition** from Aladdin, and **evidence drill-down** from Palantir — all rendered in the warm, light, printed register the constitution already mandates.

---

# 5. UI Transformation Roadmap

**Principle:** do **not** run a separate "redesign" pass over mock pages — they're being rebuilt anyway. Elevate design **in the same pass that wires the data.** Only the cross-cutting foundations come first.

- **UI Phase 0 — Foundations (rides Dev Phase 1).** Type scale; JS-accessible color/chart tokens; build `Input`/`Modal`/`Tooltip` to spec; build the `DataTable` and `ChartFrame` primitives; bring ToastContext to spec and make it non-dead. *Unblocks everything below.*
- **UI Phase 1 — The company workspace (rides Dev Phases 2, 6, 7, 8).** Score gauge + **risk-decomposition** layout, FT-quality forensic charts, red-flag presentation, editorial report typography. The core surface becomes real and beautiful at the same time it becomes real and wired.
- **UI Phase 2 — The analyst layer (rides Dev Phase 9).** ⌘K command palette, density toggle, breadcrumbs, score-history trend, evidence drill-down.
- **UI Phase 3 — Portfolio & monitoring (Horizon 2).** Watchlist becomes a sortable **risk dashboard** with score-change indicators and trend sparklines; alerting UI.
- **UI Phase 4 — Executive & export (rides Dev Phase 8, extends in Horizon 2).** Print-grade report layout (the print stylesheet already exists — build on it), PDF/CSV/XLSX export, shareable report links, eventual portfolio-level executive summary.

---

# 6. Development Roadmap for Sonnet — Ordered Phases

Each phase is **small, independently completable, and safe to stop after.** Sonnet executes **one** per "Start new phase," then writes a completion report and stops. The recommended order front-loads the cheapest safety fix and the foundations, then makes the core *honest and verified* before building more UI on top of it, then wires the surfaces, then hardens and ships. Where useful, I map each phase to Sonnet's original labels.

> **Sequencing rule that matters most:** **Phase 3 (honest scoring) must land before Phase 7 (Narrative tab)**, and **Phase 5 (migrations) must land before Phase 11 (deploy).** Everything else is flexible if the owner wants to reorder.

---

### Phase 1 — Shell Hardening: Route Guard + UI Foundations *(was: C2, F2-partial, C3, C5/C6/C7 stubs)*
- **Objective:** Close the security gap and lay the UI foundations every later phase needs.
- **Scope:** Add the auth guard to `(app)/layout.tsx` (redirect to `/login` once `!isLoading && !user`, no flash). Build `Input`, `Modal`, `Tooltip` to CLAUDE.md spec. Add a documented **type scale** and **JS-accessible color/chart tokens** to `globals.css`/Tailwind config. Bring `ToastContext` to spec (translateX enter, 3000ms, max-3 — Decision #3) and wire it into 2–3 *existing* real actions (login error, watchlist add/remove) so it stops being dead code. Build the reusable **`DataTable`** and **`ChartFrame`** primitives (empty-but-correct shells are fine if no page consumes them yet).
- **Expected files:** `frontend/app/(app)/layout.tsx`, `frontend/components/ui/{Input,Modal,Tooltip}.tsx`, `frontend/app/globals.css`, `tailwind.config.*`, `frontend/contexts/ToastContext.tsx`, new `DataTable`/`ChartFrame` components, callsites in watchlist/login.
- **Risks:** Low. Only real trap: don't redirect before `useAuth`'s initial `getMe()` resolves (loading-flash).
- **Dependencies:** None.
- **Success criteria:** Unauthenticated access to any `/(app)` route redirects to `/login`; the three primitives + DataTable + ChartFrame render in the design-system page; toasts fire on watchlist add/remove and match the spec; `next build` clean.

### Phase 2 — Wire the Company Overview Tab *(was: D2)*
- **Objective:** First real, end-to-end view of the core USP — and the first time anyone *sees* the actual scores.
- **Scope:** Replace all hardcoded literals in `company/[ticker]/page.tsx` with `useCompanyData().analysis` (`AnalysisResultWithFlags`): six `*_score` fields → component cards in a **risk-decomposition** layout, `integrity_score` → gauge, `red_flags` → timeline/items. Design the honest **"not yet analyzed"** empty state (CTA → Run Analysis). Surface a small **data-completeness/confidence** indicator if `module_details` exposes period counts.
- **Expected files:** `frontend/app/(app)/company/[ticker]/page.tsx`; minor additions to `IntegrityGauge`/`ScoreCard` for the empty state.
- **Risks:** Low–Medium — purely read-only consumption of already-typed data; main risk is empty-state polish.
- **Dependencies:** None (Phase 1 primitives help but aren't required).
- **Success criteria:** A real analysis renders real scores/flags; an un-analyzed company shows a clean CTA state; zero hardcoded analysis values remain.

### Phase 3 — Honest, Reproducible Scoring Pipeline *(was: E1, expanded — fixes C-1/C-2/C-3)*
- **Objective:** Make the Integrity Score *honest* (no constant dilution), *resilient* (no stage discards completed work), and *reproducible* (deterministic + auditable). **This is the most important backend phase.**
- **Scope:**
  1. **Refactor `analysis_worker.py` to a uniform stage loop** so per-stage failure is isolated by the orchestrator and Stage 7 always runs (kills C-2 structurally).
  2. **Separate the news fetch from persistence** in Stage 6 — news gets its own neutral-50 fallback; saving scores is a near-infallible step.
  3. **Stage 5:** feed `ConsistencyEngine` real multi-statement input derived from existing `news_text` (Decision #2) so narrative actually varies.
  4. **`fraud_scorer.py`:** when a module lacks a real signal, **renormalize weights across available modules** instead of blending in 50; **temporarily drop narrative from the weighting** until it carries real information. **Update CLAUDE.md** to document this amended scoring rule.
  5. **`gemini_client.py`:** `temperature=0` + add 429 backoff; **persist prompt + model id + raw response into `module_details`** for reproducibility/audit.
- **Expected files:** `backend/app/tasks/analysis_worker.py`, `backend/app/core/scoring/fraud_scorer.py`, `backend/app/core/narrative/consistency_engine.py`, `backend/app/core/ai/gemini_client.py`, `CLAUDE.md`.
- **Risks:** Medium — touches core scoring with **no test net yet** (that's Phase 4). Manually compare before/after scores on 2–3 real tickers; expect scores to *move* (that's the point).
- **Dependencies:** Should land **before Phase 7**. Pairs naturally with Phase 4.
- **Success criteria:** Forcing a news-fetch error still produces a saved report with real forensic scores; `narrative_score` varies across companies; a low-data company is scored only on available modules; re-running the same company yields the *same* governance/narrative scores; `module_details` contains the input + AI provenance.

### Phase 4 — Forensic Test Harness + Backtests + CI *(was: E7/F3, elevated)*
- **Objective:** Put a credibility safety net under the one thing the product cannot get wrong.
- **Scope:** Real `pytest` suite for the four forensic modules + `fraud_scorer` (deterministic known-input→known-score cases straight from CLAUDE.md's formulas); a pipeline integration test with mocked yfinance/Gemini/RSS; at least one **historical backtest** (`backtest_wirecard.py` / `backtest_enron.py`) asserting the engine flags a known fraud as HIGH/SEVERE; `conftest.py` + fixtures; a **GitHub Actions CI** workflow running the suite on push.
- **Expected files:** `backend/tests/unit/*`, `backend/tests/integration/*`, `backend/tests/conftest.py`, `scripts/backtest_*.py`, `.github/workflows/ci.yml`.
- **Risks:** Low (additive). *Best case:* a backtest reveals the engine *doesn't* flag Wirecard well — an enormously valuable finding that justifies the whole phase.
- **Dependencies:** Best immediately after Phase 3 (lock in corrected behavior).
- **Success criteria:** `pytest` runs >0 tests and passes; CI green on push; the Wirecard/Enron backtest yields HIGH/SEVERE (or the gap is documented as a known engine limitation).

### Phase 5 — Data Foundation: `AnalysisRun` + Alembic Baseline + Error Envelope *(was: E2 + E3 — fixes C-4/C-6)*
- **Objective:** Establish the canonical schema and the metering/audit layer monetization and compliance require.
- **Scope:** Add `AnalysisRun(id, user_id, company_id, analysis_result_id, run_at)` (Decision #1); `AnalysisResult` stays company-scoped. Rewrite the free-tier count to query `AnalysisRun` by user+month; log a run even on a cache hit (meter without recompute). Add a **global FastAPI exception handler** emitting `{"error":{"code","message"}}` everywhere (fixes the in-file inconsistency: `routes/analysis.py` uses the envelope at lines 49/56 but plain strings at 75/102/112). Add Pydantic schemas for `module_details` and `NarrativeSnapshot`. Generate the **Alembic baseline** (all models + `AnalysisRun`); `stamp` the dev DB; retire `create_all` in prod.
- **Expected files:** `backend/app/models/analysis_run.py` (+ schema), `backend/app/api/v1/routes/analysis.py`, `backend/app/main.py` (handler + `create_all` guard), `backend/alembic/versions/0001_baseline.py`, `backend/app/schemas/*`.
- **Risks:** Medium — first migration against a `create_all` DB; rehearse on a disposable local Postgres.
- **Dependencies:** Decision #1 (made). **Must precede Phase 11.**
- **Success criteria:** `alembic upgrade head` builds the full schema on a clean DB; quota counts correctly per user/month; every error response shares one shape.

### Phase 6 — Wire Financials Tab + Forensic Charts *(was: D3)*
- **Objective:** Real forensic charts, built once as reusable FT-quality components.
- **Scope:** Build `RevenueQualityChart`, `CashFlowChart`, `DebtTrendChart` on top of Phase 1's `ChartFrame`; rewrite `financials/page.tsx` to consume `module_details.{revenue,cashflow,debt}`; handle short/empty history gracefully (no faking a 12-quarter series from 2 points).
- **Expected files:** `frontend/components/charts/{RevenueQualityChart,CashFlowChart,DebtTrendChart}.tsx`, `frontend/app/(app)/company/[ticker]/financials/page.tsx`.
- **Risks:** Medium — first real use of nested point-arrays; edge cases on thin history.
- **Dependencies:** Phase 1 (`ChartFrame`, tokens); pattern from Phase 2.
- **Success criteria:** Real divergence/accrual/debt series render; charts match the muted FT spec; no inline Chart.js remains.

### Phase 7 — Wire Governance + Narrative Tabs *(was: D4 + D5)*
- **Objective:** Complete the AI-driven tabs against now-*honest* backend data.
- **Scope:** Build `GovernanceChecklist`; wire `governance/page.tsx` to `red_flags` filtered by `flag_type==="governance"` with a sensible event→checklist mapping. Wire `narrative/page.tsx` to `module_details.narrative.snapshots` with an honest partial state — now meaningful because Phase 3 makes narrative vary. Build `RiskRadar` if used.
- **Expected files:** `frontend/components/modules/GovernanceChecklist.tsx`, `frontend/components/charts/RiskRadar.tsx`, the governance + narrative pages.
- **Risks:** Medium — checklist mapping is a small product decision; narrative depth still news-bounded until Horizon 2 transcripts.
- **Dependencies:** **Phase 3 mandatory.**
- **Success criteria:** Governance shows real events; narrative shows real, varying snapshots/score; both have honest empty states.

### Phase 8 — Wire Report Tab + Markdown + Export *(was: D6 + export)*
- **Objective:** Render the real AI report and make it *extractable* — institutional users demand export.
- **Scope:** Add `react-markdown` (first new frontend dep — call it out); build `ReportSection`; wire `report/page.tsx` to `getReport()` → `Report.content` with editorial typography that obeys the constitution. Implement real **PDF export** (lean on the existing print stylesheet first) and **CSV/XLSX export** of the forensic series. Make "Add to Watchlist" work with toast feedback.
- **Expected files:** `frontend/app/(app)/company/[ticker]/report/page.tsx`, `frontend/components/modules/ReportSection.tsx`, an export util, `package.json`.
- **Risks:** Medium — markdown must render within strict typography rules; PDF fidelity.
- **Dependencies:** None hard; richer after Phases 2/3.
- **Success criteria:** Real report renders to spec; PDF/CSV export produce correct files; watchlist-add works.

### Phase 9 — Analyst Workflow Layer: ⌘K + Score History + Evidence Drill-down *(new — the institutional leap)*
- **Objective:** Turn a one-shot scorer into an analyst's tool, using data that mostly already exists.
- **Scope:** A **⌘K command palette** (search companies, jump to tabs, run analysis). Surface **score-over-time** (the DB already accumulates `AnalysisResult` rows — add `GET /analysis/company/{ticker}/history` + a trend chart). Make red flags **drill down to their triggering financial line / news item** (provenance captured in Phase 3).
- **Expected files:** new `CommandPalette` component, `backend/app/api/v1/routes/analysis.py` (history endpoint), drill-down wiring in overview/financials.
- **Risks:** Medium — new endpoint + new interaction surface.
- **Dependencies:** Phase 3 (provenance), Phase 5 (clean data layer).
- **Success criteria:** ⌘K navigates anywhere; a company shows its integrity-score trend across runs; clicking a red flag reveals its source data.

### Phase 10 — Settings Actions + Auth-Page Honesty + Dead-Code Sweep *(was: F1 + F3 + G1)*
- **Objective:** Finish the account surface honestly and shed the dead weight.
- **Scope:** Real `PATCH /auth/me` + `POST /auth/change-password`; wire the Settings Account tab (notification prefs as a JSON column **or** an explicit "coming soon"). Redesign forgot-password/verify-email as honest "not yet available" states and **delete the dev-toggle debug buttons** (they must never ship). **Delete** confirmed dead files: `risk_classifier.py`, `weights.py`, `api/v1/deps.py`, `api/middleware/*`, the 8 empty backend stubs (Decision #4), unused `lucide-react`. Fix the cosmetic nits (redundant ternary, `javascript:history.back()`).
- **Expected files:** backend auth additions; `settings` + auth pages; many small deletions.
- **Risks:** Low — mostly subtractive + small endpoints. If adding a `User` column, sequence after Phase 5.
- **Dependencies:** Phase 5 (if adding a column).
- **Success criteria:** Settings persists name/password; no debug buttons ship; dead files gone; `next build` + backend startup clean.

### Phase 11 — Deployment Dry-Run *(was: H1 — includes the demoted "frontend Dockerfile")*
- **Objective:** Get SentinelIQ live on Vercel + Render with real migrations and restart-resilience.
- **Scope:** Add `frontend/Dockerfile` for local docker-compose parity **or** fix compose/README to reflect that Vercel builds Next.js natively (it does — this is why I demoted it from Critical). Deploy backend + Postgres to Render (`alembic upgrade head`), frontend to Vercel; wire env vars. Add a **`/health` endpoint** and a **"stuck analysis" reaper** (mark `running` > ~10 min as `failed`) to survive Render free-tier spin-downs (§1.3). Smoke-test end-to-end on a real ticker.
- **Expected files:** `frontend/Dockerfile`, optional `render.yaml`/`vercel.json`, `backend/app/main.py` (health + reaper), README fix.
- **Risks:** Medium — first real external infra. **Confirm with the owner at each external step** (creating accounts, connecting GitHub, setting secrets) per operating rules.
- **Dependencies:** **Phase 5 mandatory** (never deploy `create_all`-only schema to managed Postgres).
- **Success criteria:** Public URLs serve the app; a real analysis runs end-to-end in prod; restarting the backend mid-analysis does not leave a permanently-`running` row.

---

## Horizon 2 — Post-MVP Product Bets (not yet numbered phases; owner decides)

These are the moves that take SentinelIQ from "working product" to "institutional platform." Listed so they're on the record, **not** scheduled.

- **Portfolio monitoring + alerting** (nightly batch re-scoring, score-change alerts) — the flagship Pro/Enterprise capability; resurrects the intent behind `data_refresh.py`.
- **Sector-relative benchmarking** — scores judged against sector norms, not just absolute thresholds.
- **Real narrative depth** — the transcript/SEC pipeline (`transcript_fetcher`, `statement_extractor`, `sentiment_scorer`, `sec_scraper`) Phase 3 deliberately defers.
- **Point-in-time / filing-grade data source** — the credibility ceiling in §1.4; likely a paid data dependency, in tension with $0/month.
- **Investigations / case files / collaboration** — saved dossiers, analyst notes, sharing, comments.
- **Enterprise auth** — refresh tokens, RBAC, SSO/SAML, MFA, auth audit logging (building on Phase 5's `AnalysisRun` audit foundation).
- **Job queue** — replace in-process `BackgroundTasks` when scale or reliability demands it (breaks $0/month — a deliberate cost decision).

---

# 7. Ordered Phase List (the execution sequence)

| Order | Phase | Track | Hard dependency |
|---|---|---|---|
| 1 | Shell Hardening (route guard + UI foundations) | Frontend/Safety | — |
| 2 | Wire Company Overview Tab | Frontend | — |
| 3 | **Honest, Reproducible Scoring Pipeline** | Backend/Core | — *(before Phase 7)* |
| 4 | Forensic Test Harness + Backtests + CI | Backend/Quality | after Phase 3 |
| 5 | Data Foundation: `AnalysisRun` + Alembic + error envelope | Backend/Data | *(before Phase 11)* |
| 6 | Wire Financials Tab + Forensic Charts | Frontend | Phase 1 |
| 7 | Wire Governance + Narrative Tabs | Frontend | **Phase 3** |
| 8 | Wire Report Tab + Markdown + Export | Frontend | — |
| 9 | Analyst Layer: ⌘K + Score History + Drill-down | Full-stack | Phases 3, 5 |
| 10 | Settings Actions + Auth Honesty + Dead-Code Sweep | Full-stack | Phase 5 (if new column) |
| 11 | Deployment Dry-Run | Infra | **Phase 5** |

**If the owner wants the shortest path to a *credible demo*:** Phases **1 → 2 → 3 → 4** alone deliver a secured shell, a real Overview screen, an *honest and reproducible* score, and a *verified* engine — the four things that make the product defensible. Everything after is breadth on a sound foundation.

---

## Working Agreement

I (Opus) review, critique, prioritize, and design. Sonnet implements, tests, refactors, and deploys. On **"Start new phase,"** Sonnet reads this roadmap, executes **only the next phase** (default order above, or as the owner amends), completes it fully, writes a completion report, and **stops**. Any change to CLAUDE.md's constitution (e.g., the Phase 3 scoring amendment, or a future dark theme) is made **explicitly and with reasons**, never silently.

**Recommended first phase to authorize: Phase 1 (Shell Hardening).** It closes the live security gap, is low-risk, and unblocks every UI phase that follows.

*End of architectural review. Awaiting the owner's go-ahead to authorize a phase.*
