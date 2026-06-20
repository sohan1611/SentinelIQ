import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
@router.head("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Unauthenticated liveness/readiness probe (ADR-012).

    Confirms the API process is up and can reach the database -- used by
    Render to detect free-tier spin-down/restart cycles. HEAD is supported
    explicitly because uptime monitors (e.g. UptimeRobot) default to HEAD
    requests for HTTP(s) checks, which otherwise hit a bare 405 here.
    """
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check database connectivity failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": "Database connectivity check failed"}},
        )

    return {"status": "ok", "database": "ok"}
