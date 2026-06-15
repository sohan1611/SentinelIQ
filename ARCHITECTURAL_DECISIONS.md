# SentinelIQ — Architectural Decision Record (ADR Ledger)

**Maintained by:** Claude Opus (Chief Architect / CTO)
**Authority:** Binding on all implementation work unless explicitly overruled by the owner.
**Created:** 2026-06-14

---

## Purpose

This file is the **permanent record of major architectural and product decisions** for SentinelIQ. It exists to:

- **Preserve institutional knowledge** — the *why* behind decisions survives context resets, model changes, and time.
- **Prevent drift** — implementation (Sonnet) must not silently diverge from the agreed vision.
- **Explain reasoning** — every ruling records the alternatives that were rejected and why.
- **Serve as the CTO's ruling book** — when a decision is ambiguous, this file decides.

This ledger sits **alongside** `CLAUDE.md`. `CLAUDE.md` is the *operational constitution* (the concrete rules, formulas, and conventions). This ledger is the *jurisprudence* (the reasoned rulings those rules rest on). Where this ledger makes an explicit ruling, it is authoritative for the subject it covers.

## How to use this file (read this, Sonnet)

1. **Before every new phase, read all four constitution documents** (see *Governance* at the end): `CLAUDE.md`, `PROJECT_STATUS_FOR_OPUS.md`, `OPUS_ARCHITECTURAL_REVIEW.md`, and this file.
2. **Treat every "Final Decision" below as a hard constraint.** Do not re-litigate a decision because it's inconvenient to implement. If implementation reveals a decision is *wrong*, stop, write up the conflict, and escalate to the owner — do not quietly work around it.
3. **When a decision and the code disagree, the decision wins** — bring the code into line (or flag the conflict). The constitution is not updated to match drifted code.
4. **Amendments are explicit.** Changing a ruling means editing this file (or `CLAUDE.md`) with a dated note and reasons — never a silent behavioral change buried in a feature commit.

## Status legend

`Accepted` — in force now · `Accepted (scheduled: Phase N)` — ruled, implementation deferred to a named roadmap phase · `Proposed` — awaiting owner ratification · `Superseded by ADR-NNN` — historical.

---

# ADR-001 — SentinelIQ Is a Premium Institutional Intelligence Platform

**Status:** Accepted · 2026-06-14

### Context
A fraud/trust-scoring product built with modern AI tooling is at constant risk of *reading* like "another AI dashboard." SentinelIQ's output informs high-stakes capital and risk decisions; its entire value rests on being *believed* by skeptical professionals. The product's positioning must be settled first, because it governs every downstream choice — visual design, copy, feature scope, and how a score is allowed to be presented.

### Alternatives Considered
- **Consumer / retail-investor app** (Robinhood-style gamified scores). *Rejected:* cheapens the forensic claim, wrong trust register, and competes on price rather than credibility.
- **Generic AI-SaaS analytics dashboard.** *Rejected:* commoditized, indistinguishable from a hundred others, and signals "auto-generated" — the opposite of forensic rigor.
- **Headless API / data feed only (no UI).** *Rejected:* abandons the analyst workflow and the analyst-style report, which *is* the deliverable.

### Final Decision
SentinelIQ is a **premium institutional intelligence platform** for professionals making high-stakes decisions (equity analysts, risk officers, auditors, investigators, funds). Every surface, sentence, and number must communicate:

> **"This platform assists billion-dollar investigative and risk decisions."**

and must never communicate:

> *"This is another AI-generated dashboard."*

The product's job is **judgment a user can defend to an investment committee** — not a number to glance at. When any decision is ambiguous, choose the option that a Bloomberg/Aladdin/Palantir user would respect.

### Implications
- **UI:** information-dense, restrained, document-grade (see ADR-002/003). No gimmicks.
- **Copy:** analyst-grade, precise, never hype. No exclamation marks, no "AI magic" language, no emoji in product surfaces.
- **AI:** outputs that drive scores must be explainable and reproducible (ADR-004).
- **Backend/DB:** auditability and provenance are first-class (ADR-004, ADR-007).
- **Future:** feature trajectory is *make the score honest → make it visible → make it an analyst workflow → make it proactive (monitoring/alerts)* — per `OPUS_ARCHITECTURAL_REVIEW.md` §2 and §6. Do not chase consumer features.

