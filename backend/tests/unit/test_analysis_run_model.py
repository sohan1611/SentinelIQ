import uuid
from datetime import datetime, timezone

from app.models.analysis_run import AnalysisRun
from app.schemas.analysis_run import AnalysisRunRecord


def test_analysis_run_record_round_trips_from_model():
    run = AnalysisRun(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        analysis_result_id=uuid.uuid4(),
        run_at=datetime.now(timezone.utc),
        counted=True,
    )

    record = AnalysisRunRecord.model_validate(run)

    assert record.id == run.id
    assert record.user_id == run.user_id
    assert record.company_id == run.company_id
    assert record.analysis_result_id == run.analysis_result_id
    assert record.run_at == run.run_at
    assert record.counted is True


def test_analysis_run_registered_on_base_metadata():
    from app.database import Base

    assert "analysis_runs" in Base.metadata.tables
    table = Base.metadata.tables["analysis_runs"]
    assert {c.name for c in table.columns} == {
        "id", "user_id", "company_id", "analysis_result_id", "run_at", "counted",
    }
