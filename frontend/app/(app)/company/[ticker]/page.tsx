import Link from "next/link";
import { IntegrityScoreGauge } from "@/components/charts/IntegrityGauge";
import { Button } from "@/components/ui/Button";
import { ModuleScoreCard } from "@/components/modules/ScoreCard";
import { RedFlagTimeline } from "@/components/charts/RedFlagTimeline";
import { RedFlagItem } from "@/components/modules/RedFlagItem";

export default function CompanyOverviewPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker || "WDI.DE";

  const componentScores = [
    { label: "Financial Quality", score: 42, color: "bg-[#C47A14]", text: "text-[#C47A14]" },
    { label: "Cash Flow Integrity", score: 31, color: "bg-[#B03028]", text: "text-[#B03028]" },
    { label: "Governance Risk", score: 28, color: "bg-[#B03028]", text: "text-[#B03028]" },
    { label: "Earnings Quality", score: 18, color: "bg-[#6E1010]", text: "text-[#6E1010]" },
    { label: "Narrative Consistency", score: 55, color: "bg-[#C47A14]", text: "text-[#C47A14]" },
  ];

  const redFlags = [
    { id: "1", date: "Jan 2022", label: "Revenue Miss", severity: "moderate" as const, type: "FINANCIAL" },
    { id: "2", date: "Apr 2022", label: "CFO Resigned", severity: "high" as const, type: "GOVERNANCE" },
    { id: "3", date: "Sep 2022", label: "Auditor Changed", severity: "high" as const, type: "GOVERNANCE" },
    { id: "4", date: "Feb 2023", label: "Debt +43%", severity: "moderate" as const, type: "FINANCIAL" },
    { id: "5", date: "Jun 2023", label: "Guidance Cut", severity: "moderate" as const, type: "NARRATIVE" },
    { id: "6", date: "Nov 2023", label: "SEC Inquiry", severity: "severe" as const, type: "REGULATORY" },
  ];

  return (
    <div className="flex flex-col md:flex-row gap-8 mt-6">
      {/* Left Column - 35% */}
      <div className="w-full md:w-[35%] flex flex-col gap-6">
        
        {/* Score Panel */}
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex flex-col">
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-6 text-center">
            CORPORATE INTEGRITY SCORE
          </div>
          <div className="mb-8">
            <IntegrityScoreGauge score={22} lastAnalyzed="June 9, 2025" />
          </div>
          
          <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />
          
          <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">
            COMPONENT SCORES
          </div>
          
          <div className="flex flex-col gap-4 mb-6">
            {componentScores.map((comp) => (
              <div key={comp.label} className="flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <span className="font-sans text-[12px] text-[#7A786F]">{comp.label}</span>
                  <span className={`font-mono text-[13px] font-medium ${comp.text}`}>{comp.score}</span>
                </div>
                <div className="w-full h-[6px] bg-[#E3DFD8] rounded-full overflow-hidden">
                  <div className={`h-full ${comp.color}`} style={{ width: `${comp.score}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />

          <div className="flex flex-col gap-2">
            <Link href={`/company/${ticker}/report`} className="w-full">
              <Button variant="primary" className="w-full">View Full Report</Button>
            </Link>
            <Button variant="secondary" className="w-full">Export PDF</Button>
            <button className="font-sans text-[13px] text-[#1C3558] hover:underline mt-2">
              Add to Watchlist
            </button>
          </div>
        </div>
      </div>

      {/* Right Column - 65% */}
      <div className="w-full md:w-[65%] flex flex-col gap-8">
        
        {/* Module Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ModuleScoreCard 
            label="Financial Quality" 
            score={42} 
            summary="Revenue growth diverging from operating cash flow." 
            href={`/company/${ticker}/financials`} 
          />
          <ModuleScoreCard 
            label="Cash Flow Integrity" 
            score={31} 
            summary="Net income exceeded operating cash flow by 40%." 
            href={`/company/${ticker}/financials`} 
          />
          <ModuleScoreCard 
            label="Governance Risk" 
            score={28} 
            summary="Three critical governance events detected in 24 months." 
            href={`/company/${ticker}/governance`} 
          />
          <ModuleScoreCard 
            label="Narrative Consistency" 
            score={55} 
            summary="Significant tone shift and contradictory guidance." 
            href={`/company/${ticker}/narrative`} 
          />
        </div>

        {/* Red Flag Timeline */}
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
              RED FLAGS DETECTED
            </h2>
            <div className="bg-[#FAE8E8] text-[#B03028] font-sans text-[10px] font-semibold px-2 py-0.5 rounded-full">
              6 flags
            </div>
          </div>
          
          <RedFlagTimeline 
            events={redFlags.map(f => ({ id: f.id, year: f.date, label: f.label, severity: f.severity }))}
          />
        </div>

        {/* Red Flag List */}
        <div>
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-2 pl-2">
            FLAG DETAILS
          </h2>
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-2 flex flex-col">
            {redFlags.map((flag) => (
              <RedFlagItem 
                key={flag.id}
                severity={flag.severity}
                date={flag.date}
                description={flag.label}
                type={flag.type}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
