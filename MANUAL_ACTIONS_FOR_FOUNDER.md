# MANUAL_ACTIONS_FOR_FOUNDER

> **⚠️ HISTORICAL SNAPSHOT (mid-June 2026).** The project has since shipped through Phase 54
> (live on Render + Vercel; EDGAR as-filed data, AI grounding, rate limiting, budget guard,
> watchlist alerting, and more are all done). Much of what this document frames as "future"
> or "not yet built" is complete. See **`PROJECT_STATE.md`** for current status and which
> items genuinely remain open. Retained for history — do not treat its forward / "never
> done" framing as current.

**Author:** Claude Opus (CTO / Chief Architect), advisory only
**Date:** 2026-06-17
**Audience:** the project owner (`sohan1611`)
**Status:** This is a checklist of actions **only you can perform** — they touch accounts,
secrets, money, legal exposure, or external services that Claude Code is forbidden from
operating (per the operating rules and ADR-012). Nothing here is code. Each item states
*why it matters*, *exact steps*, and a *priority*.

Priority legend: **Critical** (do before any public exposure) · **High** (do before/at
first deploy) · **Medium** (do within the first month live) · **Low** (housekeeping).

---

## 0. The single most important thing to understand first

**SentinelIQ has never run end-to-end against a real database or a real Gemini key.**
Every "verification" in the phase reports is *static* — `tsc --noEmit`, `pytest
--collect-only`, `ast.parse`, `alembic upgrade head --sql` in offline mode. No human or
machine has ever seen a real Integrity Score computed for a real ticker, because there is
no Postgres connection and `backend/.env` holds placeholders. The code is high quality,
but its core loop is **unproven in execution**. Your first manual job (item 1) is to close
that gap. Until you do, treat every score the product can produce as theoretical.

---

## 1. Stand up a real environment and run the core loop once — **Critical**

**Why it matters.** This is the difference between "a beautiful codebase" and "a working
product." It will surface the real failure modes (Gemini quota, yfinance shape drift,
Render cold-start timeouts, an actual hallucinated governance flag) that no static check
can. Do this *before* spending a dollar or showing anyone.

**Exact steps.**
1. Create a free Postgres (Neon or Supabase are fine for a smoke test; Render Postgres for
   the real thing — see item 4).
2. Get a Google Gemini API key (item 6).
3. Fill `backend/.env`: `DATABASE_URL=postgresql+asyncpg://...`, `GEMINI_API_KEY=...`,
   `SECRET_KEY=$(openssl rand -hex 32)`, `FRONTEND_URL=http://localhost:3000`.
4. `cd backend && alembic upgrade head` — confirm all 8 tables + `analysis_runs` + `counted`.
5. Run backend (`uvicorn app.main:app --reload`) and frontend (`npm run dev`).
6. Register a user, analyze **3 real tickers** of varying size (e.g. `AAPL`, a mid-cap, a
   thinly-covered small-cap). For each, read the governance red flags **line by line** and
   ask: *is every one of these events actually real?* Note any hallucination — that is
   your highest-priority product risk (see item 2).
7. Time the full run. If it approaches or exceeds ~50s, you have a Render free-tier
   timeout problem waiting (item 4).

**Acceptance:** three real scores produced; report renders; you have personally verified
whether governance flags are truthful.

---

## 2. Decide how to handle AI hallucination before any public exposure — **Critical**

**Why it matters.** This is the product's central legal and credibility risk and it is
**architecturally unmitigated today**. `governance_scorer.py` asks Gemini to extract
governance "events" (auditor resignations, investigations, leadership departures) from
Google News headlines with **no source-citation requirement and no grounding/verification
step**. The M-5 work validated the *shape* of the JSON, not the *truth* of the claim. Each
event becomes a persisted RedFlag, a risk label, and report prose **about a real, named
public company**. A fabricated "auditor resigned amid SEC investigation" is a defamation /
securities-commentary exposure, not a bug. The ADR-014 disclaimer is legal *cover*, not a
*fix*.

