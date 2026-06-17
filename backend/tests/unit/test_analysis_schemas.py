import uuid
from datetime import datetime

from app.models.analysis_result import AnalysisResult
from app.schemas.analysis import AnalysisResultResponse, AnalysisHistoryItem


def _module_details():
    return {
        "scores": {
            "financial": 70.0, "cashflow": 72.5, "earnings": 100.0, "debt": 65.0,
            "governance": 75.0, "narrative": 35.0, "news": 65.0,
        },
        "confidence": "high",
        "revenue": {"divergences": [0.1], "recv_ratios": [0.1]},
        "cashflow": {"accrual_ratios": [0.05]},
        "earnings": {"margins": [0.40, 0.40], "net_incomes": [50.0, 50.0]},
        "debt": {"debt_metrics": [{"debt_to_revenue": 0.5}]},
        "narrative": {
            "snapshots": [
                {"period": "2023-01", "statement_text": "Revenue grew strongly this quarter.",
                 "sentiment_label": "positive", "sentiment_score": 0.8, "source": "News"},
            ],
            "statements_used": 2,
            "provenance": [
                {"period": "2023-01", "model_id": "gemini-1.5-flash", "prompt": "p1", "raw_response": "r1"},
            ],
            "tone_shifts": [
                {"period": "2023-01", "severity": "high", "description": "Tone shifted from optimistic to cautionary"},
            ],
        },
        "governance": {
            "provenance": {"model_id": "gemini-1.5-flash", "prompt": "gov-prompt", "raw_response": "gov-raw", "low_confidence": False},
            "low_confidence": False,
        },
    }


def test_module_details_round_trips_full_shape():
    analysis = AnalysisResult(
        id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.utcnow(),
        integrity_score=70.2, financial_score=70.0, cashflow_score=72.5,
        governance_score=75.0, earnings_score=100.0, narrative_score=35.0, news_score=65.0,
        module_details=_module_details(), status="complete",
    )

    response = AnalysisResultResponse.model_validate(analysis)

    assert response.module_details.confidence == "high"
    assert response.module_details.scores["governance"] == 75.0
    assert response.module_details.scores["debt"] == 65.0
    assert response.module_details.narrative.statements_used == 2
    assert response.module_details.narrative.provenance[0]["model_id"] == "gemini-1.5-flash"
    assert response.module_details.narrative.tone_shifts[0]["severity"] == "high"
    assert response.module_details.governance.provenance["model_id"] == "gemini-1.5-flash"
    assert response.module_details.governance.low_confidence is False


def test_module_details_handles_governance_failure_shape():
    # Stage 3 (governance) failure: scores["governance"] is dropped, but
    # ctx.governance_provenance stays at its StageContext default of {} --
    # module_details["governance"] = {"provenance": {}}, not absent.
    details = _module_details()
    details["scores"].pop("governance")
    details["governance"] = {"provenance": {}}

    analysis = AnalysisResult(
        id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.utcnow(),
        module_details=details, status="complete",
    )

    response = AnalysisResultResponse.model_validate(analysis)

    assert "governance" not in response.module_details.scores
    assert response.module_details.governance.provenance == {}
    assert response.module_details.governance.low_confidence is False


def test_module_details_none_for_pending_analysis():
    analysis = AnalysisResult(
        id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.utcnow(), status="pending",
    )

    response = AnalysisResultResponse.model_validate(analysis)

    assert response.module_details is None


def test_analysis_history_item_omits_module_details():
    analysis = AnalysisResult(
        id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.utcnow(),
        integrity_score=70.2, financial_score=70.0, cashflow_score=72.5,
        governance_score=75.0, earnings_score=100.0, narrative_score=35.0, news_score=65.0,
        module_details=_module_details(), status="complete",
    )

    response = AnalysisHistoryItem.model_validate(analysis)

    assert response.integrity_score == 70.2
    assert response.governance_score == 75.0
    assert not hasattr(response, "module_details")
    assert not hasattr(response, "status")