### Future Reconsideration
Only if the owner deliberately pivots to a retail/self-serve market. That pivot would invalidate most of this ledger and must be made consciously.

---

# ADR-002 — Forensic-Editorial UI Identity

**Status:** Accepted · 2026-06-14

### Context
The owner wants the feel of Bloomberg / Aladdin / Palantir / Goldman internal tools, and explicitly *not* the look of flashy AI startups. `CLAUDE.md` already encodes a mature, opinionated design system (warm canvas, navy, Playfair/Inter/IBM Plex Mono, solid risk colors, no shadows/gradients). The risk is that future work drifts toward generic SaaS styling or "modern dashboard" clichés under deadline pressure.

### Alternatives Considered
- **Dark "trading terminal" skin** (neon-on-black, glowing gauges). *Rejected:* a cliché; cheapens a *judgment* product that is about documents and reasoning, not real-time ticks; and conflicts with the existing warm constitution. (Light/dark settled separately in ADR-003.)
- **Clean modern SaaS** (Vercel/Linear-gradient aesthetic, big rounded cards, drop shadows). *Rejected:* reads "AI-generated," violates `CLAUDE.md`'s no-shadow/no-gradient rules, and lacks institutional gravity.
- **Maximal data-terminal density** (pure Bloomberg, everything monospace, zero whitespace). *Rejected:* sacrifices the editorial dignity that makes the *report* credible; we want density *where data lives* and breathing room *where judgment is read*.

### Final Decision
SentinelIQ's identity is **"Forensic Editorial"** — the register of a top-tier audit report or a Financial Times long-read, not a trading screen.

**SentinelIQ is NOT:** flashy AI SaaS · cyberpunk · neon gradients · glowing dashboards · futuristic gimmicks.
**SentinelIQ IS:** institutional · elegant · editorial · trustworthy · investigative · premium.

**Preferred inspirations and what to take from each:**
| Inspiration | Emulate |
|---|---|
| **Financial Times / The Economist** | Editorial typography, warm printed canvas, restrained beautiful charts |
| **Bloomberg (modernized)** | Information density, keyboard-first ergonomics (⌘K), mono numerals — *not* the black skin |
| **BlackRock Aladdin** | Risk-first hierarchy; a headline number that visibly decomposes into contributing factors |
| **Palantir Foundry** | Drill-down from conclusion to source evidence |
| **Moody's / S&P CapitalIQ** | The rating + supporting-evidence document structure |
| **Stripe Dashboard / Linear** | Craft bar, restraint, keyboard nav — *not* the gradient look |

**Operating principle:** reports breathe; data tables are dense. Take density and keyboard ergonomics from the terminals, typography and chart restraint from the editorial press, risk-decomposition from Aladdin, and evidence drill-down from Palantir — all in the warm, light register the constitution mandates.

### Implications
- **UI/Frontend:** all existing `CLAUDE.md` design rules remain in force (no gradients/shadows/dark/bounce/scroll-animation/AI-illustrations). Build one real `DataTable` and one `ChartFrame` primitive; charts are muted/FT-style; numbers always IBM Plex Mono tabular. Add a comfortable/compact **density toggle** and a **⌘K command palette** (neither violates the constitution).
- **Backend/AI:** the report's markdown must render within these typography rules (ADR drives Phase 8).
- **Future:** any net-new surface is measured against the inspirations table before it ships.

### Future Reconsideration
Revisit only if user research with real institutional users shows the editorial register impedes their workflow (e.g., they demand a denser terminal mode). Even then, evolve — don't abandon.

---

# ADR-003 — Light Mode Is the Primary (and Currently Only) Experience

**Status:** Accepted · 2026-06-14 · *Constitutional ruling requested by owner*

