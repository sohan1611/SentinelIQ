"use client";

import Link from "next/link";
import { IntegrityScoreGauge } from "@/components/charts/IntegrityGauge";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Tooltip } from "@/components/ui/Tooltip";
import { ModuleScoreCard } from "@/components/modules/ScoreCard";
import { RedFlagTimeline } from "@/components/charts/RedFlagTimeline";
import { IntegrityScoreTrendChart } from "@/components/charts/IntegrityScoreTrendChart";
import { RedFlagItem } from "@/components/modules/RedFlagItem";
import { useStaggeredReveal } from "@/hooks/useStaggeredReveal";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAddToWatchlist } from "@/lib/hooks/useAddToWatchlist";
import { useCompanyContext } from "@/contexts/CompanyContext";
import { useAnalysisHistory } from "@/lib/hooks/useAnalysisHistory";
import { getScoreColor } from "@/lib/utils/scoreColor";
import { formatScore } from "@/lib/utils/formatNumber";
import { formatDate } from "@/lib/utils/formatDate";
import { normalizeSeverity, flagDate, getFlagEvidence } from "@/lib/utils/redFlag";

type ScoreKey =
  | "financial_score"
  | "cashflow_score"
  | "governance_score"
  | "earnings_score"
  | "narrative_score"
  | "news_score";

const COMPONENT_SCORES: { key: ScoreKey; label: string }[] = [
  { key: "financial_score", label: "Financial Quality" },
  { key: "cashflow_score", label: "Cash Flow Integrity" },
  { key: "governance_score", label: "Governance Risk" },
  { key: "earnings_score", label: "Earnings Quality" },
  { key: "narrative_score", label: "News Tone (experimental)" },
  { key: "news_score", label: "News Sentiment" },
];

const MODULE_CARDS: { key: ScoreKey; label: string; summary: string; tab: string }[] = [
  {
    key: "financial_score",
    label: "Financial Quality",
    summary: "Revenue growth, receivables trends, and debt levels relative to operating performance.",
    tab: "financials",
  },
  {
    key: "cashflow_score",
    label: "Cash Flow Integrity",
    summary: "Divergence between reported net income and operating cash flow (accrual ratio).",
    tab: "financials",
  },
  {
    key: "governance_score",
    label: "Governance Risk",
    summary: "Leadership changes, auditor transitions, and regulatory events from recent coverage.",
    tab: "governance",
  },
  {
    key: "narrative_score",
    label: "News Tone (experimental)",
    summary: "Sentiment across recent news headlines — experimental, zero-weighted.",
    tab: "narrative",
  },
];

const CONFIDENCE_TOOLTIPS: Record<"low" | "medium" | "high", string> = {
  high: "5 of 5 modules scored, 3+ years of history",
  medium: "Most modules scored from available data",
  low: "2 or fewer modules produced real signal",
};

