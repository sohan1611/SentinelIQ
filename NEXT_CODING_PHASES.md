# NEXT_CODING_PHASES — SentinelIQ (Sonnet workplan)

**Author:** Claude Opus (CTO / Chief Architect)
**Date:** 2026-06-17
**Audience:** Claude Sonnet (Lead Implementation Engineer), owner-authorized
**Supersedes the forward roadmap of** `OPUS_ARCHITECTURAL_REVIEW.md` §7 (Phases 9–12),
which are now **complete and verified** (commits `6e003ead` … `a0b1a2d1`). This document
defines **Phases 13 onward.**

> **Protocol (unchanged).** On "Start new phase," read all four constitution docs, execute
> **only the next authorized phase**, complete it fully, write a completion report, and
> STOP. Commit identity is owner-only (no `Co-Authored-By` trailer, ever). Push after the
> phase. Work in the small "STEP COMPLETE → NEXT" cadence already established.

**Sequencing rationale.** Ordered by the brief's priorities — **institutional trust →
explainability → reliability → scalability → elegant UX** — never by flashiness. Honesty
cleanup (13) is first because doc drift already started *this week* (the model-name
upgrade left `docs/` stale) and drift is the one thing the ADR ledger exists to kill. AI
grounding (14) is the single highest-value item: it converts the product's central legal
liability into its strongest credibility feature. The rest harden what exists before any
new capability is added.

| Phase | Title | Track | Priority |
|---|---|---|---|
| **13** | Honesty & Drift Cleanup | Docs / cleanup | **Highest (do next)** |
| 14 | AI Grounding & Anti-Hallucination | Backend / AI / credibility | Critical |
| 15 | `module_details` Schema Versioning | Full-stack / robustness | High |
| 16 | Reliability: Timeouts + AI Cost Guard | Backend / reliability | High |
| 17 | Live-Data Validation Harness | Backend / tooling | High (after founder deploy) |
| 18 | Security Hardening: Rate Limiting + Auth | Backend / security | Medium |
| 19 | Accessibility Completion + Reduced-Motion | Frontend / a11y | Medium |
| H2+ | Horizon 2 (owner-scheduled) | — | see `FUTURE_ARCHITECTURE.md` |

---

## Phase 13 — Honesty & Drift Cleanup

**Objective.** Bring every document and dead artifact back into truth with the code. No
behavior change; subtractive and corrective only.

**Why it matters.** The product's rarest asset is its intellectual honesty. Right now:
`README.md` claims it analyzes "filings, transcripts" (it does **not** —
`docs/data-sources.md` says so explicitly) and tells users to `docker-compose up -d` (the
frontend has no Dockerfile and compose seeds from a stale schema); `docs/data-sources.md`
(×3) and `docs/scoring-methodology.md` (×1) still say "Gemini 1.5 Flash" one commit after
the 2.0 upgrade; `docs/api-reference.md` and `docs/architecture.md` are **0 bytes** yet
the README points users to them; nine **0-byte stub files** remain that MR-2 (binding)
ruled should be deleted; and two schema systems coexist (`database/*.sql` + `schema.sql`
vs the authoritative `backend/alembic/`), with `docker-compose.yml` actively seeding the
*stale* one. An institutional brand cannot survive a README that contradicts its own
methodology docs.

**Dependencies.** None.

**Files/modules affected.**
- `README.md` — remove "filings/transcripts" overclaim; fix or remove the Docker
  instructions; stop pointing to empty docs.
- `docs/data-sources.md`, `docs/scoring-methodology.md` — `Gemini 1.5 Flash` →
  `Gemini 2.0 Flash` (4 occurrences total).
- `docs/api-reference.md`, `docs/architecture.md` — fill them (even minimally) or delete
  them and the README references.
