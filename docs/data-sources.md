# Data Sources

SentinelIQ's Corporate Integrity Score is only as honest as the data it's built on. This
document states, plainly, where every input comes from and what that implies for the
fraud-detection claims the product makes. It exists per **ADR-005 #7 ("Honest
Provenance")**: *"Never claim filing-grade provenance we do not have."*

---

## 1. Financial statement data — yfinance

**Source:** [`yfinance`](https://github.com/ranaroussi/yfinance) (`backend/app/services/yahoo_finance.py`),
which scrapes Yahoo Finance's published financial statements.

**What is fetched (annual periods only, `period_type: "annual"`):**

| Field | yfinance source |
|---|---|
| `revenue` | `Total Revenue` / `Operating Revenue` (income statement) |
| `net_income` | `Net Income` / `Net Income Common Stockholders` |
| `operating_cf` | `Operating Cash Flow` / `Total Cash From Operating Activities` |
| `free_cf` | `Free Cash Flow` |
| `total_debt` | `Total Debt` (balance sheet) |
| `total_assets` | `Total Assets` |
| `accounts_recv` | `Accounts Receivable` / `Net Receivables` |
| `gross_margin` | `Gross Profit / Total Revenue` (derived) |

Cached 12 hours (`company:{ticker}:financials`); company metadata (name, sector, exchange)
cached 24 hours.

### ⚠️ Critical limitation: restated, not as-filed

**Yahoo Finance — and therefore yfinance — serves the *current, restated* view of a
company's financial history, not the figures as originally filed for each period.** When
a company later restates a prior period (revises previously reported revenue, income,
debt, etc.), Yahoo's historical series updates retroactively. The **headline**
`integrity_score` is computed from this restated view. (Where SEC EDGAR coverage exists,
a separate as-filed score is also computed — see Section 2 below.)

**Why this matters for fraud forensics specifically:** a restatement is *itself* one of
the strongest fraud signals that exists — it is, by definition, an admission that
previously published numbers were wrong. SentinelIQ's forensic modules (revenue quality,
cash flow integrity, earnings quality, debt stress — see
[`scoring-methodology.md`](scoring-methodology.md)) compare period-over-period figures
*as they stand today*. If a company's aggressive original figures were later quietly
corrected, the divergence/accrual patterns that would have flagged the original fraud may
no longer be visible — the restatement can erase the very evidence these modules look
for.

**Read the headline forensic score as:** *"Does this company's financial history, as
Yahoo Finance reports it today, show signs of aggressive accounting?"* — **not** *"Did
this company's originally-filed financials show signs of fraud?"* The headline
`integrity_score` answers only the first question. Section 2 below describes the
separate as-filed signal that, where SEC EDGAR coverage exists, answers a version of the
second.

---

## 2. As-filed verification — SEC EDGAR (Phase 36/42, free, keyless)

