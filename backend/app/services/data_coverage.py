"""Classify live data-source coverage without running an analysis.

This module probes the data layer only: it makes no Gemini calls, performs no
database writes, and consumes no free-tier analysis quota. That deliberately
targets the layer where the silent-degradation bugs in Phases 61, 64, and 67
lived. Verifying one ticker is not verification: AAPL's uniform statement
columns hid the KO ragged-column bug entirely.
"""

from __future__ import annotations

from app.services.sec_edgar import (
    fetch_all_concept_histories,
    fetch_management_statements,
)
from app.services.yahoo_finance import fetch_financials


# These are the fields the forensic modules actually consume; ``free_cf`` and
# ``gross_margin`` are derived/optional and are deliberately not part of the
# health verdict.
CORE_FINANCIAL_FIELDS = (
    "revenue",
    "net_income",
    "operating_cf",
    "total_assets",
    "accounts_recv",
    "total_debt",
)

# This mirrors ``FraudScorer.compute_integrity_score``'s confidence rule, where
# a "high" tier requires ``period_count >= 3``. Fewer usable periods means the
# product can never rate this company better than "medium".
MIN_PERIODS_FOR_HIGH_CONFIDENCE = 3


def classify_coverage(
    financials: list[dict] | None,
    financials_error: str | None,
    edgar_histories: dict | None,
    mdna_statements: list[dict] | None,
) -> dict:
    """Return a pure, defensive coverage verdict for one ticker's source data."""
    records = financials if isinstance(financials, list) else []
    statements = mdna_statements if isinstance(mdna_statements, list) else []

    field_coverage = {field: 0 for field in CORE_FINANCIAL_FIELDS}
    usable_periods = 0
    for record in records:
        if not isinstance(record, dict):
            continue

        has_core_value = False
        for field in CORE_FINANCIAL_FIELDS:
            if record.get(field) is not None:
                field_coverage[field] += 1
                has_core_value = True

        if has_core_value:
            usable_periods += 1

    mdna_periods: set[str] = set()
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        period = statement.get("period")
        if period is not None:
            mdna_periods.add(str(period))

    mdna_count = len(statements)
    mdna_distinct_periods = len(mdna_periods)
    edgar_covered = bool(edgar_histories) if isinstance(edgar_histories, dict) else False
    narrative_source_would_be = (
        "edgar_mdna" if mdna_count >= 2 else "news_headlines"
    )

    issues: list[str] = []
    failed = financials_error is not None or not records or usable_periods == 0

    if financials_error is not None:
        issues.append(f"financials fetch failed: {financials_error}")
    if not records:
        issues.append("no financial data")
    elif usable_periods == 0:
        issues.append("no usable financial periods")

    if 0 < usable_periods < MIN_PERIODS_FOR_HIGH_CONFIDENCE:
        issues.append(
            "only "
            f"{usable_periods} usable periods "
            f"(need {MIN_PERIODS_FOR_HIGH_CONFIDENCE} for high confidence)"
        )

    for field in CORE_FINANCIAL_FIELDS:
        if field_coverage[field] == 0:
            issues.append(f"no coverage for {field}")

    if not edgar_covered:
        issues.append("no EDGAR XBRL coverage")

    if mdna_count < 2:
        statement_label = "statement" if mdna_count == 1 else "statements"
        issues.append(
            f"only {mdna_count} MD&A {statement_label} — "
            "narrative falls back to news headlines"
        )
    elif mdna_distinct_periods < 2:
        period_label = "period" if mdna_distinct_periods == 1 else "periods"
        issues.append(
            f"only {mdna_distinct_periods} distinct MD&A {period_label} — "
            "need 2 for an over-time comparison"
        )

    if failed:
        status = "failed"
    elif issues:
        status = "degraded"
    else:
        status = "ok"

    return {
        "period_count": len(records),
        "usable_periods": usable_periods,
        "field_coverage": field_coverage,
        "edgar_covered": edgar_covered,
        "mdna_statements": mdna_count,
        "mdna_distinct_periods": mdna_distinct_periods,
        "narrative_source_would_be": narrative_source_would_be,
        "status": status,
        "issues": issues,
    }


async def probe_ticker(ticker: str) -> dict:
    """Fetch one ticker's data sources independently and classify their coverage."""
    financials: list[dict] | None = None
    financials_error: str | None = None
    edgar_histories: dict | None = None
    mdna_statements: list[dict] | None = None

    try:
        financials = await fetch_financials(ticker)
    except Exception as exc:
        financials_error = f"{type(exc).__name__}: {exc}"

    try:
        edgar_histories = await fetch_all_concept_histories(ticker)
    except Exception:
        pass

    try:
        mdna_statements = await fetch_management_statements(ticker, limit=3)
    except Exception:
        pass

    return {
        "ticker": ticker,
        **classify_coverage(
            financials,
            financials_error,
            edgar_histories,
            mdna_statements,
        ),
    }
