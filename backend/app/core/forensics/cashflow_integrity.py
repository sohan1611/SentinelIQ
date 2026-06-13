from typing import List
from .base import BaseForensicModule, ForensicResult, RedFlagData
from app.models.financial_data import FinancialData

class CashFlowIntegrityModule(BaseForensicModule):
    def analyze(self, data: List[FinancialData]) -> ForensicResult:
        flags = []
        details = {"accrual_ratios": []}
        
        valid_periods = 0
        total_score_contribution = 0.0
        
        consecutive_high_accrual = 0
        
        sorted_data = sorted(data, key=lambda x: x.period)

        for curr in sorted_data:
            if curr.net_income is None or curr.operating_cf is None or curr.total_assets is None:
                consecutive_high_accrual = 0
                continue
                
            if curr.total_assets == 0:
                continue

            accrual_ratio = (curr.net_income - curr.operating_cf) / curr.total_assets
            details["accrual_ratios"].append({"period": curr.period, "accrual_ratio": accrual_ratio})
            
            period_score = 100.0
            if accrual_ratio >= 0.15:
                period_score = 20.0
            elif accrual_ratio >= 0.10:
                period_score = 45.0
            elif accrual_ratio >= 0.05:
                period_score = 70.0
                
            total_score_contribution += period_score
            valid_periods += 1
            
            if curr.net_income > 0 and curr.operating_cf < 0:
                flags.append(RedFlagData(
                    flag_type="cash_flow",
                    severity="severe",
                    description="Reported profit but negative operating cash flow",
                    period=curr.period
                ))
                
            if accrual_ratio > 0.10:
                consecutive_high_accrual += 1
                if consecutive_high_accrual >= 2:
                    flags.append(RedFlagData(
                        flag_type="cash_flow",
                        severity="high",
                        description="Elevated accruals ratio — potential earnings management",
                        period=curr.period
                    ))
            else:
                consecutive_high_accrual = 0

        if valid_periods == 0:
            return ForensicResult(score=50.0, flags=[], details={})
            
        final_score = total_score_contribution / valid_periods
        final_score = max(0.0, min(100.0, final_score))
        return ForensicResult(score=final_score, flags=flags, details=details)
