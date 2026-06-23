import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import bcrypt
from jose import jwt, JWTError

from app.api.deps import get_db, get_current_user
from app.api.middleware.rate_limit import rate_limit, client_ip
from app.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.audit_log import log_action

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the httpOnly JWT cookie with environment-appropriate security flags.

    Dev (FRONTEND_URL starts with http://): Secure=False, SameSite=lax —
      works across localhost ports (same registered domain).
    Prod (FRONTEND_URL starts with https://): Secure=True, SameSite=none —
      required for cross-site cookies between Vercel and Render.
    """
    is_https = settings.FRONTEND_URL.startswith("https://")
    response.set_cookie(
        key="sentineliq_token",
        value=token,
        httponly=True,
        secure=is_https,
        samesite="none" if is_https else "lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", dependencies=[Depends(rate_limit("register", 5))])
async def register(user_in: UserCreate, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Registration unavailable for this email address.",
        )
    # E-1 scaffolding: every user gets exactly one personal org, whose id
    # matches their own user id (see the 0008 migration's backfill for why
    # this 1:1 shape avoids needing a temporary id-correlation step).
    new_id = uuid.uuid4()
    org = Organization(id=new_id, name=f"{user_in.full_name or user_in.email}'s Organization")
    user = User(
        id=new_id,
        email=user_in.email,
        hashed_pw=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        org_id=new_id,
        role="owner",
    )
    db.add(org)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    _set_auth_cookie(response, token)
    log_action(db, user.id, "register", ip_address=client_ip(request))
    await db.commit()
    return {"status": "ok"}


@router.post("/login", dependencies=[Depends(rate_limit("login", 10))])
async def login(request: Request, response: Response, db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_pw):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token(
        user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    _set_auth_cookie(response, token)
    log_action(db, user.id, "login", ip_address=client_ip(request))
    await db.commit()
    return {"status": "ok"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    sentineliq_token: Optional[str] = Cookie(None),
):
    # Best-effort: log who logged out if the token is still decodable, but
    # never let a missing/expired/invalid token block clearing the cookie --
    # logout must stay idempotent regardless of session state (unlike
    # get_current_user, which intentionally raises 401 for every other route).
    if sentineliq_token:
        try:
            payload = jwt.decode(sentineliq_token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                log_action(db, user_id, "logout", ip_address=client_ip(request))
                await db.commit()
        except JWTError:
            pass

    response.delete_cookie(key="sentineliq_token", path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user