**Exact steps (choose at least the first two).**
1. **You** read item 1's governance flags and quantify the false-positive rate on ~10
   companies. You cannot delegate this judgment — you own the legal risk.
2. Decide a policy and tell Sonnet to implement it (this is Horizon-1 phase work — see
   `NEXT_CODING_PHASES.md`, Phase 13): require the model to quote the source headline for
   every event, and drop any event whose quote isn't found verbatim in the input text.
3. Engage legal review (item 11) before exposing this to anyone outside yourself.

**Acceptance:** you can state, with evidence, the governance module's false-positive rate,
and a grounding policy is scheduled or shipped.

---

## 3. GitHub repository hardening — **High**

**Why it matters.** The repo is public-by-default-assumption and is the project's crown
jewel (the ADR ledger and code are portfolio-grade). It currently has no branch
protection — a force-push or a bad merge could rewrite the history you've carefully kept
clean (recall the 2026-06-14 co-author cleanup).

**Exact steps** (GitHub → repo → Settings):
1. **Branches → Add rule** on `main`: require pull-request reviews, require status checks
   (`ci.yml`) to pass, **block force-pushes**, block deletions.
2. **Settings → Secrets and variables → Actions**: confirm no secrets are committed; CI
   needs none today (tests mock externals).
3. **Settings → General**: decide **repository visibility** consciously (item 8). If it
   stays public, do a secret-scan first (`gitleaks detect` or GitHub's secret scanning) —
   you have handled real keys in `.env` locally; confirm none leaked into history.
4. Enable **Dependabot alerts** (Security tab) — you have a `package-lock.json` and a
   `requirements.txt` to watch.

**Acceptance:** `main` is protected; secret scanning is on; visibility is a deliberate
choice.

---

## 4. Render setup (backend + Postgres) — **High**

**Why it matters.** This is the live backend. The deployment playbook
(`docs/deployment.md`) is good and accurate — follow it. Two free-tier realities will bite
if you don't plan for them.

**Exact steps.** Follow `docs/deployment.md` §1–§2 verbatim. Then specifically handle:
1. **Scheme rewrite** — Render gives you `postgresql://`; the app needs
   `postgresql+asyncpg://`. This is the #1 deploy gotcha. The playbook calls it out.
2. **Health check path** = `/health`.
3. **Set all 4 env vars** (`DATABASE_URL`, `GEMINI_API_KEY`, `SECRET_KEY`, `FRONTEND_URL`)
   in the Render dashboard — never in code.
4. **Cold-start risk:** Render free web services spin down after ~15 min idle. A cold
   start *plus* an analysis (yfinance + ~7 Gemini calls + RSS) can be slow. The reaper
   mitigates *stuck* rows but not *slow* ones. Watch item 1's timing. If it's marginal,
   consider the cheapest paid Render tier for the backend only (a conscious break from
   $0/month — your call).
5. **90-day Postgres expiry:** Render's free Postgres is deleted after 90 days. Put a
   calendar reminder to migrate/upgrade, or you lose all data (item 10).

**Acceptance:** `curl https://<render-url>/health` returns `{"status":"ok","database":"ok"}`.

---

## 5. Vercel setup (frontend) — **High**

**Why it matters.** This is the live frontend; Vercel builds Next.js natively (no
Dockerfile needed — ADR-012).

**Exact steps.** Follow `docs/deployment.md` §3:
1. New project, root directory `frontend`, framework auto-detected.
2. Set `NEXT_PUBLIC_API_URL` = the Render backend URL, **no trailing slash**.
3. After deploy, set Render's `FRONTEND_URL` to the **exact** Vercel origin (`https://`,
   no trailing slash) — it is the sole CORS allow-origin. A mismatch = every API call
   fails with a CORS error and the app looks completely broken.

