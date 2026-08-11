import pandas as pd
import pytest
from fastapi import HTTPException

from app.services import yahoo_finance


class FakeTicker:
    def __init__(self, financials, balance_sheet, cashflow):
        self.financials = financials
        self.balance_sheet = balance_sheet
        self.cashflow = cashflow


def _ragged_ticker():
    periods = [
        pd.Timestamp("2025-12-31"),
        pd.Timestamp("2024-12-31"),
        pd.Timestamp("2023-12-31"),
        pd.Timestamp("2022-12-31"),
        pd.Timestamp("2021-12-31"),
    ]

    income = pd.DataFrame(
        [
            [500.0, 400.0, 300.0, 200.0, 100.0],
            [50.0, 40.0, 30.0, 20.0, 10.0],
            [200.0, 160.0, 120.0, 80.0, 40.0],
        ],
        index=["Total Revenue", "Net Income", "Gross Profit"],
        columns=periods,
    )
    balance_sheet = pd.DataFrame(
        [
            [1000.0, 900.0, 800.0, 700.0, 600.0],
            [250.0, 225.0, 200.0, 175.0, 150.0],
            [75.0, 70.0, 65.0, 60.0, 55.0],
        ],
        index=["Total Assets", "Total Debt", "Accounts Receivable"],
        columns=periods,
    )
    cashflow = pd.DataFrame(
        [[80.0, 70.0, 60.0, 50.0]],
        index=["Operating Cash Flow"],
        columns=periods[:-1],
    )
    return FakeTicker(income, balance_sheet, cashflow)


async def test_fetch_financials_preserves_union_for_ragged_periods(monkeypatch):
    monkeypatch.setattr(yahoo_finance, "_ticker", lambda ticker: _ragged_ticker())

    results = await yahoo_finance.fetch_financials("RAGGEDUNION67")

    assert len(results) == 5


async def test_fetch_financials_keeps_partial_period_data_when_cashflow_is_missing(monkeypatch):
    monkeypatch.setattr(yahoo_finance, "_ticker", lambda ticker: _ragged_ticker())

    results = await yahoo_finance.fetch_financials("RAGGEDPARTIAL67")
    missing_cashflow_period = next(
        result for result in results if result["revenue"] == 100.0
    )

    assert missing_cashflow_period["operating_cf"] is None
    assert missing_cashflow_period["revenue"] == 100.0
    assert missing_cashflow_period["net_income"] == 10.0
    assert missing_cashflow_period["total_assets"] == 600.0


async def test_fetch_financials_populates_shared_period_fields(monkeypatch):
    monkeypatch.setattr(yahoo_finance, "_ticker", lambda ticker: _ragged_ticker())

    results = await yahoo_finance.fetch_financials("RAGGEDSHARED67")
    shared_period = next(result for result in results if result["revenue"] == 500.0)

    assert shared_period["revenue"] == 500.0
    assert shared_period["net_income"] == 50.0
    assert shared_period["gross_margin"] == 0.4
    assert shared_period["total_assets"] == 1000.0
    assert shared_period["total_debt"] == 250.0
    assert shared_period["operating_cf"] == 80.0
    assert shared_period["accounts_recv"] == 75.0


async def test_fetch_financials_empty_sheets_remain_503(monkeypatch):
    empty_ticker = FakeTicker(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    monkeypatch.setattr(yahoo_finance, "_ticker", lambda ticker: empty_ticker)

    with pytest.raises(HTTPException) as exc_info:
        await yahoo_finance.fetch_financials("RAGGEDEMPTY67")

    assert exc_info.value.status_code == 503
