import * as React from "react"

export type RiskLevel = "severe" | "high" | "moderate" | "low" | "strong" | "analyzing" | "flagged";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  risk: RiskLevel;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className = "", risk, children, ...props }, ref) => {
    const riskStyles = {
      severe: "bg-tint-severe text-risk-severe",
      high: "bg-tint-high text-risk-high",
      moderate: "bg-tint-moderate text-risk-moderate",
      low: "bg-tint-low text-risk-low",
      strong: "bg-tint-strong text-risk-strong",
      analyzing: "bg-[#F0EDE8] text-text-secondary",
      flagged: "bg-tint-high text-risk-high",
    };

    return (
      <div
        ref={ref}
        className={`inline-flex items-center rounded-[4px] px-[10px] py-[4px] text-[11px] font-semibold uppercase tracking-[0.04em] font-sans ${riskStyles[risk]} ${className}`}
        {...props}
      >
        {children}
      </div>
    )
  }
)
Badge.displayName = "Badge"

export { Badge }
