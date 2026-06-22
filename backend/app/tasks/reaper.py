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
    while True:
        try:
            async with AsyncSessionLocal() as session:
                count = await reap_stuck_analyses(session)
                if count:
                    logger.warning(f"Reaper marked {count} stuck analysis run(s) as 'error'")
        except Exception:
            logger.exception("Reaper iteration failed")
        await asyncio.sleep(REAPER_INTERVAL_SECONDS)
