from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    detail: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