**Acceptance:** register → log in → analyze a real ticker → report renders, with no CORS
errors in the browser console.

---

## 6. Gemini API key & cost posture — **High**

**Why it matters.** Gemini is the only paid-capable dependency and the pipeline is
**economically backwards**: the narrative module makes up to **5 of the ~7 Gemini calls
per analysis** while carrying **zero weight** in the score. ~200 analyses/day exhausts the
free tier (1,500 req/day), and the biggest spender is the experimental, untrusted module.

**Exact steps.**
1. Create the key at Google AI Studio; store it only in Render's env (item 4) and your
   local `.env` (gitignored — confirm).
2. Set up **billing alerts / a budget cap** in Google Cloud *before* going public, so a
   traffic spike or a loop can't run up a bill.
3. Tell Sonnet to throttle narrative to ≤2 statements (or freeze it) until the transcript
   pipeline exists — see `NEXT_CODING_PHASES.md`. This is the single biggest cost lever.
4. Rotate this key if it has ever been pasted into a chat, screenshot, or committed.

**Acceptance:** key is only in env stores; a billing cap exists; narrative spend is
throttled or scheduled to be.

---

## 7. Secrets management & rotation — **Critical (if any secret ever touched a public surface)**

**Why it matters.** `SECRET_KEY` signs every JWT; `GEMINI_API_KEY` is billable;
`DATABASE_URL` is full DB access. Leakage of any is severe.

**Exact steps.**
1. Generate `SECRET_KEY` with `openssl rand -hex 32` — never reuse a guessable string.
2. Confirm `.env` is gitignored in **both** `backend/` and `frontend/` (it is, per
   `.gitignore`), and that no real key is in git history (item 3 secret-scan).
3. Establish a rotation habit: rotate `SECRET_KEY` and `GEMINI_API_KEY` on any suspected
   exposure (note: rotating `SECRET_KEY` invalidates all existing JWTs — users re-login).
4. Never paste real secrets into issues, chats, or screenshots.

**Acceptance:** all three secrets are random, env-only, absent from history, rotatable.

---

## 8. Branding, domain & positioning decisions — **Medium**

**Why it matters.** These are judgment calls only you can make, and they directly affect
the "institutional credibility" the whole product is built around (ADR-001).

**Exact steps / decisions to make.**
1. **Domain.** `docs/deployment.md` references `sentineliq.io` / `api.sentineliq.io` as
   aspirational. Decide and register a domain (or accept `*.vercel.app` for now).
   "SentinelIQ" may have trademark collisions in the security/fintech space — do a quick
   USPTO/EUIPO search before you print it on anything.
2. **Repository visibility** (item 3) — a public repo is great for a portfolio, risky for
   a commercial product. Choose deliberately.
3. **Positioning honesty.** Your `docs/data-sources.md` is admirably honest (restated
   data, headlines-not-transcripts). Your `README.md` is **not** — it claims the product
   analyzes "filings, transcripts" (it does not) and tells users to run a Docker path that
   is broken. Fix the README yourself or have Sonnet do it (see `NEXT_CODING_PHASES.md`,
   Phase 13). The README is the first thing an evaluator reads and it currently
   contradicts your own honesty docs.

**Acceptance:** domain + visibility decided; README claims match `data-sources.md`.

---

## 9. Legal pages & disclaimers — **Critical (before public exposure)**

**Why it matters.** You are publishing algorithmic fraud-risk judgments — including LLM
prose and "red flags" — about real, named public companies. ADR-014's footer
("Algorithmic screening signal only. Not investment advice and not an accusation.") is the
*minimum* and is shipped, but it is not a substitute for actual legal pages.

**Exact steps.**
1. Add **Terms of Service** and a **Privacy Policy** (you store emails + bcrypt passwords
   — GDPR/CCPA implications even at small scale).
