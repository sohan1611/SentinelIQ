from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.api.middleware.rate_limit import rate_limit, client_ip
from app.models.user import User
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.analysis_run import AnalysisRun
from app.models.red_flag import RedFlag
from app.schemas.analysis import AnalysisRunRequest, AnalysisRunResponse, AnalysisStatusResponse, AnalysisResultResponse, AnalysisHistoryItem, RedFlagResponse, CompareItemResponse
from app.services.audit_log import log_action
from app.tasks.analysis_worker import run_full_analysis

router = APIRouter()

FREE_TIER_MONTHLY_LIMIT = 5
ANALYSIS_CACHE_TTL = timedelta(hours=6)
ANALYSIS_HISTORY_LIMIT = 24
COMPARE_MAX_TICKERS = 5


def _free_tier_usage_query(user_id, since):
    """AnalysisRun rows are the user-scoped audit/metering log (ADR-007).

    Only counted=true rows (fresh computations) consume quota. A cache-hit
    re-open still logs an AnalysisRun for the audit trail but with
    counted=false, so it's excluded here (ADR-013 / Ruling A).
    """
    return select(func.count(AnalysisRun.id)).where(
        AnalysisRun.user_id == user_id,
        AnalysisRun.run_at >= since,
        AnalysisRun.counted.is_(True),
    )


@router.post("/run", response_model=AnalysisRunResponse, dependencies=[Depends(rate_limit("analysis_run", 20))])
async def run_analysis(
    request: AnalysisRunRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = request.ticker.upper()

    first_day_of_month = datetime.now(timezone.utc).replace(tzinfo=None, day=1, hour=0, minute=0, second=0, microsecond=0)
    count_res = await db.execute(_free_tier_usage_query(current_user.id, first_day_of_month))
    count = count_res.scalar() or 0

    if count >= FREE_TIER_MONTHLY_LIMIT and current_user.tier == "free":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "LIMIT_REACHED", "message": "Monthly analysis limit reached. Upgrade to Pro."}}
        )

    res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Company not found"}})

    # Cache hit: reuse a complete AnalysisResult within the TTL -- still log a run, no recompute
    cached_res = await db.execute(
        select(AnalysisResult)
        .where(
            AnalysisResult.company_id == company.id,
            AnalysisResult.status == "complete",
            AnalysisResult.run_at >= datetime.now(timezone.utc).replace(tzinfo=None) - ANALYSIS_CACHE_TTL,
        )
        .order_by(AnalysisResult.run_at.desc())
        .limit(1)
    )
    analysis = cached_res.scalars().first()
    is_cache_hit = analysis is not None

    if not analysis:
        analysis = AnalysisResult(
            company_id=company.id,
            status="pending"
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Trigger background task
        background_tasks.add_task(run_full_analysis, company.id, analysis.id)

    # ADR-013 / Ruling A: a cache-hit re-open is still logged (audit trail,
    # ADR-007) but counted=false so it doesn't consume the free-tier quota.
    db.add(AnalysisRun(
        user_id=current_user.id,
        company_id=company.id,
        analysis_result_id=analysis.id,
        counted=not is_cache_hit,
    ))
    log_action(db, current_user.id, "analysis_run", detail={"ticker": ticker}, ip_address=client_ip(http_request))
    await db.commit()

    return {"analysis_id": analysis.id, "status": analysis.status}


@router.get("/compare", response_model=list[CompareItemResponse])
async def compare_analyses(tickers: str, db: AsyncSession = Depends(get_db)):
    """Phase 37 (F5, scoped to a comparison view): each requested ticker's
    latest completed analysis, side by side. Read-only over data that
    already exists -- no scoring changes, no new tables."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(ticker_list) < 2:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "TOO_FEW_TICKERS", "message": "Provide at least 2 tickers to compare."}},
        )
    if len(ticker_list) > COMPARE_MAX_TICKERS:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "TOO_MANY_TICKERS", "message": f"Compare up to {COMPARE_MAX_TICKERS} companies at once."}},
        )

    results: list[CompareItemResponse] = []
    for ticker in ticker_list:
        comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
        company = comp_res.scalars().first()
        if not company:
            results.append(CompareItemResponse(ticker=ticker, found=False))
            continue

        analysis_res = await db.execute(
            select(AnalysisResult)
            .where(AnalysisResult.company_id == company.id, AnalysisResult.status == "complete")
            .order_by(AnalysisResult.run_at.desc())
            .limit(1)
        )
        analysis = analysis_res.scalars().first()
        if not analysis:
            results.append(CompareItemResponse(ticker=ticker, company_name=company.name, found=True, analysis=None))
            continue

        flag_count_res = await db.execute(select(func.count(RedFlag.id)).where(RedFlag.analysis_id == analysis.id))
        flag_count = flag_count_res.scalar() or 0

        results.append(CompareItemResponse(
            ticker=ticker,
            company_name=company.name,
            found=True,
            red_flag_count=flag_count,
            analysis=AnalysisResultResponse.model_validate(analysis),
        ))

    return results


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    analysis = await db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Analysis not found"}})

    elapsed = int((datetime.now(timezone.utc).replace(tzinfo=None) - analysis.run_at).total_seconds())

    stage = "Initializing..."
    if analysis.status.startswith("running:"):
        stage = analysis.status.split("running:", 1)[1]
    elif analysis.status == "complete":
        stage = "Complete"
    elif analysis.status == "error":
        stage = "Analysis interrupted"

    status_str = analysis.status.split(":")[0] if ":" in analysis.status else analysis.status

    return {
        "status": status_str,
        "integrity_score": analysis.integrity_score,
        "stage": stage,
        "elapsed_seconds": elapsed
    }


@router.get("/company/{ticker}")
async def get_latest_analysis(ticker: str, db: AsyncSession = Depends(get_db)):
    ticker = ticker.upper()
    comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Company not found"}})

    analysis_res = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.company_id == company.id, AnalysisResult.status == "complete")
        .order_by(AnalysisResult.run_at.desc())
        .limit(1)
    )
    analysis = analysis_res.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "No complete analysis found for this company"}})

    flags_res = await db.execute(select(RedFlag).where(RedFlag.analysis_id == analysis.id))
    flags = flags_res.scalars().all()

    result_dict = AnalysisResultResponse.model_validate(analysis).model_dump()
    result_dict["red_flags"] = [RedFlagResponse.model_validate(f).model_dump() for f in flags]

    return result_dict


@router.get("/company/{ticker}/history", response_model=list[AnalysisHistoryItem])
async def get_analysis_history(ticker: str, db: AsyncSession = Depends(get_db)):
    ticker = ticker.upper()
    comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Company not found"}})

    history_res = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.company_id == company.id, AnalysisResult.status == "complete")
        .order_by(AnalysisResult.run_at.desc())
        .limit(ANALYSIS_HISTORY_LIMIT)
    )
    # Query is newest-first (so LIMIT keeps the most recent runs); reverse to
    # chronological order for the trend chart's x-axis.
    return list(reversed(history_res.scalars().all()))
