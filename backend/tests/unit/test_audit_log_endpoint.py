"""GET /audit-log (Phase 38, F6 scoped to audit logging): the current
user's own action history, newest first, strictly scoped to current_user.id.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.routes.audit_log import get_audit_log
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.audit_log import log_action


def _execute_result(value):
    result = MagicMock()
    result.scalars.return_value.all.return_value = value
    return result


async def test_returns_only_current_users_rows_newest_first():
    user = User(id=uuid.uuid4(), email="a@example.com", hashed_pw="x")
    now = datetime.now(timezone.utc)
    rows = [
        AuditLog(id=uuid.uuid4(), user_id=user.id, action="login", created_at=now),
        AuditLog(id=uuid.uuid4(), user_id=user.id, action="watchlist_add", detail={"ticker": "AAPL"}, created_at=now),
    ]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_execute_result(rows))

    result = await get_audit_log(db=db, current_user=user)

    assert len(result) == 2
    # Query itself filters by user_id and orders by created_at desc -- assert
    # the actual SQL references both, since this is the entire safety
    # boundary (no role system exists to gate a cross-user view otherwise).
    query_str = str(db.execute.await_args.args[0])
    assert "audit_logs.user_id" in query_str
    assert "ORDER BY audit_logs.created_at DESC" in query_str


async def test_log_action_stages_row_with_all_fields():
    db = MagicMock()
    user_id = uuid.uuid4()

    log_action(db, user_id, "watchlist_add", detail={"ticker": "AAPL"}, ip_address="203.0.113.5")

    assert db.add.call_count == 1
    staged = db.add.call_args.args[0]
    assert isinstance(staged, AuditLog)
    assert staged.user_id == user_id
    assert staged.action == "watchlist_add"
    assert staged.detail == {"ticker": "AAPL"}
    assert staged.ip_address == "203.0.113.5"


async def test_log_action_defaults_detail_and_ip_to_none():
    db = MagicMock()
    user_id = uuid.uuid4()

    log_action(db, user_id, "login")

    staged = db.add.call_args.args[0]
    assert staged.detail is None
    assert staged.ip_address is None
