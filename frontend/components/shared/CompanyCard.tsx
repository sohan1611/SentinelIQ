import * as React from "react";
import { Badge } from "../ui/Badge";
import type { RiskLevel } from "../ui/Badge";
import Link from "next/link";

interface CompanyCardProps {
  name: string;
  ticker: string;
  score: number;
  risk: RiskLevel;
  lastAnalyzed: string;
  href?: string;
}

export function CompanyCard({ name, ticker, score, risk, lastAnalyzed, href = "#" }: CompanyCardProps) {
  const scoreColors = {
    severe: "text-risk-severe",
    high: "text-risk-high",
    moderate: "text-risk-moderate",
    low: "text-risk-low",
    strong: "text-risk-strong",
    analyzing: "text-text-secondary",
    flagged: "text-risk-high",
  };

  return (
    <div className="w-full bg-surface border border-border rounded-[8px] p-4 flex flex-col mb-2 last:mb-0 group hover:bg-[#F1EFE9] transition-colors active:bg-[#F1EFE9]">
      {/* Row 1: Name + Risk Badge */}
      <div className="flex justify-between items-start mb-1">
        <div className="font-sans text-[14px] font-semibold text-text-primary line-clamp-1 pr-2">
          {name}
        </div>
        <div className="shrink-0">
          <Badge risk={risk}>{risk.replace("-", " ")}</Badge>
        </div>
      </div>
      
      {/* Row 2: Ticker + Score */}
      <div className="flex justify-between items-center mb-3">
        <div className="font-mono text-[12px] text-navy">
          {ticker}
        </div>
        <div className={`font-mono text-[16px] font-bold ${scoreColors[risk]}`}>
          {score}
        </div>
      </div>
      
      {/* Row 3: Date & Action */}
      <div className="flex justify-between items-center">
        <div className="font-sans text-[12px] text-text-secondary">
          Last analyzed: {lastAnalyzed}
        </div>
        <Link href={href} className="font-sans text-[12px] text-navy font-medium transition-colors group-hover:underline active:underline">
          View Report →
        </Link>
      </div>
    </div>
  );
}
