import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

STUCK_ANALYSIS_THRESHOLD_MINUTES = 10
REAPER_INTERVAL_SECONDS = 120


def _stuck_analyses_query(cutoff: datetime):
    """AnalysisResult rows stuck in a running:* state past the threshold (ADR-012)."""
    return select(AnalysisResult).where(
        AnalysisResult.status.like("running:%"),
        AnalysisResult.run_at < cutoff,
    )


async def reap_stuck_analyses(session: AsyncSession) -> int:
    """Mark stale running:* AnalysisResult rows with the terminal 'error' status.

    A Render free-tier spin-down/restart can kill the in-process background
    task mid-analysis, leaving the row frozen at running:<stage> forever and
    the frontend polling indefinitely. "error" is a new terminal status --
    it does not revive the retired "failed" status (ADR-010 / Phase 3).
    Returns the number of rows updated.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=STUCK_ANALYSIS_THRESHOLD_MINUTES)
    result = await session.execute(_stuck_analyses_query(cutoff))
    stuck = result.scalars().all()

    for analysis in stuck:
        analysis.status = "error"

    if stuck:
        await session.commit()

    return len(stuck)


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
