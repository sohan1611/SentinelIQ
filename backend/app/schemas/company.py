from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    ticker: str
    sector: Optional[str] = None
    exchange: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: UUID
    last_analyzed: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
