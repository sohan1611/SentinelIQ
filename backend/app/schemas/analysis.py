from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

class RedFlagResponse(BaseModel):
    id: UUID
    flag_type: str
    severity: str
    description: str
    period: Optional[str] = None
    event_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    id: UUID
    company_id: UUID
    run_at: datetime
    integrity_score: Optional[float] = None
    financial_score: Optional[float] = None
    cashflow_score: Optional[float] = None
    governance_score: Optional[float] = None
    earnings_score: Optional[float] = None
    narrative_score: Optional[float] = None
    news_score: Optional[float] = None
    module_details: Optional[Dict[str, Any]] = None
    status: str

    class Config:
        from_attributes = True

class AnalysisStatusResponse(BaseModel):
    status: str
    integrity_score: Optional[float] = None
    stage: str
    elapsed_seconds: int

class AnalysisRunRequest(BaseModel):
    ticker: str

class AnalysisRunResponse(BaseModel):
    analysis_id: UUID
    status: str
