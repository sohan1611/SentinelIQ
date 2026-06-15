"""GET /health (ADR-012): unauthenticated DB-connectivity probe so Render can
detect free-tier spin-down/restart cycles. No auth dependency -- only get_db.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.health import health_check


async def test_health_check_returns_ok_when_db_responds():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)

    result = await health_check(db=db)

    assert result == {"status": "ok", "database": "ok"}
    db.execute.assert_awaited_once()


async def test_health_check_raises_503_when_db_unreachable():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=ConnectionError("connection refused"))

    with pytest.raises(HTTPException) as exc_info:
        await health_check(db=db)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "error": {"code": "SERVICE_UNAVAILABLE", "message": "Database connectivity check failed"}
    }
