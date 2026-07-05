# FUTURE_ARCHITECTURE — SentinelIQ

> **⚠️ HISTORICAL SNAPSHOT (mid-June 2026).** The project has since shipped through Phase 54
> (live on Render + Vercel; EDGAR as-filed data, AI grounding, rate limiting, budget guard,
> watchlist alerting, and more are all done). Much of what this document frames as "future"
> or "not yet built" is complete. See **`PROJECT_STATE.md`** for current status and which
> items genuinely remain open. Retained for history — do not treat its forward / "never
> done" framing as current.

**Author:** Claude Opus (CTO / Chief Architect)
**Date:** 2026-06-17
**Status:** Strategic direction, advisory. Binding rulings still live in
`ARCHITECTURAL_DECISIONS.md`; concrete next phases live in `NEXT_CODING_PHASES.md`. This
document is the *telescope* — where the platform goes over 3 horizons — not the *workplan*.

> **The north star (ADR-001), restated:** SentinelIQ produces *judgment an analyst can
> defend to an investment committee*, not a number to glance at. Every horizon below is
> measured against one question: **does this make the score more defensible, or just more
> impressive?** We build the former.

---

## The one architectural truth that governs everything below

The codebase is excellent; **the data is the ceiling.** Today the "institutional fraud
intelligence platform" runs on free, restated yfinance figures, Google News RSS headlines,
a 19-word keyword sentiment bag, and an LLM guessing governance events from those
headlines. The engineering, design, and governance are genuinely senior-grade. The inputs
are hobbyist-grade. **No amount of frontend polish or pipeline rigor raises the ceiling
that the data sets.** Therefore the horizons are ordered by *credibility of signal*, not by
*coolness of feature*. The biggest single lever in this entire document is Horizon
2's point-in-time data and transcript pipeline. Everything else is supporting structure.

---

## Horizon 1 — Make it real, trustworthy, and live (0–3 months)

*Goal: every number the product shows is true, grounded in a citable source, produced
live, and safe to put in front of a real analyst. This is the "earn the right to exist"
horizon.* Detailed phases in `NEXT_CODING_PHASES.md`.

**Architectural themes:**

1. **AI grounding & anti-hallucination (the headline of H1).** The current governance
   engine is a defamation vector (see CTO audit). Introduce a *grounding contract* for
   every score-bearing AI call: the model must quote the exact source span for each claim,
   and the backend drops any claim whose quote is not found verbatim in the input. This
   turns "the AI says the auditor resigned" into "the AI says the auditor resigned, and
   here is the headline that says so" — or it doesn't persist. This is the architectural
   change that makes evidence drill-down (already built) actually *trustworthy* rather than
   drilling down to an ungrounded assertion.

2. **`module_details` schema versioning.** Promote the free-form JSON blob to a versioned
   Pydantic contract with a `schema_version` field (OPUS review §9.6; already bit the team
   once when Pydantic silently dropped `tone_shifts`/`low_confidence`). The frontend should
   read a typed, versioned shape, not reach into untyped JSON with optional chaining. This
   is cheap now and expensive later.

3. **Request/stage timeouts.** Every external call (yfinance, feedparser, Gemini) gets an
   explicit timeout. The reaper is a *safety net for stuck rows*, not a substitute for
   bounded requests — a hung socket should fail its stage in seconds, not hang the worker
   for 10 minutes until the reaper sweeps it.

4. **Cost-bounded AI.** Freeze or throttle the zero-weight narrative module (5 of ~7
   Gemini calls) until H2's transcript pipeline justifies the spend; add a global daily
   Gemini budget guard that degrades gracefully (neutral score + low-confidence) when the
   budget is hit, rather than erroring.

5. **Go live & watch it.** Deploy (Vercel + Render per `docs/deployment.md`), wire uptime
   + error monitoring onto the already-excellent structured logs, and run the core loop on
   real tickers (founder item 1). The platform cannot mature on a codebase that has never
   executed its own core loop against live data.

6. **Honesty cleanup.** Finish MR-2 (delete the 9 dead stubs or consciously amend the
   ruling to keep them as H2 markers), retire the dual schema system
   (`database/*.sql` vs Alembic), and make the README match `data-sources.md`. Drift is the
   enemy of an institutional brand.

**Exit criteria for H1:** a real analyst can analyze a real ticker at a stable URL, every
flag traces to a quoted source, nothing is silently broken, costs are bounded, and the
docs tell the truth.

---

## Horizon 2 — Raise the data ceiling & become an analyst workspace (3–12 months)

*Goal: replace the hobbyist data floor with defensible signal, and turn a single-shot
scorer into a tool analysts live in. This is the "earn the institutional label" horizon.*

1. **Point-in-time / as-filed data (the deepest credibility lever).** Build the SEC EDGAR
   pipeline (`sec_scraper.py` is a placeholder for exactly this). yfinance serves
   *restated* figures, and a restatement is itself the strongest fraud signal — the current
   data can erase the very evidence the forensic modules hunt for (`docs/data-sources.md`
   says so plainly). As-filed 10-K/10-Q data, keyed by filing date, is what lets
   SentinelIQ claim to detect what a company *originally reported* vs. what it *quietly
   corrected*. This likely means a paid dependency — a deliberate, costed break from
   $0/month (ADR-008/012). **This is the highest-value item in the entire roadmap.**

2. **Narrative done right (transcript/SEC NLP).** Build the earnings-call / MD&A transcript
   pipeline (`transcript_fetcher.py`, `statement_extractor.py`, `sentiment_scorer.py` are
   placeholders). This is the *only* way to make the "narrative" module honest by
   construction — measuring whether *management's own statements* contradict each other
   over time, not whether press-coverage mood swings. When validated, re-introduce
   narrative at its 0.10 weight and renormalize the other five back down (ADR-006 step 2).
   This is what removes the "experimental" label and justifies the LLM spend.

