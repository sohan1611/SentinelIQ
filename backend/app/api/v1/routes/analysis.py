from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.analysis_result import AnalysisResult
from app.models.red_flag import RedFlag
from app.schemas.analysis import AnalysisRunRequest, AnalysisRunResponse, AnalysisStatusResponse, AnalysisResultResponse, RedFlagResponse
from app.tasks.analysis_worker import run_full_analysis

router = APIRouter()

@router.post("/run", response_model=AnalysisRunResponse)
async def run_analysis(
    request: AnalysisRunRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = request.ticker.upper()
    
    # Check free tier limit (5/month)
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # We join with watchlist to see user's companies? Or just count analyses run by this user.
    # The prompt says: company_id IN (user's companies) AND run_at >= first day of current month
    # Actually, simpler to just count analyses in the DB for this user's watchlist? 
    # Or just track analyses per user. The schema doesn't have user_id on AnalysisResult.
    # Wait, the prompt says: "WHERE company_id IN (user's companies)".
    from app.models.watchlist import WatchlistItem
    
    count_query = select(func.count(AnalysisResult.id)).join(
        WatchlistItem, WatchlistItem.company_id == AnalysisResult.company_id
    ).where(
        WatchlistItem.user_id == current_user.id,
        AnalysisResult.run_at >= first_day_of_month
    )
    
    count_res = await db.execute(count_query)
    count = count_res.scalar() or 0
    
    if count >= 5 and current_user.tier == "free":
        raise HTTPException(
            status_code=403, 
            detail={"error": {"code": "LIMIT_REACHED", "message": "Monthly analysis limit reached. Upgrade to Pro."}}
        )
        
    # Get company
    res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Company not found"}})
        
    analysis = AnalysisResult(
        company_id=company.id,
        status="pending"
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    # Trigger background task
    background_tasks.add_task(run_full_analysis, company.id, analysis.id)
    
    return {"analysis_id": analysis.id, "status": "pending"}

@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    analysis = await db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    elapsed = int((datetime.utcnow() - analysis.run_at).total_seconds())
    
    stage = "Initializing..."
    if analysis.status.startswith("running:"):
        stage = analysis.status.split("running:", 1)[1]
    elif analysis.status == "complete":
        stage = "Complete"
    elif analysis.status == "failed":
        stage = "Failed"
        
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
        raise HTTPException(status_code=404, detail="Company not found")
        
    analysis_res = await db.execute(
        select(AnalysisResult)
        .where(AnalysisResult.company_id == company.id, AnalysisResult.status == "complete")
        .order_by(AnalysisResult.run_at.desc())
        .limit(1)
    )
    analysis = analysis_res.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No complete analysis found for this company")
        
    flags_res = await db.execute(select(RedFlag).where(RedFlag.analysis_id == analysis.id))
    flags = flags_res.scalars().all()
    
    result_dict = AnalysisResultResponse.model_validate(analysis).model_dump()
    result_dict["red_flags"] = [RedFlagResponse.model_validate(f).model_dump() for f in flags]
    
    return result_dict
