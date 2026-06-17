"use client";

import Link from "next/link";
import { NarrativeTrendChart } from "@/components/charts/NarrativeTrendChart";
import { NarrativeComparison } from "@/components/modules/NarrativeComparison";
import { ModuleScoreBadge } from "@/components/modules/ScoreCard";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useCompanyContext } from "@/contexts/CompanyContext";

function toSentiment(label: string): "OPTIMISTIC" | "CAUTIONARY" | "NEUTRAL" {
  const upper = label.toUpperCase();
  if (upper === "OPTIMISTIC" || upper === "CAUTIONARY") return upper;
  return "NEUTRAL";
}

function sentimentRisk(sentiment: "OPTIMISTIC" | "CAUTIONARY" | "NEUTRAL"): "strong" | "moderate" | "low" {
  if (sentiment === "OPTIMISTIC") return "strong";
  if (sentiment === "CAUTIONARY") return "moderate";
  return "low";
}

export default function NarrativePage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker;
  const { company, analysis, isLoading, error } = useCompanyContext();

  if (isLoading) {
    return (
      <div className="w-full flex flex-col gap-12 mt-8 pb-16">
        <section>
          <Skeleton className="w-48 h-3 mb-4" />
          <Skeleton className="w-full h-4 mb-2" />
          <Skeleton className="w-2/3 h-3" />
        </section>
        <section className="flex flex-col gap-10">
          <Skeleton className="w-full h-[160px]" />
          <Skeleton className="w-full h-[160px]" />
        </section>
        <Skeleton className="w-full h-[280px]" />
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
          NEWS TONE (EXPERIMENTAL)
        </div>
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-2">
          {company?.name ?? ticker} hasn&apos;t been analyzed yet
        </h2>
        <p className="font-sans text-[13px] text-[#7A786F] max-w-[420px] mb-6">
          Run an investigation from the overview tab to evaluate sentiment tone across recent news coverage.
        </p>
        <Link href={`/company/${ticker}`} className="font-sans text-[13px] text-[#1C3558] font-medium hover:underline">
          Go to Overview →
        </Link>
      </div>
    );
  }

  const snapshots = analysis.module_details?.narrative?.snapshots ?? [];
  const toneShifts = analysis.module_details?.narrative?.tone_shifts ?? [];

  let summary: string;
  if (snapshots.length === 0) {
    summary = "Not enough recent news coverage was available to assess tone consistency.";
  } else if (snapshots.length === 1) {
    summary = "Only one recent news item was available — not enough to compare tone across periods.";
  } else if (toneShifts.length > 0) {
    summary = `${toneShifts.length} tone shift${toneShifts.length === 1 ? "" : "s"} detected across ${snapshots.length} recent headlines.`;
  } else {
    summary = `Tone is consistent across ${snapshots.length} recent headlines — no significant shifts detected.`;
  }

  const pairs = snapshots.slice(0, -1).map((prev, i) => {
    const curr = snapshots[i + 1];
    const shift = toneShifts.find((t) => t.period === curr.period);
    return { prev, curr, shift };
  });

  return (
    <div className="w-full flex flex-col gap-12 mt-8 pb-16">

      {/* SCORE PANEL */}
      <section>
        <div className="flex items-center gap-3 mb-3">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            NEWS TONE (EXPERIMENTAL)
          </h2>
          <ModuleScoreBadge score={analysis.narrative_score} />
        </div>
        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65] mb-2">
          {summary}
        </p>
        <p className="font-sans text-[12px] text-[#B0ADA7]">
          News Tone is derived from recent headlines, shown for reference, and does not affect the Corporate Integrity Score.
        </p>
      </section>

      {/* COMPARISON BLOCKS / SINGLE STATEMENT / EMPTY STATE */}
      {snapshots.length === 0 ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-risk-strong shrink-0" />
          <span className="font-sans text-[13px] text-[#1A1A18]">
            No recent news coverage was found for this company.
          </span>
        </div>
      ) : snapshots.length === 1 ? (
        <section>
          <div className="text-[11px] font-sans font-medium uppercase text-text-secondary mb-4 tracking-[0.04em]">
            News Headline
          </div>
          <div className="border-t border-b border-border p-4 bg-surface flex flex-col items-start">
            <div className="font-mono text-[11px] text-text-secondary mb-3">{snapshots[0].period}</div>
            <p className="font-sans text-[14px] text-text-primary italic mb-4 leading-relaxed">
              &quot;{snapshots[0].statement_text}&quot;
            </p>
            <Badge risk={sentimentRisk(toSentiment(snapshots[0].sentiment_label))}>
              {toSentiment(snapshots[0].sentiment_label)}
            </Badge>
          </div>
        </section>
      ) : (
        <section className="flex flex-col gap-10">
          {pairs.map(({ prev, curr, shift }, idx) => (
            <NarrativeComparison
              key={idx}
              left={{
                period: prev.period,
                quote: prev.statement_text,
                sentiment: toSentiment(prev.sentiment_label),
              }}
              right={{
                period: curr.period,
                quote: curr.statement_text,
                sentiment: toSentiment(curr.sentiment_label),
              }}
              contradictionAlert={shift?.description}
              alertSeverity={shift ? (shift.severity === "high" ? "severe" : "moderate") : undefined}
            />
          ))}
        </section>
      )}

      {/* SENTIMENT TREND CHART */}
      <NarrativeTrendChart snapshots={snapshots} />

    </div>
  );
}
