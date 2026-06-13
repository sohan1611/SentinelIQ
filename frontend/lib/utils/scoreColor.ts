import { RISK_COLORS, RISK_TINTS } from "@/lib/constants/riskThresholds"
import { getRiskLevel } from "./riskLabel"

export function getScoreColor(score: number): string {
  return RISK_COLORS[getRiskLevel(score)]
}

export function getScoreTint(score: number): string {
  return RISK_TINTS[getRiskLevel(score)]
}
