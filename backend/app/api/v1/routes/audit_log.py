from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()

AUDIT_LOG_LIMIT = 100


@router.get("/", response_model=list[AuditLogResponse])
async def get_audit_log(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Phase 38 (F6, scoped to audit logging): the current user's own
    security-relevant action history, newest first. Strictly scoped to
    current_user.id -- there is no cross-user view, since there's no role
    system to safely gate one (see MASTER_IMPLEMENTATION_PLAN.md Phase 38)."""
    res = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(AUDIT_LOG_LIMIT)
    )
    return res.scalars().all()
