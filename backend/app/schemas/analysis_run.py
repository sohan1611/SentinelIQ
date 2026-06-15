from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AnalysisRunRecord(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    analysis_result_id: UUID
    run_at: datetime
    counted: bool

    class Config:
        from_attributes = True
