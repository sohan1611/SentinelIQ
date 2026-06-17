# Scoring Methodology

This document explains how SentinelIQ computes the **Corporate Integrity Score** (0-100)
and each of its component module scores. Every formula below is taken directly from the
current implementation — file paths are given so this document can be re-verified against
source at any time. For where the underlying data comes from (and its limitations), see
[`data-sources.md`](data-sources.md).

---

## 1. The big picture

Six module scores are computed per analysis. **Five** are blended into the headline
Corporate Integrity Score; **one** (narrative) is computed and displayed but currently
carries **zero weight** (ADR-006 — see [§7](#7-why-narrative-is-excluded)).

| Module | Score column | Weighted into Integrity Score? |
|---|---|---|
| Financial Quality (`revenue` + `debt`) | `financial_score` | Yes |
| Cash Flow Integrity | `cashflow_score` | Yes |
| Governance Risk | `governance_score` | Yes |
| Earnings Quality | `earnings_score` | Yes |
| News Sentiment | `news_score` | Yes |
| Narrative Consistency *(experimental)* | `narrative_score` | **No** |

Every module score is 0-100, where **higher = healthier / lower risk**. The final
Integrity Score maps to a risk label:

```python
# backend/app/core/scoring/fraud_scorer.py — FraudScorer.classify_risk
0–20:   "severe"   → SEVERE RISK
21–40:  "high"     → HIGH RISK
41–60:  "moderate" → MODERATE RISK
61–80:  "low"      → LOW RISK
81–100: "strong"   → STRONG INTEGRITY
```

---

## 2. Weight vector

```python
# backend/app/core/scoring/fraud_scorer.py
BASE_WEIGHTS: dict[str, float] = {
    "financial":   0.3333,
    "cashflow":    0.2222,
    "governance":  0.1667,
    "earnings":    0.1667,
    "news":        0.1111,
}  # sum = 1.0000; narrative intentionally absent
```

These are the original weights (financial 0.30, cashflow 0.20, governance 0.15, earnings
0.15, news 0.10 — summing to 0.90, with narrative originally at 0.10) renormalized by
×(1/0.9) so the five remaining modules sum to exactly 1.0. See
[ADR-005/006](../ARCHITECTURAL_DECISIONS.md) and the CLAUDE.md "Fraud Score Weights"
Phase 3 amendment.

---

## 3. Renormalization rule — "no dilution by neutral fill"

```python
# backend/app/core/scoring/fraud_scorer.py — FraudScorer.compute_integrity_score
available = {k: v for k, v in scores.items() if k in BASE_WEIGHTS and v is not None}
if not available:
    return 50.0, "low"

total_weight = sum(BASE_WEIGHTS[k] for k in available)
weighted_sum = sum(BASE_WEIGHTS[k] * v for k, v in available.items())
integrity_score = round(weighted_sum / total_weight, 1)
```

**Absence ≠ neutral.** A module key that is `None` or missing from `scores` means its
pipeline stage produced **no real signal** (network/AI failure, zero financial periods,
etc.). That module is dropped from *both* the numerator and the denominator — the
remaining modules' weights are rescaled to sum to 1.0 among themselves, so the score
reflects only what was actually measured.

A module that legitimately computed exactly `50.0` from real data is still "available"
and weighted normally — `None`/missing is the only thing that triggers exclusion. This
distinction is produced upstream by `analysis_worker.py`'s per-stage fallbacks, not by
`fraud_scorer.py` itself.

`narrative` is never a key in `BASE_WEIGHTS`, so even though `scores["narrative"]` is
always present (for display), the `available` filter silently drops it from the weighted
sum — no special-casing needed.

---

## 4. Confidence tier

```python
# backend/app/core/scoring/fraud_scorer.py — FraudScorer._confidence_tier
def _confidence_tier(self, available_count: int, total_count: int, period_count: int) -> str:
    if available_count <= 2:
        return "low"
    if available_count == total_count and period_count >= 3:
        return "high"
    return "medium"
```

Where `available_count` = number of the 5 `BASE_WEIGHTS` modules with real signal
(`!= None`), `total_count` = 5, and `period_count` = number of `FinancialData` periods
fetched for the company. Persisted at `AnalysisResult.module_details.confidence` and
shown as a chip on the Overview tab.

---

## 5. Forensic modules (deterministic, from financial statements)

All four operate on `FinancialData` rows sorted by `period` ascending. "Valid period"
means the fields each formula needs are non-`None` (see Error Handling rule 1 — periods
with missing fields are skipped, never crash). If **zero** valid periods exist, the
module returns `score = 50.0` (Error Handling rule 2 — a module-internal fallback,
distinct from the orchestrator-level `None`-and-renormalize behavior in §3).

### 5a. Revenue Quality
`backend/app/core/forensics/revenue_quality.py`

For each consecutive period pair:
```
rev_growth = (curr.revenue - prev.revenue) / abs(prev.revenue)
ocf_growth = (curr.operating_cf - prev.operating_cf) / abs(prev.operating_cf)
divergence = rev_growth - ocf_growth
recv_ratio = curr.accounts_recv / curr.revenue
```

Starting from 100:
- `divergence > 0.15` → **-15**
- `divergence > 0.30` → **-25** (additional, on top of the -15 above)
- `recv_ratio` increase over the prior period `> 0.10` → **-10**

Red flags:
- `divergence > 0.20` for **2+ consecutive periods** → **HIGH** — "Revenue growing
  significantly faster than cash flow"
- `recv_ratio` increases for **3+ consecutive periods** (any increase, not just `> 0.10`)
  → **MODERATE** — "Receivables expanding faster than revenue"

### 5b. Cash Flow Integrity
`backend/app/core/forensics/cashflow_integrity.py`

Per period (Sloan Accrual Ratio):
```
accrual_ratio = (net_income - operating_cf) / total_assets
```

Each valid period gets a score by ratio, and the module score is the **average** across
all valid periods:
```
accrual_ratio >= 0.15 → 20
accrual_ratio >= 0.10 → 45
accrual_ratio >= 0.05 → 70
otherwise             → 100
```

Red flags:
- `net_income > 0` **and** `operating_cf < 0` in the same period → **SEVERE** —
  "Reported profit but negative operating cash flow"
- `accrual_ratio > 0.10` for **2+ consecutive periods** → **HIGH** — "Elevated accruals
  ratio — potential earnings management"

### 5c. Earnings Quality
`backend/app/core/forensics/earnings_quality.py`

For each consecutive period pair:
```
margin_delta = curr.gross_margin - prev.gross_margin
rev_growth   = (curr.revenue - prev.revenue) / abs(prev.revenue)
ni_growth    = (curr.net_income - prev.net_income) / abs(prev.net_income)
```

Starting from 100 (deductions accumulate across all periods, not per-period averaged):
- `abs(margin_delta) > 0.08` → **-20** (can fire once per period pair)
- After all periods, if 2+ `ni_growth` values exist: compute the coefficient of variation
  `cv = stdev(ni_growth) / abs(mean(ni_growth))`. If `cv > 1.5` → **-25** (once, total)

Red flags:
- `margin_delta > 0.10` **and** `rev_growth <= 0.05` → **MODERATE** — "Unusual gross
  margin spike — accounting change possible"
- `ni_growth > 0.50` **and** `rev_growth <= 0.10` → **HIGH** — "Earnings spike
  inconsistent with revenue growth"

### 5d. Debt Stress
`backend/app/core/forensics/debt_analysis.py`

For each consecutive period pair:
```
debt_to_revenue   = curr.total_debt / curr.revenue
debt_growth       = (curr.total_debt - prev.total_debt) / abs(prev.total_debt)
interest_coverage = curr.operating_cf / (curr.total_debt * 0.05)   # 5% proxy interest rate
```

Starting from 100, deductions accumulate per period:
- `debt_to_revenue > 1.0` → **-20**
- `debt_to_revenue > 2.0` → **-20 additional** (up to -40 total at high leverage)
- `debt_growth > 0.30` → **-15**
- `interest_coverage < 2.0` (when computable) → **-20**

Red flag:
- `debt_growth > 0.40` **and** `rev_growth <= 0` → **HIGH** — "Debt growing significantly
  faster than revenue" (stored as `flag_type="cash_flow"` — grouped with cash flow in the
  financials view)

### 5e. Financial Quality (blend)
`backend/app/tasks/analysis_worker.py` — `_stage_forensics`

```python
financial_score = (revenue_quality_score + debt_stress_score) / 2
```

Debt Stress is not its own weight in `BASE_WEIGHTS` — its score is folded into
`financial_score` via this 50/50 blend. The raw `debt` score is still recorded in
`module_details.scores.debt` for transparency, but only the blended `financial_score`
participates in the Integrity Score weighting.

---

## 6. AI-scored modules (Gemini 2.5 Flash, `temperature=0`)

Both modules below run at `temperature=0` with a pinned `model_id`, with the exact prompt
and raw response persisted to `module_details.{governance,narrative}.provenance` (ADR-004
— deterministic, explainable, auditable AI).

### 6a. Governance Risk
`backend/app/core/governance/governance_scorer.py`

**Grounding gate (Phase 14).** Every governance event returned by Gemini must include a
`source_quote` — an exact phrase from the input `news_text` that supports the claim.
Before scoring, the backend checks `source_quote` against `news_text` (verbatim, then
normalized: lowercase + collapse punctuation/whitespace). Events that fail this check are
**dropped** — they receive no deduction and are not persisted as `RedFlag` records. This
prevents fabricated events from becoming persisted risk labels on real companies. Events
with an empty or missing `source_quote` are also dropped (treated as ungrounded). A
genuine finding that Gemini failed to quote verbatim may be lost — this is intentional:
false negatives on a grounding check are safer than false positives on a defamation risk.
The grounded `source_quote` is stored in `module_details.governance.flags[*].source_quote`
and surfaced in the evidence panel on the Overview page.

- If the fetched news text is shorter than `MIN_NEWS_TEXT_LENGTH` (40 characters), Gemini
  is **not called** — returns `50.0` with `low_confidence: true` (Error Handling rule 2b;
  "empty governance ≠ 100").
- Otherwise, Gemini extracts a list of governance events (leadership changes, auditor
  transitions, regulatory action, etc.), each with a severity. Starting from 100:
  ```
  severity == "moderate" → -15
  severity == "high"     → -25
  severity == "severe"   → -35
  ```
- If Gemini fails (`events is None`): `50.0` with `low_confidence: true`.
- A real review that finds **zero** events legitimately returns `100.0` with
  `low_confidence: false` — "checked, all clear" is distinct from "couldn't check."

### 6b. Narrative Consistency *(experimental — see §7)*
`backend/app/core/narrative/consistency_engine.py`

- If fewer than 2 news "statements" are available (`fetch_news_statements`), Gemini is
  **not called** — returns `50.0`.
- Otherwise, Gemini scores each statement's sentiment (`sentiment_score`, 0-1). Statements
  are sorted by period, and for each consecutive pair:
  ```
  diff = abs(curr.sentiment_score - prev.sentiment_score)
  ```
  - `diff > 0.6` → a "tone shift" entry, severity `"high"` if `diff > 0.8` else
    `"moderate"` (recorded in `module_details.narrative.tone_shifts`, not as a `RedFlag`)
- Final score:
  ```
  avg_contradiction = mean(all diffs)
  narrative_score = max(0, 100 - avg_contradiction * 100)
  ```
  i.e., the more consecutive headlines swing in tone, the lower the score.

---

## 7. Why narrative is excluded

`narrative_score` is **always computed and displayed** (it's a real, varying number once
≥2 news statements exist), but it is **not** a key in `BASE_WEIGHTS`, so §3's `available`
filter silently drops it from the weighted sum regardless of its value.

**Rationale (ADR-006):** the current narrative pipeline derives "statements" from news
*headlines* (see [`data-sources.md`](data-sources.md)), not from management's own
earnings-call or filing language. It measures press-coverage tone consistency — a real
but different signal than the "management narrative consistency" the product name
implies. Until a real transcript pipeline exists (Horizon 2 — see `FUTURE_ARCHITECTURE.md`), narrative is shown as
**"News Tone (experimental)"** and carries zero weight rather than diluting the Integrity
Score with a constant or a misleadingly-labeled signal.

When the transcript pipeline lands and is validated, narrative is intended to be
re-introduced at its original 0.10 weight, with the other five weights renormalized back
down accordingly.

---

## 8. News Sentiment
`backend/app/services/news_aggregator.py` — `fetch_news_sentiment`

Keyword-based, not AI-based:

1. Gather up to 10 headlines per feed (Google News, Yahoo Finance RSS, Reuters Business
   News) from the last 30 days, up to 20 total.
2. For each headline, count word-level matches:
   - Positive: `profit, growth, beat, strong, record, raised, upgraded` → **+1** each
   - Negative: `fraud, loss, miss, decline, investigation, sec, resigned, lawsuit, warning, downgrade, restatement, concern` → **-1** each
3. `raw_avg = mean(per-headline scores)`, clamped to `[-1, 1]`
4. `news_score = ((raw_avg + 1) / 2) * 100` — maps `[-1, 1] → [0, 100]`

If no headlines are found (any reason), returns `50.0` (neutral) — this fallback is
**unchanged by Phase 3**: `news` always has *some* value, so it's always "available" in
§3's renormalization, contributing its full `0.1111` weight even on a quiet news day.
