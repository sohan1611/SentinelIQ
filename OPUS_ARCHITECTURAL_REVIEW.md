# SentinelIQ — Architectural Review & Roadmap (v2, AUTHORITATIVE)

**Author:** Claude Opus, acting as Chief Architect / CTO / Product Strategist
**Audience:** Claude Sonnet (Lead Implementation Engineer), and the project owner
**Date:** 2026-06-15
**Supersedes:** v1 (2026-06-14), whose forward roadmap (Phases 1–11) is now consumed — Phases 1–8 are complete and verified. This document is the **authoritative architectural guide for all future implementation phases.**
**Inputs reviewed:** a direct, code-level re-read this session of the load-bearing source — `analysis_worker.py`, `fraud_scorer.py`, all four forensic modules, `gemini_client.py`, `governance_scorer.py`, `consistency_engine.py`, `news_aggregator.py`, `report_generator.py`, `routes/analysis.py`, `main.py`, `database.py`, and the company overview page — plus `PROJECT_STATUS_FOR_OPUS.md` (the as-built verification) and the ADR ledger. Where a claim rests on prior-session verification rather than this turn's read, it is marked.

> **Status & use of this document.** This is a review and a plan, not code. On a future **"Start new phase"** command, Sonnet reads this file, executes exactly **one** phase from §7/§8, fully, writes a `## Phase Completion Report`, and stops. Design direction lives in `ARCHITECTURAL_DECISIONS.md` (ADR-002/003) and `CLAUDE.md`; the as-built state of Phases 1–8 lives in `PROJECT_STATUS_FOR_OPUS.md`. This doc is authoritative for *what comes next and why*.

---

## 0. Owner Rulings (BINDING — 2026-06-15)

Two decisions were escalated to the owner during this review and are now resolved. They are binding and should be ratified into `ARCHITECTURAL_DECISIONS.md` as ADR-013 and ADR-014 in Phase 9 (which already touches docs).

**Ruling A — Cache-hit quota (amends ADR-007).** A cached re-open **does not consume** a free user's monthly quota. Only a *fresh computation* counts against the 5/month limit. The `AnalysisRun` row should still be written on a cache hit (audit trail preserved), but flagged so it is **excluded from the quota count**. Implementation in Phase 10, §8.

**Ruling B — Legal disclaimer wording (becomes ADR-014).** Every analysis view shows, persistently:

> **"Algorithmic screening signal only. Not investment advice and not an accusation."**

The owner has reserved the right to expand this before any public release. Implementation in Phase 9, §8.

---

## 1. Executive Summary

Phases 1–8 are complete and, on the whole, **genuinely strong work** — the engineering is well above typical MVP quality. The stage-isolated pipeline, weight renormalization, AI provenance capture, Alembic baseline, global error envelope, and JS-accessible design tokens are all correct and well-built. I verified the load-bearing claims against source; they hold.

**The one-sentence state of the project:** *SentinelIQ now has an honest, reproducible, tested quantitative core wrapped in a real (no longer mock) single-company UI — but three small defects let the product display claims it cannot defend, one reliability gap will produce stuck analyses on the deployment target, and the narrative module is honest in its score weighting yet dishonest in its labeling.*