### Context
The owner referenced the Bloomberg **dark** terminal as an aspiration, while `CLAUDE.md` explicitly states **"No dark mode."** This is a direct conflict that must be resolved explicitly rather than left for whoever next touches a stylesheet to decide by accident.

### Alternatives Considered
- **Dark mode as primary** (Bloomberg-terminal literal). *Rejected:* contradicts the warm-canvas identity (ADR-002), and a glowing dark UI undercuts the "considered document" trust signal. The Bloomberg *value* is density + keyboard ergonomics, not the black background — and those we adopt without the skin.
- **Ship both light and dark from the start.** *Rejected:* doubles design/QA surface for zero validated demand pre-launch; invites palette drift; the warm palette does not trivially invert.
- **Warm dark theme** (ink-on-charcoal, not neon-on-black). *Considered, deferred:* the only dark variant that would respect the identity — but still premature.

### Final Decision
**Light mode is the primary and only experience.** The warm off-white canvas (`#F6F4EF`) is core to SentinelIQ's identity. Dark mode stays **out of scope**. If a dark theme is ever introduced, it must be a **deliberate constitutional amendment** to this ADR and `CLAUDE.md`, and it must be a *warm* dark (ink-on-charcoal), never a neon terminal.

### Implications
- **UI/Frontend:** no `dark:` variants, no theme context, no system-preference dark switching. The existing `CLAUDE.md` "No dark mode" rule is hereby **ratified**, not merely inherited.
- **Future:** a warm-dark theme is the *only* sanctioned future dark direction, and only post-launch with real user demand.

### Future Reconsideration
Post-launch, if institutional users with all-day screen exposure explicitly request a low-light mode. Trigger: a documented user request, not a designer's preference.

---

# ADR-004 — Deterministic, Explainable, Auditable AI

**Status:** Accepted (controls scheduled: Phase 3) · 2026-06-14

### Context
The scoring pipeline uses Gemini for the governance score, the narrative score, and the analyst report. Verified in source: `gemini_client.py` calls the model with **no `generation_config`**, i.e. at Gemini's default (~1.0) temperature. Consequence: the **same company can receive different governance/narrative scores and different report prose on repeated runs.** For a product whose entire claim is trustworthiness, a score that won't reproduce is a foundational defect, not a polish item.

### Alternatives Considered
- **Leave AI fully generative (status quo).** *Rejected:* non-reproducible scores are indefensible to an investment committee; identical inputs producing different verdicts destroys credibility.
- **Remove AI from scoring entirely** (quant-only score; AI for prose only). *Considered, partially adopted in spirit:* the headline number leans hardest on the deterministic quant core, and AI-derived sub-scores are constrained (low temperature) and explainable. But governance signal genuinely benefits from LLM extraction, so we keep it — under determinism controls.
- **Cache the first AI result forever per company.** *Rejected as the mechanism:* hides the underlying non-determinism rather than fixing it, and stale governance data is itself a risk; caching is a performance tool (ADR-008), not a determinism fix.

### Final Decision
AI outputs are split into two classes:

1. **Score-bearing / decision-driving outputs** (governance score, narrative score, any future AI sub-score): **must be deterministic and reproducible.** Run at **`temperature = 0`**, with a pinned model id, and **persist the exact prompt, model id, and raw response into `module_details`** so any score can be reproduced and audited after the fact. Add basic 429/backoff handling.
2. **Creative / presentational outputs** (the analyst report prose): may run at low-but-nonzero temperature for readability, but the **factual content it asserts must derive from the deterministic scores and flags**, never invent numbers. The report explains the verdict; it does not compute it.

**Risk and fraud scores must always be explainable and reproducible.** That is non-negotiable.

### Implications
- **AI systems:** `gemini_client.py` gains `generation_config` (temp 0 for scoring) + provenance capture; report generation kept separate and constrained.
- **Database:** `module_details` JSON stores AI provenance (prompt/model/response) per analysis.
- **Backend:** scoring is reproducible given a stored input snapshot.
- **Frontend:** enables future "show the evidence / show the reasoning" drill-down (Phase 9).
- **Future:** any new AI feature must declare which class it belongs to before merging.