export default function CompanyOverviewPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker;

  const { company, analysis, isLoading, error, analysisStatus, isRunning, analysisError, startAnalysis: start } = useCompanyContext();
  const { isAdding, add: handleAddToWatchlist } = useAddToWatchlist(ticker);
  const { history, isLoading: isHistoryLoading } = useAnalysisHistory(ticker);

  const isLoaded = !isLoading;
  const { styles: moduleStyles, showSkeletons, skeletonStyle } = useStaggeredReveal(4, 40, isLoaded);

  const periodCount = analysis
    ? Math.max(
        analysis.module_details?.revenue?.divergences?.length ?? 0,
        analysis.module_details?.revenue?.recv_ratios?.length ?? 0,
        analysis.module_details?.cashflow?.accrual_ratios?.length ?? 0,
        analysis.module_details?.earnings?.margins?.length ?? 0,
        analysis.module_details?.earnings?.net_incomes?.length ?? 0,
        analysis.module_details?.debt?.debt_metrics?.length ?? 0
      )
    : 0;

  const confidence = analysis?.module_details?.confidence;

  const isFinanciallyBlind =
    confidence === "low" &&
    analysis?.financial_score == null &&
    analysis?.cashflow_score == null &&
    analysis?.earnings_score == null;

  const hasNullModules =
    analysis != null &&
    COMPONENT_SCORES.some(({ key }) => analysis[key] == null);

  return (
    <div className="flex flex-col md:flex-row gap-8 mt-6 relative">

      {/* Skeletons Overlay */}
      {showSkeletons && (
        <div className="absolute inset-0 z-10 bg-canvas pointer-events-none" style={skeletonStyle}>
          <div className="flex flex-col md:flex-row gap-8">
            <div className="w-full md:w-[35%] flex flex-col gap-6">
              <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex flex-col items-center">
                <Skeleton className="w-[180px] h-[14px] mb-6" />
                <Skeleton className="w-[200px] h-[100px] rounded-t-full mb-8" />
                <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />
                <Skeleton className="w-[120px] h-[14px] mb-4" />
                <div className="flex flex-col gap-4 mb-6 w-full">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="flex flex-col gap-2">
                      <div className="flex justify-between">
                        <Skeleton className="w-[100px] h-[12px]" />
                        <Skeleton className="w-[20px] h-[12px]" />
                      </div>
                      <Skeleton className="w-full h-[6px] rounded-full" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="w-full md:w-[65%] flex flex-col gap-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-5 h-[140px]">
                    <Skeleton className="w-1/2 h-[16px] mb-4" />
                    <Skeleton className="w-[60px] h-[32px] mb-4" />
                    <Skeleton className="w-full h-[14px]" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {error ? (
        <div className="w-full bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-[14px] text-[#B03028] mb-1">Couldn&apos;t load this company.</div>
          <div className="font-sans text-[12px] text-[#7A786F]">{error}</div>
        </div>
      ) : !analysis ? (
        <div className="w-full bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center text-center">
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-3">
            CORPORATE INTEGRITY SCORE
          </div>
          <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-2">
            {company?.name ?? ticker} hasn&apos;t been analyzed yet
          </h2>
          <p className="font-sans text-[13px] text-[#7A786F] max-w-[420px] mb-6">
            Run an investigation to generate its Corporate Integrity Score, forensic breakdowns, and red-flag timeline.
          </p>
          <Button
            variant="primary"
            isLoading={isRunning}
            loadingText={analysisStatus?.stage ?? "Starting analysis..."}
            onClick={() => start(ticker)}
          >
            Run Analysis
          </Button>
          {analysisError && (
            <div className="font-sans text-[12px] text-[#B03028] mt-4">
              {analysisError}
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Left Column - 35% */}
          <div className="w-full md:w-[35%] flex flex-col gap-6">

            {/* Score Panel */}
            <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex flex-col relative z-0">
              <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-6 text-center">
                CORPORATE INTEGRITY SCORE
              </div>
              <div className="mb-8 flex flex-col items-center gap-3">
                <IntegrityScoreGauge
                  score={analysis.integrity_score ?? 0}
                  lastAnalyzed={formatDate(company?.last_analyzed ?? analysis.run_at)}
                  startAnimation={isLoaded}
                  muted={isFinanciallyBlind}
                />
                {confidence && (
                  <Tooltip content={CONFIDENCE_TOOLTIPS[confidence]} side="bottom">
                    <Badge risk="analyzing">Confidence: {confidence.toUpperCase()}</Badge>
                  </Tooltip>
                )}
                {isFinanciallyBlind && (
                  <p className="font-sans text-[11px] text-[#7A786F] text-center leading-[1.5] max-w-[220px] uppercase tracking-[0.05em]">
                    {analysis.module_details?.financial_data_status === "rate_limited"
                      ? "Financial data temporarily unavailable — please retry. Score reflects governance and news signals only"
                      : "Financial data unavailable — score reflects governance and news signals only"}
                  </p>
                )}
              </div>

              <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />

              <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
                COMPONENT SCORES
              </div>

              <div className="flex flex-col gap-4 mb-2">
                {COMPONENT_SCORES.map(({ key, label }) => {
                  const score = analysis[key];
                  const hasScore = score !== null && score !== undefined;
                  const color = hasScore ? getScoreColor(score) : "#B0ADA7";
                  return (
                    <div key={key} className="flex flex-col gap-1">
                      <div className="flex justify-between items-start">
                        <span className="font-sans text-[12px] text-[#7A786F]">{label}</span>
                        <div className="flex flex-col items-end">
                          <span className="font-mono text-[13px] font-medium" style={{ color }}>
                            {formatScore(score)}
                          </span>
                          {!hasScore && (
                            <span className="font-sans text-[10px] text-[#B0ADA7]">Unavailable</span>
                          )}
                        </div>
                      </div>
                      <div
                        role="meter"
                        aria-label={label}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={score ?? 0}
                        aria-valuetext={hasScore ? `${Math.round(score as number)} out of 100` : "No signal available"}
                        className="w-full h-[6px] bg-[#E3DFD8] rounded-full overflow-hidden"
                      >
                        {hasScore && (
                          <div aria-hidden="true" className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {hasNullModules && (
                <p className="font-sans text-[11px] text-[#B0ADA7] leading-[1.5] mb-3">
                  Unavailable modules are excluded from the score and renormalized per the{" "}
                  <Link href="/methodology" className="text-[#1C3558] underline underline-offset-2">
                    scoring methodology
                  </Link>.
                </p>
              )}

              <div className="font-sans text-[11px] text-[#B0ADA7] mb-6">
                {periodCount > 0
                  ? `Based on ${periodCount} reporting period${periodCount === 1 ? "" : "s"} of financial history.`
                  : "Limited financial history available — some scores reflect neutral baselines."}
              </div>

              <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />

              <div className="flex flex-col gap-2">
                <Link href={`/company/${ticker}/report`} className="w-full">
                  <Button variant="primary" className="w-full">View Full Report</Button>
                </Link>
                <Button variant="secondary" className="w-full" onClick={() => window.print()}>Export PDF</Button>
                <button
                  onClick={handleAddToWatchlist}
                  disabled={isAdding}
                  className="font-sans text-[13px] text-[#1C3558] hover:underline mt-2 disabled:opacity-50 disabled:no-underline disabled:cursor-not-allowed"
                >
                  {isAdding ? "Adding..." : "Add to Watchlist"}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - 65% */}
          <div className="w-full md:w-[65%] flex flex-col gap-8 relative z-0">

            {/* Module Grid with Stagger */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {MODULE_CARDS.map((m, i) => (
                <div key={m.key} style={moduleStyles[i]}>
                  <ModuleScoreCard
                    label={m.label}
                    score={analysis[m.key]}
                    summary={m.summary}
                    href={`/company/${ticker}/${m.tab}`}
                  />
                </div>
              ))}
            </div>

            {/* Integrity Score Trend */}
            <div style={moduleStyles[3]}>
              <IntegrityScoreTrendChart history={history} isLoading={isHistoryLoading} />
            </div>

            {analysis.red_flags.length > 0 ? (
              <>
                {/* Red Flag Timeline */}
                <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6" style={moduleStyles[3]}>
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
                      RED FLAGS DETECTED
                    </h2>
                    <div className="bg-[#FAE8E8] text-[#B03028] font-sans text-[10px] font-semibold px-2 py-0.5 rounded-full">
                      {analysis.red_flags.length} flag{analysis.red_flags.length === 1 ? "" : "s"}
                    </div>
                  </div>

                  <RedFlagTimeline
                    events={analysis.red_flags.map((f) => ({
                      id: f.id,
                      year: flagDate(f),
                      label: f.description,
                      severity: normalizeSeverity(f.severity),
                    }))}
                  />
                </div>

                {/* Red Flag List */}
                <div style={moduleStyles[3]}>
                  <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-2 pl-2">
                    FLAG DETAILS
                  </h2>
                  <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-2 flex flex-col">
                    {analysis.red_flags.map((flag) => (
                      <RedFlagItem
                        key={flag.id}
                        severity={normalizeSeverity(flag.severity)}
                        date={flagDate(flag)}
                        description={flag.description}
                        type={flag.flag_type.replace(/_/g, " ")}
                        evidence={getFlagEvidence(flag, analysis.module_details)}
                        analysisId={analysis.id}
                        flagId={flag.id}
                      />
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex items-center gap-3" style={moduleStyles[3]}>
                <div className="w-2 h-2 rounded-full bg-risk-strong shrink-0" />
                <span className="font-sans text-[13px] text-[#1A1A18]">No red flags were detected in this analysis.</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