**Where the work is strongest (protect, don't touch):**
- **Pipeline correctness.** `analysis_worker.py:256` runs stages in an isolated loop; `database.py:14` sets `expire_on_commit=False`, which is precisely what makes it safe for the report stage to read flag/snapshot ORM objects collected across earlier commits. This pairing is subtle and correct.
- **Scoring math.** `fraud_scorer.compute_integrity_score` (`fraud_scorer.py:14`) renormalizes over modules with real signal, honors the `None`-vs-`50.0` distinction, and degrades to `(50.0, "low")` when nothing is available. All four forensic modules match CLAUDE.md's formulas exactly, including the divide-by-zero guards.
- **Data & error foundations.** `AnalysisRun` cleanly separates metering from cacheable results; the three-handler error envelope (`main.py:44`) is correct and avoids double-wrapping.

**Where it falls short (the headlines of this review):**

1. **[Credibility] The narrative module mislabels news headlines as "management commentary"** and persists news-cycle mood swings as forensic "narrative" red flags. Zero-weighting (ADR-006) protected the *score*; it did not protect the *flags, snapshots, or report prose*. This is the most important finding.
2. **[Credibility] Missing scores render as a red `0.0`.** A failed module (`None`) is visually identical to a real catastrophic score (`page.tsx:181`, `analysis[key] ?? 0`). This silently violates ADR-005's "missing-data honest, not silent."
3. **[Credibility] No news coverage yields a perfect `100.0` governance score** (`governance_scorer.py:26`) — absence of signal masquerading as positive signal.
4. **[Reliability] In-process `BackgroundTasks` + no reaper + Render free-tier spin-down = permanently stuck analyses** (`analysis.py:78`). The frontend polls a `running:` row forever.
5. **[Legal] No disclaimers anywhere** on a product that publishes algorithmic fraud-risk judgments about real, named public companies. Resolved by Ruling B; must ship.

None of these require rework. All are surgical. The fix order is deliberate: **make the output honest (Phase 9), make the backend reliable and live (Phase 10), then build the analyst workflow (Phase 11)** — never the reverse.

---

## 2. Review of Completed Phases (1–8)

| Phase | Commit | Grade | Verdict |
|---|---|---|---|
| 1 — Shell Hardening | `e1aef878` | **Excellent** | Guard, primitives, JS tokens clean. Nothing to fix. |
| 2 — Overview wiring | `36580d51` | **Needs Revision** | Real data wiring good; **null renders as red 0.0**; confidence ignored in favor of a hand-rolled period heuristic. |
| 3 — Scoring pipeline | `bbb092f4` | **Good (architecture) / Needs Revision (narrative substance)** | Stage isolation, renormalization, provenance are textbook-correct. Narrative is fed semantically wrong inputs. |
| 4 — Tests + CI | `1c193813` | **Good** | 70 tests collect; backtests now real (`backend/scripts/`); CI present. Duplicate 0-byte stubs at repo root; assertion quality not graded this review. |
| 5 — Data foundation | `4e968b0c` | **Excellent** | AnalysisRun, Alembic, error envelope correct. Minor: check-then-act race; cache-hit metering (now corrected by Ruling A). |
| 6 — Financials charts | `58ab07b8` | **Good** | Clean ChartFrame reuse, empty states. (Relied on prior read + page structure.) |
| 7 — Governance/Narrative | `63029f0b` | **Good / Needs Revision** | Governance wiring good; narrative tab inherits Phase 3's substance problem. Dead `RiskRadar.tsx` stub. |
| 8 — Report + exports | `88e99b8c` | **Good** | Markdown rendering solid; report prose propagates the narrative mislabel; PDF is `window.print()` (acceptable MVP). |

### Detailed findings (by severity, with evidence)

**[Blocker-class, small fixes — product makes claims it cannot defend]**

- **N-1 — Narrative = news headlines mislabeled as management commentary.** `fetch_news_statements` (`news_aggregator.py:72`) returns Google News *headlines* tagged `source:"News"`, period = article publish date. `ConsistencyEngine` (`consistency_engine.py:46`) scores each, then flags "significant tone shift between {period} and {period}" as a **narrative red flag** (`severity high/moderate`). A positive headline Monday + negative Wednesday becomes a forensic "contradiction." The frontend labels the module "tone and consistency of *management commentary* across reporting periods" (`page.tsx:58`) and the report calls it "linguistic analysis of recent management commentary." It is not. Fix: stop persisting narrative red flags, relabel as "News Tone (experimental)," correct the report framing. (Phase 9.)
- **N-2 — Missing scores render as red 0.0.** Worker stores `None` for a failed module (`analysis_worker.py:185`); API returns null; overview does `analysis[key] ?? 0` (`page.tsx:181`) → full-width severe-red bar at 0.0. A Gemini outage is indistinguishable from a catastrophic finding. Fix: render "—/Unavailable," never a risk color, for null. (Phase 9.)
- **N-3 — Empty governance → 100.** `GovernanceScorer.analyze` starts at 100 and only deducts (`governance_scorer.py:26`); empty events → pristine 100. Obscure/thin-news companies score falsely perfect. Fix: neutral 50 + low-confidence when input is empty/below a minimum. (Phase 9.)

**[High — reliability]**

- **R-1 — Stuck analyses.** `background_tasks.add_task(run_full_analysis, …)` (`analysis.py:78`) is in-process; no reaper, no terminal timeout. A Render free-tier spin-down mid-run freezes the row at `running:` and the UI polls forever. Fix: `/health` + a reaper marking stale `running:` rows as a terminal `"error"` the UI handles. (Phase 10.)
- **R-2 — Free-tier metering.** Cache hits burn quota (corrected by Ruling A); count-then-insert is race-able at the boundary (low stakes; note it). (Phase 10.)

**[Medium — honesty/quality debt]**

- **M-1 — Shallow provenance.** `raw_response` stores the extracted `.text`, not the true API response (`gemini_client.py:76`) — loses `finish_reason`, safety blocks, token counts, exactly what an audit needs when a score looks wrong. (Phase 11 or opportunistic.)
- **M-2 — Confidence not surfaced.** `module_details.confidence` exists; the page recomputes its own `periodCount` (`page.tsx:73`) instead. Two sources of truth. (Phase 9.)
- **M-3 — News sentiment is a negation-blind keyword bag** (`news_aggregator.py:45`) over partly-dead feeds (Reuters businessNews is generic + deprecated). Weight 0.1111, low blast radius; acknowledge. (Phase 12 / Horizon 2.)
- **M-4 — Three redundant fetches of the same Google News feed per analysis** + a duplicate `import time` (`news_aggregator.py:39`). (Phase 12.)
- **M-5 — No HTTP schema validation on AI JSON.** A parseable-but-malformed governance object (`severity:"kinda bad"`) silently falls through to a 15-pt deduction via `.get("severity","moderate")`. (Phase 11.)

**[Low — cosmetic/dead code]** dead `status=="failed"` branches (`analysis.py:103`, `page.tsx:149`); two 0-byte `scripts/backtest_*.py` at repo root; unused 1-byte `RiskRadar.tsx`; `classify_risk` risk-banding duplicated backend/frontend; `google.generativeai` is the deprecated SDK and `gemini-1.5-flash` is a generation behind. (Phase 12.)

---

## 3. Architectural Review

- **System architecture — Good, one honest ceiling.** Clean separation (forensics / AI engines / scoring / orchestration / routes); adding a forensic module is localized. The one extensibility wart: `analysis_worker.py` hardcodes the `financial=(revenue+debt)/2` blend and the stage list — fine now, a config-driven registry later. Technical debt is low and localized.
- **Backend — Good.** RESTful, consistent envelope. Gaps: no HTTP rate limiting (only the business gate); no structured logging / request IDs (bare-string `logger.error` is un-greppable in aggregate); no `/health`; no metrics/tracing. Auth (JWT/bcrypt) MVP-adequate (prior ruling); no refresh/revocation.
- **Frontend — Good.** Clean hierarchy + token system; constitution respected. State is per-page hooks + polling; no shared cache, so Overview→Financials→Governance re-fetches the same analysis three times (Phase 11 query cache). Accessibility unverified — custom gauge/bars likely need ARIA. The null-as-zero bug (N-2) is the one correctness defect.
- **Database — Excellent for the stage.** Sound schema; `AnalysisRun` separation is right; Alembic is the source of truth. Forward risk: `module_details` is free-form JSON with no schema validation and the UI reaches deep into it with optional chaining — a backend shape change fails silently in the UI. Add a versioned Pydantic schema + `schema_version` before it grows.
- **AI systems — the weakest pillar.** Prompts externalized, `temperature=0` for score-bearing calls, default temp for prose (correct per ADR-004). But: hallucination risk is high and under-controlled — governance extraction asks an LLM to name governance events from headlines with **no source-citation requirement and no grounding check**, and those become persisted RedFlags about real companies. JSON parsing has no schema validation (M-5). Cost: ~7 Gemini calls/analysis (1 governance + up to 5 narrative + 1 report); ~200 analyses/day exhausts the free tier, and the biggest spender (narrative, 5 calls) carries *zero weight* — economically backwards until transcripts (H1).

---

## 4. Product Review

- **Senior engineer:** impressive bones; I'd extend this codebase happily and refuse to ship narrative as labeled.
- **Founder:** the core loop demos well on a large-cap; the differentiator is real. The first analyst who spots a Reuters headline labeled "management commentary," or a red 0.0 that's actually a timeout, won't return. Credibility is the product.
- **Recruiter/evaluator:** senior-grade work; the ADR ledger and renormalization rationale are portfolio-quality. Observability + a live deploy would make it production-grade.
- **Power user (analyst):** delighted by the gauge, forensic charts, plain-language report, honest narrative partial-states. Frustrated that red flags don't trace to a source, there's no score history (though the DB has it), missing data looks like terrible data, and "narrative consistency" is news sentiment.
- **PM:** *polished* — design system, overview, financials, report. *Unfinished* — narrative honesty, evidence traceability, history, deploy reliability. *Over-engineered* — 5 LLM calls for a zero-weight mislabeled signal. *Under-engineered* — observability, disclaimers, missing-data UX. *Remove for now* — narrative red flags + "management commentary" framing.

---

## 5. Gap Analysis

**Legend:** ✅ Existing · 🟡 Partial · ❌ Missing

| Dimension | Status | Note |
|---|---|---|
| Core loop (ticker→score→report) | ✅ | End-to-end works. |
| Honest missing-data UX | ❌ | Null → red 0.0 (N-2). |
| Narrative honesty | 🟡 | Zero-weighted; mislabeled + spurious flags (N-1). |
| Evidence drill-down (flag→source) | ❌ | Provenance stored, never surfaced. |
| Score history / trend | ❌ | DB accumulates runs; no endpoint/UI. |
| Deploy reliability (reaper, `/health`) | ❌ | R-1. |
| HTTP rate limiting | ❌ | Only business gate. |
| Observability (structured logs, request IDs, metrics) | ❌ | Bare-string logging. |
| **Legal disclaimers** | ❌ → resolved by Ruling B | Must ship (Phase 9). |
| Security (refresh/revocation/RBAC) | 🟡 | MVP-adequate JWT. |
| Accessibility | 🟡 | Unverified; gauge/bars need ARIA. |
| Testing | 🟡 | 70 unit/integration; no E2E. |
| Analytics / telemetry | ❌ | None. |
| Frontend query cache | 🟡 | Re-fetches per tab. |
| Docs (`data-sources.md`, `scoring-methodology.md`) | ❌ | ADR-005 #7 mandated; still missing. |
| Monitoring/alerting | ❌ | None. |
| Cost controls (Gemini budget) | 🟡 | Per-call fallback only. |

**Legal gap (no constitution doc addresses it).** SentinelIQ publishes algorithmic fraud-risk judgments — including LLM prose and governance "red flags" — about named public companies. A hallucinated "auditor resigned amid investigation" rendered as a finding is a **defamation / securities-commentary exposure**, not just a bug. Ruling B's disclaimer is the minimum; evidence traceability (Phase 11) and a "report an error" path complete the mitigation. **User-Ready blocker for any public exposure.**

**User Ready** = an analyst can analyze a real ticker, *trust and verify* what they see, never hit a silently-broken state, at a stable URL, with legal cover. Requires Phases 9 + 10 (+ a deploy).
**Production Ready** = multi-user-safe, observable, secure, cost-bounded, legally reviewed, built on defensible data. Requires Horizon 2.

---

## 6. Design Direction (unchanged from v1 — still binding)

Recorded compactly so it isn't lost; full rationale in ADR-002/003 and v1 history.

- **"Forensic editorial," not "trading terminal."** Warm off-white canvas (#F6F4EF), navy, serif/mono pairing — the register of an FT long-read / audit report / private-bank dossier. **Light mode only** (ADR-003); any dark theme would be a deliberate constitutional amendment, and even then *warm dark*, never neon.
- **Risk-decomposition (Aladdin):** headline score visibly breaks into its weighted components, which break into flags. Already the Overview layout.
- **Evidence drill-down (Palantir):** every flag traces to its source — the Phase 11 leap.
- **Density + ⌘K (Bloomberg ergonomics, not its skin):** a comfortable/compact toggle and a command palette (Phase 11).
- **FT-quality charts:** muted fills, hairline gridlines, mono axis labels, no glow/3D/scroll-animation; the only motion is the 700ms gauge arc. Enforced via the existing `ChartFrame`.
- **Tables:** hairline dividers, no zebra, right-aligned mono numerals, via the existing `DataTable`.

---

## 7. Revised Roadmap

**Resequencing rationale.** v1's Phase 9 (Analyst Workflow Layer) assumed the displays were honest and the backend reliable. This review shows neither holds. Building ⌘K and drill-down on dishonest displays is building on sand. So honesty precedes reliability precedes workflow.

**Old → new mapping:** v1 Phase 9 (workflow) → **new Phase 11**; v1 Phase 10 (cleanup) → **new Phase 12**; v1 Phase 11 (deploy) → folded into **new Phase 10**. **New Phase 9 (Integrity & Honesty Hardening) is inserted ahead of everything as the next phase to execute.**

| Order | Phase | Track | Hard dependency |
|---|---|---|---|
| **9** | **Integrity & Honesty Hardening** | Full-stack / Credibility | — *(next to execute)* |
| 10 | Reliability & Deployment Readiness | Backend / Infra | Phase 5 ✅ |
| 11 | Analyst Workflow Layer (⌘K + History + Drill-down) | Full-stack | Phases 9, 5 ✅ |
| 12 | Cleanup & Settings/Auth Honesty | Full-stack | Phase 5 ✅ |
| H1–H5 | Horizon 2 (owner-scheduled) | — | — |

### Phase 9 — Integrity & Honesty Hardening *(NEXT)*
- **Goal:** every number and label is either true or honestly marked unavailable; legal cover present.
- **Features:** null-vs-zero UI fix (N-2); narrative relabel + red-flag suppression (N-1); empty-governance fix (N-3); surface confidence (M-2); write `docs/data-sources.md` + `docs/scoring-methodology.md`; persistent disclaimer (Ruling B); ratify ADR-013/014.
- **Dependencies:** none. **Do not touch score math.**
- **Risks:** narrative relabel spans Phase 7 UI + the report prompt; keep `fraud_scorer` untouched.
- **Success criteria:** a failed module shows "—/Unavailable," never red 0.0; nothing labels news as "management commentary"; no narrative red flags persist; empty governance ≠ 100; `module_details.confidence` visible; disclaimer on every analysis view; both docs exist; ADR-013/014 recorded.

### Phase 10 — Reliability & Deployment Readiness
- **Goal:** no stuck analyses; survives a free-tier restart; live at a URL; quota is fair.
- **Features:** apply Ruling A (cache hits don't consume quota); `/health`; stuck-analysis reaper introducing a terminal `"error"` status (not the retired `"failed"`) with explicit UI handling; structured logging + request/analysis correlation IDs; Vercel + Render deploy dry-run.
- **Dependencies:** Phase 5 ✅.
- **Risks:** reintroducing a terminal non-`complete` status — do it deliberately as `"error"`, not by reviving dead `"failed"` paths. External deploy steps need owner confirmation (ADR-012).
- **Success criteria:** killing the worker mid-run yields a user-visible "interrupted — retry" within N minutes; `/health` 200; cached re-opens don't decrement quota; app reachable at a stable URL.

### Phase 11 — Analyst Workflow Layer *(was v1 Phase 9)*
- **Goal:** turn a one-shot scorer into an analyst tool.
- **Features:** ⌘K command palette; `GET /analysis/company/{ticker}/history` + score-trend chart (data already in DB); **evidence drill-down** (now meaningful — Phase 9 made provenance honest, Phase 6 exposes the forensic series); deepen provenance to the true raw response (M-1); governance JSON schema validation (M-5); frontend query cache.
- **Dependencies:** Phases 9, 5.
- **Success criteria:** every flag traces to a source; history renders for any company with ≥2 runs; ⌘K navigates; cross-tab nav reuses one fetch.

### Phase 12 — Cleanup & Settings/Auth Honesty *(was v1 Phase 10)*
- **Goal:** remove dead weight; honest stub pages.
- **Features:** delete root 0-byte backtests, dead `status=="failed"` branches, unused `RiskRadar.tsx`; consolidate the three Google-News fetches; honest "not yet available" auth/settings stubs (MR-3); ARIA pass on gauge/bars; consider `google-genai` SDK + 2.x Flash migration.
- **Note:** low-risk, subtractive; can be folded opportunistically into 9–11.

### Horizon 2 (owner-scheduled, re-ranked)
- **H1 — Narrative done right (transcript/SEC pipeline).** The only way to make narrative honest *by construction*: ingest earnings-call transcripts / SEC filings, then re-introduce narrative at 0.10 weight (ADR-006 step 2). Justifies the LLM spend. **Raised in priority** — it's what removes the "experimental" label.
- **H2 — Point-in-time / filing-grade data.** Deepest credibility lever; yfinance restated data can hide the fraud signal. Likely a paid dependency (tension with $0/month).
- **H3 — Concurrency & cost.** Replace in-process `BackgroundTasks` with a job queue (breaks $0/month — owner cost ruling); global Gemini budget guard; adopt Redis or formally enforce single-instance (ADR-008).
- **H4 — Monetization surface.** Portfolio monitoring + alerting (resurrect `data_refresh.py`); sector-relative benchmarking. The paid tier.
- **H5 — Enterprise hardening.** Refresh tokens / revocation / RBAC / SSO / MFA / audit logging (on `AnalysisRun`); uptime + error-rate monitoring; product analytics; E2E tests; accessibility/SEO audits; formal legal review.

---

## 8. Instructions for Sonnet (per phase, ordered by priority)

> Execute only the authorized phase. Smallest sensible commits, root-cause fixes, completion report, then STOP. Commit identity is owner-only (no Co-Authored-By trailer, ever). Push after the phase (standing instruction).

### Phase 9 — Integrity & Honesty Hardening
1. **Null-as-zero (highest impact, smallest change).** Stop coercing `analysis[key] ?? 0` in the component-score rows and progress bars (`frontend/app/(app)/company/[ticker]/page.tsx:180`). When a score is `null`, render a muted "—" labeled "Unavailable" with no risk-colored bar (use border/skeleton tint). Apply the same rule to the `ModuleScoreCard` grid (`page.tsx:228`) and the financials/governance/narrative tabs. A `null` score must be visually distinct from a low score.
2. **Suppress narrative red flags + relabel.** In `_stage_narrative` (`backend/app/tasks/analysis_worker.py:136`), keep computing/persisting snapshots and the (zero-weighted) narrative score, but **do not persist `cont_flags` as `RedFlag` records** until a real transcript source exists. Relabel the module "News Tone (experimental)" everywhere user-facing (`page.tsx:32/57`, the narrative tab, `report_generator.py` framing). Snapshots' `source` is already "News"; make the surrounding labels match that truth.
3. **Empty governance ≠ 100.** In `GovernanceScorer.analyze` (`backend/app/core/governance/governance_scorer.py:20`), when `news_text` is empty/below a documented minimum length, return `50.0` + a low-confidence marker rather than `100.0`. Document the threshold.
4. **Surface confidence.** Replace the hand-rolled `periodCount` heuristic (`page.tsx:73`) with `analysis.module_details.confidence`; render a "Confidence: Low/Medium/High" chip near the gauge with a tooltip (CLAUDE.md tier definition). Keep the period sentence as secondary context.
5. **Write the mandated docs (ADR-005 #7):** `docs/data-sources.md` (yfinance = restated, *not* as-filed point-in-time; news = Google News RSS; state the fraud-forensics limitation explicitly) and `docs/scoring-methodology.md` (weight vector, renormalization rule, each module formula, narrative exclusion).
6. **Disclaimer (Ruling B):** add a persistent, constitution-compliant (no color-blocking) footer/line on every analysis view: **"Algorithmic screening signal only. Not investment advice and not an accusation."**
7. **Ratify ADRs:** add ADR-013 (cache-hit metering, Ruling A) and ADR-014 (disclaimer, Ruling B) to `ARCHITECTURAL_DECISIONS.md`.
8. Completion report; commit; push.

### Phase 10 — Reliability & Deployment Readiness
1. **Ruling A:** keep writing the `AnalysisRun` on a cache hit but exclude it from quota — add a boolean (e.g. `cache_hit`/`counted`) to `AnalysisRun` (small Alembic migration) and filter it out of `_free_tier_usage_query` (`backend/app/api/v1/routes/analysis.py:23`). Only fresh computes decrement the 5/month.
2. **`/health`** (DB connectivity), no auth.
3. **Reaper + terminal `"error"`:** mark any `running:` `AnalysisResult` older than ~10 min as `"error"`; update `useAnalysis` + the overview/empty states to show a real "analysis interrupted — retry" terminal state. Do not revive the dead `"failed"` paths — introduce `"error"` cleanly.
4. **Structured logging:** JSON logs + a correlation ID threaded through `run_full_analysis`'s per-stage logs.
5. **Deploy dry-run** to Vercel + Render (`alembic upgrade head`); **stop and confirm with the owner before any external/account-touching step** (ADR-012).

### Phase 11 — Analyst Workflow Layer
1. `GET /analysis/company/{ticker}/history` + a trend chart on `ChartFrame`.
2. Evidence drill-down: surface stored governance/narrative provenance and forensic source rows behind each red flag (read-only).
3. Deepen provenance to store the true raw API response (not just `.text`) (M-1); add governance JSON schema validation (M-5).
4. ⌘K command palette; frontend query cache so cross-tab nav reuses one fetch.

### Phase 12 — Cleanup
Delete root 0-byte backtests, dead `status=="failed"` branches (`analysis.py:103`, `page.tsx:149`), unused `RiskRadar.tsx`; consolidate the three Google-News fetches + remove the duplicate `import time`; honest auth/settings stubs (MR-3); ARIA pass; evaluate `google-genai` + 2.x Flash.

---

## 9. Prioritized Recommendations

1. **Immediate next step:** Phase 9 in full. Null-as-zero and the narrative relabel are an afternoon each and each removes a credibility landmine; ship the disclaimer with them.
2. **High-impact:** reaper + `/health` (Phase 10) — without it the first deploy generates infinite-spinner reports; evidence drill-down (Phase 11) — converts "demo" into "tool I trust."
3. **Medium:** confidence surfacing; structured logging + request IDs; query cache; deeper provenance; governance schema validation.
4. **Nice to have:** ⌘K; score-history trend; SEO/accessibility audit; `google-genai` + 2.x Flash.
5. **Avoid for now:** no more investment in news-derived narrative (no extra LLM calls, no UI elevation — freeze behind "experimental" until H1); no Redis/queue until the cost ruling (ADR-008); do not build new analyst features on dishonest displays — Phase 9 precedes Phase 11.
6. **Tech debt:** versioned Pydantic schema + `schema_version` for `module_details` before it grows; make the `financial=(revenue+debt)/2` blend + stage list config, not hardcode, when a 6th module appears.

---

## Working Agreement

Opus reviews, critiques, prioritizes, designs. Sonnet implements, tests, refactors, deploys. On **"Start new phase,"** Sonnet executes **only the next phase** (Phase 9 next, per §7), completes it, writes a completion report, and stops. CLAUDE.md / ADR amendments are explicit and dated, never silent.

**Recommended next phase to authorize: Phase 9 (Integrity & Honesty Hardening).**

*End of v2 architectural review. Authoritative for future phases. Awaiting the owner's go-ahead.*
