# PROJECT_STATE — SentinelIQ

**Date:** 2026-07-05
**Status:** Authoritative current-state summary. Supersedes the forward-looking framing of
the mid-June 2026 planning docs; see `CLAUDE.md`'s amendment log for the detailed, phase-by-phase
ledger.

---

## Where it stands

SentinelIQ has been **live** on Render (backend) and Vercel (frontend) since ~Phase 30 —
both auto-deploy from `main`. Development has since shipped through **Phase 54**. For the
full phase-by-phase history, rulings, and rationale, see the amendment log at the top of
`CLAUDE.md` — this document is a pointer and summary, not a duplicate of that ledger.

---

## What shipped since the mid-June 2026 planning docs

The five docs dated 2026-06-15 to 2026-06-17 (`NEXT_CODING_PHASES.md`, `FUTURE_ARCHITECTURE.md`,
`PROJECT_STATUS_FOR_OPUS.md`, `MANUAL_ACTIONS_FOR_FOUNDER.md`, `OPUS_ARCHITECTURAL_REVIEW.md`)
describe a project that "has never run live" and frame a large amount of now-completed work
as future. All of the following have since shipped:

| Phase(s) | What shipped |
|---|---|
| 36 | Restatement detector wired into the analysis pipeline |
| 37 | Company comparison view |
| 38 | Audit logging (F6) |
| 39–41 | Governance grounding, stuck-analysis reaper, EDGAR/cache bounds |
| **42** | **As-filed forensic score from SEC EDGAR (C-2)** — the docs' "highest-value data item," done for **$0** via keyless EDGAR access |
| 43 | Precision/recall validation harness (H-5) |
| 44 | Security hardening: rate limiting + security headers (H-2, S-1, S-2) |
| 45 | Reliability/observability + Gemini daily-budget guard (A-4, S-4, S-6) |
| 46 | Organization/role scaffolding (E-1) |
| 47 | Watchlist monitoring/alerting (E-4) |
| 48 | Per-stage DB session isolation (A-1) |
| 50 | Data-retention & incident-response policy (E-5) |
| 51 | Accessibility pass on charts/score cards (U-4) |
| 52 | Frontend test infrastructure + first suite (U-5 Step 1) |
| 53 | Real JWT token revocation (E-2) |
| 54 | Auth-gated analysis-output read endpoints (S-3) |
| 22 *(earlier)* | Legal pages: Terms, Privacy, Methodology, Data Sources |

---

## In-flight

- **PR #36** — Phase 55: negation-aware news sentiment (VADER)
- **PR #37** — Phase 56: frontend test coverage, 17 → 128 tests

---

## Open items / forward backlog

- **Narrative module is still zero-weight / experimental** — it scores news *mood*, not
  management transcripts, and does not yet contribute to the Integrity Score.
- **This doc-reconciliation pass** (Phase 57) — bringing the stale planning docs into truth.
- **Narrative-from-EDGAR spike** — a proposed, owner-gated path to make the narrative
  module honest using free EDGAR text instead of a paid transcript vendor.
- **Paid Horizon-2 levers** (transcript vendor, sector-relative data, etc.) remain
  owner-gated and out of scope while the project holds to its ~$0/month budget ceiling.
