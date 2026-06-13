from typing import List
from .base import BaseForensicModule, ForensicResult, RedFlagData
from app.models.financial_data import FinancialData

class DebtStressModule(BaseForensicModule):
    def analyze(self, data: List[FinancialData]) -> ForensicResult:
        flags = []
        details = {"debt_metrics": []}
        
        sorted_data = sorted(data, key=lambda x: x.period)
        
        valid_periods = 0
        score = 100.0
        
        for i in range(1, len(sorted_data)):
            prev = sorted_data[i-1]
            curr = sorted_data[i]
            
            if curr.total_debt is None or prev.total_debt is None or curr.revenue is None or prev.revenue is None or curr.operating_cf is None:
                continue
                
            if curr.revenue == 0:
                continue
                
            valid_periods += 1
            
            debt_to_revenue = curr.total_debt / curr.revenue
            debt_growth = (curr.total_debt - prev.total_debt) / abs(prev.total_debt) if prev.total_debt != 0 else 0
            
            interest_expense_proxy = curr.total_debt * 0.05
            interest_coverage = curr.operating_cf / interest_expense_proxy if interest_expense_proxy != 0 else float('inf')
            
            details["debt_metrics"].append({
                "period": curr.period,
                "debt_to_revenue": debt_to_revenue,
                "debt_growth": debt_growth,
                "interest_coverage": interest_coverage
            })
            
            period_score_deduction = 0
            if debt_to_revenue > 1.0:
                period_score_deduction += 20
            if debt_to_revenue > 2.0:
                period_score_deduction += 20
                
            if debt_growth > 0.30:
                period_score_deduction += 15
                
            if interest_coverage < 2.0:
                period_score_deduction += 20
                
            score -= period_score_deduction
            
            rev_growth = (curr.revenue - prev.revenue) / abs(prev.revenue) if prev.revenue != 0 else 0
            if debt_growth > 0.40 and rev_growth <= 0:
                flags.append(RedFlagData(
                    flag_type="cash_flow", # Debt is grouped under cash flow/financials
                    severity="high",
                    description="Debt growing significantly faster than revenue",
                    period=curr.period
                ))
                
        if valid_periods == 0:
            return ForensicResult(score=50.0, flags=[], details={})
            
        score = max(0.0, min(100.0, score))
        return ForensicResult(score=score, flags=flags, details=details)
