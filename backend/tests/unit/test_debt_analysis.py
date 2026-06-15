from app.core.forensics.debt_analysis import DebtStressModule


def test_insufficient_data_returns_neutral_score(make_financial_data):
    data = [make_financial_data("2023")]

    result = DebtStressModule().analyze(data)

    assert result.score == 50.0
    assert result.flags == []
    assert result.details == {}


def test_healthy_company_scores_100(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=200.0, revenue=1000.0, operating_cf=100.0),
        make_financial_data("2022", total_debt=210.0, revenue=1100.0, operating_cf=110.0),
    ]

    result = DebtStressModule().analyze(data)

    assert result.score == 100.0
    assert result.flags == []


def test_debt_to_revenue_between_1_and_2_deducts_20(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=1500.0, revenue=1000.0, operating_cf=200.0),
        make_financial_data("2022", total_debt=1500.0, revenue=1000.0, operating_cf=200.0),
    ]

    result = DebtStressModule().analyze(data)

    # debt_to_revenue == 1.5 (> 1.0, not > 2.0): -20.
    assert result.score == 80.0
    assert result.flags == []


def test_debt_to_revenue_over_2_deducts_additional_20(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=2500.0, revenue=1000.0, operating_cf=300.0),
        make_financial_data("2022", total_debt=2500.0, revenue=1000.0, operating_cf=300.0),
    ]

    result = DebtStressModule().analyze(data)

    # debt_to_revenue == 2.5 (> 1.0 AND > 2.0): -20 - 20 = -40.
    assert result.score == 60.0
    assert result.flags == []


def test_interest_coverage_below_2_deducts_20(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=500.0, revenue=1000.0, operating_cf=20.0),
        make_financial_data("2022", total_debt=500.0, revenue=1000.0, operating_cf=20.0),
    ]

    result = DebtStressModule().analyze(data)

    # debt_to_revenue == 0.5 (no deduction), interest_coverage == 0.8 (< 2.0): -20.
    assert result.score == 80.0
    assert result.flags == []


def test_debt_growth_outpacing_flat_revenue_triggers_high_flag(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=1000.0, revenue=1000.0, operating_cf=500.0),
        make_financial_data("2022", total_debt=1500.0, revenue=1000.0, operating_cf=500.0),
    ]

    result = DebtStressModule().analyze(data)

    # debt_to_revenue == 1.5 (-20) and debt_growth == 0.5 > 0.30 (-15) = -35.
    # debt_growth (0.5) > 0.40 and rev_growth (0) <= 0 -> flag.
    assert result.score == 65.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "cash_flow"
    assert flag.severity == "high"
    assert flag.description == "Debt growing significantly faster than revenue"
    assert flag.period == "2022"


def test_deductions_accumulate_across_periods(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=1500.0, revenue=1000.0, operating_cf=300.0),
        make_financial_data("2022", total_debt=1500.0, revenue=1000.0, operating_cf=300.0),
        make_financial_data("2023", total_debt=1500.0, revenue=1000.0, operating_cf=300.0),
    ]

    result = DebtStressModule().analyze(data)

    # Two periods each deduct 20 (debt_to_revenue == 1.5); deductions accumulate
    # across periods rather than averaging, unlike cashflow_integrity.
    assert result.score == 60.0
    assert result.flags == []


def test_score_floors_at_zero_with_compounding_debt_stress(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=1000.0, revenue=400.0, operating_cf=10.0),
        make_financial_data("2022", total_debt=1500.0, revenue=400.0, operating_cf=10.0),
        make_financial_data("2023", total_debt=2300.0, revenue=400.0, operating_cf=10.0),
    ]

    result = DebtStressModule().analyze(data)

    # Each period deducts 75 (debt_to_revenue > 2.0, debt_growth > 0.30,
    # interest_coverage < 2.0): -150 total, clamped to 0. Both periods also
    # trigger the debt-outpacing-revenue flag.
    assert result.score == 0.0
    assert len(result.flags) == 2
    assert all(f.severity == "high" and f.flag_type == "cash_flow" for f in result.flags)


def test_zero_debt_yields_none_interest_coverage_and_no_penalty(make_financial_data):
    data = [
        make_financial_data("2021", total_debt=0.0, revenue=1000.0, operating_cf=100.0),
        make_financial_data("2022", total_debt=0.0, revenue=1100.0, operating_cf=120.0),
    ]

    result = DebtStressModule().analyze(data)

    # Zero debt -> interest_expense_proxy == 0 -> interest_coverage is None, not
    # float('inf') (Infinity is not valid JSON and would break module_details
    # serialization). No debt also means no interest burden, so the
    # "interest_coverage < 2.0" penalty must not fire.
    assert result.score == 100.0
    assert result.flags == []
    assert result.details["debt_metrics"][0]["interest_coverage"] is None
