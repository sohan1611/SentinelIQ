from typing import List
from .base import BaseForensicModule, ForensicResult, RedFlagData
from app.models.financial_data import FinancialData
import math

class EarningsQualityModule(BaseForensicModule):
    def analyze(self, data: List[FinancialData]) -> ForensicResult:
        flags = []
        details = {"margins": [], "net_incomes": []}
        
        sorted_data = sorted(data, key=lambda x: x.period)
        
        valid_periods = 0
        score = 100.0
        
        net_income_growth_rates = []
        
        for i in range(1, len(sorted_data)):
            prev = sorted_data[i-1]
            curr = sorted_data[i]
            
            if curr.gross_margin is None or prev.gross_margin is None or curr.net_income is None or prev.net_income is None or curr.revenue is None or prev.revenue is None:
                continue
                
            details["margins"].append({"period": curr.period, "gross_margin": curr.gross_margin})
            details["net_incomes"].append({"period": curr.period, "net_income": curr.net_income})
            valid_periods += 1
            
            margin_delta = curr.gross_margin - prev.gross_margin
            
            if abs(margin_delta) > 0.08:
                score -= 20
                
            rev_growth = (curr.revenue - prev.revenue) / abs(prev.revenue) if prev.revenue != 0 else 0
            
            if margin_delta > 0.10 and rev_growth <= 0.05:
                flags.append(RedFlagData(
                    flag_type="earnings",
                    severity="moderate",
                    description="Unusual gross margin spike — accounting change possible",
                    period=curr.period
                ))
                
            if prev.net_income != 0:
                ni_growth = (curr.net_income - prev.net_income) / abs(prev.net_income)
                net_income_growth_rates.append(ni_growth)
                
                if ni_growth > 0.50 and rev_growth <= 0.10:
                    flags.append(RedFlagData(
                        flag_type="earnings",
                        severity="high",
                        description="Earnings spike inconsistent with revenue growth",
                        period=curr.period
                    ))
                    
        if len(net_income_growth_rates) > 1:
            mean_ni_growth = sum(net_income_growth_rates) / len(net_income_growth_rates)
            variance = sum((x - mean_ni_growth) ** 2 for x in net_income_growth_rates) / len(net_income_growth_rates)
            std_dev = math.sqrt(variance)
            cv = std_dev / abs(mean_ni_growth) if mean_ni_growth != 0 else 0
            
            if cv > 1.5:
                score -= 25
                
        if valid_periods == 0:
            return ForensicResult(score=50.0, flags=[], details={})
            
        score = max(0.0, min(100.0, score))
        return ForensicResult(score=score, flags=flags, details=details)