**Source:** `data.sec.gov`'s public XBRL company-facts API (`backend/app/services/
sec_edgar.py`) — no API key, no cost, ~10 req/sec fair-access guidance. For companies
with U.S. SEC XBRL coverage, this returns the *entire* historical filing record: every
value ever reported for every concept, across every filing and every amendment, each
tagged with its accession number and filed date.

This serves two distinct purposes, both **additive** to the yfinance-based scoring
above, not a replacement for it:

1. **Restatement detection** (`restatement_detector.py`, Phase 35/36) — compares every
   period's filed values across amendments; a changed value for an already-filed period
   surfaces as a `RedFlag` (`flag_type="restatement"`). Flag-only — does not affect any
   score.
2. **As-filed forensic score** (`as_filed_adapter.py`, Phase 42 / ADR-005-adjacent
   "C-2") — runs the *same* forensic modules a second time against the figures as they
   stood on each filing's *original* date (the earliest-filed value per period, not the
   restated one), producing a parallel score set persisted at
   `module_details.as_filed.{scores, delta, coverage, period_count}`. **This never moves
   the headline `integrity_score`** — it is a second, independently-computed signal
   shown alongside the first, and the delta between the two is itself informative (a
   large divergence between as-filed and restated figures is a tell worth reading).

**Coverage is not universal.** Foreign private issuers filing Form 20-F, and any company
without SEC XBRL data, have no EDGAR coverage at all (`fetch_all_concept_histories`
returns `None`) — `module_details.restatement_check.coverage` and
`module_details.as_filed.coverage` are both `False` in that case, and the analysis falls
back to the yfinance-only path with no as-filed signal.

---

## 3. News data — Google News RSS (+ supplementary feeds)

**Source:** [`feedparser`](https://github.com/kurtmckee/feedparser) over public RSS feeds
(`backend/app/services/news_aggregator.py`). No paid news API is used.

Three distinct functions consume RSS, for three distinct purposes:

| Function | Feed(s) | Purpose | Cache TTL |
|---|---|---|---|
| `fetch_news_text` | `news.google.com/rss/search?q={ticker}` (top 10) | Raw headline text fed to the governance prompt | not cached |
| `fetch_news_sentiment` | Google News, Yahoo Finance RSS, Reuters Business News (top 10 each, last 30 days, max 20 scored) | Keyword-based positive/negative sentiment → `news_score` | 2 hours |
| `fetch_news_statements` | `news.google.com/rss/search?q={ticker}` (top `limit`, default 5) | Per-headline "statements" with publish date, fed to narrative consistency analysis | 2 hours |

`fetch_news_sentiment` falls back to `50.0` (neutral) if no headlines are found or fetch
fails for all feeds — see `scoring-methodology.md` for how this interacts with the weight
vector.

### ⚠️ Limitation: headlines, not transcripts

Everything SentinelIQ calls "narrative" or "governance evidence" is currently derived from
**news headlines**, not from:

- Earnings call transcripts
- Management's prepared remarks or investor presentations
- SEC filings (10-K/10-Q MD&A sections, proxy statements)

This means:

- **Governance scoring** (`governance_scorer.py`) evaluates what *journalists reported*
  about leadership changes, auditor transitions, investigations, etc. — not primary
  source statements.
- **Narrative consistency** (`consistency_engine.py`) measures whether *press coverage
  tone* is internally consistent across recent headlines — not whether *management's own
  statements* contradict each other over time. This is why `narrative_score` is currently
  excluded from the weight vector (ADR-006) and labeled "experimental" in the UI.

A real earnings-call/SEC transcript pipeline (Horizon 2 — see `FUTURE_ARCHITECTURE.md`) is the plan for closing this gap.

---

## 4. AI analysis — Google Gemini 2.5 Flash

**Source:** Google Gemini 2.5 Flash (free tier, 1,500 requests/day), via
`backend/app/core/ai/gemini_client.py`.

Used for two score-bearing tasks:

- **Governance event extraction** (`governance_scorer.py`) — reads recent news text,
  extracts governance-relevant events (leadership changes, auditor transitions,
  investigations, etc.) with a severity per event.
- **Narrative contradiction detection** (`consistency_engine.py`) — reads recent news
  "statements" and scores tone consistency across them.

Both run at **`temperature=0`** with a pinned `model_id` (per ADR-004, for
reproducibility), and persist the exact prompt + raw response in
`AnalysisResult.module_details.{governance,narrative}.provenance` for auditability. If a
news-text input is too short to meaningfully evaluate (under 40 characters — shorter than
a single typical headline), Gemini is not called at all and the module returns a neutral
score with a `low_confidence` marker (see CLAUDE.md, Error Handling rule 2b).

**Reliability guards (Phase 16).** Each Gemini call has a 30-second timeout
(`GEMINI_CALL_TIMEOUT_SECONDS`) — a hung API response fails its stage rather than
blocking the pipeline. A per-process daily counter (`GEMINI_DAILY_BUDGET = 200`, reset
at UTC midnight) caps total requests as a runaway-loop guard; when hit, AI modules return
their neutral fallback with no API call and the analysis continues normally.

---

## 5. What SentinelIQ does NOT use

To set expectations explicitly — the following are **not** part of the current pipeline,
despite stub files existing in the codebase for future use:

- **Earnings call or investor-day transcripts** (Horizon 2)
- **Any paid or real-time financial data provider**
- **Insider trading / Form 4 data**
- **Social media or analyst-estimate data**
- **Alternative data** (satellite imagery, credit card data, web traffic)

---

## 6. Summary

| Data | Source | Point-in-time? | Used for |
|---|---|---|---|
| Financial statements | yfinance (Yahoo Finance) | **No — restated/current view** | Revenue, cash flow, earnings, debt forensics (headline score) |
| As-filed verification | SEC EDGAR XBRL (`data.sec.gov`) | **Yes — where covered** | Restatement flags + parallel as-filed score (not blended into headline score) |
| News headlines | Google News / Yahoo Finance / Reuters RSS | Yes (publish date) | News sentiment, governance events, narrative consistency |
| AI extraction/scoring | Google Gemini 2.5 Flash, `temperature=0` | N/A | Governance events, narrative contradictions |

Every limitation above is a reason SentinelIQ's output is framed as an **algorithmic
screening signal**, not a definitive fraud determination — see the disclaimer shown on
every analysis view.
