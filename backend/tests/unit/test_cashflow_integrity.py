from app.core.forensics.cashflow_integrity import CashFlowIntegrityModule


def test_insufficient_data_returns_neutral_score(make_financial_data):
    data = [make_financial_data("2023", net_income=None)]

    result = CashFlowIntegrityModule().analyze(data)

    assert result.score == 50.0
    assert result.flags == []
    assert result.details == {}


def test_healthy_company_scores_100(make_financial_data):
    data = [
        make_financial_data("2021", net_income=100.0, operating_cf=100.0, total_assets=1000.0),
        make_financial_data("2022", net_income=110.0, operating_cf=105.0, total_assets=1000.0),
    ]

    result = CashFlowIntegrityModule().analyze(data)

    assert result.score == 100.0
    assert result.flags == []


def test_accrual_ratio_at_005_boundary_scores_70(make_financial_data):
    data = [make_financial_data("2023", net_income=150.0, operating_cf=100.0, total_assets=1000.0)]

    result = CashFlowIntegrityModule().analyze(data)

    # accrual_ratio == 0.05 -> the ">= 0.05" bucket (70), not the "< 0.05" bucket (100).
    assert result.score == 70.0
    assert result.flags == []


def test_accrual_ratio_at_010_boundary_scores_45_without_flag(make_financial_data):
    data = [make_financial_data("2023", net_income=200.0, operating_cf=100.0, total_assets=1000.0)]

    result = CashFlowIntegrityModule().analyze(data)

    # accrual_ratio == 0.10 -> the ">= 0.10" score bucket (45), but the red-flag
    # counter requires "> 0.10" (strict), so it does not increment here.
    assert result.score == 45.0
    assert result.flags == []


def test_accrual_ratio_at_015_boundary_scores_20(make_financial_data):
    data = [make_financial_data("2023", net_income=250.0, operating_cf=100.0, total_assets=1000.0)]

    result = CashFlowIntegrityModule().analyze(data)

    assert result.score == 20.0
    assert result.flags == []


def test_two_consecutive_high_accrual_periods_trigger_high_flag(make_financial_data):
    data = [
        make_financial_data("2021", net_income=220.0, operating_cf=100.0, total_assets=1000.0),
        make_financial_data("2022", net_income=220.0, operating_cf=100.0, total_assets=1000.0),
    ]

    result = CashFlowIntegrityModule().analyze(data)

    # accrual_ratio == 0.12 each period -> 45 each, averaged to 45.
    assert result.score == 45.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "cash_flow"
    assert flag.severity == "high"
    assert flag.description == "Elevated accruals ratio — potential earnings management"
    assert flag.period == "2022"


def test_profit_with_negative_operating_cashflow_triggers_severe_flag(make_financial_data):
    data = [make_financial_data("2023", net_income=100.0, operating_cf=-50.0, total_assets=1000.0)]

    result = CashFlowIntegrityModule().analyze(data)

    assert result.score == 20.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "cash_flow"
    assert flag.severity == "severe"
    assert flag.description == "Reported profit but negative operating cash flow"
    assert flag.period == "2023"


def test_mixed_periods_average_not_accumulate(make_financial_data):
    data = [
        make_financial_data("2021", net_income=100.0, operating_cf=100.0, total_assets=1000.0),  # accrual 0.00 -> 100
        make_financial_data("2022", net_income=220.0, operating_cf=100.0, total_assets=1000.0),  # accrual 0.12 -> 45
    ]

    result = CashFlowIntegrityModule().analyze(data)

    # Final score is the average of per-period scores (100 and 45), not a
    # cumulative deduction.
    assert result.score == 72.5
    assert result.flags == []
