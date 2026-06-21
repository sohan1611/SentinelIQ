from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def log_action(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    detail: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Stages an AuditLog row -- caller commits, same convention as RedFlag/
    FinancialData rows elsewhere in this codebase (added alongside the rest
    of the request's writes, not as a separate transaction)."""
    db.add(AuditLog(user_id=user_id, action=action, detail=detail, ip_address=ip_address))
