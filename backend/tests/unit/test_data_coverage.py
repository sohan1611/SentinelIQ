"""Unit tests for the pure data-source coverage classifier."""

from app.services.data_coverage import classify_coverage


def make_financial_record(period: str, **overrides: object) -> dict:
    record = {
        "period": period,
        "period_type": "annual",
        "revenue": 100,
        "net_income": 20,
        "operating_cf": 25,
        "free_cf": 15,
        "total_debt": 50,
        "total_assets": 200,
        "accounts_recv": 30,
        "gross_margin": 0.4,
    }
    record.update(overrides)
    return record


def make_mdna_statement(period: str) -> dict:
    return {
        "period": period,
        "text": "Management discussion and analysis.",
        "source": "sec_edgar",
    }


def healthy_financials(count: int = 4) -> list[dict]:
    return [make_financial_record(str(2025 - index)) for index in range(count)]


def healthy_mdna_statements() -> list[dict]:
    return [
        make_mdna_statement("2025"),
        make_mdna_statement("2024"),
        make_mdna_statement("2023"),
    ]


def test_classify_coverage_healthy_company_is_ok() -> None:
    result = classify_coverage(
        healthy_financials(),
        None,
        {"Revenue": [{"fy": "2025"}]},
        healthy_mdna_statements(),
    )

    assert result["status"] == "ok"
    assert result["issues"] == []
    assert result["narrative_source_would_be"] == "edgar_mdna"
    assert result["usable_periods"] == 4
    assert result["mdna_distinct_periods"] == 3


def test_classify_coverage_financials_error_fails() -> None:
    result = classify_coverage(
        healthy_financials(),
        "HTTPException: 404: No financial data available for this ticker.",
        {"Revenue": [{"fy": "2025"}]},
        healthy_mdna_statements(),
    )

    assert result["status"] == "failed"


def test_classify_coverage_excludes_empty_ragged_period() -> None:
    ragged_period = make_financial_record(
        "2021",
        revenue=None,
        net_income=None,
        operating_cf=None,
        total_assets=None,
        accounts_recv=None,
        total_debt=None,
    )
    result = classify_coverage(
        [*healthy_financials(), ragged_period],
        None,
        {"Revenue": [{"fy": "2025"}]},
        healthy_mdna_statements(),
    )

    assert result["period_count"] == 5
    assert result["usable_periods"] == 4
    assert result["field_coverage"]["operating_cf"] == 4


def test_classify_coverage_missing_operating_cf_is_degraded() -> None:
    result = classify_coverage(
        [
            make_financial_record(str(2025 - index), operating_cf=None)
            for index in range(4)
        ],
        None,
        {"Revenue": [{"fy": "2025"}]},
        healthy_mdna_statements(),
    )

    assert result["status"] == "degraded"
    assert result["field_coverage"]["operating_cf"] == 0
    assert "no coverage for operating_cf" in result["issues"]


def test_classify_coverage_two_usable_periods_is_degraded() -> None:
    result = classify_coverage(
        healthy_financials(count=2),
        None,
        {"Revenue": [{"fy": "2025"}]},
        healthy_mdna_statements(),
    )

    assert result["status"] == "degraded"
    assert "only 2 usable periods (need 3 for high confidence)" in result["issues"]


def test_classify_coverage_missing_edgar_is_degraded() -> None:
    result = classify_coverage(
        healthy_financials(),
        None,
        None,
        healthy_mdna_statements(),
    )

    assert result["status"] == "degraded"
    assert result["edgar_covered"] is False
    assert "no EDGAR XBRL coverage" in result["issues"]


def test_classify_coverage_same_period_mdna_is_flagged() -> None:
    result = classify_coverage(
        healthy_financials(),
        None,
        {"Revenue": [{"fy": "2025"}]},
        [
            make_mdna_statement("2025"),
            make_mdna_statement("2025"),
            make_mdna_statement("2025"),
        ],
    )

    assert result["status"] == "degraded"
    assert result["mdna_statements"] == 3
    assert result["mdna_distinct_periods"] == 1
    assert result["narrative_source_would_be"] == "edgar_mdna"
    assert any("distinct MD&A period" in issue for issue in result["issues"])


def test_classify_coverage_all_none_fails_safely() -> None:
    result = classify_coverage(None, None, None, None)

    assert result["status"] == "failed"
    assert result["period_count"] == 0
    assert result["usable_periods"] == 0
