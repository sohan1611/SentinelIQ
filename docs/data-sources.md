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
debt, etc.), Yahoo's historical series updates retroactively. SentinelIQ has no access to
point-in-time, as-filed figures (e.g., the original 10-K/10-Q as filed with the SEC on its
original date).

**Why this matters for fraud forensics specifically:** a restatement is *itself* one of
the strongest fraud signals that exists — it is, by definition, an admission that
previously published numbers were wrong. SentinelIQ's forensic modules (revenue quality,
cash flow integrity, earnings quality, debt stress — see
[`scoring-methodology.md`](scoring-methodology.md)) compare period-over-period figures
*as they stand today*. If a company's aggressive original figures were later quietly
corrected, the divergence/accrual patterns that would have flagged the original fraud may
no longer be visible — the restatement can erase the very evidence these modules look
for.

**Read the forensic score as:** *"Does this company's financial history, as Yahoo Finance
reports it today, show signs of aggressive accounting?"* — **not** *"Did this company's
originally-filed financials show signs of fraud?"* These are different questions, and
SentinelIQ can currently only answer the first. Closing this gap would require a
point-in-time SEC EDGAR pipeline (see `backend/app/services/sec_scraper.py`, an unused
stub — Horizon 2).

---

## 2. News data — Google News RSS (+ supplementary feeds)

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

A real earnings-call/SEC transcript pipeline (`backend/app/services/transcript_fetcher.py`,
currently an unused stub) is the Horizon 2 plan for closing this gap.

---

## 3. AI analysis — Google Gemini 1.5 Flash

**Source:** Google Gemini 1.5 Flash (free tier, 1,500 requests/day), via
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

---

## 4. What SentinelIQ does NOT use

To set expectations explicitly — the following are **not** part of the current pipeline,
despite stub files existing in the codebase for future use:

- **SEC EDGAR / as-filed regulatory data** (`sec_scraper.py` — unused stub, Horizon 2)
- **Earnings call or investor-day transcripts** (`transcript_fetcher.py` — unused stub,
  Horizon 2)
- **Any paid or point-in-time financial data provider**
- **Insider trading / Form 4 data**
- **Social media or analyst-estimate data**

---

## Summary

| Data | Source | Point-in-time? | Used for |
|---|---|---|---|
| Financial statements | yfinance (Yahoo Finance) | **No — restated/current view** | Revenue, cash flow, earnings, debt forensics |
| News headlines | Google News / Yahoo Finance / Reuters RSS | Yes (publish date) | News sentiment, governance events, narrative consistency |
| AI extraction/scoring | Google Gemini 1.5 Flash, `temperature=0` | N/A | Governance events, narrative contradictions |

Every limitation above is a reason SentinelIQ's output is framed as an **algorithmic
screening signal**, not a definitive fraud determination — see the disclaimer shown on
every analysis view.