3. **Sector-relative scoring.** A 1.2 debt-to-revenue ratio means something very different
   for a utility than for a SaaS company. Introduce sector benchmarks so module thresholds
   are relative, not absolute (ADR-005 principle #1, "without changing it"). This is a
   large credibility jump for low engineering cost once the data is there.

4. **Concurrency, queue & multi-instance.** Replace in-process `BackgroundTasks` with a
   real job queue (and Redis for shared cache/state), lifting the single-instance
   constraint (ADR-008). The stage-loop in `analysis_worker.py` was deliberately designed
   to be the task unit for exactly this migration (ADR-010). A costed decision, triggered
   by measured load or an uptime SLA — not speculation.

5. **Analyst workspace features.** Watchlist-driven **portfolio monitoring + alerting**
   (re-score on a schedule, alert on a ±10 swing or a new severe flag — the Settings page
   already advertises these, now honestly disabled); company comparison / peer view;
   exportable, branded PDF dossiers (beyond `window.print()`); saved analyses with notes.
   This is the surface a paid tier is built on.

6. **Event timeline & relationship mapping (the Palantir thread).** Move from "flags on one
   company" toward "events across time and entities" — a timeline of governance/financial
   events per company, and the first edges of a relationship graph (shared auditors,
   directors, subsidiaries). This is the architectural seed for Horizon 3.

**Exit criteria for H2:** the score rests on as-filed data + real management language,
benchmarked by sector; the platform monitors portfolios and supports an analyst's daily
workflow; it can run multi-instance under load; there is a defensible paid tier.

---

## Horizon 3 — The platform BlackRock, McKinsey, and Palantir would build together (1–3 years)

*Goal: stop being a scorer of single companies and become an entity-intelligence platform —
a system of record for corporate trust. This is the "category-defining" horizon.* Each
strand maps to one of the three lenses in the brief.

**The Aladdin lens — risk as a portfolio primitive.**
- Integrity Score becomes a *monitored risk factor*, not a one-shot reading: continuous
  re-scoring, drift detection, and contribution analysis ("this fund's aggregate integrity
  risk rose because three holdings' accrual ratios deteriorated this quarter").
- Scenario / what-if: "if this company restates, how does my exposure change?"
- An API/data-feed product (ADR-001 rejected *API-only*, but an API *alongside* the
  analyst UI is the institutional distribution model) so the score flows into existing risk
  systems.

**The Palantir lens — entities, relationships, and provenance as first-class.**
- A full **knowledge graph**: companies, people (directors, executives, auditors),
  filings, events, and the edges between them. Fraud is rarely one company in isolation —
  it's a shared auditor, a recycled CFO, a web of related-party transactions. The graph is
  where the *non-obvious* signal lives.
- **Explainable AI as the core UX**, not a drill-down afterthought: every score, edge, and
  flag carries its full provenance chain back to a primary source. The H1 grounding
  contract and the existing provenance capture (ADR-004) are the foundation stones for
  this; H3 makes provenance the *product*.
- **Collaborative investigations:** multiple analysts annotating, sharing, and building a
  case on a shared workspace — with an audit trail (the `AnalysisRun` model, ADR-007, is
  the first stone).

**The McKinsey/BlackRock-credibility lens — institutional trust & governance.**
- **Model governance:** versioned scoring models, backtested and validated against a
  growing corpus of known frauds (the Wirecard/Enron backtests are the seed); published
  precision/recall so the score is *defensible with statistics*, not just disclaimers.
- **Enterprise hardening (ADR-009 Horizon 2 / OPUS H5):** SSO/SAML, RBAC, refresh-token
  rotation + revocation, MFA, full audit logging, SOC-2-track controls — the table stakes
  for selling to a bank's risk team.
- **Multi-agent forensic workflows:** specialized agents (a filings agent, a litigation
  agent, a related-party agent, an adversarial "devil's advocate" agent that tries to
  *refute* each flag) whose findings are reconciled into a single defensible verdict —
  the natural evolution of today's single-pass pipeline, and a direct upgrade path for the
  stage-loop architecture.

**What it looks like in one sentence:** a continuously-monitored, graph-backed, fully
provenance-traceable corporate-trust intelligence platform that an analyst *investigates
within*, a risk system *consumes from*, and a committee *trusts the output of* — because
every number traces to an as-filed primary source and a validated, versioned model.

**The honest gating reality:** H3 is unreachable without H2's data foundation, and H2's
data foundation breaks the $0/month constraint. The single most important strategic
decision ahead of you is **when to spend money on data**, because that — not engineering
effort — is what converts SentinelIQ from an exceptionally well-built demo into an
institution-grade product.

---

## Cross-cutting principles for all horizons

- **Honesty scales or the brand dies.** The product's rarest asset is its intellectual
  honesty (`data-sources.md`, the "experimental" narrative label, null≠0). Every new
  feature must be honest *by construction*. The day the product overclaims is the day it
  becomes "another AI dashboard."
- **Provenance is permanent.** Never ship a score-bearing output without storing what
  produced it. ADR-004's provenance capture is the foundation of the entire H3 vision.
- **Determinism for judgment, creativity only for prose.** ADR-004's two-class split holds
  at every horizon: scores reproduce; only the report's language may vary.
- **Cost is a deliberate decision, never an accident.** $0/month is a constraint to break
  *consciously* (data, queue, multi-instance), with a costing, not to drift past.
- **The constitution evolves by amendment, never by drift.** New major decisions become
  ADR-015, ADR-016, … with the same rigor. The ledger is the moat.
