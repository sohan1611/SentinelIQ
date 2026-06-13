from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db
from app.models.company import Company
from app.models.report import Report
from app.schemas.report import ReportResponse

router = APIRouter()

@router.get("/company/{ticker}", response_model=ReportResponse)
async def get_report(ticker: str, db: AsyncSession = Depends(get_db)):
    ticker = ticker.upper()
    comp_res = await db.execute(select(Company).where(Company.ticker == ticker))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    rep_res = await db.execute(
        select(Report)
        .where(Report.company_id == company.id)
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    report = rep_res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this company")
        
    return report
