"""GET /alerts + POST /alerts/{id}/read (Phase 47 / E-4 Step 3): the
current user's risk-band-change alerts. Strictly scoped to current_user.id,
same convention as audit-log -- the mark-read ownership check is the real
security boundary here (a 404 on someone else's alert, not just a missing
one), so it gets its own explicit test rather than relying on code review.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
import pytest

from app.api.v1.routes.alerts import get_alerts, mark_alert_read, ALERTS_LIMIT
from app.models.user import User
from app.models.company import Company
from app.models.watchlist_alert import WatchlistAlert


def _all_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def _scalar_result(value):
    result = MagicMock()
    result.scalar.return_value = value
    return result


@pytest.fixture
def user():
    return User(id=uuid.uuid4(), email="a@example.com", hashed_pw="x")


@pytest.fixture
def company():
    return Company(id=uuid.uuid4(), name="Acme Corp", ticker="ACME", sector="Tech", exchange="NASDAQ")


async def test_returns_only_current_users_alerts_newest_first(user, company):
    now = datetime.now(timezone.utc)
    alert = WatchlistAlert(
        id=uuid.uuid4(), user_id=user.id, company_id=company.id, analysis_id=uuid.uuid4(),
        previous_score=85.0, new_score=55.0, previous_risk="strong", new_risk="moderate",
        is_read=False, created_at=now,
    )

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_all_result([(alert, company)]), _scalar_result(1)])

    result = await get_alerts(db=db, current_user=user)

    assert result["unread_count"] == 1
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["id"] == alert.id
    assert result["alerts"][0]["company"] is company

    list_query_str = str(db.execute.await_args_list[0].args[0])
    assert "watchlist_alerts.user_id" in list_query_str
    assert "ORDER BY watchlist_alerts.created_at DESC" in list_query_str
    assert f"LIMIT {ALERTS_LIMIT}" in list_query_str or "LIMIT" in list_query_str


async def test_unread_count_is_independent_of_the_limited_list(user, company):
    # The list query can be capped at ALERTS_LIMIT while unread_count must
    # still reflect every unread row -- proven here by returning an empty
    # list alongside a nonzero count, which could only happen if the two
    # queries are genuinely independent.
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_all_result([]), _scalar_result(7)])

    result = await get_alerts(db=db, current_user=user)

    assert result["alerts"] == []
    assert result["unread_count"] == 7

    count_query_str = str(db.execute.await_args_list[1].args[0])
    assert "watchlist_alerts.is_read" in count_query_str


async def test_unread_count_defaults_to_zero_when_scalar_is_none(user):
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_all_result([]), _scalar_result(None)])

    result = await get_alerts(db=db, current_user=user)

    assert result["unread_count"] == 0


async def test_mark_alert_read_flips_flag_and_commits(user, company):
    alert = WatchlistAlert(
        id=uuid.uuid4(), user_id=user.id, company_id=company.id, analysis_id=uuid.uuid4(),
        previous_score=85.0, new_score=55.0, previous_risk="strong", new_risk="moderate",
        is_read=False,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=alert)

    result = await mark_alert_read(str(alert.id), db=db, current_user=user)

    assert alert.is_read is True
    assert db.commit.await_count == 1
    assert result == {"message": "Alert marked as read"}


async def test_mark_alert_read_404s_when_alert_missing(user):
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await mark_alert_read(str(uuid.uuid4()), db=db, current_user=user)

    assert exc_info.value.status_code == 404


async def test_mark_alert_read_404s_when_alert_owned_by_another_user(user, company):
    other_users_alert = WatchlistAlert(
        id=uuid.uuid4(), user_id=uuid.uuid4(), company_id=company.id, analysis_id=uuid.uuid4(),
        previous_score=85.0, new_score=55.0, previous_risk="strong", new_risk="moderate",
        is_read=False,
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=other_users_alert)

    with pytest.raises(HTTPException) as exc_info:
        await mark_alert_read(str(other_users_alert.id), db=db, current_user=user)

    assert exc_info.value.status_code == 404
    assert other_users_alert.is_read is False  # never mutated
    assert db.commit.await_count == 0
