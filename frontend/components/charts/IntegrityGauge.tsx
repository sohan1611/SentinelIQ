import * as React from "react";
import { Skeleton } from "../ui/Skeleton";

interface IntegrityGaugeProps {
  score: number;
  lastAnalyzed: string;
  loading?: boolean;
}

function getRiskDetails(score: number) {
  if (score <= 20) return { color: "text-risk-severe", stroke: "stroke-risk-severe", label: "SEVERE RISK" };
  if (score <= 40) return { color: "text-risk-high", stroke: "stroke-risk-high", label: "HIGH RISK" };
  if (score <= 60) return { color: "text-risk-moderate", stroke: "stroke-risk-moderate", label: "MODERATE RISK" };
  if (score <= 80) return { color: "text-navy", stroke: "stroke-navy", label: "LOW RISK" };
  return { color: "text-risk-strong", stroke: "stroke-risk-strong", label: "STRONG INTEGRITY" };
}

export function IntegrityScoreGauge({ score, lastAnalyzed, loading }: IntegrityGaugeProps) {
  const radius = 90; // Desktop SVG radius
  const circumference = 2 * Math.PI * radius;
  // 270 degree sweep = 75% of circle
  const dasharray = `${circumference * 0.75} ${circumference * 0.25}`;
  // Offset to start at bottom left (135 degrees offset)
  const offset = circumference * 0.625; 
  
  // Calculate fill based on score (0-100 mapped to 0-0.75 of circumference)
  const fillPercentage = score / 100;
  const fillDasharray = `${circumference * 0.75 * fillPercentage} ${circumference}`;

  const risk = getRiskDetails(score);

  if (loading) {
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center mb-4">
          <Skeleton className="absolute w-full h-full rounded-full opacity-30" />
          <Skeleton className="w-[80px] h-[60px]" />
        </div>
        <Skeleton className="w-[120px] h-[16px]" />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center">
        <svg
          className="absolute top-0 left-0 w-full h-full transform -rotate-90"
          viewBox="0 0 200 200"
        >
          {/* Background Arc */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            className="stroke-border"
            strokeWidth="8"
            strokeDasharray={dasharray}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
          {/* Foreground Arc */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            className={risk.stroke}
            strokeWidth="8"
            strokeDasharray={fillDasharray}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>

        <div className="flex flex-col items-center justify-center z-10 mt-4 md:mt-6">
          <div className={`font-mono text-5xl md:text-[72px] font-bold leading-none ${risk.color}`}>
            {score}
          </div>
          <div className="font-mono text-sm md:text-[18px] text-text-secondary mt-1">
            /100
          </div>
          <div className={`font-sans text-[11px] font-medium uppercase tracking-[0.04em] mt-2 md:mt-3 ${risk.color}`}>
            {risk.label}
          </div>
        </div>
      </div>
      <div className="font-sans text-[12px] text-text-secondary mt-6 md:mt-8">
        Last analyzed: {lastAnalyzed}
      </div>
    </div>
  );
}
