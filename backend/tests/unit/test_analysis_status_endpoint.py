"""GET /analysis/{id}/status stage-text mapping (Phase 10 Step 3): the new "error"
terminal status (set by the reaper, see backend/app/tasks/reaper.py) must map to a
human-readable "Analysis interrupted" stage -- distinct from the retired "failed"
status's "Failed" stage, which is left untouched (Phase 12 cleanup scope).
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from app.api.v1.routes.analysis import get_analysis_status
from app.models.analysis_result import AnalysisResult


async def test_get_analysis_status_maps_error_to_analysis_interrupted():
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="error",
        run_at=datetime.utcnow() - timedelta(minutes=15),
        integrity_score=None,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=analysis)

    result = await get_analysis_status(str(analysis.id), db=db)

    assert result["status"] == "error"
    assert result["stage"] == "Analysis interrupted"


async def test_get_analysis_status_running_stage_unaffected():
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="running:forensics",
        run_at=datetime.utcnow(),
        integrity_score=None,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=analysis)

    result = await get_analysis_status(str(analysis.id), db=db)

    assert result["status"] == "running"
    assert result["stage"] == "forensics"
