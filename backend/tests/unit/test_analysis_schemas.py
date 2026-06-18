"""Round-trip and schema-version tests for ModuleDetails (Phase 15).

Covers:
- Full-shape round-trip through AnalysisResultResponse
- schema_version=1 written on new rows, schema_version=0 default on old rows
- Old rows (no schema_version) still deserialize without error
- Governance failure shape (empty provenance)
- Pending analysis (null module_details)
- AnalysisHistoryItem omits module_details
"""
import uuid
from datetime import datetime, timezone

from app.models.analysis_result import AnalysisResult
from app.schemas.analysis import (
    AnalysisResultResponse,
    AnalysisHistoryItem,
    ModuleDetails,
    CURRENT_SCHEMA_VERSION,
)


def _module_details_v1():
    """Valid schema_version=1 module_details dict — matches Phase 15 typed shape."""
    return {
        "schema_version": 1,
        "scores": {
            "financial": 70.0, "cashflow": 72.5, "earnings": 100.0, "debt": 65.0,
            "governance": 75.0, "narrative": 35.0, "news": 65.0,
        },
        "confidence": "high",
        "revenue": {
            "divergences": [{"period": "2023-12-31", "divergence": 0.12}],
            "recv_ratios": [{"period": "2023-12-31", "recv_ratio": 0.08}],
        },
        "cashflow": {
            "accrual_ratios": [{"period": "2023-12-31", "accrual_ratio": 0.05}],
        },
        "earnings": {
            "margins": [{"period": "2023-12-31", "gross_margin": 0.40}],
            "net_incomes": [{"period": "2023-12-31", "net_income": 50000000.0}],
        },
        "debt": {
            "debt_metrics": [{
                "period": "2023-12-31",
                "debt_to_revenue": 0.5,
                "debt_growth": 0.08,
                "interest_coverage": 4.2,
            }],
        },
        "narrative": {
            "snapshots": [
                {
                    "period": "2024-01-15",
                    "statement_text": "Revenue grew strongly this quarter.",
                    "sentiment_label": "optimistic",
                    "sentiment_score": 0.8,
                    "source": "News",
                    "source_quote": "Revenue grew strongly",
                },
            ],
            "statements_used": 1,
            "provenance": [
                {"period": "2024-01-15", "model_id": "gemini-2.5-flash", "prompt": "p1", "raw_response": "r1"},
            ],
            "tone_shifts": [
                {"period": "2024-01-15", "severity": "high", "description": "Tone shifted"},
            ],
        },
        "governance": {
            "provenance": {
                "model_id": "gemini-2.5-flash",
                "prompt": "gov-prompt",
                "raw_response": {
                    "finish_reason": "STOP",
                    "safety_ratings": [],
                    "prompt_token_count": 120,
                    "candidates_token_count": 40,
                },
                "low_confidence": False,
            },
            "low_confidence": False,
            "flags": [
                {
                    "flag_type": "governance",
                    "severity": "high",
                    "description": "CFO resigned",
                    "period": "2024-01-10",
                    "source_quote": "Apple CFO resigned unexpectedly",
                },
            ],
        },
    }


def _legacy_module_details():
    """Pre-Phase-15 row: no schema_version key, revenue/cashflow/etc. are free-form dicts."""
    d = _module_details_v1()
    d.pop("schema_version")  # simulate old row
    return d


# ---------------------------------------------------------------------------
# schema_version tests
# ---------------------------------------------------------------------------

def test_schema_version_defaults_to_zero_for_legacy_rows():
    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            module_details=_legacy_module_details(), status="complete",
        )
    )
    assert response.module_details.schema_version == 0


def test_schema_version_is_one_for_current_rows():
    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            module_details=_module_details_v1(), status="complete",
        )
    )
    assert response.module_details.schema_version == CURRENT_SCHEMA_VERSION == 1


def test_current_schema_version_constant_is_one():
    assert CURRENT_SCHEMA_VERSION == 1


# ---------------------------------------------------------------------------
# Full shape round-trip (v1)
# ---------------------------------------------------------------------------

