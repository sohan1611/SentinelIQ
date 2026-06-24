import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.watchlist import WatchlistItem
from app.models.analysis_result import AnalysisResult
from app.tasks.analysis_worker import run_full_analysis

logger = logging.getLogger(__name__)

# Phase 47 (E-4): the "monitoring" half -- Step 1's alert detector only fires
# opportunistically, whenever any analysis happens to complete. This loop is
# what makes the watchlist an actual early-warning feed rather than a
# passive bookmark list. Constants deliberately conservative: a once-daily
# per-company cadence, throttled to a handful per tick, given the live
# yfinance rate-limiting already observed (Phase 43) and the shared
# GEMINI_DAILY_BUDGET=200/day ceiling this loop draws from like any caller.
STALE_AFTER_HOURS = 24
REFRESH_INTERVAL_SECONDS = 3600
MAX_REFRESHES_PER_TICK = 3


def _due_companies_query(cutoff: datetime):
    """Companies on at least one user's watchlist that are either never
    analyzed or stale past the cutoff. DISTINCT must include last_analyzed
    (not just id) because Postgres requires ORDER BY expressions to appear
    in the SELECT list under DISTINCT -- last_analyzed is functionally
    determined by id, so this still yields exactly one row per company."""
    return (
        select(Company.id, Company.last_analyzed)
        .join(WatchlistItem, WatchlistItem.company_id == Company.id)
        .where(or_(Company.last_analyzed.is_(None), Company.last_analyzed < cutoff))
        .distinct()
        .order_by(Company.last_analyzed.asc().nulls_first())
        .limit(MAX_REFRESHES_PER_TICK)
    )


async def find_due_companies(session: AsyncSession) -> list[UUID]:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=STALE_AFTER_HOURS)
    result = await session.execute(_due_companies_query(cutoff))
    return [row[0] for row in result.all()]


async def trigger_refresh(session: AsyncSession, company_id: UUID) -> None:
    """Starts a system-triggered analysis for one company. No AnalysisRun
    row is logged -- that table meters user-initiated free-tier quota
    consumption (ADR-007/013); a scheduled tick has no acting user."""
    analysis = AnalysisResult(company_id=company_id, status="pending")
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    await run_full_analysis(company_id, analysis.id)


async def watchlist_refresher_loop():
    """Runs every REFRESH_INTERVAL_SECONDS: finds due companies, refreshes
    each in turn. One bad tick (or one company's refresh failing) must
    never kill the loop -- same discipline as reaper_loop."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                due = await find_due_companies(session)
                for company_id in due:
                    try:
                        await trigger_refresh(session, company_id)
                    except Exception:
                        logger.exception(f"Watchlist refresh failed for company {company_id}")
                if due:
                    logger.info(f"Watchlist refresher processed {len(due)} due compan{'y' if len(due) == 1 else 'ies'}")
        except Exception:
            logger.exception("Watchlist refresher iteration failed")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
