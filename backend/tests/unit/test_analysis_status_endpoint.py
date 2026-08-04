"""GET /analysis/{id}/status stage-text mapping (Phase 10 Step 3): the new "error"
terminal status (set by the reaper, see backend/app/tasks/reaper.py) must map to a
human-readable "Analysis interrupted" stage -- distinct from the retired "failed"
status's "Failed" stage, which is left untouched (Phase 12 cleanup scope).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

import app.api.v1.routes.analysis as analysis_routes
from app.api.v1.routes.analysis import get_analysis_status
from app.models.analysis_result import AnalysisResult
from app.models.user import User


@pytest.fixture(autouse=True)
def _no_ondemand_reap(monkeypatch):
    """Phase 60: the status endpoint now runs a throttled on-demand reap before
    reading the row. These tests cover the stage-text mapping, not reaping, and
    they pass an AsyncMock session -- letting the real reap run against it would
    store a Mock (not an int) in the reaper's module-level `_last_reaped_count`,
    which persists for the whole test session and later breaks JSON-serialising
    GET /health. Neutralise it here so each concern is tested where it belongs.
    """
    monkeypatch.setattr(analysis_routes, "maybe_reap_stuck_analyses", AsyncMock(return_value=None))


@pytest.fixture
def current_user():
    return User(id=uuid.uuid4(), email="test@example.com", hashed_pw="x")


async def test_get_analysis_status_maps_error_to_analysis_interrupted(current_user):
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="error",
        run_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15),
        integrity_score=None,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=analysis)

    result = await get_analysis_status(str(analysis.id), db=db, current_user=current_user)

    assert result["status"] == "error"
    assert result["stage"] == "Analysis interrupted"


async def test_get_analysis_status_running_stage_unaffected(current_user):
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="running:forensics",
        run_at=datetime.now(timezone.utc).replace(tzinfo=None),
        integrity_score=None,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=analysis)

    result = await get_analysis_status(str(analysis.id), db=db, current_user=current_user)

    assert result["status"] == "running"
    assert result["stage"] == "forensics"


async def test_get_analysis_status_survives_a_failing_ondemand_reap(monkeypatch, current_user):
    """Phase 60: the on-demand reap is an opportunistic optimisation riding on a
    read path. If it raises (e.g. the DB is degraded), the caller must still get
    their status -- the reap must never be able to take down the endpoint the
    frontend polls every 3 seconds."""
    monkeypatch.setattr(
        analysis_routes,
        "maybe_reap_stuck_analyses",
        AsyncMock(side_effect=RuntimeError("database unavailable")),
    )
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status="complete",
        run_at=datetime.now(timezone.utc).replace(tzinfo=None),
        integrity_score=72.5,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=analysis)

    result = await get_analysis_status(str(analysis.id), db=db, current_user=current_user)

    assert result["status"] == "complete"
    assert result["integrity_score"] == 72.5