2. Add an explicit **methodology & limitations** disclosure link (you already have
   `docs/data-sources.md` and `docs/scoring-methodology.md` — surface them in the product
   footer; they are excellent liability mitigation precisely because they are honest).
3. Get item 11 (legal review) before any non-you user touches it.

**Acceptance:** ToS + Privacy live; methodology linked in-product.

---

## 10. Database backup & data-retention policy — **Medium**

**Why it matters.** Render free Postgres expires at 90 days and free tiers rarely have
robust backups. Losing the DB loses all analyses, users, and the `AnalysisRun` audit trail
(ADR-007).

**Exact steps.**
1. Schedule a recurring `pg_dump` (even a manual monthly one to start).
2. Calendar the 90-day expiry (item 4).
3. Decide a retention policy for `AnalysisRun` / `AnalysisResult` (relevant once you have
   real users + privacy policy, item 9).

**Acceptance:** a backup exists; expiry is calendared.

---

## 11. Engage legal review before first external user — **Critical**

**Why it matters.** Defamation/securities-commentary exposure on named public companies is
not a risk you should carry on a self-drafted disclaimer alone. This is the one item
where "move fast" is wrong.

**Exact steps.** Brief a lawyer with: the product's claim, `data-sources.md` (the honest
limitations), the disclaimer wording (ADR-014), and the hallucination risk (item 2). Ask
specifically about (a) liability for an AI-fabricated governance claim, (b) whether the
disclaimer wording is sufficient, (c) ToS limitation-of-liability language.

**Acceptance:** counsel has signed off on the disclaimer + ToS, or told you what to change.

---

## 12. Pricing & monetization strategy — **Low (until validated)**

**Why it matters.** The Settings page already shows a "$19/month Pro" tier (now honestly
disabled). Before you wire real payments, the *product* has to be worth paying for, which
today means item 1 + item 2 + a real data source (see `FUTURE_ARCHITECTURE.md`, Horizon
2). Don't build Stripe before the score is trustworthy.

**Exact steps (when ready).** Validate willingness-to-pay with 5 real analysts first;
choose a payment provider (Stripe); note that *entering payment/financial credentials and
executing transactions is a manual, human-only action* — Claude can build the integration
but cannot operate it.

**Acceptance:** deferred until the score is defensible; recorded here so it isn't built
prematurely.

---

## 13. Production monitoring & alerting — **Medium (at deploy)**

**Why it matters.** You have excellent *structured logs* (Phase 10: JSON + correlation
IDs) but **nowhere they're being watched**. A stuck reaper, a Gemini quota wall, or a
spike in 500s would be invisible to you.

**Exact steps.**
1. Pipe Render logs to a free log viewer or set up Render's own alerting.
2. Add uptime monitoring (e.g. a free UptimeRobot hitting `/health` every few minutes —
   this *also* keeps the free tier warm, mitigating cold starts from item 4).
3. Set up Gemini billing alerts (item 6) and a Sentry-style error tracker (free tier) for
   the frontend.

**Acceptance:** you get notified when `/health` fails or errors spike.

---

## Priority summary

| # | Action | Priority |
|---|---|---|
| 1 | Run the core loop once on real data | **Critical** |
| 2 | Decide hallucination handling | **Critical** |
| 7 | Secrets rotation (if exposed) | **Critical** |
| 9 | Legal pages & disclaimers | **Critical** |
| 11 | Legal review before first user | **Critical** |
| 3 | GitHub hardening | High |
| 4 | Render setup | High |
| 5 | Vercel setup | High |
| 6 | Gemini key & cost posture | High |
| 8 | Branding / domain / README honesty | Medium |
| 10 | DB backup & retention | Medium |
| 13 | Monitoring & alerting | Medium |
| 12 | Pricing strategy | Low |

**The five Criticals gate any public exposure. Items 3–6 gate the first deploy. Do not
show this to an outside analyst until 1, 2, 9, and 11 are done.**
