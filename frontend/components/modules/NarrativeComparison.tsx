import * as React from "react";
import { Badge } from "../ui/Badge";

interface Statement {
  period: string; // e.g. "Q1 2023"
  quote: string;
  sentiment: "OPTIMISTIC" | "CAUTIONARY" | "NEUTRAL";
}

interface NarrativeComparisonProps {
  left: Statement;
  right: Statement;
  contradictionAlert?: string;
  alertSeverity?: "moderate" | "severe";
}

export function NarrativeComparison({ left, right, contradictionAlert, alertSeverity }: NarrativeComparisonProps) {
  const sentimentMap = {
    OPTIMISTIC: "strong", // green
    CAUTIONARY: "moderate", // amber
    NEUTRAL: "low",
  } as const;

  return (
    <div className="w-full">
      <div className="text-[11px] font-sans font-medium uppercase text-text-secondary mb-4 tracking-[0.04em]">
        Management Statement Comparison
      </div>
      
      <div className="flex flex-col md:flex-row border-t border-b border-border divide-y md:divide-y-0 md:divide-x divide-border">
        {/* Left Column */}
        <div className="flex-1 p-4 flex flex-col items-start bg-surface">
          <div className="font-mono text-[11px] text-text-secondary mb-3">{left.period}</div>
          <p className="font-sans text-[14px] text-text-primary italic mb-4 leading-relaxed flex-1">
            "{left.quote}"
          </p>
          <Badge risk={sentimentMap[left.sentiment]}>{left.sentiment}</Badge>
        </div>

        {/* Right Column */}
        <div className="flex-1 p-4 flex flex-col items-start bg-surface">
          <div className="font-mono text-[11px] text-text-secondary mb-3">{right.period}</div>
          <p className="font-sans text-[14px] text-text-primary italic mb-4 leading-relaxed flex-1">
            "{right.quote}"
          </p>
          <Badge risk={sentimentMap[right.sentiment]}>{right.sentiment}</Badge>
        </div>
      </div>

      {contradictionAlert && (
        <div className={`mt-4 pl-4 py-1 border-l-[1px] ${alertSeverity === "severe" ? "border-risk-high" : "border-risk-moderate"}`}>
          <p className={`font-sans text-[13px] ${alertSeverity === "severe" ? "text-risk-high" : "text-risk-moderate"}`}>
            {contradictionAlert}
          </p>
        </div>
      )}
    </div>
  );
}
