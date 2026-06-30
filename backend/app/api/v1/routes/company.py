from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db, get_current_user
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyResponse
from app.services.yahoo_finance import fetch_company_info

router = APIRouter()

@router.get("/search", response_model=List[CompanyResponse])
async def search_companies(q: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Search by name or ticker
    query = select(Company).where(
        (Company.ticker.ilike(f"%{q}%")) | (Company.name.ilike(f"%{q}%"))
    ).limit(10)
    result = await db.execute(query)
    companies = result.scalars().all()
    return companies

@router.get("/{ticker}", response_model=CompanyResponse)
async def get_company(ticker: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticker = ticker.upper()
    result = await db.execute(select(Company).where(Company.ticker == ticker))
    company = result.scalars().first()
    
    if company:
        return company
        
    # If not in DB, fetch from yfinance
    try:
        info = await fetch_company_info(ticker)
        company = Company(
            name=info.get("longName", ticker),
            ticker=ticker,
            sector=info.get("sector"),
            exchange=info.get("exchange")
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=404, detail="Company not found")
