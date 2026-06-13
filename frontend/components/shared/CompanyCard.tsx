"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import { Badge } from "../ui/Badge";
import type { RiskLevel } from "../ui/Badge";
import Link from "next/link";

interface CompanyCardProps {
  name: string;
  ticker: string;
  score: number | null;
  risk: RiskLevel;
  lastAnalyzed: string;
  href?: string;
  scoreDelta?: "increased" | "decreased" | null;
}

export function CompanyCard({ name, ticker, score, risk, lastAnalyzed, href = "#", scoreDelta = null }: CompanyCardProps) {
  const [flashColor, setFlashColor] = useState<string>("transparent");
  const [displayScore, setDisplayScore] = useState<number | null>(score);
  const [scoreOpacity, setScoreOpacity] = useState(1);

  useEffect(() => {
    if (scoreDelta) {
      setFlashColor(scoreDelta === "decreased" ? "#FAE8E8" : "#E4F2EB");
      setScoreOpacity(0); // fade out

      const t1 = setTimeout(() => {
        setDisplayScore(score);
        setScoreOpacity(1); // fade in
      }, 150);

      const t2 = setTimeout(() => {
        setFlashColor("transparent");
      }, 400);

      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    } else {
      setDisplayScore(score);
      setScoreOpacity(1);
    }
  }, [scoreDelta, score]);

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
    <div 
      className="w-full border border-border rounded-[8px] p-4 flex flex-col mb-2 last:mb-0 group hover:bg-[#F1EFE9] active:bg-[#EAE7E0] transition-colors var(--duration-instant) var(--ease-out)"
      style={{ backgroundColor: flashColor !== "transparent" ? flashColor : undefined }}
    >
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
        <div 
          className={`font-mono text-[16px] font-bold ${scoreColors[risk]}`}
          style={{
            opacity: scoreOpacity,
            transition: "opacity 150ms var(--ease-out)"
          }}
        >
          {displayScore === null ? "—" : displayScore}
        </div>
      </div>
      
      {/* Row 3: Date & Action */}
      <div className="flex justify-between items-center">
        <div className="font-sans text-[12px] text-text-secondary">
          Last analyzed: {lastAnalyzed}
        </div>
        <Link href={href} className="font-sans text-[12px] text-navy font-medium group-hover:underline active:underline">
          View Report →
        </Link>
      </div>
    </div>
  );
}
