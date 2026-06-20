"use client";

import Link from "next/link";
import { use } from "react";
import { RedFlagTimeline } from "@/components/charts/RedFlagTimeline";
import { GovernanceChecklist } from "@/components/modules/GovernanceChecklist";
import { ModuleScoreBadge } from "@/components/modules/ScoreCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { useCompanyContext } from "@/contexts/CompanyContext";
import { normalizeSeverity, flagDate } from "@/lib/utils/redFlag";

export default function GovernancePage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const { company, analysis, isLoading, error } = useCompanyContext();

  if (isLoading) {
    return (
      <div className="w-full flex flex-col gap-12 mt-8 pb-16">
        <section>
          <Skeleton className="w-32 h-3 mb-4" />
          <Skeleton className="w-56 h-5 mb-3" />
          <Skeleton className="w-full h-4" />
        </section>
        <section>
          <Skeleton className="w-48 h-3 mb-4" />
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
            {[0, 1, 2].map((i) => (
              <div key={i} className={`flex justify-between items-center gap-4 px-5 py-4 ${i !== 2 ? "border-b border-[#E3DFD8]" : ""}`}>
                <Skeleton className="flex-1 h-3" />
                <Skeleton className="w-[90px] h-5 rounded-[4px]" />
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center mt-8">
        <div className="font-sans text-[14px] text-[#B03028] mb-1">Couldn&apos;t load this company.</div>
        <div className="font-sans text-[12px] text-[#7A786F]">{error}</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="w-full bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center text-center mt-8">
        <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-3">
          GOVERNANCE RISK
        </div>
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-2">
          {company?.name ?? ticker} hasn&apos;t been analyzed yet
        </h2>
        <p className="font-sans text-[13px] text-[#7A786F] max-w-[420px] mb-6">
          Run an investigation from the overview tab to evaluate governance risk from recent coverage.
        </p>
        <Link href={`/company/${ticker}`} className="font-sans text-[13px] text-[#1C3558] font-medium hover:underline">
          Go to Overview →
        </Link>
      </div>
    );
  }

  const governanceFlags = analysis.red_flags.filter((f) => f.flag_type === "governance");
  const lowConfidence = analysis.module_details?.governance?.low_confidence ?? false;

  let summary: string;
  if (analysis.governance_score === null || analysis.governance_score === undefined) {
    summary = "Governance signal unavailable for this analysis — the evaluation could not be completed.";
  } else if (lowConfidence) {
    summary = "Limited recent news coverage was available for this company — governance could not be meaningfully assessed.";
  } else if (governanceFlags.length > 0) {
    summary = `${governanceFlags.length} governance red flag${governanceFlags.length === 1 ? "" : "s"} identified from recent coverage.`;
  } else {
    summary = "No governance red flags were identified from recent coverage.";
  }

  return (
    <div className="w-full flex flex-col gap-12 mt-8 pb-16">

      {/* SCORE PANEL */}
      <section>
        <div className="flex items-center gap-3 mb-3">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            GOVERNANCE RISK
          </h2>
          <ModuleScoreBadge score={analysis.governance_score} />
        </div>
        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65] mb-2">
          {summary}
        </p>
        {lowConfidence && (
          <p className="font-sans text-[12px] text-[#B0ADA7]">
            This score reflects a neutral baseline due to limited recent news coverage, not a completed governance review.
          </p>
        )}
      </section>

      {/* GOVERNANCE EVENTS CHECKLIST */}
      <section>
        <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
          GOVERNANCE EVENTS
        </div>
        <GovernanceChecklist flags={governanceFlags} />
      </section>

      {/* EVENT TIMELINE */}
      {governanceFlags.length > 0 && (
        <section>
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
            GOVERNANCE EVENT TIMELINE
          </div>
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
            <RedFlagTimeline
              events={governanceFlags.map((f) => ({
                id: f.id,
                year: flagDate(f),
                label: f.description,
                severity: normalizeSeverity(f.severity),
              }))}
            />
          </div>
        </section>
      )}

    </div>
  );
}
