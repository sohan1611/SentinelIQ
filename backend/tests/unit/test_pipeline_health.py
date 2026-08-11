import pytest

from app.services.pipeline_health import (
    MAX_TRACKED_ANALYSES,
    WEIGHTED_MODULES,
    get_pipeline_status,
    record_analysis_outcome,
    reset_pipeline_health,
)


@pytest.fixture(autouse=True)
def reset_health_state():
    reset_pipeline_health()
    yield
    reset_pipeline_health()


def healthy_scores():
    return {module: 50.0 for module in WEIGHTED_MODULES}


def test_records_healthy_analysis():
    record_analysis_outcome(healthy_scores(), "high")

    status = get_pipeline_status()

    assert status["analyses_recorded"] == 1
    assert status["degraded_analyses"] == 0
    assert status["degraded_pct"] == 0.0
    assert status["signal_degraded"] is False


def test_detects_three_missing_financial_modules_regression():
    outage_scores = {
        "financial": None,
        "cashflow": None,
        "governance": 50.0,
        "earnings": None,
        "news": 50.0,
    }

    for _ in range(3):
        record_analysis_outcome(outage_scores, "low")

    status = get_pipeline_status()

    assert status["degraded_analyses"] == 3
    assert status["degraded_pct"] == 100.0
    assert status["signal_degraded"] is True
    assert status["module_failures"] == {
        "financial": 3,
        "cashflow": 3,
        "governance": 0,
        "earnings": 3,
        "news": 0,
    }


def test_absent_weighted_module_counts_as_missing():
    scores = healthy_scores()
    del scores["cashflow"]

    record_analysis_outcome(scores, "medium")

    status = get_pipeline_status()

    assert status["degraded_analyses"] == 1
    assert status["module_failures"]["cashflow"] == 1


def test_narrative_none_does_not_degrade_analysis():
    scores = healthy_scores()
    scores["narrative"] = None

    record_analysis_outcome(scores, "high")

    assert get_pipeline_status()["degraded_analyses"] == 0


def test_minimum_sample_gate_prevents_single_failure_alarm():
    record_analysis_outcome({module: None for module in WEIGHTED_MODULES}, "low")

    assert get_pipeline_status()["signal_degraded"] is False


def test_recent_analysis_ring_buffer_is_bounded():
    for _ in range(MAX_TRACKED_ANALYSES + 10):
        record_analysis_outcome(healthy_scores(), "high")

    assert get_pipeline_status()["analyses_recorded"] == MAX_TRACKED_ANALYSES


def test_confidence_tallies_mixed_tiers():
    record_analysis_outcome(healthy_scores(), "low")
    record_analysis_outcome(healthy_scores(), "low")
    record_analysis_outcome(healthy_scores(), "high")

    assert get_pipeline_status()["confidence"] == {"low": 2, "medium": 0, "high": 1}


def test_empty_pipeline_status():
    status = get_pipeline_status()

    assert status["analyses_recorded"] == 0
    assert status["degraded_pct"] == 0.0
    assert status["signal_degraded"] is False
    assert status["last_recorded_at"] is None
