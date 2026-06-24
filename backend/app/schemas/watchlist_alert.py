from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .company import CompanyResponse

class WatchlistAlertResponse(BaseModel):
    id: UUID
    company: CompanyResponse
    previous_score: float
    new_score: float
    previous_risk: str
    new_risk: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    alerts: list[WatchlistAlertResponse]
    unread_count: int
