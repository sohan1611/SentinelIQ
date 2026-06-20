"use client";

import Link from "next/link";
import { use } from "react";
import { CashFlowChart } from "@/components/charts/CashFlowChart";
import { DebtTrendChart } from "@/components/charts/DebtTrendChart";
import { RevenueQualityChart } from "@/components/charts/RevenueQualityChart";
import { ModuleScoreBadge } from "@/components/modules/ScoreCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { useCompanyContext } from "@/contexts/CompanyContext";

export default function FinancialsPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const { company, analysis, isLoading, error } = useCompanyContext();

  if (isLoading) {
    return (
      <div className="w-full flex flex-col gap-6 mt-6 pb-16">
        {[0, 1, 2].map((i) => (
          <div key={i} className="bg-surface border border-border rounded-card p-5">
            <Skeleton className="w-40 h-3 mb-2" />
            <Skeleton className="w-64 h-3 mb-4" />
            <Skeleton className="w-full h-[240px]" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-surface border border-border rounded-card p-10 flex flex-col items-center justify-center text-center mt-6">
        <div className="font-sans text-sm text-risk-high mb-1">Couldn&apos;t load this company.</div>
        <div className="font-sans text-xs text-text-secondary">{error}</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="w-full bg-surface border border-border rounded-card p-10 flex flex-col items-center text-center mt-6">
        <div className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary mb-3">
          FINANCIAL FORENSICS
        </div>
        <h2 className="font-sans text-lg font-semibold text-text-primary mb-2">
          {company?.name ?? ticker} hasn&apos;t been analyzed yet
        </h2>
        <p className="font-sans text-sm text-text-secondary max-w-[420px] mb-6">
          Run an investigation from the overview tab to generate revenue, cash flow, and debt forensics.
        </p>
        <Link href={`/company/${ticker}`} className="font-sans text-sm text-navy font-medium hover:underline">
          Go to Overview →
        </Link>
      </div>
    );
  }

  const details = analysis.module_details;
  const divergences = details?.revenue?.divergences ?? [];
  const recvRatios = details?.revenue?.recv_ratios ?? [];
  const accrualRatios = details?.cashflow?.accrual_ratios ?? [];
  const debtMetrics = details?.debt?.debt_metrics ?? [];
  const debtScore = details?.scores?.debt;

  return (
    <div className="w-full flex flex-col gap-6 mt-6 pb-16">
      <RevenueQualityChart
        divergences={divergences}
        recvRatios={recvRatios}
        actions={<ModuleScoreBadge score={analysis.financial_score} />}
      />
      <CashFlowChart
        accrualRatios={accrualRatios}
        actions={<ModuleScoreBadge score={analysis.cashflow_score} />}
      />
      <DebtTrendChart
        debtMetrics={debtMetrics}
        actions={<ModuleScoreBadge score={debtScore} />}
      />
    </div>
  );
}
