from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from .company import CompanyResponse

class WatchlistRequest(BaseModel):
    ticker: str

class WatchlistItemResponse(BaseModel):
    id: UUID
    company: CompanyResponse
    added_at: datetime
    latest_score: Optional[float] = None

    class Config:
        from_attributes = True
