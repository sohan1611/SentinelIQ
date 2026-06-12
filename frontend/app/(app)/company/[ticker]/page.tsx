import Link from "next/link"
import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"

export default function CompanyAnalysisPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker || "SMCI";
  
  return (
    <div className="mx-auto max-w-[1100px] px-8 py-12">
      {/* Header Block */}
      <div className="mb-12 flex items-end justify-between border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-semibold font-sans text-primary">Super Micro Computer, Inc.</h1>
            <span className="rounded bg-surface px-2 py-1 font-mono text-sm text-navy border border-border">{ticker}</span>
            <span className="text-xs font-medium text-secondary bg-canvas px-2 py-1 border border-border rounded">Technology Hardware</span>
          </div>
        </div>
        <div className="text-sm text-secondary text-right">
          Last analyzed: June 9, 2025
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-12 mb-16">
        {/* Score Hero */}
        <div className="flex flex-col items-center justify-center py-6">
          <div className="relative flex h-48 w-48 items-center justify-center rounded-full border-[12px] border-risk-moderate-bg">
            <div className="absolute top-0 left-0 h-full w-full rounded-full border-[12px] border-risk-moderate border-t-transparent border-l-transparent rotate-45"></div>
            <div className="text-center flex flex-col items-center mt-2">
              <span className="font-mono text-[64px] font-bold leading-none text-risk-moderate">42</span>
              <span className="font-mono text-xl text-secondary">/100</span>
            </div>
          </div>
          <div className="mt-6">
            <Badge risk="moderate">Moderate Risk</Badge>
          </div>
        </div>

        {/* Module Grid */}
        <div className="grid grid-cols-2 gap-6">
          <Card className="p-6 flex flex-col justify-between">
            <div>
              <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Financial Quality</div>
              <div className="mb-2 font-mono text-3xl font-medium text-risk-high">28</div>
              <p className="text-sm text-primary mb-4">Revenue growth diverging from operating cash flow for 3 quarters.</p>
            </div>
            <Link href={`/company/${ticker}/financials`} className="text-xs font-medium text-navy hover:underline">View Details →</Link>
          </Card>
          
          <Card className="p-6 flex flex-col justify-between">
            <div>
              <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Governance Risk</div>
              <div className="mb-2 font-mono text-3xl font-medium text-risk-high">34</div>
              <p className="text-sm text-primary mb-4">High executive turnover and recent change in independent auditing firm.</p>
            </div>
            <Link href={`/company/${ticker}/governance`} className="text-xs font-medium text-navy hover:underline">View Details →</Link>
          </Card>

          <Card className="p-6 flex flex-col justify-between">
            <div>
              <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Cash Flow Integrity</div>
              <div className="mb-2 font-mono text-3xl font-medium text-risk-moderate">55</div>
              <p className="text-sm text-primary mb-4">DSO (Days Sales Outstanding) increasing faster than revenue.</p>
            </div>
            <Link href={`/company/${ticker}/financials`} className="text-xs font-medium text-navy hover:underline">View Details →</Link>
          </Card>

          <Card className="p-6 flex flex-col justify-between">
            <div>
              <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Narrative Consistency</div>
              <div className="mb-2 font-mono text-3xl font-medium text-risk-low">78</div>
              <p className="text-sm text-primary mb-4">Management tone remains consistent with historical baselines.</p>
            </div>
            <Link href={`/company/${ticker}/narrative`} className="text-xs font-medium text-navy hover:underline">View Details →</Link>
          </Card>
        </div>
      </div>

      {/* Red Flag Timeline */}
      <div>
        <h3 className="mb-6 text-[11px] font-medium uppercase tracking-wider text-secondary">Red Flags Detected</h3>
        <div className="relative pt-8 pb-4">
          <div className="absolute top-[45px] left-0 w-full h-[1px] bg-border z-0"></div>
          
          <div className="relative z-10 flex justify-between px-4">
            {/* Timeline Item 1 */}
            <div className="flex flex-col items-center w-32">
              <span className="text-[10px] text-secondary font-mono mb-2">Q3 2023</span>
              <div className="h-3 w-3 rounded-full bg-risk-moderate ring-4 ring-canvas mb-3"></div>
              <span className="text-xs text-center text-primary font-medium">Inventory buildup</span>
            </div>

            {/* Timeline Item 2 */}
            <div className="flex flex-col items-center w-32">
              <span className="text-[10px] text-secondary font-mono mb-2">Q4 2023</span>
              <div className="h-3 w-3 rounded-full bg-risk-high ring-4 ring-canvas mb-3"></div>
              <span className="text-xs text-center text-primary font-medium">CFO Resignation</span>
            </div>

            {/* Timeline Item 3 */}
            <div className="flex flex-col items-center w-32">
              <span className="text-[10px] text-secondary font-mono mb-2">Q1 2024</span>
              <div className="h-3 w-3 rounded-full bg-risk-moderate ring-4 ring-canvas mb-3"></div>
              <span className="text-xs text-center text-primary font-medium">Debt spike +43%</span>
            </div>

            {/* Timeline Item 4 */}
            <div className="flex flex-col items-center w-32">
              <span className="text-[10px] text-secondary font-mono mb-2">Q1 2024</span>
              <div className="h-3 w-3 rounded-full bg-risk-high ring-4 ring-canvas mb-3"></div>
              <span className="text-xs text-center text-primary font-medium">Auditor replaced</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-16 flex justify-end">
         <Link href={`/company/${ticker}/report`} className="text-navy font-medium hover:underline text-sm">
           View Full AI Report →
         </Link>
      </div>
    </div>
  )
}
