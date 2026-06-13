import type { RiskLevel } from "@/components/ui/Badge"
import { RISK_THRESHOLDS } from "@/lib/constants/riskThresholds"

export function getRiskLevel(score: number): RiskLevel {
  const tier = RISK_THRESHOLDS.find((t) => score <= t.max)
  return tier ? tier.level : "strong"
}

export function getRiskLabel(score: number): string {
  const tier = RISK_THRESHOLDS.find((t) => score <= t.max)
  return tier ? tier.label : "Strong Integrity"
}
