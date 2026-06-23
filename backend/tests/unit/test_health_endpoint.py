"""GET /health (ADR-012): unauthenticated DB-connectivity probe so Render can
detect free-tier spin-down/restart cycles. No auth dependency -- only get_db.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import app.tasks.reaper as reaper_module
from app.api.health import health_check


async def test_health_check_returns_ok_when_db_responds(monkeypatch):
    monkeypatch.setattr(reaper_module, "_last_run_at", None)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)

    result = await health_check(db=db)

    assert result["status"] == "ok"
    assert result["database"] == "ok"
    db.execute.assert_awaited_once()


async def test_health_check_includes_reaper_status(monkeypatch):
    # S-6: the reaper's own health rides along on the endpoint Render/
    # UptimeRobot already polls, without changing this endpoint's status
    # code or its existing status/database fields.
    monkeypatch.setattr(reaper_module, "_last_run_at", None)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)

    result = await health_check(db=db)

    assert result["reaper"]["stale"] is True
    assert "last_reaped_count" in result["reaper"]


async def test_health_check_raises_503_when_db_unreachable():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=ConnectionError("connection refused"))

    with pytest.raises(HTTPException) as exc_info:
        await health_check(db=db)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "error": {"code": "SERVICE_UNAVAILABLE", "message": "Database connectivity check failed"}
    }
