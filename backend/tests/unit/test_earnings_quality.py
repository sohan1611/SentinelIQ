from app.core.forensics.earnings_quality import EarningsQualityModule


def test_insufficient_data_returns_neutral_score(make_financial_data):
    data = [make_financial_data("2023")]

    result = EarningsQualityModule().analyze(data)

    assert result.score == 50.0
    assert result.flags == []
    assert result.details == {}


def test_stable_margins_and_growth_no_flags(make_financial_data):
    data = [
        make_financial_data("2021", gross_margin=0.40, net_income=100.0, revenue=1000.0),
        make_financial_data("2022", gross_margin=0.40, net_income=110.0, revenue=1100.0),
        make_financial_data("2023", gross_margin=0.40, net_income=121.0, revenue=1210.0),
    ]

    result = EarningsQualityModule().analyze(data)

    assert result.score == 100.0
    assert result.flags == []


def test_margin_delta_over_008_deducts_20(make_financial_data):
    data = [
        make_financial_data("2021", gross_margin=0.40, net_income=100.0, revenue=1000.0),
        make_financial_data("2022", gross_margin=0.50, net_income=110.0, revenue=1100.0),
    ]

    result = EarningsQualityModule().analyze(data)

    # margin_delta == 0.10 -> |delta| > 0.08 deducts 20, but is not > 0.10
    # (strict), so the margin-spike flag does not fire.
    assert result.score == 80.0
    assert result.flags == []


def test_margin_spike_with_flat_revenue_triggers_moderate_flag(make_financial_data):
    data = [
        make_financial_data("2021", gross_margin=0.40, net_income=100.0, revenue=1000.0),
        make_financial_data("2022", gross_margin=0.55, net_income=105.0, revenue=1020.0),
    ]

    result = EarningsQualityModule().analyze(data)

    assert result.score == 80.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "earnings"
    assert flag.severity == "moderate"
    assert flag.description == "Unusual gross margin spike — accounting change possible"
    assert flag.period == "2022"


def test_net_income_spike_with_weak_revenue_triggers_high_flag(make_financial_data):
    data = [
        make_financial_data("2021", gross_margin=0.40, net_income=100.0, revenue=1000.0),
        make_financial_data("2022", gross_margin=0.42, net_income=160.0, revenue=1050.0),
    ]

    result = EarningsQualityModule().analyze(data)

    assert result.score == 100.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "earnings"
    assert flag.severity == "high"
    assert flag.description == "Earnings spike inconsistent with revenue growth"
    assert flag.period == "2022"


def test_high_coefficient_of_variation_in_net_income_growth_deducts_25(make_financial_data):
    data = [
        make_financial_data("2021", gross_margin=0.40, net_income=100.0, revenue=1000.0),
        make_financial_data("2022", gross_margin=0.40, net_income=300.0, revenue=1300.0),  # ni_growth = 2.0
        make_financial_data("2023", gross_margin=0.40, net_income=150.0, revenue=1300.0),  # ni_growth = -0.5
        make_financial_data("2024", gross_margin=0.40, net_income=75.0, revenue=1300.0),   # ni_growth = -0.5
    ]

    result = EarningsQualityModule().analyze(data)

    # Growth rates [2.0, -0.5, -0.5] -> cv ~= 3.54 (> 1.5): -25.
    # No margin deltas, and the first pair's rev_growth (0.30) keeps the
    # net-income-spike flag (ni_growth > 0.50 and rev_growth <= 0.10) from firing.
    assert result.score == 75.0
    assert result.flags == []
