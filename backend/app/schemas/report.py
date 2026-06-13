from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ReportResponse(BaseModel):
    id: UUID
    company_id: UUID
    analysis_id: UUID
    content: str
    generated_at: datetime

    class Config:
        from_attributes = True