- The 9 zero-byte stubs (`backend/app/core/governance/{board_analysis,exec_turnover}.py`,
  `backend/app/core/narrative/{sentiment_scorer,statement_extractor,transcript_parser}.py`,
  `backend/app/core/scoring/{risk_classifier,weights}.py`,
  `backend/app/services/{sec_scraper,transcript_fetcher}.py`) — **resolve MR-2**: either
  delete them (preferred per the ruling; intent is tracked in `FUTURE_ARCHITECTURE.md` H2)
  **or** write a dated amendment to MR-2 in `ARCHITECTURAL_DECISIONS.md` consciously
  keeping them as H2 markers. Not silently half-done. Note `data-sources.md` references
  `sec_scraper.py`/`transcript_fetcher.py` — keep doc and decision consistent.
- `database/` (raw SQL migrations + `schema.sql`) and `docker-compose.yml` — retire the
  raw-SQL schema as a source of truth; make compose run `alembic upgrade head` (or remove
  the frontend service / add a frontend Dockerfile) so the local path matches production.
- A single source of truth for the model name (e.g. reference `DEFAULT_MODEL_ID`) to stop
  this drift recurring.

**Risks.** Very low (no runtime code). Only risk: deleting a stub that is secretly
imported — grep each before deletion (they are 0 bytes, so safe).

**Success criteria.** README claims match `data-sources.md`; no doc says "1.5 Flash"; no
0-byte file remains unresolved (deleted or consciously documented); one schema system;
`docker-compose up` either works or is removed from the README; a fresh reader can trust
every doc.

---

## Phase 14 — AI Grounding & Anti-Hallucination

**Objective.** Make every score-bearing AI claim *grounded*: the model must cite the exact
source span for each governance event (and each narrative claim), and the backend drops
any claim whose citation is not found verbatim in the input text.

**Why it matters.** This is the product's central credibility and **legal** risk and it is
architecturally unmitigated today. `governance_scorer.py` asks Gemini to extract
governance events from headlines with no grounding; each becomes a persisted `RedFlag` +
risk label + report prose about a **real named public company**. M-5 validated JSON shape,
not truth. A fabricated "auditor resigned amid investigation" is a defamation vector that
the ADR-014 disclaimer covers legally but does not *fix*. Grounding also makes the
already-built evidence drill-down (Phase 11) actually trustworthy — it would drill down to
a *quoted source*, not an ungrounded assertion.

**Dependencies.** Phase 13 (clean base); founder item 2 (the owner must first quantify the
false-positive rate on real data — this phase implements the policy that follows).

**Files/modules affected.**
- `backend/app/core/ai/prompts/governance_prompt.txt`,
  `backend/app/core/ai/prompts/narrative_prompt.txt` — require a `source_quote` field per
  event/claim.
- `backend/app/core/governance/governance_scorer.py` — add `source_quote` to
  `GovernanceEvent`; **drop any event whose `source_quote` is not a verbatim substring of
  `news_text`**; only grounded events deduct points and persist as flags.
- `backend/app/core/narrative/consistency_engine.py` — same grounding gate for any claim.
- `frontend/lib/utils/redFlag.ts` + `frontend/components/modules/RedFlagItem.tsx` —
  surface the grounded `source_quote` in the evidence panel.
- `backend/tests/` — add tests with an ungrounded/hallucinated event in the mock response
  and assert it is dropped.
- `docs/scoring-methodology.md` — document the grounding contract.

**Risks.** Over-aggressive dropping could zero out governance on legitimately-phrased
events (model paraphrases instead of quoting) — mitigate with a fuzzy/normalized substring
match and log drops for tuning. Keep `temperature=0` (ADR-004).

**Success criteria.** No governance flag persists without a verbatim source quote from the
input; a hallucinated event in a test is provably dropped; the evidence panel shows the
quote; false-positive rate (founder-measured) drops materially.

---

## Phase 15 — `module_details` Schema Versioning

**Objective.** Replace the free-form `module_details` JSON with a versioned Pydantic
contract carrying `schema_version`, consumed by a typed frontend shape.

**Why it matters.** `module_details` is untyped JSON the UI reaches into with optional
chaining; a backend shape change fails *silently* in the UI. This already happened —
Phase 11 Step 2 had to fix `tone_shifts`/`low_confidence` being silently dropped by
Pydantic's `extra="ignore"`. It will recur as the blob grows (it grows every horizon). Fix
it while it's small (OPUS review §9.6).

