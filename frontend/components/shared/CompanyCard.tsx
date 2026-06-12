import * as React from "react";
import { Badge } from "../ui/Badge";
import type { RiskLevel } from "../ui/Badge";

interface CompanyCardProps {
  name: string;
  ticker: string;
  score: number;
  risk: RiskLevel;
  lastAnalyzed: string;
}

export function CompanyCard({ name, ticker, score, risk, lastAnalyzed }: CompanyCardProps) {
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
    <div className="flex items-center justify-between w-full py-[16px] border-b border-border hover:bg-[#F1EFE9] transition-colors bg-surface px-4 -mx-4 group">
      {/* Left section: Name & Ticker */}
      <div className="flex flex-col w-[200px] shrink-0">
        <div className="font-sans text-[14px] font-semibold text-text-primary mb-1">
          {name}
        </div>
        <div className="font-mono text-[12px] text-navy">
          {ticker}
        </div>
      </div>

      {/* Middle section: Score & Badge */}
      <div className="flex items-center w-[180px] shrink-0 gap-3">
        <div className={`font-mono text-[16px] font-bold ${scoreColors[risk]}`}>
          {score}
        </div>
        <Badge risk={risk}>{risk.replace("-", " ")}</Badge>
      </div>

      {/* Right section: Date & Action */}
      <div className="flex items-center justify-between flex-1 pl-8">
        <div className="font-sans text-[12px] text-text-secondary">
          {lastAnalyzed}
        </div>
        <button className="font-sans text-[12px] text-navy bg-transparent border-none p-0 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100">
          View Report
        </button>
      </div>
    </div>
  );
}
