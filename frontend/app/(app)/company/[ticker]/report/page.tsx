"use client";

import Link from "next/link";
import { use } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { RecommendationBox } from "@/components/modules/RecommendationBox";
import { ReportSection } from "@/components/modules/ReportSection";
import { buildForensicsCsv, downloadCsv } from "@/lib/utils/exportCsv";
import { useAddToWatchlist } from "@/lib/hooks/useAddToWatchlist";
import { useCompanyContext } from "@/contexts/CompanyContext";
import { useReport } from "@/lib/hooks/useReport";
import { formatDate } from "@/lib/utils/formatDate";
import { formatScore } from "@/lib/utils/formatNumber";
import { getRiskLevel, getRiskLabel } from "@/lib/utils/riskLabel";
import { getScoreColor } from "@/lib/utils/scoreColor";
import type { AnalysisResultWithFlags } from "@/types/analysis";

function buildRecommendation(analysis: AnalysisResultWithFlags): { variant: "standard" | "action-required"; body: string } {
  const riskLevel = getRiskLevel(analysis.integrity_score ?? 0);
  const flagCount = analysis.red_flags.length;
  const confidence = analysis.module_details?.confidence;
  const isActionRequired = riskLevel === "severe" || riskLevel === "high";

  let body: string;
  if (isActionRequired) {
    body = `This analysis identified ${flagCount} red flag${flagCount === 1 ? "" : "s"} consistent with known precursors to financial misstatement or governance failure. Independent due diligence and review of primary source filings is strongly advised before any investment or credit decision.`;
  } else if (flagCount > 0) {
    body = `This analysis identified ${flagCount} red flag${flagCount === 1 ? "" : "s"}. The overall integrity profile remains within an acceptable range, but continued monitoring of these items is recommended.`;
  } else {
    body = "No red flags were identified in this analysis. The overall integrity profile is consistent with sound financial reporting and governance practices.";
  }

  if (confidence === "low") {
    body += " Confidence in this score is low due to limited available data — treat conclusions as preliminary.";
  }

  return { variant: isActionRequired ? "action-required" : "standard", body };
}

export default function ReportPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const { company, analysis, isLoading: companyLoading, error } = useCompanyContext();
  const { report, isLoading: reportLoading } = useReport(ticker, !!analysis);
  const { isAdding, add: handleAddToWatchlist } = useAddToWatchlist(ticker);

  const isLoading = companyLoading || (!!analysis && reportLoading);

  if (isLoading) {
    return (
      <div className="w-full flex justify-center mt-8 pb-16">
        <div className="w-full max-w-[760px] flex flex-col">
          <div className="mb-8">
            <Skeleton className="w-36 h-3 mb-3" />
            <Skeleton className="w-64 h-6 mb-2" />
            <Skeleton className="w-48 h-3 mb-3" />
            <Skeleton className="w-28 h-5 rounded-[4px]" />
          </div>
          <div className="w-full h-px bg-border mb-8" />
          <div className="flex flex-col gap-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="w-full h-4" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full flex justify-center mt-8 pb-16">
        <div className="w-full max-w-[760px] bg-surface border border-border rounded-card p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-sm text-risk-high mb-1">Couldn&apos;t load this company.</div>
          <div className="font-sans text-xs text-text-secondary">{error}</div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="w-full flex justify-center mt-8 pb-16">
        <div className="w-full max-w-[760px] bg-surface border border-border rounded-card p-10 flex flex-col items-center text-center">
          <div className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary mb-3">
            AI FORENSIC REPORT
          </div>
          <h2 className="font-sans text-lg font-semibold text-text-primary mb-2">
            {company?.name ?? ticker} hasn&apos;t been analyzed yet
          </h2>
          <p className="font-sans text-sm text-text-secondary max-w-[420px] mb-6">
            Run an investigation from the overview tab to generate a full forensic report.
          </p>
          <Link href={`/company/${ticker}`} className="font-sans text-sm text-navy font-medium hover:underline">
            Go to Overview →
          </Link>
        </div>
      </div>
    );
  }

  const riskLevel = getRiskLevel(analysis.integrity_score ?? 0);
  const riskLabel = getRiskLabel(analysis.integrity_score ?? 0);
  const recommendation = buildRecommendation(analysis);

  const handleExportCsv = () => {
    const generatedAt = report?.generated_at ?? analysis.run_at;
    downloadCsv(`${ticker}-forensics.csv`, buildForensicsCsv(ticker, generatedAt, analysis.module_details));
  };

  return (
    <div className="w-full flex justify-center mt-8 pb-16">
      <div className="w-full max-w-[760px] flex flex-col">

        {/* PAGE HEADER */}
        <div className="mb-8">
          <div className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary mb-3">
            AI FORENSIC REPORT
          </div>
          <h1 className="font-sans text-[24px] font-semibold text-text-primary mb-2">
            {company?.name ?? ticker}
          </h1>

          <div className="flex items-center gap-2 mb-3">
            <span className="font-mono text-[12px] text-text-secondary">{ticker}</span>
            <span className="text-border">·</span>
            <span className="font-sans text-[12px] text-text-secondary">
              Generated {formatDate(report?.generated_at ?? analysis.run_at)}
            </span>
            <span className="text-border">·</span>
            <span className="font-mono text-[12px] text-text-secondary">
              Analysis #{analysis.id.slice(0, 8).toUpperCase()}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium" style={{ color: getScoreColor(analysis.integrity_score ?? 0) }}>
              {formatScore(analysis.integrity_score)} / 100
            </span>
            <Badge risk={riskLevel}>{riskLabel}</Badge>
          </div>
        </div>

        <div className="w-full h-px bg-border mb-8" />

        {/* REPORT BODY */}
        {report?.content ? (
          <ReportSection content={report.content} />
        ) : (
          <div className="bg-surface border border-border rounded-card p-6 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-risk-strong shrink-0" />
            <span className="font-sans text-[13px] text-text-primary">
              Report content is not yet available for this analysis.
            </span>
          </div>
        )}

        <div className="w-full h-px bg-border my-10" />

        {/* RECOMMENDATION BOX */}
        <div className="mb-10">
          <RecommendationBox variant={recommendation.variant} body={recommendation.body} />
        </div>

        {/* DISCLAIMER */}
        <div className="mb-12">
          <p className="font-sans text-[11px] text-text-muted italic text-center leading-relaxed">
            This report is generated from publicly available information using AI-assisted forensic analysis. It does not constitute financial advice, legal opinion, or a finding of fraud. All conclusions are probabilistic and subject to the limitations of available data.
          </p>
        </div>

        {/* PAGE ACTIONS */}
        <div className="flex justify-end items-center gap-4 print-hidden">
          <button
            onClick={handleAddToWatchlist}
            disabled={isAdding}
            className="font-sans text-[13px] text-navy hover:underline px-4 disabled:opacity-50 disabled:no-underline disabled:cursor-not-allowed"
          >
            {isAdding ? "Adding..." : "Add to Watchlist"}
          </button>
          <Button variant="secondary" onClick={handleExportCsv}>Export Data (CSV)</Button>
          <Button variant="secondary" onClick={() => window.print()}>Export PDF</Button>
        </div>

      </div>
    </div>
  );
}
