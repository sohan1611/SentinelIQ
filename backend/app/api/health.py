import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pipeline_health import get_pipeline_status
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

    The "pipeline" field (Phase 65) reports, over the last N completed
    analyses held in memory, how many were computed with a weighted forensic
    module missing -- the signal that would have exposed the yfinance outage
    that left `financial`/`cashflow`/`earnings` dead for two months while the
    product kept publishing scores. `signal_degraded: true` means an upstream
    feed has most likely died, not that this API is unhealthy.

    Both extra fields are read from in-process state ONLY. This endpoint makes
    no database call at all -- that is deliberate and load-bearing: Render and
    uptime monitors poll it on a schedule, and a query here would keep Neon's
    free-tier compute from ever idling (the exact failure Phase 59 fixed).

    Like "reaper", "pipeline" must NEVER change this endpoint's status code.
    Conflating a degraded data feed with "the API is down" would recreate the
    Phase 30 false-alarm outage, where a healthy backend was reported down.
    """
    return {
        "status": "ok",
        "reaper": get_reaper_status(),
        "pipeline": get_pipeline_status(),
    }


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
