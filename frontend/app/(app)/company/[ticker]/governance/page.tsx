"use client";

import React from "react";
import { Badge, RiskLevel } from "@/components/ui/Badge";
import Link from "next/link";

export default function GovernancePage() {
  const checklist = [
    { indicator: "CFO Stability", status: "RESIGNED Q2 2022", risk: "high" as const },
    { indicator: "Auditor Continuity", status: "CHANGED Q3 2022", risk: "high" as const },
    { indicator: "Board Independence", status: "UNDER REVIEW", risk: "moderate" as const },
    { indicator: "Audit Opinion Quality", status: "QUALIFIED FY2022", risk: "high" as const },
    { indicator: "Director Turnover", status: "2 EXITS IN 18 MONTHS", risk: "moderate" as const },
    { indicator: "Regulatory Inquiries", status: "SEC INQUIRY FILED", risk: "severe" as const },
  ];

  const eventLog = [
    { date: "Jan 2022", event: "Revenue Miss", severity: "moderate" as const, source: "SEC Filing" },
    { date: "Apr 2022", event: "CFO Resigned", severity: "high" as const, source: "Press Release" },
    { date: "Sep 2022", event: "Auditor Changed", severity: "high" as const, source: "SEC Filing" },
    { date: "Feb 2023", event: "Debt +43%", severity: "moderate" as const, source: "SEC Filing" },
    { date: "Jun 2023", event: "Guidance Cut", severity: "moderate" as const, source: "Press Release" },
    { date: "Nov 2023", event: "SEC Inquiry", severity: "severe" as const, source: "SEC Filing" },
  ];

  return (
    <div className="w-full flex flex-col gap-12 mt-8 pb-16">
      
      {/* SECTION A: Governance Score Panel */}
      <section>
        <div className="flex flex-col mb-6">
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
            GOVERNANCE RISK
          </div>
          <div className="flex items-center gap-4 mb-3">
            <span className="font-mono text-[40px] font-bold text-[#B03028] leading-none">
              28<span className="text-[20px] text-[#7A786F]"> / 100</span>
            </span>
            <Badge risk="high">HIGH RISK</Badge>
          </div>
          <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65]">
            Three critical governance events detected in 24 months.
          </p>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
          {checklist.map((item, idx) => (
            <div 
              key={item.indicator} 
              className={`flex justify-between items-center px-5 h-[48px] ${idx !== checklist.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}
            >
              <div className="font-sans text-[13px] text-[#1A1A18]">{item.indicator}</div>
              <div>
                <Badge risk={item.risk}>{item.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION B: Governance Event Log */}
      <section>
        <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
          GOVERNANCE EVENT TIMELINE
        </div>
        
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E3DFD8]">
                <th className="w-[15%] py-3 px-5 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">DATE</th>
                <th className="w-[45%] py-3 px-5 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">EVENT</th>
                <th className="w-[20%] py-3 px-5 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">SEVERITY</th>
                <th className="w-[20%] py-3 px-5 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F] text-right">SOURCE</th>
              </tr>
            </thead>
            <tbody>
              {eventLog.map((row, idx) => (
                <tr key={idx} className={`h-[52px] hover:bg-[#F1EFE9] transition-colors ${idx !== eventLog.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}>
                  <td className="px-5 font-mono text-[12px] text-[#7A786F]">{row.date}</td>
                  <td className="px-5 font-sans text-[14px] text-[#1A1A18]">{row.event}</td>
                  <td className="px-5">
                    <Badge risk={row.severity}>{row.severity.toUpperCase()}</Badge>
                  </td>
                  <td className="px-5 text-right">
                    <Link href="#" className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      {row.source}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
}