### Future Reconsideration
If a future model offers seeded determinism guarantees or materially better structured-output reliability, revisit the exact mechanism — but never the principle that scores must reproduce.

---

# ADR-005 — Fraud & Risk Scoring Philosophy

**Status:** Accepted (weight/renormalization change scheduled: Phase 3) · 2026-06-14

### Context
The Integrity Score is the product. Verified issues in source: `fraud_scorer.py` blends a fixed `value × weight` for six modules, substituting `50.0` for any missing module. Because the narrative module is currently a stub that always returns `50.0` (ADR-006), **10% of every company's score is a constant carrying no information**, pulling every result toward the mean. There is also no signal of how *complete* the underlying data is — a 2-period company and a 12-period company render the same authoritative gauge (false precision).

### Alternatives Considered
- **Keep substituting 50 for missing modules (status quo).** *Rejected:* injects noise, mutes real signal, and makes low-data and rich-data analyses indistinguishable.
- **Drop any company with incomplete data.** *Rejected:* too brittle; most real companies have *some* gap; we'd refuse to score most of the market.
- **Full statistical confidence intervals on the score.** *Rejected:* false rigor — our data quality (free yfinance/RSS) doesn't support honest CIs, and a ± band would imply a precision we don't have.

### Final Decision
The scoring philosophy is governed by these principles:

