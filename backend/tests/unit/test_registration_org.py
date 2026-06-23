"""Registration creates a personal Organization for every new user (Phase 46 / E-1).

Scaffolding only -- no multi-member orgs, no role enforcement yet. Every
user's org id matches their own user id (see the 0008 migration's backfill
docstring for why this 1:1 shape is deliberate).
"""
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.routes.auth import register
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import UserCreate


def _db_with_no_existing_user():
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


async def test_registration_stages_one_organization_and_one_user():
    user_in = UserCreate(email="new@example.com", password="secret123", full_name="New User")
    db = _db_with_no_existing_user()

    await register(user_in=user_in, request=MagicMock(), response=MagicMock(), db=db)

    staged = [call.args[0] for call in db.add.call_args_list]
    orgs = [obj for obj in staged if isinstance(obj, Organization)]
    users = [obj for obj in staged if isinstance(obj, User)]
    assert len(orgs) == 1
    assert len(users) == 1


async def test_new_user_org_id_matches_their_own_id():
    user_in = UserCreate(email="new@example.com", password="secret123", full_name="New User")
    db = _db_with_no_existing_user()

    await register(user_in=user_in, request=MagicMock(), response=MagicMock(), db=db)

    staged = [call.args[0] for call in db.add.call_args_list]
    org = next(obj for obj in staged if isinstance(obj, Organization))
    user = next(obj for obj in staged if isinstance(obj, User))

    assert user.org_id == org.id
    assert user.id == org.id


async def test_new_user_gets_owner_role():
    user_in = UserCreate(email="new@example.com", password="secret123", full_name="New User")
    db = _db_with_no_existing_user()

    await register(user_in=user_in, request=MagicMock(), response=MagicMock(), db=db)

    staged = [call.args[0] for call in db.add.call_args_list]
    user = next(obj for obj in staged if isinstance(obj, User))
    assert user.role == "owner"


async def test_org_name_derived_from_full_name():
    user_in = UserCreate(email="new@example.com", password="secret123", full_name="New User")
    db = _db_with_no_existing_user()

    await register(user_in=user_in, request=MagicMock(), response=MagicMock(), db=db)

    staged = [call.args[0] for call in db.add.call_args_list]
    org = next(obj for obj in staged if isinstance(obj, Organization))
    assert org.name == "New User's Organization"


async def test_org_name_falls_back_to_email_when_no_full_name():
    user_in = UserCreate(email="noname@example.com", password="secret123")
    db = _db_with_no_existing_user()

    await register(user_in=user_in, request=MagicMock(), response=MagicMock(), db=db)

    staged = [call.args[0] for call in db.add.call_args_list]
    org = next(obj for obj in staged if isinstance(obj, Organization))
    assert org.name == "noname@example.com's Organization"