**Dependencies.** Phase 13.

**Files/modules affected.**
- `backend/app/schemas/analysis.py` — a versioned `ModuleDetails` model with explicit
  sub-models (`revenue`, `cashflow`, `earnings`, `debt`, `narrative`, `governance`,
  `scores`, `confidence`) + `schema_version: int`.
- `backend/app/tasks/analysis_worker.py` (`_stage_score_persist`) — write through the typed
  model.
- `frontend/types/analysis.ts` — mirror the versioned shape; handle older rows
  (`schema_version` absent → legacy reader).
- `backend/tests/unit/test_analysis_schemas.py` — round-trip + version tests.

**Risks.** Existing rows lack `schema_version` — the reader must treat missing as v0 and
not crash. Keep changes additive; do not invalidate stored analyses.

**Success criteria.** `module_details` is a typed, versioned contract; a missing field is a
type error at build time, not a silent runtime gap; old analyses still render.

---

## Phase 16 — Reliability: Request Timeouts + AI Cost Guard

**Objective.** Bound every external call with an explicit timeout, and add a global Gemini
daily-budget guard that degrades gracefully.

**Why it matters.** No external call (`yfinance`, `feedparser`, Gemini) has a timeout
today; a hung socket hangs the worker for 10 minutes until the reaper sweeps it — a poor
experience and a Render-free-tier hazard. Separately, the pipeline is economically
backwards: narrative makes ~5 of ~7 Gemini calls per analysis while carrying **zero
weight**; ~200 analyses/day exhausts the free tier on the *least* valuable module.

**Dependencies.** Phase 13.

**Files/modules affected.**
- `backend/app/core/ai/gemini_client.py` — per-call timeout on
  `client.aio.models.generate_content`; a process-wide daily call counter that returns a
  neutral/low-confidence result (not an error) when the budget is hit.
- `backend/app/services/yahoo_finance.py`, `backend/app/services/news_aggregator.py` —
  timeouts on the `to_thread`/feedparser/yfinance calls.
- `backend/app/tasks/analysis_worker.py` (`_stage_narrative`) — throttle narrative to ≤2
  statements (or gate it behind a feature flag) until H2 transcripts justify the spend.
- `docs/data-sources.md` / `docs/scoring-methodology.md` — note the budget behavior.

