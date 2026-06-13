"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { PageTransition } from "@/components/layout/PageTransition";
import { Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { useCompanyData } from "@/lib/hooks/useCompanyData";
import { useAnalysis } from "@/lib/hooks/useAnalysis";
import { formatDate } from "@/lib/utils/formatDate";

export default function CompanyLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { ticker: string };
}) {
  const ticker = params.ticker;
  const pathname = usePathname();

  const isReport = pathname.includes("/report");

  const tabs = [
    { label: "Overview", href: `/company/${ticker}` },
    { label: "Financials", href: `/company/${ticker}/financials` },
    { label: "Governance", href: `/company/${ticker}/governance` },
    { label: "Narrative", href: `/company/${ticker}/narrative` },
    { label: "Report", href: `/company/${ticker}/report` },
  ];

  // Active tab index for underline slide
  const activeTabIndex = tabs.findIndex(tab => 
    tab.href === `/company/${ticker}` 
      ? pathname === `/company/${ticker}` 
      : pathname.startsWith(tab.href)
  );

  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0 });
  const tabsRef = useRef<(HTMLAnchorElement | null)[]>([]);

  useEffect(() => {
    if (activeTabIndex !== -1 && tabsRef.current[activeTabIndex]) {
      const activeTab = tabsRef.current[activeTabIndex]!;
      setIndicatorStyle({
        left: activeTab.offsetLeft,
        width: activeTab.offsetWidth,
      });
    }
  }, [activeTabIndex, pathname]);

  const { company, isLoading: isCompanyLoading, error: companyError, refetch } = useCompanyData(ticker);
  const { status: analysisStatus, isRunning, error: analysisError, start } = useAnalysis(refetch);

  // Auto-dismiss the status bar a few seconds after the run finishes
  const [statusDismissed, setStatusDismissed] = useState(false);

  useEffect(() => {
    if (analysisStatus?.status === "complete" || analysisStatus?.status === "failed") {
      setStatusDismissed(false);
      const t = setTimeout(() => setStatusDismissed(true), 3000);
      return () => clearTimeout(t);
    }
  }, [analysisStatus]);

  const isAnalysisComplete = analysisStatus?.status === "complete";
  const isAnalysisFailed = analysisStatus?.status === "failed";
  const showStatusBar = isRunning || !!analysisError || (!!analysisStatus && !statusDismissed);

  return (
    <div className="w-full max-w-[1200px] relative">
      {!isReport && (
        <div className="mb-0">
          <div className="flex justify-between items-end pb-4">
            <div>
              {companyError ? (
                <>
                  <h1 className="font-sans text-[26px] font-semibold text-[#1A1A18] mb-2">{ticker}</h1>
                  <div className="font-sans text-[13px] text-[#B03028]">{companyError}</div>
                </>
              ) : isCompanyLoading ? (
                <>
                  <Skeleton className="h-[32px] w-[240px] mb-2" />
                  <Skeleton className="h-[16px] w-[320px]" />
                </>
              ) : (
                <>
                  <h1 className="font-sans text-[26px] font-semibold text-[#1A1A18] mb-2">
                    {company?.name ?? ticker}
                  </h1>
                  <div className="flex items-center gap-2 font-sans text-[13px] text-[#7A786F]">
                    <span className="font-mono text-[#1C3558]">{company?.ticker ?? ticker}</span>
                    {company?.sector && (
                      <>
                        <span className="text-[#E3DFD8]">·</span>
                        <span>{company.sector}</span>
                      </>
                    )}
                    {company?.exchange && (
                      <>
                        <span className="text-[#E3DFD8]">·</span>
                        <span>{company.exchange}</span>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
            <div className="flex flex-col items-end gap-2 shrink-0">
              <div className="font-sans text-[12px] text-[#B0ADA7]">
                Last analyzed: {isCompanyLoading ? "—" : formatDate(company?.last_analyzed)}
              </div>
              <Button
                variant="secondary"
                className="!text-[12px]"
                disabled={isRunning || isCompanyLoading}
                onClick={() => start(company?.ticker ?? ticker)}
              >
                {isRunning ? "Analyzing..." : "Run Analysis"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Running Status Bar */}
      {showStatusBar && (
        <div
          className={`w-full h-[36px] border-t border-b border-[#E3DFD8] flex items-center justify-between px-4 mb-4 transition-colors duration-300 ${
            analysisError || isAnalysisFailed ? "bg-[#FAE8E8]" : isAnalysisComplete ? "bg-[#E4F2EB]" : "bg-[#F0EDE8]"
          }`}
        >
          <div className="flex items-center gap-3">
            {analysisError || isAnalysisFailed ? (
              <span className="font-sans text-[12px] text-[#B03028]">
                {analysisError ?? "Analysis failed. Please try again."}
              </span>
            ) : isAnalysisComplete ? (
              <>
                <div className="font-sans text-[14px] text-[#1A6B3C] font-bold">✓</div>
                <span className="font-sans text-[12px] text-[#1A6B3C]">Investigation complete.</span>
              </>
            ) : (
              <>
                <div className="flex gap-1">
                  <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_0ms]" />
                  <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_200ms]" />
                  <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_400ms]" />
                </div>
                <span className="font-sans text-[12px] text-[#7A786F]">
                  {analysisStatus?.stage ?? "Starting analysis..."}
                </span>
              </>
            )}
          </div>
          {analysisStatus && !analysisError && !isAnalysisFailed && (
            <div className="font-mono text-[12px] text-[#B0ADA7]">
              {Math.floor(analysisStatus.elapsed_seconds / 60)}:{(analysisStatus.elapsed_seconds % 60).toString().padStart(2, "0")}
            </div>
          )}
        </div>
      )}

      {/* Sub-navigation */}
      <div className={`w-full flex items-center border-b border-[#E3DFD8] bg-[#FFFFFF] ${isReport ? 'mb-8' : 'mb-8'} px-2 pt-2 rounded-t-[8px] relative`}>
        {tabs.map((tab, i) => {
          const isActive = activeTabIndex === i;
          return (
            <Link
              key={tab.label}
              href={tab.label === "Overview" ? `/company/${ticker}` : tab.href}
              ref={el => { tabsRef.current[i] = el }}
              className={`px-4 py-3 font-sans text-[14px] transition-colors var(--duration-fast) var(--ease-out) ${
                isActive ? "font-semibold text-[#1A1A18]" : "text-[#7A786F] hover:text-[#1A1A18]"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
        {/* Animated Underline */}
        <div 
          className="absolute bottom-[-1px] h-[2px] bg-[#1C3558]"
          style={{
            left: indicatorStyle.left,
            width: indicatorStyle.width,
            transition: "left var(--duration-fast) var(--ease-out), width var(--duration-fast) var(--ease-out)"
          }}
        />
      </div>

      <div className="w-full">
        <PageTransition>{children}</PageTransition>
      </div>
    </div>
  );
}
