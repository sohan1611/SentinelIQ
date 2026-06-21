from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

# Incremented whenever ModuleDetails adds a new required field or changes
# the shape of an existing sub-model. Readers treat schema_version == 0 as
# "legacy" (pre-Phase-15 row — all optional fields will have their defaults).
CURRENT_SCHEMA_VERSION = 1


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


# ---------------------------------------------------------------------------
# Typed forensic sub-models (Phase 15 — each mirrors frontend/types/analysis.ts)
# ---------------------------------------------------------------------------

class DivergencePoint(BaseModel):
    period: str
    divergence: float


class ReceivablesRatioPoint(BaseModel):
    period: str
    recv_ratio: float


class RevenueModuleDetails(BaseModel):
    divergences: List[DivergencePoint] = []
    recv_ratios: List[ReceivablesRatioPoint] = []


class AccrualRatioPoint(BaseModel):
    period: str
    accrual_ratio: float


class CashflowModuleDetails(BaseModel):
    accrual_ratios: List[AccrualRatioPoint] = []


class MarginPoint(BaseModel):
    period: str
    gross_margin: float


class NetIncomePoint(BaseModel):
    period: str
    net_income: float


class EarningsModuleDetails(BaseModel):
    margins: List[MarginPoint] = []
    net_incomes: List[NetIncomePoint] = []


class DebtMetricPoint(BaseModel):
    period: str
    debt_to_revenue: float
    debt_growth: float
    interest_coverage: Optional[float] = None


class DebtModuleDetails(BaseModel):
    debt_metrics: List[DebtMetricPoint] = []


# ---------------------------------------------------------------------------
# AI / narrative / governance sub-models (unchanged from Phase 14)
# ---------------------------------------------------------------------------

class NarrativeModuleDetails(BaseModel):
    snapshots: List[Dict[str, Any]] = []
    statements_used: int = 0
    provenance: List[Dict[str, Any]] = []
    tone_shifts: List[Dict[str, Any]] = []


class GovernanceModuleDetails(BaseModel):
    provenance: Dict[str, Any] = {}
    low_confidence: bool = False
    flags: List[Dict[str, Any]] = []


class RestatementCheckDetails(BaseModel):
    """Phase 36: distinguishes 'checked, no restatements found' from 'no
    EDGAR coverage for this company' -- absence of flags must never be
    silently read as a clean check when coverage itself is the unknown."""
    coverage: bool = False
    facts_checked: int = 0


# ---------------------------------------------------------------------------
# Versioned top-level container (schema_version = 0 means pre-Phase-15 row)
# ---------------------------------------------------------------------------

class ModuleDetails(BaseModel):
    schema_version: int = 0
    scores: Dict[str, float] = {}
    confidence: Optional[str] = None
    revenue: RevenueModuleDetails = RevenueModuleDetails()
    cashflow: CashflowModuleDetails = CashflowModuleDetails()
    earnings: EarningsModuleDetails = EarningsModuleDetails()
    debt: DebtModuleDetails = DebtModuleDetails()
    narrative: NarrativeModuleDetails = NarrativeModuleDetails()
    governance: GovernanceModuleDetails = GovernanceModuleDetails()
    financial_data_status: Optional[str] = None
    restatement_check: RestatementCheckDetails = RestatementCheckDetails()


# ---------------------------------------------------------------------------
# API response schemas
# ---------------------------------------------------------------------------

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


class CompareItemResponse(BaseModel):
    """Phase 37 (F5, scoped to a comparison view): one column of GET
    /analysis/compare. `found=False` means the ticker isn't a known company
    at all; `found=True, analysis=None` means it's a known company with no
    completed analysis yet -- two distinct honest states, never collapsed
    into a single silent gap."""
    ticker: str
    company_name: Optional[str] = None
    found: bool
    analysis: Optional[AnalysisResultResponse] = None
    red_flag_count: int = 0


class AnalysisRunRequest(BaseModel):
    ticker: str


class AnalysisRunResponse(BaseModel):
    analysis_id: UUID
    status: str
