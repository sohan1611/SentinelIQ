"""Unit tests for the EDGAR -> FinancialData as-filed adapter (Phase 42 / C-2).

Pure data transformation -- no network, no DB. Fixtures use the exact raw
entry shape sec_edgar.extract_concept_history returns: {start, end, val,
accn, form, filed}.
"""
from app.core.forensics.as_filed_adapter import build_as_filed_periods


def _entry(end, val, accn, form="10-K", filed="2020-01-01", start=None):
    return {"start": start, "end": end, "val": val, "accn": accn, "form": form, "filed": filed}


def test_single_filing_per_period_is_used_directly():
    histories = {"revenue": [_entry("2019-12-31", 1000.0, "A1", filed="2020-01-15")]}
    rows = build_as_filed_periods(histories)
    assert len(rows) == 1
    assert rows[0]["period"] == "2019-12-31"
    assert rows[0]["period_type"] == "annual"
    assert rows[0]["revenue"] == 1000.0


def test_restated_period_picks_the_earliest_filed_value_not_the_latest():
    # Original 10-K reported 1000; a later 10-K/A restated it to 800. The
    # as-filed adapter must report the ORIGINAL 1000 -- that's the entire
    # point of "as-filed" vs "restated" (yfinance would give 800).
    histories = {
        "revenue": [
            _entry("2019-12-31", 1000.0, "A1", form="10-K", filed="2020-01-15"),
            _entry("2019-12-31", 800.0, "A2", form="10-K/A", filed="2020-06-01"),
        ]
    }
    rows = build_as_filed_periods(histories)
    assert len(rows) == 1
    assert rows[0]["revenue"] == 1000.0


def test_quarterly_filings_are_excluded():
    histories = {
        "revenue": [
            _entry("2019-12-31", 1000.0, "A1", form="10-K", filed="2020-01-15"),
            _entry("2019-09-30", 250.0, "Q1", form="10-Q", filed="2019-10-15"),
        ]
    }
    rows = build_as_filed_periods(histories)
    assert len(rows) == 1
    assert rows[0]["period"] == "2019-12-31"


def test_concept_with_only_quarterly_filings_contributes_no_period():
    histories = {"revenue": [_entry("2019-09-30", 250.0, "Q1", form="10-Q")]}
    assert build_as_filed_periods(histories) == []


def test_missing_concept_for_a_period_is_none_not_zero():
    histories = {
        "revenue": [_entry("2019-12-31", 1000.0, "A1")],
        # net_income has no entry at all for this period.
    }
    rows = build_as_filed_periods(histories)
    assert rows[0]["revenue"] == 1000.0
    assert rows[0]["net_income"] is None


def test_gross_margin_and_free_cf_always_none():
    histories = {"revenue": [_entry("2019-12-31", 1000.0, "A1")]}
    rows = build_as_filed_periods(histories)
    assert rows[0]["gross_margin"] is None
    assert rows[0]["free_cf"] is None


def test_multiple_distinct_periods_produce_sorted_rows():
    histories = {
        "revenue": [
            _entry("2020-12-31", 1200.0, "A2", filed="2021-02-01"),
            _entry("2019-12-31", 1000.0, "A1", filed="2020-01-15"),
        ]
    }
    rows = build_as_filed_periods(histories)
    assert [r["period"] for r in rows] == ["2019-12-31", "2020-12-31"]


def test_total_debt_approx_concept_maps_to_total_debt_field():
    histories = {"total_debt_approx": [_entry("2019-12-31", 500.0, "A1")]}
    rows = build_as_filed_periods(histories)
    assert rows[0]["total_debt"] == 500.0


def test_unrecognized_concept_key_is_ignored():
    histories = {"some_future_concept": [_entry("2019-12-31", 1.0, "A1")]}
    assert build_as_filed_periods(histories) == []


def test_empty_histories_returns_empty_list():
    assert build_as_filed_periods({}) == []
