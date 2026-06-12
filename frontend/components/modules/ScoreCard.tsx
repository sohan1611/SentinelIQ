import * as React from "react";
import { Card } from "../ui/Card";
import { Skeleton } from "../ui/Skeleton";
import Link from "next/link";

interface ModuleScoreCardProps {
  label: string;
  score: number;
  summary: string;
  href?: string;
  loading?: boolean;
}

function getScoreColor(score: number) {
  if (score <= 40) return { border: "border-l-risk-high", text: "text-risk-high" };
  if (score <= 60) return { border: "border-l-risk-moderate", text: "text-risk-moderate" };
  if (score <= 80) return { border: "border-l-navy", text: "text-navy" };
  return { border: "border-l-risk-strong", text: "text-risk-strong" };
}

export function ModuleScoreCard({ label, score, summary, href = "#", loading }: ModuleScoreCardProps) {
  if (loading) {
    return (
      <Card className="w-full md:w-[260px] h-[160px] p-4 flex flex-col justify-between border-l-[3px] border-l-border">
        <Skeleton className="w-24 h-3 mb-2" />
        <Skeleton className="w-16 h-10 mb-2" />
        <div className="w-full h-[1px] bg-border my-2" />
        <Skeleton className="w-full h-3 mb-1" />
        <Skeleton className="w-3/4 h-3" />
      </Card>
    );
  }

  const colors = getScoreColor(score);

  return (
    <Card className={`w-full md:w-[260px] h-[160px] flex flex-col justify-between border-l-[3px] ${colors.border}`}>
      <div className="p-4 flex flex-col h-full">
        <div className="font-sans text-[10px] font-medium uppercase tracking-[0.04em] text-text-secondary mb-2 line-clamp-1">
          {label}
        </div>
        <div className="flex items-baseline mb-2">
          <span className={`font-mono text-[40px] font-bold leading-none ${colors.text}`}>
            {score}
          </span>
          <span className="font-mono text-[16px] text-text-secondary ml-1">
            /100
          </span>
        </div>
        <div className="w-full h-[1px] bg-border mb-3" />
        <p className="font-sans text-[13px] text-text-primary leading-tight line-clamp-2 mb-auto">
          {summary}
        </p>
        <div className="text-right mt-2">
          <Link href={href} className="font-sans text-[12px] text-navy font-medium transition-colors hover:text-[#142848]">
            View Details →
          </Link>
        </div>
      </div>
    </Card>
  );
}
