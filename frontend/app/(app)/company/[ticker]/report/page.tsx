"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RecommendationBox } from "@/components/modules/RecommendationBox";

export default function ReportPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker || "WDI.DE";

  return (
    <div className="w-full flex justify-center mt-8 pb-16">
      <div className="w-full max-w-[760px] flex flex-col">
        
        {/* PAGE HEADER */}
        <div className="mb-8">
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-3">
            AI FORENSIC REPORT
          </div>
          <h1 className="font-sans text-[24px] font-semibold text-[#1A1A18] mb-2">Wirecard AG</h1>
          
          <div className="flex items-center gap-2 mb-3">
            <span className="font-mono text-[12px] text-[#7A786F]">{ticker === "WDI.DE" ? "WDI.DE" : ticker}</span>
            <span className="text-[#E3DFD8]">·</span>
            <span className="font-sans text-[12px] text-[#7A786F]">Generated June 9, 2025</span>
            <span className="text-[#E3DFD8]">·</span>
            <span className="font-sans text-[12px] text-[#7A786F]">Analysis #2891</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium text-[#B03028]">22 / 100</span>
            <Badge risk="high">HIGH RISK</Badge>
          </div>
        </div>

        <div className="w-full h-[1px] bg-[#E3DFD8] mb-8" />

        {/* REPORT BODY SECTIONS */}
        <div className="flex flex-col gap-10 font-sans text-[15px] text-[#1A1A18] leading-[1.8]">
          
          <section>
            <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-1">
              EXECUTIVE SUMMARY
            </div>
            <h2 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-3">
              Executive Summary
            </h2>
            <p>
              Wirecard AG presents a Corporate Integrity Score of 22 out of 100, placing it in the High Risk category. The investigation identified critical divergences between reported financial performance and underlying cash generation, alongside three significant governance events within a 24-month window.
            </p>
          </section>

          <section>
            <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-1">
              KEY CONCERNS
            </div>
            <h2 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-3">
              Key Concerns
            </h2>
            <ul className="flex flex-col gap-2 font-sans text-[14px] text-[#1A1A18] leading-[1.75]">
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>Operating cash flow declined for four consecutive quarters while net income was reported as positive.</span></li>
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>CFO resigned in Q2 2022 with no successor named for 90 days.</span></li>
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>Auditor replaced in Q3 2022, two quarters after a qualified opinion.</span></li>
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>Revenue-to-receivables ratio expanded <span className="font-mono text-[13px]">2.8×</span> in 18 months.</span></li>
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>Management guidance revised downward twice in the same fiscal year.</span></li>
              <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span><span>SEC initiated an informal inquiry in November 2023.</span></li>
            </ul>
          </section>

          <section>
            <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-1">
              FINANCIAL ANALYSIS
            </div>
            <h2 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-3">
              Financial Analysis
            </h2>
            <p>
              Net income of <span className="font-mono text-[14px]">€415M</span> in FY2022 was accompanied by operating cash outflow of <span className="font-mono text-[14px]">€112M</span> — a divergence of <span className="font-mono text-[14px]">€527M</span> that is inconsistent with the reported margin profile. This represents the widest gap between accrual earnings and cash realization in the company's public history.
            </p>
          </section>

          <section>
            <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-1">
              GOVERNANCE OBSERVATIONS
            </div>
            <h2 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-3">
              Governance Observations
            </h2>
            <p>
              The departure of the CFO in April 2022 was followed by a change in auditors in September 2022. This sequencing of executive turnover followed by audit rotation is historically correlated with elevated financial restatement probability.
            </p>
          </section>

          <section>
            <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-1">
              NARRATIVE REVIEW
            </div>
            <h2 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-3">
              Narrative Review
            </h2>
            <p className="mb-6">
              Linguistic analysis of management commentary reveals significant deterioration in forward-looking sentiment.
            </p>
            
            <div className="flex flex-col gap-6 pl-4 border-l-2 border-[#E3DFD8]">
              <div>
                <div className="font-mono text-[11px] text-[#7A786F] mb-1">Q2 2022</div>
                <p className="italic font-sans text-[14px] text-[#1A1A18]">"We reaffirm full-year revenue guidance of €5.4B with high confidence."</p>
              </div>
              <div>
                <div className="font-mono text-[11px] text-[#7A786F] mb-1">Q4 2022</div>
                <p className="italic font-sans text-[14px] text-[#1A1A18]">"Given evolving market conditions, we are withdrawing forward guidance for FY2023."</p>
              </div>
            </div>
          </section>

        </div>

        <div className="w-full h-[1px] bg-[#E3DFD8] my-10" />

        {/* RECOMMENDATION BOX */}
        <div className="mb-10">
          <RecommendationBox
            variant="action-required"
            body="Patterns detected in this analysis are consistent with known precursors to material financial misstatement. Independent due diligence and review of primary source filings is strongly advised before any investment or credit decision."
          />
        </div>

        {/* DISCLAIMER */}
        <div className="mb-12">
          <p className="font-sans text-[11px] text-[#B0ADA7] italic text-center leading-relaxed">
            This report is generated from publicly available information using AI-assisted forensic analysis. It does not constitute financial advice, legal opinion, or a finding of fraud. All conclusions are probabilistic and subject to the limitations of available data.
          </p>
        </div>

        {/* PAGE ACTIONS */}
        <div className="flex justify-end items-center gap-4">
          <button className="font-sans text-[13px] text-[#1C3558] hover:underline px-4">
            Share Report
          </button>
          <Button variant="secondary">
            Export PDF
          </Button>
        </div>

      </div>
    </div>
  );
}
