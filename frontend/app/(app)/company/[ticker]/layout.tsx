"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { PageTransition } from "@/components/layout/PageTransition";

export default function CompanyLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { ticker: string };
}) {
  const ticker = params.ticker || "WDI.DE";
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

  // Analysis State (Toggleable for review)
  const [analysisState, setAnalysisState] = useState<"idle" | "running" | "complete">("idle");
  const [elapsed, setElapsed] = useState(0);
  const [stageIndex, setStageIndex] = useState(0);

  const stages = [
    "Fetching financial data...",
    "Running financial forensics...",
    "Analyzing cash flow patterns...",
    "Evaluating governance indicators...",
    "Processing narrative consistency...",
    "Computing Integrity Score...",
    "Generating report..."
  ];

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (analysisState === "running") {
      timer = setInterval(() => {
        setElapsed(prev => {
          if (prev >= 60) {
            setAnalysisState("complete");
            return prev;
          }
          // Advance stage every 8 seconds
          setStageIndex(Math.min(Math.floor(prev / 8), 6));
          return prev + 1;
        });
      }, 1000);
    } else if (analysisState === "idle") {
      setElapsed(0);
      setStageIndex(0);
    }
    return () => clearInterval(timer);
  }, [analysisState]);

  useEffect(() => {
    if (analysisState === "complete") {
      const t = setTimeout(() => setAnalysisState("idle"), 2000);
      return () => clearTimeout(t);
    }
  }, [analysisState]);

  return (
    <div className="w-full max-w-[1200px] relative">
      {/* Dev Toggle for Analysis State */}
      <div className="absolute top-0 right-0 flex gap-2 -mt-10">
        <button onClick={() => setAnalysisState("running")} className="text-xs text-blue-500">Run Analysis</button>
      </div>

      {!isReport && (
        <div className="mb-0">
          <div className="flex justify-between items-end pb-4">
            <div>
              <h1 className="font-sans text-[26px] font-semibold text-[#1A1A18] mb-2">Wirecard AG</h1>
              <div className="flex items-center gap-2 font-sans text-[13px] text-[#7A786F]">
                <span className="font-mono text-[#1C3558]">{ticker === "WDI.DE" ? "WDI.DE" : ticker}</span>
                <span className="text-[#E3DFD8]">·</span>
                <span>Financial Technology</span>
                <span className="text-[#E3DFD8]">·</span>
                <span>Frankfurt Stock Exchange</span>
              </div>
            </div>
            <div className="font-sans text-[12px] text-[#B0ADA7]">
              Last analyzed: June 9, 2025
            </div>
          </div>
        </div>
      )}

      {/* Analysis Running Status Bar */}
      {analysisState !== "idle" && (
        <div 
          className={`w-full h-[36px] border-t border-b border-[#E3DFD8] flex items-center justify-between px-4 mb-4 transition-colors duration-300 ${
            analysisState === "complete" ? "bg-[#E4F2EB]" : "bg-[#F0EDE8]"
          }`}
          style={{ opacity: analysisState === "complete" ? (elapsed === 0 ? 0 : 1) : 1 }} // simple fade out handling
        >
          <div className="flex items-center gap-3">
            {analysisState === "running" ? (
              <div className="flex gap-1">
                <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_0ms]" />
                <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_200ms]" />
                <div className="w-[6px] h-[6px] rounded-full bg-[#1C3558] animate-[pulse_1.5s_infinite_400ms]" />
              </div>
            ) : (
              <div className="font-sans text-[14px] text-[#1A6B3C] font-bold">✓</div>
            )}
            
            <span className={`font-sans text-[12px] ${analysisState === "complete" ? "text-[#1A6B3C]" : "text-[#7A786F]"}`}>
              {analysisState === "running" 
                ? `Investigation in progress — ${stages[stageIndex]}`
                : "Investigation complete."
              }
            </span>
          </div>
          <div className="font-mono text-[12px] text-[#B0ADA7]">
            {Math.floor(elapsed / 60)}:{(elapsed % 60).toString().padStart(2, "0")}
          </div>
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
