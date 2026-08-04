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
async def health_check():
    """Unauthenticated shallow liveness probe (ADR-012).

    Confirms only that the API process is up. It deliberately makes NO
    database call: Render and uptime monitors poll this path on a schedule,
    and a ``SELECT 1`` on every probe prevents Neon free-tier compute from
    reaching its five-minute idle suspension window. Use ``/health/db`` for
    the deep, manual/occasional database-connectivity check instead.

    HEAD is supported explicitly because uptime monitors (e.g. UptimeRobot)
    default to HEAD requests for HTTP(s) checks, which otherwise hit a bare
    405 here. The Phase 30 false-alarm lesson still applies: a healthy backend
    must not be reported down simply because the monitoring method is HEAD.

    The "reaper" field (S-6) surfaces the stuck-analysis reaper's own
    health -- the strongest internal pipeline-health signal this app has,
    previously visible only in stdout logs nobody watches. Deliberately does
    NOT affect this endpoint's status code: a stale reaper is a real
    degradation worth surfacing, but it is not evidence that the API is down.
    """
    return {"status": "ok", "reaper": get_reaper_status()}


@router.get("/health/db")
@router.head("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Unauthenticated deep database-connectivity probe (ADR-012).

    This retains the explicit ``SELECT 1`` check for manual and occasional
    diagnostics. It must not be used for Render or uptime-monitor health
    checks: routine database traffic keeps Neon's free-tier compute awake and
    exhausts its limited monthly allowance instead of letting it scale to zero.

    HEAD is supported for parity with the shallow probe and because uptime
    monitors default to HEAD; use it only when a deliberate deep check is
    required, not as a polling target.
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