1. **Quant core leads.** The deterministic forensic modules (revenue, cashflow, earnings, debt) are the backbone of trust. The headline number must lean hardest on them.
2. **No dilution by neutral fill.** When a module has **no real signal**, it is **excluded and the remaining weights are renormalized** — the score reflects what is actually known, not a guess. (This **amends** `CLAUDE.md`'s "return 50.0 neutral" rule; the amendment is scheduled for Phase 3 and must be written into `CLAUDE.md` then.)
3. **News is a minor, nudging signal** (weight 0.10). News sentiment is noisy and lagging; it may move a score at the margin but must never dominate it.
4. **Missing-data handling is honest, not silent.** If too few modules carry real signal to produce a trustworthy score, the analysis is marked **low confidence** rather than emitting a falsely precise number.
5. **Confidence is surfaced, not faked.** Instead of statistical CIs, expose a **data-completeness/confidence tier** (e.g., High/Medium/Low, driven by number of periods and number of modules with real signal). Show it next to the gauge.
6. **Explainability is mandatory.** Every Integrity Score decomposes into its module scores; every module score traces to its formula + inputs (the `module_details` snapshot); every red flag traces to the data that triggered it; AI sub-scores carry provenance (ADR-004).
7. **Honest provenance.** yfinance returns *current/restated* figures, not as-of-filing-date data — and restatements are themselves a fraud signal we may therefore miss. **Never claim filing-grade provenance we do not have.** Document this limitation in `docs/data-sources.md`.

### Implications
- **Backend/AI:** `fraud_scorer.py` renormalizes over present modules; a confidence tier is computed alongside the score.
- **Database:** `module_details` must carry enough input snapshot to reproduce and explain any score.
- **Frontend/UI:** the Overview tab shows the confidence tier and decomposition (Phases 2, 9); red flags drill down to evidence (Phase 9).
- **Future:** sector-relative thresholds (Horizon 2) refine principle #1 without changing it.

### Future Reconsideration
When a higher-quality (paid, point-in-time) data source is adopted, revisit principles #5 and #7 — better data may justify tighter precision claims.

---

# ADR-006 — Narrative Scoring Strategy

**Status:** Accepted (implementation scheduled: Phase 3) · 2026-06-14

### Context
The narrative module is one of the advertised "five independent forensic analyses," but verified in source: `analysis_worker.py` Stage 5 feeds it a **single hardcoded mock statement**, so it can never reach the 2-snapshot minimum, the `narrative_score` is always `50.0`, and zero contradictions are ever detected. The engine itself (`consistency_engine.py`) is correct; it is **starved of input**. Building a real earnings-call/SEC transcript pipeline is a large effort (multiple empty stub modules exist for it).

### Alternatives Considered
- **Build the full transcript pipeline now** (`transcript_fetcher`, `statement_extractor`, `sentiment_scorer`, `sec_scraper`). *Rejected for now:* large scope, new external dependencies, and possibly new cost — blocks the core fix for weeks. Deferred to Horizon 2.
- **Leave the mock in place.** *Rejected:* it silently poisons every score (ADR-005) and misrepresents the product.
- **Delete narrative entirely.** *Rejected:* it's a genuine differentiator worth building; we just shouldn't fake it.

### Final Decision
Two-step strategy:

1. **Now (Phase 3):** feed the narrative engine **real multi-period statements derived from the news text we already fetch** — an honest, shippable signal using existing data. **Until narrative carries real signal, exclude it from the weight vector and renormalize the other modules** (per ADR-005 #2) rather than blending in a constant 50.
2. **Horizon 2:** build the transcript/SEC pipeline for deeper, statement-level narrative analysis. When it lands and is validated, **re-introduce narrative at its 0.10 weight.**

### Implications
- **Backend/AI:** Stage 5 input changes; `fraud_scorer` weight vector changes (and `CLAUDE.md` is amended to record the temporary 5-module renormalization).
- **Frontend/UI:** the Narrative tab (Phase 7) shows real, varying snapshots with an honest partial state — and must be wired **after** Phase 3, never before (building it on always-flat data would bake in mock assumptions).
- **Future:** the transcript pipeline is the trigger to restore the original 6-module weighting.

### Future Reconsideration
When the transcript pipeline ships (Horizon 2), revisit the weight vector and this ADR.

---

# ADR-007 — `AnalysisRun` Data Model & User-Ownership

**Status:** Accepted (implementation scheduled: Phase 5) · 2026-06-14

### Context
The free-tier "5 analyses/month" gate is structurally broken: verified in source, `AnalysisResult` has **no `user_id`**, so `routes/analysis.py` counts a user's usage by joining through `WatchlistItem` — which both under-counts (analyses on un-watchlisted companies are invisible) and over-counts (other users' analyses on a shared company count against you). The code's own comments agonize over this. A correct fix needs a clear ownership model.

### Alternatives Considered
- **Add `user_id` directly to `AnalysisResult`.** *Rejected:* conflates "who requested this" with "the analysis of this company." Two users analyzing AAPL would create duplicate `AnalysisResult` rows, duplicating expensive computation and making "the latest analysis of AAPL" ambiguous (latest by whom?).
- **No persistent metering; rely on an in-memory counter.** *Rejected:* dies on restart, can't audit, can't bill.

### Final Decision
**Separate the artifact from the event:**
- **`AnalysisResult` stays company-scoped** — the canonical, cacheable, *shareable* analysis of a company.
- **Add `AnalysisRun(id, user_id, company_id, analysis_result_id, run_at)`** — a user-scoped log of *who requested an analysis, when*.

The free-tier gate counts `AnalysisRun` rows by `user_id` within the calendar month. On a cache hit (a fresh `AnalysisResult` exists within TTL), **still log an `AnalysisRun`** so the user is metered without recomputation. This model also becomes the **audit trail** institutional/enterprise customers require.

### Implications
- **Database:** new `AnalysisRun` table + its Alembic baseline (Phase 5).
- **Backend:** `POST /analysis/run` rewrites its count query; cache hits log a run.
- **Frontend:** unaffected directly; enables correct quota messaging.
- **Future:** first foundation stone for enterprise audit logging and per-seat billing (Horizon 2). Score-history (Phase 9) reads accumulated `AnalysisResult` rows; usage analytics read `AnalysisRun`.

### Future Reconsideration
If multi-tenant/organization accounts arrive, extend with an `organization_id` dimension rather than reworking ownership.

---

# ADR-008 — Caching, Persistence & the Single-Instance Operating Constraint

**Status:** Accepted · 2026-06-14

### Context
`CLAUDE.md` mandates an in-memory dict cache (no Redis) to hold hosting at $0/month. Verified: the cache (`cache.py`) and the background-task model (`BackgroundTasks`) **both implicitly assume a single process.** This is fine today but is an undocumented constraint that would break silently the moment a second instance/replica exists.

### Alternatives Considered
- **Adopt Redis now.** *Rejected:* breaks the $0/month constraint for no current benefit at single-instance scale.
- **Leave the assumption undocumented (status quo).** *Rejected:* an invisible architectural landmine; whoever scales to 2 instances would face mysterious cache misses and fragmented job state.

### Final Decision
- **Caching is an in-memory, process-local performance optimization** with the documented TTLs (`info` 24h, `financials` 12h, `news` 2h). It is *not* a source of truth and not shared across processes.
- **Persistence rule:** anything that must survive a restart or be shared between users lives in **Postgres**, never only in the cache. Analyses, reports, flags, snapshots are always persisted.
- **The system is explicitly a single-instance deployment** for now. This constraint is **recorded here** and must be respected: do not introduce a second replica without first replacing the cache and job model with shared infrastructure (Redis + a real queue — Horizon 2, a deliberate cost decision).

### Implications
- **Backend:** safe to rely on the in-memory cache; must not rely on it for correctness or cross-user state.
- **Deployment (ADR-012):** Render config stays single-instance; a "stuck analysis" reaper compensates for restarts.
- **Future:** scaling past one instance is a planned, costed migration (Redis + queue), not an incidental change.

### Future Reconsideration
When sustained load approaches the single-instance ceiling or reliability SLAs require it. Trigger: measured contention or an uptime requirement, not speculation.

---

# ADR-009 — Route Protection & Authentication Posture

**Status:** Accepted (guard scheduled: Phase 1) · 2026-06-14

### Context
Verified: `app/(app)/layout.tsx` performs **no auth check** — every protected route (`/dashboard`, `/watchlist`, `/company/[ticker]`, `/settings`) is reachable without a JWT. For a product positioned as institutional (ADR-001), an unguarded app shell is an unacceptable look even pre-launch.

### Alternatives Considered
- **Next.js `middleware.ts` edge guard.** *Considered:* good for redirects, but the JWT lives in `localStorage` (client-only), which edge middleware can't read; would require moving the token to cookies — a larger change.
- **Per-page guards.** *Rejected:* repetitive, easy to forget on a new page.
- **Leave unguarded until later (status quo).** *Rejected:* security/credibility gap.

### Final Decision
Guard at the **`(app)` layout level**: redirect to `/login` once auth has resolved and there is no user (`!isLoading && !user`), avoiding the pre-resolution flash. This is the smallest correct change given the current `localStorage` token model. (Migrating to httpOnly cookies + middleware is a future hardening, not required now.)

**Broader auth posture (recorded, deferred):** the current JWT+bcrypt model is MVP-grade. Refresh tokens, revocation, RBAC, SSO/SAML, MFA, and auth audit logging are **predictable enterprise requirements** but **not MVP blockers**. The `AnalysisRun` audit table (ADR-007) is the first stone toward auditability.

### Implications
- **Frontend:** layout guard (Phase 1).
- **Backend:** unchanged now; enterprise auth is Horizon 2.
- **Future:** cookie-based tokens + edge middleware if/when SSR or stricter security is needed.

### Future Reconsideration
At the first enterprise/security-conscious customer conversation, or when introducing SSR-protected routes.

---

# ADR-010 — Pipeline Resilience: Uniform Stage Isolation

**Status:** Accepted (implementation scheduled: Phase 3) · 2026-06-14

### Context
`CLAUDE.md` promises "the pipeline never aborts on a single-stage failure." Verified: every stage honors this *except* Stage 6, which (a) sets `status="failed"` and `return`s — skipping report generation — and worse, (b) wraps a **flaky news network call in the same `try` as the persistence of already-computed forensic scores**, so a transient news hiccup discards good work and produces no report.

### Alternatives Considered
- **Patch Stage 6's `try`/`except` in place.** *Rejected as insufficient:* fixes the symptom but leaves the fragile structure (next refactor could reintroduce it).
- **Full job-framework rewrite.** *Rejected as overkill:* the $0/month single-instance model doesn't justify it yet (ADR-008).

### Final Decision
Refactor `analysis_worker.py` into a **uniform stage loop**: an ordered list of named stages, each isolated by the *orchestrator's* error handling with a neutral fallback, accumulating into a shared context, with **persistence as a separate, near-infallible final step** and **Stage 7 (report) always reached.** Network calls (e.g. news) get their own fallback and never gate persistence. This makes the "never abort" invariant **structural**, not per-stage discipline, and makes each stage unit-testable (ADR-011).

### Implications
- **Backend:** `analysis_worker.py` restructured (within Phase 3, alongside the scoring fixes).
- **Future:** the stage-list abstraction is the natural seam for a real queue later (ADR-008 Horizon 2).

### Future Reconsideration
When migrating to an external job queue, the stage loop becomes the task unit.

---

# ADR-011 — Testing Is a Credibility Requirement, Not Optional

**Status:** Accepted (implementation scheduled: Phase 4) · 2026-06-14

### Context
Verified: zero automated tests exist; all test files are 0-byte stubs. The forensic engine — the product's entire credibility — is **deterministic pure math with formulas written down in `CLAUDE.md`**, making it simultaneously the most important and the easiest thing to test.

### Alternatives Considered
- **Defer tests until post-launch (Sonnet's original Low ranking).** *Overruled:* an untested fraud-scoring engine cannot be honestly sold as institutional-grade, and every Phase-3 scoring change risks silent regression with no net.
- **Manual testing only.** *Rejected:* not repeatable, not CI-enforceable, doesn't survive refactors.

### Final Decision
Testing the scoring core is a **first-class, early deliverable (Phase 4)**, not a backlog item:
- Deterministic unit tests for all four forensic modules + `fraud_scorer`, with known-input→known-score cases drawn straight from `CLAUDE.md`'s formulas.
- A pipeline integration test (mocked yfinance/Gemini/RSS).
- At least one **historical backtest** (Wirecard/Enron) asserting the engine flags a known fraud as HIGH/SEVERE — *or* documenting the gap if it doesn't (itself a valuable finding).
- **GitHub Actions CI** running the suite on push (free, preserves $0/month).

### Implications
- **Backend:** real `tests/` suite + `conftest.py`/fixtures; CI workflow.
- **Future:** every subsequent backend phase extends the suite; CI gates merges.

### Future Reconsideration
The *floor* only rises. This decision is not revisited downward.

---

# ADR-012 — Deployment Shape & the $0/Month Constraint

**Status:** Accepted (execution scheduled: Phase 11) · 2026-06-14

### Context
`CLAUDE.md` targets Vercel (frontend) + Render free tier (backend + Postgres), $0/month. Sonnet flagged a missing `frontend/Dockerfile` as Critical. Verified reality: **Vercel builds Next.js natively and does not use a Dockerfile** — the missing file only breaks the local `docker-compose` convenience path, not the production deploy.

### Alternatives Considered
- **Treat the missing Dockerfile as a deploy blocker (Sonnet's framing).** *Overruled:* it doesn't block the Vercel path; it's a local-parity nicety.
- **Move off free tier for reliability.** *Rejected now:* the $0/month constraint stands until there's a reason (and budget) to relax it.

### Final Decision
- **Deployment shape:** Vercel (frontend, native build) + Render (backend + managed Postgres), **$0/month**, **single instance** (ADR-008).
- **`frontend/Dockerfile`** is **High, not Critical** — add it for local `docker-compose` parity (or fix compose/README to reflect Vercel's native build), in Phase 11.
- **Migrations gate deploys:** never deploy to managed Postgres with `create_all`-only schema management. **Phase 5 (Alembic baseline) is a hard prerequisite for Phase 11.**
- **Restart resilience:** add a `/health` endpoint and a startup **"stuck analysis" reaper** (mark `running` > ~10 min as `failed`) to survive Render free-tier spin-downs.
- **External steps require owner confirmation:** creating Render/Vercel projects, connecting GitHub, and setting secrets are owner-in-the-loop actions (per operating rules).

### Implications
- **Infra/Backend:** `/health` + reaper; Alembic gates the deploy.
- **Frontend:** Dockerfile or doc fix; Vercel project.
- **Future:** the move off free tier (and to multi-instance, Redis, a queue) is one coordinated, costed decision (ADR-008 Horizon 2).

### Future Reconsideration
When uptime/scale requirements or a paying customer justify leaving the free tier.

---

# Minor Rulings

Smaller decisions, recorded for completeness so they aren't silently reversed.

- **MR-1 — ToastContext conforms to the constitution.** The implemented toast deviates from `CLAUDE.md` (translateY both directions, 4000ms, no max-3 cap). **Ruling:** bring the *code* to the *spec* (translateX enter, 3000ms, max-3) — the constitution wins. Scheduled: Phase 1. *(= OPUS review Decision #3.)*
- **MR-2 — Dead/stub files are deleted, not carried.** The 0-byte backend stubs (`risk_classifier.py`, `weights.py`, `api/v1/deps.py`, `api/middleware/*`, the 8 "planned" modules) and unused deps (`lucide-react`) are **deleted** in the cleanup phase; their *intent* is tracked in `OPUS_ARCHITECTURAL_REVIEW.md` (Horizon 2) and re-created only when their feature is scheduled. Empty files are not a plan. Scheduled: Phase 10. *(= OPUS review Decision #4.)*
- **MR-3 — Honest stubs over fake flows.** Forgot-password / verify-email pages must become honest "not yet available" states with the dev-only debug toggles **removed**, unless real email flows are explicitly prioritized. Scheduled: Phase 10.

---

# Governance — How These Documents Bind Sonnet

### The four constitution documents

| Document | Role |
|---|---|
| `CLAUDE.md` | **Operational constitution** — concrete rules, formulas, conventions, design system. |
| `PROJECT_STATUS_FOR_OPUS.md` | **Current-state ground truth** — what exists, what's broken, what's mock. |
| `OPUS_ARCHITECTURAL_REVIEW.md` | **The plan** — phased roadmap, ordered execution, success criteria. |
| `ARCHITECTURAL_DECISIONS.md` (this file) | **The ruling book** — *why*, with binding decisions and rejected alternatives. |

### Mandatory protocol

1. **Before starting any new phase**, Sonnet reads **all four** documents before making any architectural or UI change.
2. Sonnet executes **only the next authorized phase**, completes it fully, writes a **completion report**, and **stops**.
3. Sonnet **follows these decisions unless explicitly overruled by the owner.** A decision that's inconvenient is still binding; a decision that's *wrong* is escalated, not worked around.
4. **Amendments are explicit and dated.** Any change to a ruling here (or to `CLAUDE.md`) is a conscious edit with reasons — never a silent behavioral change inside a feature commit. The CTO (Opus) authors amendments; the owner ratifies anything constitutional (e.g., ADR-003 light/dark, ADR-005's scoring change).
5. **Precedence:** for any subject this ledger explicitly rules on, this ledger is authoritative. For concrete rules/formulas/conventions, `CLAUDE.md` is authoritative. The owner overrides both.

### Pending / scheduled amendments to `CLAUDE.md`

These are **ruled but not yet applied** — to be written into `CLAUDE.md` when their phase executes (so doc and code change together):

- **Scoring rule (ADR-005/006):** replace "if ALL periods … return 50.0 neutral" / the fixed 6-module weight blend with **weight renormalization over modules that carry real signal**, and the **temporary 5-module weight vector** (narrative excluded until transcripts land). Apply in **Phase 3**.
- **Design-system reference:** add a short pointer in `CLAUDE.md` to this ledger and the reading protocol (applied now — see below).

---

*End of ADR ledger. New major decisions are appended as ADR-013, ADR-014, … with the same structure. This file is authoritative; keep it honest.*
