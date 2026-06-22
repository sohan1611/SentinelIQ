"""Adapts raw SEC EDGAR concept histories (as fetched by sec_edgar.py) into
FinancialData-shaped period rows using the AS-ORIGINALLY-FILED value for
each (concept, period) -- the earliest filed_date on record -- rather than
the latest/restated value. This is what lets the existing forensic modules
run on point-in-time data instead of yfinance's restated figures
(Phase 42 / C-2 / STRAT-1).

Restricted to annual filings (10-K / 10-K/A) only, matching the existing
yfinance-based pipeline's own period_type="annual" granularity -- mixing
annual and quarterly periods in the same consecutive-period comparison
would compare incommensurable figures (e.g. one quarter's revenue against
a full fiscal year's).
"""

# histories' raw entry keys (sec_edgar.py: extract_concept_history) are
# {start, end, val, accn, form, filed} -- NOT the same names as the
# persisted EdgarFinancialFact columns.
CONCEPT_TO_FIELD = {
    "revenue": "revenue",
    "net_income": "net_income",
    "operating_cf": "operating_cf",
    "total_assets": "total_assets",
    "accounts_recv": "accounts_recv",
    "total_debt_approx": "total_debt",
}


def _is_annual_filing(form: str) -> bool:
    return form.startswith("10-K")


def build_as_filed_periods(histories: dict[str, list[dict]]) -> list[dict]:
    """Returns one dict per distinct fiscal-year period_end found across any
    concept, each shaped like FinancialData's fields. A field with no EDGAR
    coverage for that period stays None -- never backfilled to 0 (this
    codebase's "absence is not neutral" rule). gross_margin and free_cf are
    always None in this first cut: EDGAR's currently-fetched concepts don't
    include cost-of-revenue, so gross margin can't be computed yet.
    """
    earliest: dict[tuple[str, str], dict] = {}
    for concept, entries in histories.items():
        if concept not in CONCEPT_TO_FIELD:
            continue
        for e in entries:
            if not _is_annual_filing(e["form"]):
                continue
            key = (concept, e["end"])
            current = earliest.get(key)
            if current is None or e["filed"] < current["filed"]:
                earliest[key] = e

    period_ends = sorted({end for (_, end) in earliest})

    rows = []
    for period_end in period_ends:
        row = {
            "period": period_end,
            "period_type": "annual",
            "free_cf": None,
            "gross_margin": None,
        }
        for concept, field in CONCEPT_TO_FIELD.items():
            entry = earliest.get((concept, period_end))
            row[field] = entry["val"] if entry else None
        rows.append(row)
    return rows
