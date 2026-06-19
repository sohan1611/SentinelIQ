"""Auth security hardening (Phase 18 Step 3): /register must not reveal whether
an email is already registered (user enumeration protection).

The message must be generic — it must not contain "already exists" or any
phrasing that confirms the email is taken.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.routes.auth import register
from app.schemas.user import UserCreate


def _db_with_existing_user():
    existing = MagicMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = existing
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


async def test_duplicate_email_raises_400():
    user_in = UserCreate(email="taken@example.com", password="secret123", full_name="Test")
    with pytest.raises(HTTPException) as exc_info:
        await register(user_in=user_in, response=MagicMock(), db=_db_with_existing_user())
    assert exc_info.value.status_code == 400


async def test_duplicate_email_message_does_not_reveal_existence():
    user_in = UserCreate(email="taken@example.com", password="secret123", full_name="Test")
    with pytest.raises(HTTPException) as exc_info:
        await register(user_in=user_in, response=MagicMock(), db=_db_with_existing_user())

    detail = str(exc_info.value.detail).lower()
    assert "already exists" not in detail
    assert "already registered" not in detail


async def test_duplicate_email_returns_generic_message():
    user_in = UserCreate(email="taken@example.com", password="secret123", full_name="Test")
    with pytest.raises(HTTPException) as exc_info:
        await register(user_in=user_in, response=MagicMock(), db=_db_with_existing_user())

    assert "unavailable" in str(exc_info.value.detail).lower()
