from app.core.forensics.forensics_runner import ForensicsRunner


def test_single_period_returns_neutral_scores_for_all_modules(make_financial_data):
    # net_income=None fails cashflow's per-period validity check (-> 0 valid
    # periods -> neutral). The other 3 modules operate on pairs, so a single
    # period already yields 0 valid periods regardless of field values.
    data = [make_financial_data("2023", net_income=None)]

    result = ForensicsRunner().run_forensics(data)

    assert set(result.keys()) == {"revenue", "cashflow", "earnings", "debt", "all_flags"}
    for key in ("revenue", "cashflow", "earnings", "debt"):
        assert result[key].score == 50.0
        assert result[key].flags == []
        assert result[key].details == {}
    assert result["all_flags"] == []


def test_all_flags_aggregates_across_modules_in_order(make_financial_data):
    data = [
        make_financial_data(
            "2021", revenue=1000.0, operating_cf=100.0, accounts_recv=100.0,
            net_income=50.0, total_debt=500.0, total_assets=1000.0, gross_margin=0.40,
        ),
        make_financial_data(
            "2022", revenue=1000.0, operating_cf=-50.0, accounts_recv=100.0,
            net_income=50.0, total_debt=900.0, total_assets=1000.0, gross_margin=0.40,
        ),
    ]

    result = ForensicsRunner().run_forensics(data)

    assert result["revenue"].score == 60.0
    assert result["cashflow"].score == 72.5
    assert result["earnings"].score == 100.0
    assert result["debt"].score == 65.0

    assert result["revenue"].flags == []
    assert result["earnings"].flags == []
    assert len(result["cashflow"].flags) == 1
    assert len(result["debt"].flags) == 1

    # all_flags is the concatenation of revenue, cashflow, earnings, debt flags, in order.
    assert result["all_flags"] == result["cashflow"].flags + result["debt"].flags
    assert result["all_flags"][0].severity == "severe"
    assert result["all_flags"][1].severity == "high"
