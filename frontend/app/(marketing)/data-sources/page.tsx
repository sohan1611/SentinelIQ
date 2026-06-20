import type { Metadata } from "next"
import Link from "next/link"

export const metadata: Metadata = {
  title: "Data Sources — SentinelIQ",
  description: "Where SentinelIQ's data comes from, what it means, and what it cannot tell you.",
}

export default function DataSourcesPage() {
  return (
    <div className="w-full bg-canvas min-h-screen">
      <div className="max-w-[720px] mx-auto px-5 md:px-6 py-16 md:py-24">

        <div className="font-sans text-[10px] uppercase tracking-[0.1em] text-text-muted mb-4">
          METHODOLOGY
        </div>
        <h1 className="font-sans text-[28px] md:text-[36px] font-semibold text-text-primary leading-[1.2] mb-3">
          Data Sources
        </h1>
        <p className="font-sans text-[13px] text-text-muted mb-4">
          Where every input to the Corporate Integrity Score comes from, and what that
          implies for the signals it produces. We state limitations plainly — the score
          is only as honest as the data beneath it.
        </p>
        <p className="font-sans text-[13px] text-text-muted mb-12">
          For how the score is calculated from these inputs, see{" "}
          <Link href="/methodology" className="text-[#1C3558] hover:underline">
            Scoring Methodology
          </Link>.
        </p>

        <div className="flex flex-col gap-10 font-sans text-[14px] text-text-primary leading-[1.7]">

          {/* 1 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              1. FINANCIAL STATEMENTS — YAHOO FINANCE (VIA YFINANCE)
            </div>
            <p className="text-text-secondary mb-4">
              Annual financial statement data is fetched from Yahoo Finance using the
              open-source yfinance library. Fields collected: revenue, net income,
              operating cash flow, free cash flow, total debt, total assets, accounts
              receivable, and gross margin. Data is cached for 12 hours.
            </p>

            <div className="bg-[#FDF2DC] border border-[#C47A14] rounded-[6px] px-4 py-3 mb-4">
              <p className="font-sans text-[13px] font-medium text-[#C47A14] mb-1">
                Critical limitation: restated, not as-filed
              </p>
              <p className="font-sans text-[13px] text-text-secondary">
                Yahoo Finance serves the <em>current, restated</em> view of a company&apos;s
                financial history — not the figures as originally filed with the SEC.
                When a company restates a prior period, Yahoo&apos;s historical series updates
                retroactively. SentinelIQ has no access to point-in-time, as-filed figures.
              </p>
            </div>

            <p className="text-text-secondary">
              This matters specifically for fraud forensics: a restatement is itself one of
              the strongest fraud signals that exists — it is an admission that previously
              published numbers were wrong. If a company&apos;s aggressive original figures were
              later corrected, the divergence patterns that would have flagged the original
              manipulation may no longer be visible in the restated data. Read forensic scores
              as: <em>&quot;Does this company&apos;s financial history, as Yahoo Finance reports it today,
              show signs of aggressive accounting?&quot;</em> — not as a verdict on originally-filed
              figures.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 2 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              2. NEWS DATA — RSS FEEDS (GOOGLE NEWS, YAHOO FINANCE, REUTERS)
            </div>
            <p className="text-text-secondary mb-4">
              News data is fetched from public RSS feeds using the open-source feedparser
              library — no paid news API. Three distinct pipelines use news for different
              purposes:
            </p>
            <div className="border border-border rounded-[6px] overflow-hidden mb-4">
              <table className="w-full font-sans text-[13px]">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Purpose</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Cache</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Governance event extraction (fed to Gemini)", "Not cached"],
                    ["News Sentiment scoring (keyword analysis)", "2 hours"],
                    ["Narrative Consistency (tone analysis)", "2 hours"],
                  ].map(([purpose, cache], i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 text-text-secondary">{purpose}</td>
                      <td className="px-4 py-3 font-mono text-[12px] text-text-secondary">{cache}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="bg-[#FDF2DC] border border-[#C47A14] rounded-[6px] px-4 py-3">
              <p className="font-sans text-[13px] font-medium text-[#C47A14] mb-1">
                Headlines, not transcripts
              </p>
              <p className="font-sans text-[13px] text-text-secondary">
                Everything SentinelIQ calls &quot;governance evidence&quot; or &quot;narrative&quot; is derived
                from news headlines — not from earnings call transcripts, management prepared
                remarks, or SEC filings (10-K/10-Q MD&A, proxy statements). Governance scoring
                evaluates what journalists reported; narrative measures press-coverage tone
                consistency. These are real signals, but different ones than management
                narrative analysis would produce. This is why Narrative Consistency is
                labeled &quot;experimental&quot; and carries zero weight in the Integrity Score.
              </p>
            </div>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 3 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              3. AI ANALYSIS — GOOGLE GEMINI 2.5 FLASH
            </div>
            <p className="text-text-secondary mb-4">
              Two modules — Governance Risk and Narrative Consistency — use Google Gemini
              2.5 Flash (free tier). Both run at temperature=0 with a pinned model version
              for reproducibility. The exact prompt and raw API response are persisted per
              analysis, so every AI-influenced score can be traced back to its exact inputs.
            </p>
            <p className="text-text-secondary mb-4">
              For governance events specifically: every event Gemini extracts must include a
              verbatim source quote from the input news text. Events that fail this grounding
              check are dropped before scoring — this prevents fabricated governance findings
              from becoming persisted risk labels on real companies.
            </p>
            <p className="text-text-secondary">
              Each Gemini call has a 30-second timeout. A per-process daily cap of 200
              requests (well below Gemini&apos;s 1,500/day free limit) guards against runaway
              loops. When the cap is reached or a call times out, the affected module
              returns a neutral score and the analysis continues normally.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 4 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              4. WHAT SENTINELIQ DOES NOT USE
            </div>
            <p className="text-text-secondary mb-4">
              To set expectations explicitly, the following are not part of the current pipeline:
            </p>
            <ul className="flex flex-col gap-2 text-text-secondary">
              {[
                "SEC EDGAR / as-filed point-in-time regulatory filings",
                "Earnings call or investor-day transcripts",
                "Any paid or real-time financial data provider",
                "Insider trading / Form 4 data",
                "Social media or analyst-estimate data",
                "Alternative data (satellite imagery, credit card data, web traffic)",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-[#B0ADA7] mt-[2px]">—</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 5 — summary table */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              5. SUMMARY
            </div>
            <div className="border border-border rounded-[6px] overflow-hidden">
              <table className="w-full font-sans text-[13px]">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Data</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Source</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Point-in-time?</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Financial statements", "yfinance (Yahoo Finance)", "No — restated"],
                    ["News headlines", "Google News / Yahoo Finance / Reuters RSS", "Yes (publish date)"],
                    ["AI extraction", "Google Gemini 2.5 Flash", "N/A"],
                  ].map(([data, source, pit], i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 text-text-primary">{data}</td>
                      <td className="px-4 py-3 text-text-secondary">{source}</td>
                      <td className={`px-4 py-3 font-mono text-[12px] ${pit.startsWith("No") ? "text-[#C47A14]" : "text-text-secondary"}`}>{pit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

        </div>
      </div>
    </div>
  )
}