def test_module_details_round_trips_full_shape():
    analysis = AnalysisResult(
        id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
        integrity_score=70.2, financial_score=70.0, cashflow_score=72.5,
        governance_score=75.0, earnings_score=100.0, narrative_score=35.0, news_score=65.0,
        module_details=_module_details_v1(), status="complete",
    )

    response = AnalysisResultResponse.model_validate(analysis)

    assert response.module_details.schema_version == 1
    assert response.module_details.confidence == "high"
    assert response.module_details.scores["governance"] == 75.0
    assert response.module_details.scores["debt"] == 65.0


def test_typed_forensic_sub_models_round_trip():
    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            module_details=_module_details_v1(), status="complete",
        )
    )
    md = response.module_details

    assert md.revenue.divergences[0].period == "2023-12-31"
    assert md.revenue.divergences[0].divergence == 0.12
    assert md.revenue.recv_ratios[0].recv_ratio == 0.08

    assert md.cashflow.accrual_ratios[0].accrual_ratio == 0.05

    assert md.earnings.margins[0].gross_margin == 0.40
    assert md.earnings.net_incomes[0].net_income == 50000000.0

    assert md.debt.debt_metrics[0].debt_to_revenue == 0.5
    assert md.debt.debt_metrics[0].interest_coverage == 4.2


def test_narrative_and_governance_sub_models_round_trip():
    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            module_details=_module_details_v1(), status="complete",
        )
    )
    md = response.module_details

    assert md.narrative.statements_used == 1
    assert md.narrative.provenance[0]["model_id"] == "gemini-2.5-flash"
    assert md.narrative.tone_shifts[0]["severity"] == "high"
    # source_quote preserved in snapshots (List[Dict[str, Any]])
    assert md.narrative.snapshots[0]["source_quote"] == "Revenue grew strongly"

    assert md.governance.provenance["model_id"] == "gemini-2.5-flash"
    assert md.governance.low_confidence is False
    assert md.governance.flags[0]["source_quote"] == "Apple CFO resigned unexpectedly"


# ---------------------------------------------------------------------------
# Empty sub-models default correctly
# ---------------------------------------------------------------------------

def test_empty_forensic_sub_models_default_to_empty_lists():
    md = ModuleDetails()
    assert md.revenue.divergences == []
    assert md.cashflow.accrual_ratios == []
    assert md.earnings.margins == []
    assert md.debt.debt_metrics == []
    assert md.schema_version == 0


def test_module_details_handles_governance_failure_shape():
    details = _module_details_v1()
    details["scores"].pop("governance")
    details["governance"] = {"provenance": {}}

    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            module_details=details, status="complete",
        )
    )

    assert "governance" not in response.module_details.scores
    assert response.module_details.governance.provenance == {}
    assert response.module_details.governance.low_confidence is False
    assert response.module_details.governance.flags == []


def test_module_details_none_for_pending_analysis():
    response = AnalysisResultResponse.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc), status="pending",
        )
    )
    assert response.module_details is None


def test_analysis_history_item_omits_module_details():
    response = AnalysisHistoryItem.model_validate(
        AnalysisResult(
            id=uuid.uuid4(), company_id=uuid.uuid4(), run_at=datetime.now(timezone.utc),
            integrity_score=70.2, financial_score=70.0, cashflow_score=72.5,
            governance_score=75.0, earnings_score=100.0, narrative_score=35.0, news_score=65.0,
            module_details=_module_details_v1(), status="complete",
        )
    )
    assert response.integrity_score == 70.2
    assert response.governance_score == 75.0
    assert not hasattr(response, "module_details")
    assert not hasattr(response, "status")


# ---------------------------------------------------------------------------
# model_dump writes schema_version=1 (write-through path)
# ---------------------------------------------------------------------------

def test_model_dump_includes_schema_version():
    md = ModuleDetails.model_validate({"schema_version": CURRENT_SCHEMA_VERSION, "confidence": "medium"})
    dumped = md.model_dump()
    assert dumped["schema_version"] == CURRENT_SCHEMA_VERSION


def test_model_dump_forensic_sub_models_serialize_to_dicts():
    md = ModuleDetails.model_validate({
        "schema_version": 1,
        "revenue": {"divergences": [{"period": "2023", "divergence": 0.1}], "recv_ratios": []},
    })
    dumped = md.model_dump()
    assert dumped["revenue"]["divergences"][0] == {"period": "2023", "divergence": 0.1}
    assert isinstance(dumped["revenue"]["divergences"][0], dict)
