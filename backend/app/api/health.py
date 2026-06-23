import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.tasks.reaper import get_reaper_status

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

    The "reaper" field (S-6) surfaces the stuck-analysis reaper's own
    health -- the strongest internal pipeline-health signal this app has,
    previously visible only in stdout logs nobody watches. Deliberately
    does NOT affect this endpoint's status code: a stale reaper is a real
    degradation worth surfacing, but conflating it with "the API/DB is
    down" risks the exact false-alarm pattern Phase 30 traced back to a
    missing HEAD handler (a healthy backend wrongly reported as down).
    """
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check database connectivity failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": "Database connectivity check failed"}},
        )

    return {"status": "ok", "database": "ok", "reaper": get_reaper_status()}
