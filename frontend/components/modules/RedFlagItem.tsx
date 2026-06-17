import * as React from "react";
import { Badge, RiskLevel } from "../ui/Badge";
import { Skeleton } from "../ui/Skeleton";

export type Severity = "severe" | "high" | "moderate";

export interface EvidenceRow {
  label: string;
  value: string;
}

interface RedFlagItemProps {
  severity: Severity;
  date: string;
  description: string;
  type: string;
  loading?: boolean;
  evidence?: EvidenceRow[];
}

export function RedFlagItem({ severity, date, description, type, loading, evidence = [] }: RedFlagItemProps) {
  const [expanded, setExpanded] = React.useState(false);

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

  const hasEvidence = evidence.length > 0;

  return (
    <div className="border-b border-border">
      <div
        className="group flex items-center w-full py-3 hover:bg-[#F1EFE9] transition-colors bg-transparent px-2 -mx-2"
        style={{ cursor: hasEvidence ? "pointer" : "default" }}
        onClick={hasEvidence ? () => setExpanded((v) => !v) : undefined}
      >
        <div className={`w-2 h-2 rounded-full shrink-0 mr-4 ${dotColors[severity]}`} />
        <div className="font-mono text-[12px] text-text-secondary w-[80px] shrink-0">
          {date}
        </div>
        <div className="font-sans text-[14px] text-text-primary flex-1 truncate pr-4">
          {description}
        </div>
        <div className="shrink-0 flex items-center gap-3">
          {hasEvidence && (
            <span className="font-sans text-[11px] text-[#1C3558] hover:underline">
              {expanded ? "Hide" : "Evidence"}
            </span>
          )}
          <Badge risk="flagged">{type}</Badge>
        </div>
      </div>
      {expanded && hasEvidence && (
        <div className="flex flex-col gap-1 pb-3 pl-6 pr-2">
          {evidence.map((row) => (
            <div key={row.label} className="flex justify-between max-w-[320px]">
              <span className="font-sans text-[12px] text-text-secondary">{row.label}</span>
              <span className="font-mono text-[12px] text-text-primary">{row.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
