from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.watchlist_alert import WatchlistAlert
from app.schemas.watchlist_alert import AlertListResponse

router = APIRouter()

ALERTS_LIMIT = 50


@router.get("/", response_model=AlertListResponse)
async def get_alerts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Phase 47 (E-4): the current user's risk-band-change alerts, newest
    first. unread_count is a separate, unscoped-by-limit query -- a nav
    badge must reflect ALL unread alerts, not just the page returned here."""
    res = await db.execute(
        select(WatchlistAlert, Company)
        .join(Company, WatchlistAlert.company_id == Company.id)
        .where(WatchlistAlert.user_id == current_user.id)
        .order_by(WatchlistAlert.created_at.desc())
        .limit(ALERTS_LIMIT)
    )
    rows = res.all()

    alerts = [
        {
            "id": alert.id,
            "company": company,
            "previous_score": alert.previous_score,
            "new_score": alert.new_score,
            "previous_risk": alert.previous_risk,
            "new_risk": alert.new_risk,
            "is_read": alert.is_read,
            "created_at": alert.created_at,
        }
        for alert, company in rows
    ]

    count_res = await db.execute(
        select(func.count(WatchlistAlert.id)).where(
            WatchlistAlert.user_id == current_user.id,
            WatchlistAlert.is_read.is_(False),
        )
    )
    unread_count = count_res.scalar() or 0

    return {"alerts": alerts, "unread_count": unread_count}


@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = await db.get(WatchlistAlert, alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Alert not found"}})

    alert.is_read = True
    await db.commit()

    return {"message": "Alert marked as read"}
