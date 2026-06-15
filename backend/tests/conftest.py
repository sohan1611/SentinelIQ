import pytest

from app.models.financial_data import FinancialData


@pytest.fixture
def make_financial_data():
    """Factory for in-memory FinancialData rows (no DB session required).

    Defaults describe a "healthy" period; pass overrides as kwargs to
    construct the scenario under test, e.g.
    make_financial_data("2023", revenue=1200.0, operating_cf=-50.0).
    """

    def _make(period: str, **kwargs) -> FinancialData:
        defaults = dict(
            period_type="annual",
            revenue=1000.0,
            net_income=100.0,
            operating_cf=100.0,
            free_cf=80.0,
            total_debt=200.0,
            total_assets=1000.0,
            accounts_recv=100.0,
            gross_margin=0.4,
        )
        defaults.update(kwargs)
        return FinancialData(period=period, **defaults)

    return _make