**Risks.** Timeouts too tight cause spurious neutral scores on slow-but-fine networks —
choose generous values (e.g. 15–20s) and log timeouts. The budget guard must fail
*neutral*, never crash (preserve ADR-010's "never abort").

**Success criteria.** Every external call has a timeout; a simulated hang fails its stage
in seconds, not minutes; Gemini calls per analysis drop (narrative throttled); a budget
breach yields a clean low-confidence result.

---

## Phase 17 — Live-Data Validation Harness

**Objective.** A repeatable smoke-test path that runs the real core loop against a real DB
+ real Gemini key, plus fixes for whatever the first real run surfaces.

**Why it matters.** The product has never executed its core loop on live data (every check
to date is static). The first real run *will* surface issues no static check can —
yfinance shape drift, Gemini quota/format reality, real governance hallucinations,
cold-start timing. This phase turns "it compiles" into "it works."

**Dependencies.** Founder items 1, 4, 6 (a real DB + key must exist first). Phases 13–14
(so the first real scores are honest and grounded).

**Files/modules affected.**
- `backend/scripts/` — a `smoke_test.py` that runs `run_full_analysis` against a configured
  DB for a list of real tickers and prints the resulting scores + flags for human review.
- `backend/tests/integration/` — promote any real-world failure into a regression test
  (with mocked externals so CI stays free).
- Whatever core files the first run reveals as broken (cannot predict precisely — that is
  the point of the phase).

**Risks.** Requires real credentials (owner-supplied) — this phase is partly gated on the
founder. Keep secrets out of the repo and CI.

**Success criteria.** A documented command produces real scores for ≥3 real tickers;
issues found are fixed and regression-tested; the team has seen the product actually work.

---

## Phase 18 — Security Hardening: Rate Limiting + Auth Posture

**Objective.** Add HTTP rate limiting to auth + analysis endpoints; close auth-posture
gaps that don't require the full enterprise-auth lift.

**Why it matters.** `auth.py` login/register have **no rate limiting** — the login
endpoint is brute-forceable and the 5/month gate is business logic, not security.
`register` leaks user existence ("The user with this email already exists"). For a product
positioned as institutional, these are visible gaps. (Full refresh-token/RBAC/SSO remains
Horizon 2 per ADR-009 — not this phase.)

**Dependencies.** Phase 13.

**Files/modules affected.**
- `backend/app/main.py` or a new middleware — IP-based rate limiting (a lightweight
  in-memory limiter respecting the single-instance constraint, ADR-008).
- `backend/app/api/v1/routes/auth.py` — neutralize the register enumeration message;
  consider a small login backoff.
- `backend/app/api/v1/routes/analysis.py` — rate-limit `POST /run` beyond the monthly gate.
- `backend/tests/` — limiter tests.

**Risks.** In-memory limiting resets on restart and is per-instance (acceptable under
ADR-008; note it). Don't lock out legitimate users — tune thresholds.

**Success criteria.** Repeated failed logins are throttled; register no longer reveals
account existence; `/analysis/run` is rate-limited; documented as single-instance-scoped.

---

## Phase 19 — Accessibility Completion + Reduced-Motion

**Objective.** Extend the Phase-12 ARIA pass beyond the gauge/bars to the full app, and
honor `prefers-reduced-motion`.

**Why it matters.** Phase 12 added `role="meter"` to the gauge and component bars only.
Tables (`DataTable`), the ⌘K command palette, nav, the `Modal` (focus trap + focus
return), and form error associations were not audited; the 700ms gauge animation ignores
`prefers-reduced-motion` (a WCAG concern, and restraint is on-brand per ADR-002).
Institutional buyers increasingly require accessibility conformance.

**Dependencies.** None (can run anytime; placed late as it's polish, not credibility).

**Files/modules affected.**
- `frontend/components/layout/CommandPalette.tsx` — `role="dialog"`, focus trap, `aria-activedescendant` for the listbox.
- `frontend/components/ui/Modal.tsx` — focus trap + return-focus-on-close.
- `frontend/components/ui/DataTable.tsx` — proper table semantics / scope.
- `frontend/components/charts/IntegrityGauge.tsx` — respect `prefers-reduced-motion`
  (render final state without the arc/counter animation).
- Form inputs (`Input.tsx`, auth pages) — `aria-describedby` wiring for errors.

**Risks.** Minimal; visual-only. Verify keyboard flows manually.

**Success criteria.** Keyboard-only navigation works across palette/modal/tables; reduced-
motion users get a static gauge; an automated a11y pass (axe) shows no critical violations.

---

## Horizon 2 phases (owner-scheduled — summary only)

Detailed in `FUTURE_ARCHITECTURE.md`. These break the $0/month constraint and/or add major
capability; each needs an explicit owner go-ahead and its own ADR before it becomes a
numbered phase here:

- **H2-A — SEC EDGAR point-in-time data pipeline** (`sec_scraper.py`) — the deepest
  credibility lever; likely paid. *The single highest-value future investment.*
- **H2-B — Transcript/SEC narrative NLP** (`transcript_fetcher.py`, `statement_extractor.py`,
  `sentiment_scorer.py`) — makes narrative honest by construction; re-introduce at 0.10
  weight (ADR-006 step 2).
- **H2-C — Sector-relative thresholds** — large credibility gain, low cost once data exists.
- **H2-D — Job queue + Redis + multi-instance** (ADR-008) — the stage-loop is already the
  task unit (ADR-010).
- **H2-E — Portfolio monitoring + alerting** (the paid-tier surface; Settings already
  advertises it).
- **H2-F — Enterprise auth** (refresh/revocation/RBAC/SSO/MFA/audit) (ADR-009 H2).

---

*End of workplan. Phases 13–19 are Horizon 1 hardening; everything beyond is owner-gated
Horizon 2. Recommended next phase to authorize: **Phase 13 (Honesty & Drift Cleanup).***
