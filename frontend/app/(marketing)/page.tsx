import { SearchBar } from "@/components/layout/SearchBar";
import { Badge } from "@/components/ui/Badge";

export default function LandingPage() {
  return (
    <div className="w-full bg-canvas text-text-primary font-sans">
      
      {/* SECTION 2 — Hero */}
      <section className="pt-16 md:pt-24 pb-16 md:pb-20 px-5 md:px-6 max-w-[720px] mx-auto text-center flex flex-col items-center">
        <div className="text-[10px] md:text-[11px] font-sans uppercase tracking-[0.1em] text-text-secondary mb-6">
          CORPORATE FRAUD EARLY WARNING
        </div>
        
        <h1 className="font-serif text-[36px] md:text-[56px] font-normal text-text-primary leading-[1.2] md:leading-[1.15] max-w-[600px] mb-6">
          Know before the market does.
        </h1>
        
        <p className="font-sans text-[15px] md:text-[18px] text-text-secondary leading-[1.65] max-w-[560px] mb-10 md:mb-12">
          SentinelIQ analyzes financial statements, management language, and governance behavior to surface early warning signs of corporate fraud — before they become public knowledge.
        </p>

        <div className="w-full max-w-[640px] mb-4">
          <SearchBar variant="hero" />
        </div>
        
        <div className="font-sans text-[11px] md:text-[12px] text-text-muted">
          No account required for a preview. Analyzed 2,400+ public companies.
        </div>
      </section>

      {/* SECTION 3 — Trust Strip */}
      <section className="border-t border-b border-border py-8 md:py-6 px-5 md:px-6">
        <div className="max-w-[1080px] mx-auto flex flex-col md:flex-row items-center justify-center gap-4 md:gap-6">
          <span className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-muted text-center md:text-left">
            SIGNALS IDENTIFIED IN
          </span>
          <div className="font-sans text-[13px] text-text-secondary flex flex-col md:flex-row items-center gap-3 md:gap-3 text-center">
            <span>Enron</span>
            <span className="text-border hidden md:inline">·</span>
            <span>Wirecard</span>
            <span className="text-border hidden md:inline">·</span>
            <span>Satyam Computer Services</span>
            <span className="text-border hidden md:inline">·</span>
            <span>Luckin Coffee</span>
          </div>
        </div>
      </section>

      {/* SECTION 4 — Feature Strip */}
      <section className="py-16 md:py-24 px-0 md:px-6">
        <div className="max-w-[1080px] mx-auto grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-border">
          
          <div className="px-5 md:px-0 md:pr-12 py-8 md:py-0">
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-4">
              FINANCIAL FORENSICS
            </div>
            <h3 className="font-sans text-[17px] font-semibold text-text-primary leading-[1.4] mb-4">
              Revenue growth that doesn’t match cash flow is always the first warning sign.
            </h3>
            <p className="font-sans text-[14px] text-text-secondary leading-[1.7]">
              SentinelIQ tracks the gap between reported earnings and actual cash generation — a disconnect that preceded every major accounting scandal of the past two decades.
            </p>
          </div>

          <div className="px-5 md:px-12 py-8 md:py-0">
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-4">
              NARRATIVE ANALYSIS
            </div>
            <h3 className="font-sans text-[17px] font-semibold text-text-primary leading-[1.4] mb-4">
              Executives who change their story always leave a record.
            </h3>
            <p className="font-sans text-[14px] text-text-secondary leading-[1.7]">
              Our AI cross-references earnings call transcripts quarter by quarter, surfacing contradictions, tone shifts, and the creeping vagueness that appears long before a restatement is filed.
            </p>
          </div>

          <div className="px-5 md:px-0 md:pl-12 py-8 md:py-0">
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-4">
              GOVERNANCE RISK
            </div>
            <h3 className="font-sans text-[17px] font-semibold text-text-primary leading-[1.4] mb-4">
              A CFO resignation is not a routine personnel change.
            </h3>
            <p className="font-sans text-[14px] text-text-secondary leading-[1.7]">
              Unexpected auditor switches, consecutive director departures, and qualified audit opinions are governance signals that precede regulatory action more often than most investors realize.
            </p>
          </div>

        </div>
      </section>

      {/* SECTION 5 — How It Works */}
      <section id="how-it-works" className="py-16 md:py-24 px-5 md:px-6">
        <div className="max-w-[1080px] mx-auto flex flex-col items-center">
          <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-6 text-center">
            HOW IT WORKS
          </div>
          <h2 className="font-sans text-[22px] md:text-[28px] font-semibold text-text-primary text-center max-w-[520px] mb-6">
            Five independent analyses. One Corporate Integrity Score.
          </h2>
          <p className="font-sans text-[14px] md:text-[15px] text-text-secondary text-center max-w-[560px] leading-[1.7] mb-12 md:mb-16">
            Every investigation runs five forensic checks in parallel — financial statement quality, cash flow integrity, earnings behavior, governance risk, and management narrative consistency. Results are weighted and combined into a single score from 0 to 100.
          </p>

          <div className="w-full max-w-[800px]">
            <div className="flex h-[8px] rounded-full overflow-hidden mb-4">
              <div className="w-1/5 bg-risk-severe"></div>
              <div className="w-1/5 bg-risk-high"></div>
              <div className="w-1/5 bg-risk-moderate"></div>
              <div className="w-1/5 bg-navy"></div>
              <div className="w-1/5 bg-risk-strong"></div>
            </div>
            
            {/* Desktop Score Scale */}
            <div className="hidden md:flex justify-between w-full px-2 mb-10 font-mono text-[12px]">
              <div className="w-1/5 text-left text-risk-severe">0–20<br/>SEVERE RISK</div>
              <div className="w-1/5 text-center text-risk-high pr-6">21–40<br/>HIGH RISK</div>
              <div className="w-1/5 text-center text-risk-moderate">41–60<br/>MODERATE RISK</div>
              <div className="w-1/5 text-center text-navy pl-6">61–80<br/>LOW RISK</div>
              <div className="w-1/5 text-right text-risk-strong">81–100<br/>STRONG INTEGRITY</div>
            </div>

            {/* Mobile Score Scale (Initials only) */}
            <div className="flex md:hidden justify-between w-full px-1 mb-8 font-mono text-[10px]">
              <div className="w-1/5 text-left text-risk-severe">0–20<br/>SR</div>
              <div className="w-1/5 text-center text-risk-high">21–40<br/>HR</div>
              <div className="w-1/5 text-center text-risk-moderate">41–60<br/>MR</div>
              <div className="w-1/5 text-center text-navy">61–80<br/>LR</div>
              <div className="w-1/5 text-right text-risk-strong">81–100<br/>SI</div>
            </div>
            
            {/* Mobile Score Legend */}
            <div className="flex md:hidden flex-wrap items-center justify-center gap-x-4 gap-y-2 font-mono text-[10px] mb-10 text-text-secondary">
              <span>SR—Severe Risk</span>
              <span>HR—High Risk</span>
              <span>MR—Moderate Risk</span>
              <span>LR—Low Risk</span>
              <span>SI—Strong Integrity</span>
            </div>

            {/* Module Labels */}
            <div className="flex flex-col md:flex-row flex-wrap items-center justify-center gap-2 md:gap-2 font-sans text-[11px] text-text-muted text-center">
              <span>Financial Quality</span>
              <span className="hidden md:inline">·</span>
              <span>Cash Flow Integrity</span>
              <span className="hidden md:inline">·</span>
              <span>Governance Risk</span>
              <span className="hidden md:inline">·</span>
              <span>Earnings Quality</span>
              <span className="hidden md:inline">·</span>
              <span>Narrative Consistency</span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 6 — Case Studies */}
      <section id="case-studies" className="py-16 md:py-24 px-5 md:px-6 bg-canvas">
        <div className="max-w-[1080px] mx-auto">
          <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-6 text-center md:text-left">
            RETROACTIVE ANALYSIS
          </div>
          <h2 className="font-sans text-[22px] md:text-[24px] font-semibold text-text-primary max-w-[480px] mb-6 text-center md:text-left mx-auto md:mx-0">
            The warning signs were there. Most investors didn’t know where to look.
          </h2>
          <p className="font-sans text-[14px] text-text-secondary max-w-[520px] leading-[1.7] mb-10 md:mb-12 text-center md:text-left mx-auto md:mx-0">
            SentinelIQ’s scoring model has been back-tested against companies where fraud was later confirmed. In each case, warning signals were detectable months or years before public exposure.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-10">
            {/* Tile 1 */}
            <div className="bg-surface border border-border rounded-[8px] p-4 md:p-5 flex flex-col">
              <div className="font-sans text-[14px] font-semibold text-text-primary mb-1">Enron Corporation</div>
              <div className="font-mono text-[12px] text-navy mb-4 md:mb-6">ENE</div>
              <div className="flex items-baseline mb-4">
                <span className="font-mono text-[28px] md:text-[36px] font-bold text-risk-high">28</span>
                <span className="font-sans text-[12px] md:text-[16px] text-text-secondary ml-1">/ 100</span>
              </div>
              <div className="mb-4">
                <Badge risk="high">HIGH RISK</Badge>
              </div>
              <p className="font-sans text-[11px] md:text-[12px] text-text-secondary leading-[1.6]">
                Revenue–cash flow divergence detected 18 months before Chapter 11 filing.
              </p>
            </div>

            {/* Tile 2 */}
            <div className="bg-surface border border-border rounded-[8px] p-4 md:p-5 flex flex-col">
              <div className="font-sans text-[14px] font-semibold text-text-primary mb-1">Wirecard AG</div>
              <div className="font-mono text-[12px] text-navy mb-4 md:mb-6">WDI.DE</div>
              <div className="flex items-baseline mb-4">
                <span className="font-mono text-[28px] md:text-[36px] font-bold text-risk-high">22</span>
                <span className="font-sans text-[12px] md:text-[16px] text-text-secondary ml-1">/ 100</span>
              </div>
              <div className="mb-4">
                <Badge risk="high">HIGH RISK</Badge>
              </div>
              <p className="font-sans text-[11px] md:text-[12px] text-text-secondary leading-[1.6]">
                Receivables anomaly and auditor tension flagged Q3 2018 — 18 months before collapse.
              </p>
            </div>

            {/* Tile 3 */}
            <div className="bg-surface border border-border rounded-[8px] p-4 md:p-5 flex flex-col">
              <div className="font-sans text-[14px] font-semibold text-text-primary mb-1">Satyam Computer Services</div>
              <div className="font-mono text-[12px] text-navy mb-4 md:mb-6">SAY</div>
              <div className="flex items-baseline mb-4">
                <span className="font-mono text-[28px] md:text-[36px] font-bold text-risk-high">31</span>
                <span className="font-sans text-[12px] md:text-[16px] text-text-secondary ml-1">/ 100</span>
              </div>
              <div className="mb-4">
                <Badge risk="high">HIGH RISK</Badge>
              </div>
              <p className="font-sans text-[11px] md:text-[12px] text-text-secondary leading-[1.6]">
                Cash balance inconsistencies and governance deterioration across 4 quarters.
              </p>
            </div>

            {/* Tile 4 */}
            <div className="bg-surface border border-border rounded-[8px] p-4 md:p-5 flex flex-col">
              <div className="font-sans text-[14px] font-semibold text-text-primary mb-1">Luckin Coffee Inc.</div>
              <div className="font-mono text-[12px] text-navy mb-4 md:mb-6">LK</div>
              <div className="flex items-baseline mb-4">
                <span className="font-mono text-[28px] md:text-[36px] font-bold text-risk-severe">19</span>
                <span className="font-sans text-[12px] md:text-[16px] text-text-secondary ml-1">/ 100</span>
              </div>
              <div className="mb-4">
                <Badge risk="severe">SEVERE RISK</Badge>
              </div>
              <p className="font-sans text-[11px] md:text-[12px] text-text-secondary leading-[1.6]">
                Negative free cash flow for 3 consecutive quarters despite reported revenue acceleration.
              </p>
            </div>
          </div>

          <p className="font-sans text-[11px] text-text-muted text-center italic">
            Scores are retroactive estimates based on publicly available data at the time. Not investment advice.
          </p>
        </div>
      </section>

      {/* SECTION 7 — Second CTA */}
      <section className="bg-surface border-t border-b border-border py-16 md:py-24 px-5 md:px-6">
        <div className="max-w-[720px] mx-auto flex flex-col items-center text-center">
          <h2 className="font-sans text-[22px] md:text-[28px] font-semibold text-text-primary mb-4 md:mb-6">
            Start with any company.
          </h2>
          <p className="font-sans text-[14px] md:text-[15px] text-text-secondary max-w-[440px] leading-[1.65] mb-8 md:mb-10">
            Enter a stock ticker or company name to see the Corporate Integrity Score and key risk signals. No account required.
          </p>
          <div className="w-full max-w-[640px]">
            <SearchBar variant="hero" />
          </div>
        </div>
      </section>

    </div>
  )
}
