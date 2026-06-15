from app.core.forensics.revenue_quality import RevenueQualityModule


def test_insufficient_data_returns_neutral_score(make_financial_data):
    data = [make_financial_data("2023")]

    result = RevenueQualityModule().analyze(data)

    assert result.score == 50.0
    assert result.flags == []
    assert result.details == {}


def test_stable_revenue_and_cashflow_no_flags(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1100.0, operating_cf=110.0, accounts_recv=110.0),
        make_financial_data("2023", revenue=1210.0, operating_cf=121.0, accounts_recv=121.0),
    ]

    result = RevenueQualityModule().analyze(data)

    assert result.score == 100.0
    assert result.flags == []
    assert len(result.details["divergences"]) == 2
    assert all(d["divergence"] == 0 for d in result.details["divergences"])


def test_single_period_moderate_divergence_deducts_15(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1180.0, operating_cf=100.0, accounts_recv=118.0),
    ]

    result = RevenueQualityModule().analyze(data)

    assert result.score == 85.0
    assert result.flags == []


def test_two_consecutive_high_divergence_periods_trigger_high_flag(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1250.0, operating_cf=100.0, accounts_recv=125.0),
        make_financial_data("2023", revenue=1562.5, operating_cf=100.0, accounts_recv=156.25),
    ]

    result = RevenueQualityModule().analyze(data)

    # Two consecutive periods with divergence == 0.25 (> 0.15 each, but not > 0.30):
    # -15 per period = -30 total.
    assert result.score == 70.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "revenue"
    assert flag.severity == "high"
    assert flag.description == "Revenue growing significantly faster than cash flow"
    assert flag.period == "2023"


def test_receivables_ratio_rising_three_periods_triggers_moderate_flag(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1100.0, operating_cf=110.0, accounts_recv=110.0),     # recv_ratio 0.10
        make_financial_data("2023", revenue=1210.0, operating_cf=121.0, accounts_recv=145.2),     # recv_ratio 0.12
        make_financial_data("2024", revenue=1331.0, operating_cf=133.1, accounts_recv=186.34),    # recv_ratio 0.14
        make_financial_data("2025", revenue=1464.1, operating_cf=146.41, accounts_recv=234.256),  # recv_ratio 0.16
    ]

    result = RevenueQualityModule().analyze(data)

    # Revenue and OCF grow in lockstep (divergence == 0 throughout), so the only
    # effect is the receivables flag - score stays at 100.
    assert result.score == 100.0
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag.flag_type == "revenue"
    assert flag.severity == "moderate"
    assert flag.description == "Receivables expanding faster than revenue"
    assert flag.period == "2025"


def test_receivables_ratio_jump_over_threshold_deducts_10(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1100.0, operating_cf=110.0, accounts_recv=110.0),  # recv_ratio 0.10
        make_financial_data("2023", revenue=1210.0, operating_cf=121.0, accounts_recv=290.4),  # recv_ratio 0.24
    ]

    result = RevenueQualityModule().analyze(data)

    # recv_ratio jumps from 0.10 to 0.24 (> 0.10 increase) in one step: -10.
    # Only a single increase, so the 3-consecutive-period flag does not fire.
    assert result.score == 90.0
    assert result.flags == []


def test_score_floors_at_zero_with_extreme_divergence(make_financial_data):
    data = [
        make_financial_data("2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2022", revenue=1350.0, operating_cf=100.0, accounts_recv=135.0),
        make_financial_data("2023", revenue=1822.5, operating_cf=100.0, accounts_recv=182.25),
        make_financial_data("2024", revenue=2460.375, operating_cf=100.0, accounts_recv=246.0375),
    ]

    result = RevenueQualityModule().analyze(data)

    # Three consecutive periods with divergence == 0.35 (> 0.30): -40 each = -120,
    # clamped to 0.
    assert result.score == 0.0


def test_zero_prior_revenue_pair_is_skipped_without_resetting_state(make_financial_data):
    data = [
        make_financial_data("2021", revenue=0.0, operating_cf=100.0, accounts_recv=50.0),
        make_financial_data("2022", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
        make_financial_data("2023", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0),
    ]

    result = RevenueQualityModule().analyze(data)

    # The 2021->2022 pair is skipped (prev.revenue == 0) without counting toward
    # valid_periods_for_growth or resetting consecutive counters; only the
    # 2022->2023 pair (zero divergence) is scored.
    assert result.score == 100.0
    assert result.flags == []
    assert len(result.details["divergences"]) == 1
