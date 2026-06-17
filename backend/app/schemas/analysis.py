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

class NarrativeSnapshotResponse(BaseModel):
    id: UUID
    company_id: UUID
    period: Optional[str] = None
    statement_text: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    source: Optional[str] = None
    fetched_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NarrativeModuleDetails(BaseModel):
    snapshots: List[Dict[str, Any]] = []
    statements_used: int = 0
    provenance: List[Dict[str, Any]] = []
    tone_shifts: List[Dict[str, Any]] = []

class GovernanceModuleDetails(BaseModel):
    provenance: Dict[str, Any] = {}
    low_confidence: bool = False

class ModuleDetails(BaseModel):
    scores: Dict[str, float] = {}
    confidence: Optional[str] = None
    revenue: Dict[str, Any] = {}
    cashflow: Dict[str, Any] = {}
    earnings: Dict[str, Any] = {}
    debt: Dict[str, Any] = {}
    narrative: NarrativeModuleDetails = NarrativeModuleDetails()
    governance: GovernanceModuleDetails = GovernanceModuleDetails()

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
    module_details: Optional[ModuleDetails] = None
    status: str

    class Config:
        from_attributes = True

class AnalysisHistoryItem(BaseModel):
    id: UUID
    run_at: datetime
    integrity_score: Optional[float] = None
    financial_score: Optional[float] = None
    cashflow_score: Optional[float] = None
    governance_score: Optional[float] = None
    earnings_score: Optional[float] = None
    narrative_score: Optional[float] = None
    news_score: Optional[float] = None

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
