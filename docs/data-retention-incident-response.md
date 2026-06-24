# Data Retention & Incident Response

This document states, plainly, how long SentinelIQ keeps data, what happens when a user
asks for it to be deleted, and what the operational response is for each realistic
failure mode this system has actually been built to handle (or hasn't). It exists per
the same **"Honest Provenance"** principle as [`data-sources.md`](data-sources.md):
*never claim a posture we do not have.*

This is written for a **single-owner, pre-revenue project**, not as an enterprise
SOC-2 document. Where a capability genuinely doesn't exist yet (an admin deletion panel,
an on-call rotation, a second financial-data vendor), this document says so rather than
implying otherwise.

The user-facing counterpart to this document is the
[Privacy Policy](../frontend/app/(marketing)/privacy/page.tsx) (`/privacy`), specifically
its "Data Retention" and "Your Rights" sections. Everything below must stay consistent
with what that page already promises — this document adds the operational detail behind
those promises, it does not redefine them.

---

## 1. Data retention, table by table

**No automated purging or expiry exists anywhere in this codebase today.** Confirmed by
inspection: the only `DELETE` in the entire backend is the user-initiated
`DELETE /watchlist/{ticker}` endpoint (removing one watchlist entry). Every other table
grows indefinitely until manually pruned.

| Table | Scope | Retention today |
|---|---|---|
| `users` | Per-user | Indefinite, until account deletion (Section 2) |
| `organizations` | Per-user (singleton, Phase 46) | Indefinite, tied to the owning user |
| `companies` | Shared (per-ticker) | Indefinite — never deleted once a ticker is first searched |
| `financial_data` | Per-company | Indefinite |
| `analysis_results` | Per-company | Indefinite — retained on purpose to power the score-trend history feature |
| `red_flags` | Per-analysis | Indefinite |
| `reports` | Per-analysis | Indefinite |
| `narrative_snapshots` | Per-company | Indefinite |
| `edgar_facts` | Per-company | Indefinite (deduplicated on insert, Phase 41 / H-4, but never pruned) |
| `watchlist` | Per-user | Until the user removes the item (implemented) or deletes their account |
| `watchlist_alerts` | Per-user | Indefinite, until account deletion |
| `analysis_runs` | Per-user | Indefinite — this is the free-tier quota audit trail (ADR-007); deleting it would also erase quota history |
| `audit_logs` | Per-user | Indefinite, append-only by design (see the model's own docstring) |
| `gemini_daily_budget` | Global, by date | Indefinite — one tiny row per UTC day; never grows large enough to matter |

In-memory caches (financial data, news, EDGAR ticker/CIK map) are **not** in this table —
they live in process memory only, are bounded (Phase 41 / A-3), and expire automatically
on TTLs of 2 hours to 7 days depending on the key. They are never written to the database
and disappear entirely on every process restart.

---

## 2. Account deletion process

The Privacy Policy promises: *"You may request deletion of your account and associated
data at any time by contacting us through the feedback mechanism... We will process
deletion requests within 30 days."*

**There is currently no self-service or admin-panel deletion tool.** This is a manual
process, performed by the owner directly against the production database, when a
deletion request arrives through the feedback mechanism. The rows actually deleted are
scoped to **user-identifying** tables only:

- `users`, `organizations` (the requesting user's own singleton org)
- `watchlist`, `watchlist_alerts`
- `audit_logs`, `analysis_runs`

**Company-scoped tables are explicitly NOT deleted** as part of an account-deletion
request: `analysis_results`, `red_flags`, `reports`, `financial_data`,
`narrative_snapshots`, `edgar_facts`. These describe the company that was analyzed, not
the user who ran the analysis, and contain no information identifying the requester —
this matches the Privacy Policy's existing carve-out that such data "may be retained in
aggregate or anonymized form."

---

## 3. Incident response, by failure mode

| Failure | Detection (already built) | Response |
|---|---|---|
| Render free-tier spin-down kills an in-process analysis mid-run | Stuck-analysis reaper (`backend/app/tasks/reaper.py`) marks rows frozen at `running:*`/`pending` past 10 minutes as `status="error"` | No action needed — automatic. User sees "Analysis was interrupted. Please retry." |
| yfinance rate-limits or fails | `_stage_financials` catches the 503, sets `financial_data_status="rate_limited"`, that module's scores become `None` and are excluded + renormalized (ADR-005) | No action needed — automatic graceful degradation, not a crash |
| Gemini API outage, timeout, or daily quota exhausted | 30-second per-call timeout; persisted daily budget counter (`GeminiDailyBudget`, cap 200/day, Phase 45 / A-4) | No action needed for routine cases — governance/narrative fall back to neutral 50 automatically. If this is happening *every* day, the owner should check whether `GEMINI_DAILY_BUDGET` needs raising relative to real usage |
| Database connectivity loss | `GET /health` (and its `HEAD` variant) checks live DB connectivity; UptimeRobot polls it every 5 minutes (Phase 30) | Owner is alerted by UptimeRobot; check Render's Postgres/Neon dashboard for an outage, restart the backend service if connectivity has silently dropped |
| A security vulnerability is reported | Privacy Policy section 7 directs reporters to the in-app feedback mechanism | Owner assesses severity, patches the code, **rotates any exposed secret** (e.g. `SECRET_KEY`, `GEMINI_API_KEY`) via Render's environment variables, redeploys, and records what happened and when it was fixed |
| A vendor (yfinance or Gemini) permanently changes terms, pricing, or shuts off | No automated detection — this would surface as a sustained spike in `financial_data_status="unavailable"` or governance/narrative permanently returning neutral 50 | See Section 4 — there is currently no automated failover for either vendor; this requires manual intervention and, for yfinance, is the reason the EDGAR as-filed path (Phase 42) exists as a partial hedge |

---

## 4. Vendor concentration risk — stated plainly

The forensic scoring pipeline depends on two vendors with no formal SLA and no paid
contract:

- **yfinance** is still the **primary** source for the headline `integrity_score`'s
  financial inputs. SEC EDGAR (Phase 36/42) adds restatement detection and a parallel
  as-filed score, but this is an **additive hedge, not a replacement** — if yfinance
  became unavailable entirely, the headline score's financial/cashflow/earnings/debt
  modules would degrade to `None` (excluded + renormalized, per ADR-005), not to an
  EDGAR-only score. See [`data-sources.md`](data-sources.md) Section 2 for what EDGAR
  coverage actually does and does not extend to.
- **Google Gemini** (governance + narrative scoring) has **no failover provider at all**.
  If Gemini's free tier were discontinued or made unaffordable, both modules would
  permanently return their neutral-50 fallback — by design, this never crashes the
  pipeline, but there is currently no path back to a real governance or narrative score
  without integrating a second AI provider.

Neither gap is scheduled for remediation at this project's current stage — both are
explicitly free-tier, single-vendor dependencies accepted as a cost/risk trade-off
appropriate to a pre-revenue project, not an oversight. This section exists so that
trade-off is visible, not buried.
