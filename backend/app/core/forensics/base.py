from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.financial_data import FinancialData

class RedFlagData(BaseModel):
    flag_type: str
    severity: str
    description: str
    period: str | None = None

class ForensicResult(BaseModel):
    score: float
    flags: List[RedFlagData]
    details: Dict[str, Any]

class BaseForensicModule:
    def analyze(self, data: List[FinancialData]) -> ForensicResult:
        raise NotImplementedError
