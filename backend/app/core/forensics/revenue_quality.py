from typing import List
from .base import BaseForensicModule, ForensicResult, RedFlagData
from app.models.financial_data import FinancialData

class RevenueQualityModule(BaseForensicModule):
    def analyze(self, data: List[FinancialData]) -> ForensicResult:
        flags = []
        details = {"divergences": [], "recv_ratios": []}
        
        # Sort data by period (newest to oldest or oldest to newest)
        # We need consecutive pairs, so oldest to newest is easier
        sorted_data = sorted(data, key=lambda x: x.period)
        
        valid_periods_for_growth = 0
        score = 100.0
        
        consecutive_high_divergence = 0
        consecutive_recv_increase = 0
        prev_recv_ratio = None
        
        for i in range(1, len(sorted_data)):
            prev = sorted_data[i-1]
            curr = sorted_data[i]
            
            if prev.revenue is None or curr.revenue is None or prev.operating_cf is None or curr.operating_cf is None or curr.accounts_recv is None:
                consecutive_high_divergence = 0
                consecutive_recv_increase = 0
                prev_recv_ratio = None
                continue
                
            if prev.revenue == 0 or prev.operating_cf == 0:
                continue
                
            rev_growth = (curr.revenue - prev.revenue) / abs(prev.revenue)
            ocf_growth = (curr.operating_cf - prev.operating_cf) / abs(prev.operating_cf)
            divergence = rev_growth - ocf_growth
            
            recv_ratio = curr.accounts_recv / curr.revenue if curr.revenue != 0 else 0
            
            details["divergences"].append({"period": curr.period, "divergence": divergence})
            details["recv_ratios"].append({"period": curr.period, "recv_ratio": recv_ratio})
            valid_periods_for_growth += 1
            
            if divergence > 0.15:
                score -= 15
            if divergence > 0.30:
                score -= 25
                
            if divergence > 0.20:
                consecutive_high_divergence += 1
                if consecutive_high_divergence >= 2:
                    flags.append(RedFlagData(
                        flag_type="revenue",
                        severity="high",
                        description="Revenue growing significantly faster than cash flow",
                        period=curr.period
                    ))
            else:
                consecutive_high_divergence = 0
                
            if prev_recv_ratio is not None:
                recv_increase = recv_ratio - prev_recv_ratio
                if recv_increase > 0.10:
                    score -= 10
                
                if recv_increase > 0:
                    consecutive_recv_increase += 1
                    if consecutive_recv_increase >= 3:
                        flags.append(RedFlagData(
                            flag_type="revenue",
                            severity="moderate",
                            description="Receivables expanding faster than revenue",
                            period=curr.period
                        ))
                else:
                    consecutive_recv_increase = 0
                    
            prev_recv_ratio = recv_ratio

        if valid_periods_for_growth == 0:
            return ForensicResult(score=50.0, flags=[], details={})

        score = max(0.0, min(100.0, score))
        return ForensicResult(score=score, flags=flags, details=details)
