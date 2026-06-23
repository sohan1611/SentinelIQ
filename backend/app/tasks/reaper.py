import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

STUCK_ANALYSIS_THRESHOLD_MINUTES = 10
REAPER_INTERVAL_SECONDS = 120
# S-6: tolerate one slow iteration before calling the loop "stale" --
# 3x interval, not 1x, to avoid false alarms from a single delayed tick.
_STALE_AFTER_SECONDS = REAPER_INTERVAL_SECONDS * 3

# Module-level reaper health state, surfaced via GET /health (S-6) -- the
# only existing free, already-monitored (UptimeRobot, Phase 30) signal this
# app has. Updated at the end of EVERY loop iteration, including no-op runs
# (count=0 still proves the loop is alive).
_last_run_at: datetime | None = None
_last_reaped_count: int = 0


def get_reaper_status() -> dict:
    """Returns the reaper's own health, for GET /health to surface (S-6).

    `stale=True` means the loop hasn't completed an iteration recently --
    either it never started, or it's stuck/crashed past its own exception
    handler. This is a STRONGER signal than the per-reap warning log, which
    only fires when something was actually reaped.
    """
    is_stale = (
        _last_run_at is None
        or (datetime.now(timezone.utc) - _last_run_at).total_seconds() > _STALE_AFTER_SECONDS
    )
    return {
        "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
        "last_reaped_count": _last_reaped_count,
        "stale": is_stale,
    }


def _stuck_analyses_update(cutoff: datetime):
    """Atomic, conditional UPDATE for AnalysisResult rows stuck past the
    threshold (ADR-012) -- either mid-run (running:*) or never picked up by
    the worker at all (pending, Phase 40 / H-1: a BackgroundTask lost to a
    restart in the window between the row's commit and the worker's first
    status update). The WHERE clause is re-evaluated against each row's
    CURRENT state at write time, so a worker that completes the analysis
    between the reaper's scan and its write can never be clobbered back to
    'error' (Phase 40 / A-2) -- the row simply no longer matches by the time
    this UPDATE runs against it.
    """
    return (
        update(AnalysisResult)
        .where(
            or_(
                AnalysisResult.status.like("running:%"),
                AnalysisResult.status == "pending",
            ),
            AnalysisResult.run_at < cutoff,
        )
        .values(status="error")
    )


async def reap_stuck_analyses(session: AsyncSession) -> int:
    """Mark stale running:*/pending AnalysisResult rows with the terminal
    'error' status.

    A Render free-tier spin-down/restart can kill the in-process background
    task mid-analysis (leaving the row frozen at running:<stage>) or before
    it ever starts (leaving the row frozen at pending) -- both freeze the
    frontend polling indefinitely. "error" is a new terminal status -- it
    does not revive the retired "failed" status (ADR-010 / Phase 3).
    Returns the number of rows updated.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=STUCK_ANALYSIS_THRESHOLD_MINUTES)
    result = await session.execute(_stuck_analyses_update(cutoff))
    await session.commit()
    return result.rowcount


async def reaper_loop():
    """Runs reap_stuck_analyses immediately, then every REAPER_INTERVAL_SECONDS.

    The immediate first pass covers the "startup reaper" case (ADR-012) --
    a fresh process recovering from a Render free-tier spin-down -- while the
    recurring loop also catches rows that get stuck while this instance stays
    warm.
    """
    global _last_run_at, _last_reaped_count
    while True:
        try:
            async with AsyncSessionLocal() as session:
                count = await reap_stuck_analyses(session)
                if count:
                    logger.warning(f"Reaper marked {count} stuck analysis run(s) as 'error'")
            _last_run_at = datetime.now(timezone.utc)
            _last_reaped_count = count
        except Exception:
            logger.exception("Reaper iteration failed")
        await asyncio.sleep(REAPER_INTERVAL_SECONDS)
