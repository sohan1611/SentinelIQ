import * as React from "react";
import { Badge, RiskLevel } from "../ui/Badge";
import { Skeleton } from "../ui/Skeleton";

export type Severity = "severe" | "high" | "moderate";

interface RedFlagItemProps {
  severity: Severity;
  date: string;
  description: string;
  type: string;
  loading?: boolean;
}

export function RedFlagItem({ severity, date, description, type, loading }: RedFlagItemProps) {
  if (loading) {
    return (
      <div className="flex items-center w-full py-3 border-b border-border">
        <Skeleton className="w-2 h-2 rounded-full mr-4" />
        <Skeleton className="w-[80px] h-4 mr-4" />
        <Skeleton className="flex-1 h-4 mr-4" />
        <Skeleton className="w-[80px] h-5 rounded-[4px]" />
      </div>
    );
  }

  const dotColors = {
    severe: "bg-risk-severe",
    high: "bg-risk-high",
    moderate: "bg-risk-moderate",
  };

  return (
    <div className="group flex items-center w-full py-3 border-b border-border hover:bg-[#F1EFE9] transition-colors bg-transparent px-2 -mx-2">
      <div className={`w-2 h-2 rounded-full shrink-0 mr-4 ${dotColors[severity]}`} />
      <div className="font-mono text-[12px] text-text-secondary w-[80px] shrink-0">
        {date}
      </div>
      <div className="font-sans text-[14px] text-text-primary flex-1 truncate pr-4">
        {description}
      </div>
      <div className="shrink-0">
        <Badge risk="flagged">{type}</Badge>
      </div>
    </div>
  );
}
