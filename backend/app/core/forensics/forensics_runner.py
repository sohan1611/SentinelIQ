from typing import List, Dict, Any
from app.models.financial_data import FinancialData
from .revenue_quality import RevenueQualityModule
from .cashflow_integrity import CashFlowIntegrityModule
from .earnings_quality import EarningsQualityModule
from .debt_analysis import DebtStressModule
from .base import ForensicResult

class ForensicsRunner:
    def run_forensics(self, financial_data: List[FinancialData]) -> Dict[str, Any]:
        revenue_result = RevenueQualityModule().analyze(financial_data)
        cashflow_result = CashFlowIntegrityModule().analyze(financial_data)
        earnings_result = EarningsQualityModule().analyze(financial_data)
        debt_result = DebtStressModule().analyze(financial_data)

        all_flags = []
        all_flags.extend(revenue_result.flags)
        all_flags.extend(cashflow_result.flags)
        all_flags.extend(earnings_result.flags)
        all_flags.extend(debt_result.flags)

        return {
            "revenue": revenue_result,
            "cashflow": cashflow_result,
            "earnings": earnings_result,
            "debt": debt_result,
            "all_flags": all_flags
        }
