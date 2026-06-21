from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db, get_current_user
from app.api.middleware.rate_limit import client_ip
from app.models.user import User
from app.models.company import Company
from app.models.watchlist import WatchlistItem
from app.models.analysis_result import AnalysisResult
from app.schemas.watchlist import WatchlistRequest, WatchlistItemResponse
from app.services.audit_log import log_action

router = APIRouter()

@router.get("/", response_model=List[WatchlistItemResponse])
async def get_watchlist(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(
        select(WatchlistItem, Company)
        .join(Company, WatchlistItem.company_id == Company.id)
        .where(WatchlistItem.user_id == current_user.id)
    )
    items = res.all()
    
    response = []
    for wl_item, company in items:
        # Get latest score
        ans_res = await db.execute(
            select(AnalysisResult.integrity_score)
            .where(AnalysisResult.company_id == company.id, AnalysisResult.status == "complete")
            .order_by(AnalysisResult.run_at.desc())
            .limit(1)
        )
        score = ans_res.scalar()
        
        response.append({
            "id": wl_item.id,
            "company": company,
            "added_at": wl_item.added_at,
            "latest_score": score
        })
        
    return response

@router.post("/")
async def add_to_watchlist(request: WatchlistRequest, http_request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticker = request.ticker.upper()
    comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = comp_res.scalars().first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found. Search for it first to initialize.")

    check_res = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.company_id == company.id)
    )
    if check_res.scalars().first():
        raise HTTPException(status_code=409, detail="Company already in watchlist")

    item = WatchlistItem(user_id=current_user.id, company_id=company.id)
    db.add(item)
    log_action(db, current_user.id, "watchlist_add", detail={"ticker": ticker}, ip_address=client_ip(http_request))
    await db.commit()

    return {"message": "Added to watchlist"}

@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str, http_request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticker = ticker.upper()
    comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    check_res = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.company_id == company.id)
    )
    item = check_res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Company not in watchlist")

    await db.delete(item)
    log_action(db, current_user.id, "watchlist_remove", detail={"ticker": ticker}, ip_address=client_ip(http_request))
    await db.commit()

    return {"message": "Removed from watchlist"}
