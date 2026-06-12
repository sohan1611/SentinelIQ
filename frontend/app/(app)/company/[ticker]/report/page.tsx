import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"

export default function AIReportPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker || "SMCI";

  return (
    <div className="mx-auto max-w-[760px] px-6 py-16">
      {/* Header */}
      <div className="mb-12 border-b border-border pb-8">
        <div className="mb-6 text-[11px] font-medium uppercase tracking-wider text-secondary">
          AI Forensic Report
        </div>
        <h1 className="mb-4 font-serif text-4xl text-primary">Super Micro Computer, Inc.</h1>
        <div className="flex items-center gap-4 text-sm text-secondary">
          <span>June 9, 2025</span>
          <span>•</span>
          <div className="flex items-center gap-2">
            <span>Integrity Score:</span>
            <span className="font-mono font-medium text-risk-moderate">42/100</span>
            <Badge risk="moderate">Moderate Risk</Badge>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="prose prose-sm md:prose-base prose-neutral max-w-none text-primary">
        <h3 className="text-lg font-semibold mb-4 uppercase text-[12px] tracking-wider text-secondary">Key Concerns</h3>
        <ul className="list-disc pl-5 mb-8 space-y-2 text-primary leading-relaxed">
          <li>Operating cash flow continues to lag significantly behind reported net income, suggesting low-quality earnings.</li>
          <li>Recent resignation of the CFO and replacement of the independent auditing firm raises substantial governance red flags.</li>
          <li>Inventory levels have spiked <span className="font-mono">43%</span> year-over-year while revenue growth decelerated.</li>
        </ul>

        <h3 className="text-lg font-semibold mb-4 mt-8 uppercase text-[12px] tracking-wider text-secondary">Financial Analysis</h3>
        <p className="mb-4 leading-relaxed">
          The primary driver of the lowered integrity score is the growing divergence between recognized revenue and cash generated from operations. In Q1 2024, the company reported <span className="font-mono">$3.85B</span> in revenue (a <span className="font-mono">12%</span> YoY increase), but operating cash flow was negative <span className="font-mono">-$125M</span>. 
        </p>
        <p className="mb-8 leading-relaxed">
          Furthermore, Days Sales Outstanding (DSO) has stretched from <span className="font-mono">42</span> days to <span className="font-mono">68</span> days over the last three quarters, indicating potential issues with receivables collection or aggressive revenue recognition practices.
        </p>

        <h3 className="text-lg font-semibold mb-4 mt-8 uppercase text-[12px] tracking-wider text-secondary">Governance Observations</h3>
        <p className="mb-8 leading-relaxed">
          Governance metrics have deteriorated significantly. The unexpected departure of the Chief Financial Officer right before the annual audit, followed by the immediate replacement of the auditing firm, historically correlates with a high probability of accounting restatements. 
        </p>

        <h3 className="text-lg font-semibold mb-4 mt-8 uppercase text-[12px] tracking-wider text-secondary">Narrative Review</h3>
        <p className="mb-12 leading-relaxed">
          Management tone remains relatively consistent. However, during the recent earnings call Q&A, executives deflected three direct questions regarding the timeline for cash flow normalization, shifting the topic to total addressable market (TAM) expansion.
        </p>
      </div>

      {/* Recommendation Box */}
      <div className="my-12 border border-border bg-surface p-6 rounded-card">
        <p className="text-sm font-medium text-primary">
          Further investigation is advised before making investment or credit decisions. The combination of declining cash flow quality and auditor replacement warrants caution.
        </p>
      </div>

      {/* Footer / Export */}
      <div className="flex justify-end pt-8">
        <Button variant="secondary">Export PDF Report</Button>
      </div>
    </div>
  )
}
