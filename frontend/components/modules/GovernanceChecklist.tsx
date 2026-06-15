import * as React from "react";
import { Badge } from "../ui/Badge";
import { Skeleton } from "../ui/Skeleton";
import type { RedFlag } from "@/types/analysis";
import { normalizeSeverity, flagDate } from "@/lib/utils/redFlag";

interface GovernanceChecklistProps {
  flags: RedFlag[];
  loading?: boolean;
}

export function GovernanceChecklist({ flags, loading }: GovernanceChecklistProps) {
  if (loading) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`flex justify-between items-center gap-4 px-5 py-4 ${i !== 2 ? "border-b border-[#E3DFD8]" : ""}`}>
            <Skeleton className="flex-1 h-3" />
            <Skeleton className="w-[90px] h-5 rounded-[4px]" />
          </div>
        ))}
      </div>
    );
  }

  if (flags.length === 0) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-risk-strong shrink-0" />
        <span className="font-sans text-[13px] text-[#1A1A18]">
          No governance red flags were detected in this analysis.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
      {flags.map((flag, idx) => (
        <div
          key={flag.id}
          className={`flex justify-between items-start gap-4 px-5 py-4 ${idx !== flags.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}
        >
          <div className="flex flex-col gap-1">
            <div className="font-sans text-[13px] text-[#1A1A18] leading-[1.5]">{flag.description}</div>
            <div className="font-mono text-[11px] text-[#B0ADA7]">{flagDate(flag)}</div>
          </div>
          <div className="shrink-0">
            <Badge risk={normalizeSeverity(flag.severity)}>{flag.severity.toUpperCase()}</Badge>
          </div>
        </div>
      ))}
    </div>
  );
}
