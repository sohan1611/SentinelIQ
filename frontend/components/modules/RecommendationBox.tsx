import * as React from "react";

export interface RecommendationBoxProps {
  variant?: "standard" | "action-required";
  body: string;
}

export function RecommendationBox({ variant = "standard", body }: RecommendationBoxProps) {
  const isActionRequired = variant === "action-required";
  
  const containerClasses = isActionRequired
    ? "border-y border-r border-border border-l-[3px] border-l-risk-high bg-surface rounded-[6px] p-[20px]"
    : "border border-border bg-surface rounded-[6px] p-[20px]";

  const label = isActionRequired ? "INVESTIGATION RECOMMENDED" : "ANALYST NOTE";

  return (
    <div className={containerClasses}>
      <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3 font-medium">
        {label}
      </div>
      <p className="font-sans text-[14px] text-text-primary leading-[1.7] whitespace-pre-line">
        {body}
      </p>
    </div>
  );
}
