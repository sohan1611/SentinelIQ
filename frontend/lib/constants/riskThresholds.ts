import type { RiskLevel } from "@/components/ui/Badge"

export interface RiskTier {
  max: number;
  level: RiskLevel;
  label: string;
}

// Risk classification per integrity score, 0-100.
export const RISK_THRESHOLDS: RiskTier[] = [
  { max: 20, level: "severe", label: "Severe Risk" },
  { max: 40, level: "high", label: "High Risk" },
  { max: 60, level: "moderate", label: "Moderate Risk" },
  { max: 80, level: "low", label: "Low Risk" },
  { max: 100, level: "strong", label: "Strong Integrity" },
]

// Solid risk colors — exact hex per design system, never gradients.
export const RISK_COLORS: Record<RiskLevel, string> = {
  severe: "#6E1010",
  high: "#B03028",
  moderate: "#C47A14",
  low: "#1C3558",
  strong: "#1A6B3C",
  analyzing: "#7A786F",
  flagged: "#B03028",
}

// Badge/tint background colors.
export const RISK_TINTS: Record<RiskLevel, string> = {
  severe: "#F5DADA",
  high: "#FAE8E8",
  moderate: "#FDF2DC",
  low: "#E4F2EB",
  strong: "#D6EDE0",
  analyzing: "#F0EDE8",
  flagged: "#FAE8E8",
}
