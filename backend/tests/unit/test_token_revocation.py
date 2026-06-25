"""Token revocation (Phase 53 / E-2 free scaffolding): /auth/logout previously
only cleared the cookie client-side -- a copied/leaked token kept working for
its full lifetime even after "logout". This tests the actual kill switch:
logout now revokes the token's jti server-side, and get_current_user checks
the blocklist before trusting an otherwise-valid signature/exp.
"""

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.deps import get_current_user
from app.api.v1.routes.auth import create_access_token, logout
from app.models.user import User


def _request_with_no_auth_header():
    req = MagicMock()
    req.headers = {}
    return req


def _fake_db(revoked=None, user=None):
    db = AsyncMock()
    db.get = AsyncMock(return_value=revoked)
    result = MagicMock()
    result.scalars.return_value.first.return_value = user
    db.execute = AsyncMock(return_value=result)
    return db


async def test_get_current_user_succeeds_for_a_fresh_unrevoked_token():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, expires_delta=timedelta(minutes=60))
    fake_user = User(id=user_id, email="a@example.com", hashed_pw="x")
    db = _fake_db(revoked=None, user=fake_user)

    result = await get_current_user(request=_request_with_no_auth_header(), db=db, sentineliq_token=token)

    assert result is fake_user


async def test_get_current_user_rejects_a_revoked_token():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, expires_delta=timedelta(minutes=60))
    db = _fake_db(revoked=MagicMock(), user=User(id=user_id, email="a@example.com", hashed_pw="x"))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=_request_with_no_auth_header(), db=db, sentineliq_token=token)

    assert exc_info.value.status_code == 401


async def test_logout_revokes_the_tokens_jti():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, expires_delta=timedelta(minutes=60))
    # MagicMock, not AsyncMock, as the base -- db.add() is synchronous on a
    # real AsyncSession (only execute/commit/get are async); a blanket
    # AsyncMock would make log_action's correct, unawaited db.add(...) call
    # look like a dropped coroutine.
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.commit = AsyncMock()
    response = MagicMock()

    result = await logout(request=MagicMock(), response=response, db=db, sentineliq_token=token)

    assert result == {"status": "ok"}
    # Two db.execute calls: the revoke-insert (ON CONFLICT DO NOTHING), then
    # the opportunistic prune-delete of already-expired blocklist rows.
    assert db.execute.await_count == 2
    response.delete_cookie.assert_called_once_with(key="sentineliq_token", path="/")


async def test_logout_with_no_cookie_is_an_idempotent_noop():
    db = AsyncMock()
    response = MagicMock()

    result = await logout(request=MagicMock(), response=response, db=db, sentineliq_token=None)

    assert result == {"status": "ok"}
    db.execute.assert_not_called()
    response.delete_cookie.assert_called_once_with(key="sentineliq_token", path="/")


async def test_logout_with_a_malformed_token_is_an_idempotent_noop():
    db = AsyncMock()
    response = MagicMock()

    result = await logout(request=MagicMock(), response=response, db=db, sentineliq_token="not-a-real-jwt")

    assert result == {"status": "ok"}
    db.execute.assert_not_called()
    response.delete_cookie.assert_called_once_with(key="sentineliq_token", path="/")
