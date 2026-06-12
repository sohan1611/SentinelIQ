import { Card } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-20 text-center">
      <div className="max-w-3xl mx-auto mb-20">
        <h1 className="mb-6 font-serif text-[56px] leading-[1.1] text-primary">
          Know before the market does.
        </h1>
        <p className="mb-10 text-[18px] leading-relaxed text-secondary">
          SentinelIQ detects early warning signs of corporate fraud by analyzing financial statements, management language, and governance behavior.
        </p>
        <div className="relative mx-auto max-w-xl">
          <input 
            type="text" 
            placeholder="Search a company or ticker — e.g. TSLA, Wirecard, Satyam"
            className="w-full rounded-btn border border-border bg-surface px-4 py-4 text-base shadow-sm focus:border-navy focus:outline-none focus:ring-1 focus:ring-navy"
          />
        </div>
        <p className="mt-4 text-[13px] text-secondary">
          Analyzed 2,400+ companies. No account required for preview.
        </p>
      </div>

      <div className="mb-24 grid grid-cols-1 gap-12 text-left md:grid-cols-3">
        <div>
          <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Financial Forensics</div>
          <h3 className="mb-3 text-lg font-semibold text-primary">Revenue that doesn't match cash flow is the first warning sign.</h3>
          <p className="text-sm leading-relaxed text-secondary">We trace anomalies between reported net income and actual operating cash flows over multiple quarters.</p>
        </div>
        <div>
          <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Narrative Consistency</div>
          <h3 className="mb-3 text-lg font-semibold text-primary">Management tone often shifts before numbers do.</h3>
          <p className="text-sm leading-relaxed text-secondary">Our NLP engine detects evasive language, shifting explanations, and contradictions across earnings calls.</p>
        </div>
        <div>
          <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-secondary">Governance Risk</div>
          <h3 className="mb-3 text-lg font-semibold text-primary">Sudden auditor changes are rarely a coincidence.</h3>
          <p className="text-sm leading-relaxed text-secondary">We track executive turnover, related-party transactions, and board independence metrics to flag governance red flags.</p>
        </div>
      </div>

      <div className="text-left border-t border-border pt-16">
        <h4 className="mb-8 text-[11px] font-medium uppercase tracking-wider text-secondary text-center">
          Companies Flagged Before Public Exposure
        </h4>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          {[
            { name: "Enron", year: "2001", score: 14, risk: "severe" },
            { name: "Wirecard", year: "2020", score: 21, risk: "severe" },
            { name: "Satyam", year: "2009", score: 28, risk: "high" },
            { name: "Luckin Coffee", year: "2020", score: 32, risk: "high" },
          ].map((c) => (
            <Card key={c.name} className="p-5">
              <div className="mb-1 text-sm font-semibold text-primary">{c.name}</div>
              <div className="mb-6 text-xs text-secondary">Fraud Exposed: {c.year}</div>
              <div className="text-xs text-secondary mb-1">Integrity Score</div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xl font-bold text-risk-severe">{c.score}</span>
                <span className="text-[10px] text-secondary">/ 100</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
