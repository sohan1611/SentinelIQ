"""Health endpoints (ADR-012): shallow liveness at /health and an occasional
deep database-connectivity check at /health/db. Neither endpoint requires auth.
"""

import inspect
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.tasks.reaper as reaper_module
from app.api.health import database_health_check, health_check
from app.database import get_db
from app.main import app


async def test_health_check_returns_ok_without_database(monkeypatch):
    monkeypatch.setattr(reaper_module, "_last_run_at", None)

    assert not inspect.signature(health_check).parameters

    result = await health_check()

    assert result["status"] == "ok"
    assert "database" not in result


async def test_health_check_includes_reaper_status(monkeypatch):
    # S-6: the reaper's own health rides along on the shallow endpoint Render/
    # UptimeRobot polls, without changing this endpoint's status code.
    monkeypatch.setattr(reaper_module, "_last_run_at", None)

    result = await health_check()

    assert result["reaper"]["stale"] is True
    assert "last_reaped_count" in result["reaper"]


def test_health_check_succeeds_when_database_is_unavailable():
    async def unavailable_db():
        raise AssertionError("The shallow health check must not access the database")

    app.dependency_overrides[get_db] = unavailable_db
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_database_health_check_returns_ok_when_db_responds():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)

    result = await database_health_check(db=db)

    assert result == {"status": "ok", "database": "ok"}
    db.execute.assert_awaited_once()


async def test_database_health_check_raises_503_when_db_unreachable():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=ConnectionError("connection refused"))

    with pytest.raises(HTTPException) as exc_info:
        await database_health_check(db=db)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "error": {"code": "SERVICE_UNAVAILABLE", "message": "Database connectivity check failed"}
    }
