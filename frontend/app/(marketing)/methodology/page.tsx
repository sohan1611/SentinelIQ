import type { Metadata } from "next"
import Link from "next/link"

export const metadata: Metadata = {
  title: "Scoring Methodology — SentinelIQ",
  description: "How SentinelIQ computes the Corporate Integrity Score — formulas, weights, and confidence tiers explained.",
}

export default function MethodologyPage() {
  return (
    <div className="w-full bg-canvas min-h-screen">
      <div className="max-w-[720px] mx-auto px-5 md:px-6 py-16 md:py-24">

        <div className="font-sans text-[10px] uppercase tracking-[0.1em] text-text-muted mb-4">
          METHODOLOGY
        </div>
        <h1 className="font-sans text-[28px] md:text-[36px] font-semibold text-text-primary leading-[1.2] mb-3">
          Scoring Methodology
        </h1>
        <p className="font-sans text-[13px] text-text-muted mb-4">
          How the Corporate Integrity Score is calculated — every formula, weight, and
          confidence tier. Formulas are taken directly from the live implementation.
        </p>
        <p className="font-sans text-[13px] text-text-muted mb-12">
          For where the underlying data comes from and its limitations, see{" "}
          <Link href="/data-sources" className="text-[#1C3558] hover:underline">
            Data Sources
          </Link>.
        </p>

        <div className="flex flex-col gap-10 font-sans text-[14px] text-text-primary leading-[1.7]">

          {/* 1 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              1. THE BIG PICTURE
            </div>
            <p className="text-text-secondary mb-4">
              Each analysis produces six module scores (0–100, higher = healthier). Five are
              blended into the headline Corporate Integrity Score. One — Narrative Consistency
              — is computed and displayed but currently carries zero weight (see section 7).
            </p>
            <div className="border border-border rounded-[6px] overflow-hidden mb-4">
              <table className="w-full font-sans text-[13px]">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Module</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">In Integrity Score?</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Financial Quality", "Yes"],
                    ["Cash Flow Integrity", "Yes"],
                    ["Governance Risk", "Yes"],
                    ["Earnings Quality", "Yes"],
                    ["News Sentiment", "Yes"],
                    ["Narrative Consistency (experimental)", "No"],
                  ].map(([module, included], i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 text-text-primary">{module}</td>
                      <td className={`px-4 py-3 font-medium ${included === "Yes" ? "text-[#1A6B3C]" : "text-[#B0ADA7]"}`}>{included}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-text-secondary">
              The Integrity Score maps to a risk label:
              100–81 = Strong Integrity · 80–61 = Low Risk · 60–41 = Moderate Risk · 40–21 = High Risk · 20–0 = Severe Risk.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 2 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              2. WEIGHT VECTOR
            </div>
            <p className="text-text-secondary mb-4">
              The five scored modules are weighted as follows. These are the original weights
              (summing to 0.90 with narrative included) renormalized by ×(1/0.9) so the
              active five sum exactly to 1.0.
            </p>
            <div className="border border-border rounded-[6px] overflow-hidden mb-4">
              <table className="w-full font-sans text-[13px]">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Module</th>
                    <th className="px-4 py-3 text-right font-medium text-text-secondary text-[11px] uppercase tracking-[0.06em]">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Financial Quality", "33.3%"],
                    ["Cash Flow Integrity", "22.2%"],
                    ["Governance Risk", "16.7%"],
                    ["Earnings Quality", "16.7%"],
                    ["News Sentiment", "11.1%"],
                  ].map(([module, weight], i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 text-text-primary">{module}</td>
                      <td className="px-4 py-3 text-right font-mono text-text-primary">{weight}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 3 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              3. RENORMALIZATION — ABSENCE IS NOT NEUTRAL
            </div>
            <p className="text-text-secondary mb-4">
              If a module's pipeline stage fails to produce a real score (network failure,
              zero financial periods, AI timeout), that module is excluded from{" "}
              <em>both</em> the numerator and the denominator. The remaining modules'
              weights are rescaled to sum to 1.0 among themselves — the score reflects only
              what was actually measured.
            </p>
            <p className="text-text-secondary">
              A module that legitimately computes exactly 50 from real data is still
              included and weighted normally. Only <code className="font-mono text-[13px] bg-[#F0EDE8] px-1 rounded">null</code>/missing
              triggers exclusion. This is produced upstream in the analysis pipeline,
              not inferred inside the scoring formula.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 4 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              4. CONFIDENCE TIER
            </div>
            <p className="text-text-secondary mb-4">
              Each analysis carries a confidence tier shown on the Overview tab:
            </p>
            <div className="flex flex-col gap-2">
              {[
                ["High", "All 5 modules scored AND 3+ years of financial history"],
                ["Medium", "3–4 modules scored, or fewer than 3 years of history"],
                ["Low", "2 or fewer modules produced real signal"],
              ].map(([tier, desc]) => (
                <div key={tier} className="flex items-start gap-3">
                  <span className="font-mono text-[13px] text-[#1C3558] w-16 shrink-0">{tier}</span>
                  <span className="font-sans text-[13px] text-text-secondary">{desc}</span>
                </div>
              ))}
            </div>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 5 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              5. FORENSIC MODULES (DETERMINISTIC)
            </div>
            <p className="text-text-secondary mb-6">
              Four modules derive scores from annual financial statement data using
              deterministic formulas — no AI. All operate on consecutive period pairs sorted
              by date. Periods with missing required fields are skipped; a module with zero
              valid periods returns 50 (neutral baseline).
            </p>

            <div className="flex flex-col gap-6">
              <div>
                <p className="font-medium text-text-primary mb-2">5a. Revenue Quality (blended into Financial Quality)</p>
                <p className="text-text-secondary text-[13px] mb-2">
                  Per consecutive period pair: <code className="font-mono bg-[#F0EDE8] px-1 rounded">divergence = revenue_growth − operating_CF_growth</code> and{" "}
                  <code className="font-mono bg-[#F0EDE8] px-1 rounded">recv_ratio = accounts_receivable / revenue</code>.
                  Starting from 100: −15 if divergence &gt; 0.15; −25 more if divergence &gt; 0.30;
                  −10 if recv_ratio increases by more than 0.10. Red flags at 2+ consecutive high divergences (HIGH)
                  or 3+ consecutive receivables increases (MODERATE).
                </p>
              </div>

              <div>
                <p className="font-medium text-text-primary mb-2">5b. Cash Flow Integrity</p>
                <p className="text-text-secondary text-[13px] mb-2">
                  Sloan Accrual Ratio per period:{" "}
                  <code className="font-mono bg-[#F0EDE8] px-1 rounded">(net_income − operating_CF) / total_assets</code>.
                  Score per period: ≥0.15 → 20, ≥0.10 → 45, ≥0.05 → 70, otherwise 100. Module score = average
                  across all valid periods. SEVERE flag when net income is positive but operating cash flow is
                  negative in the same period.
                </p>
              </div>

              <div>
                <p className="font-medium text-text-primary mb-2">5c. Earnings Quality</p>
                <p className="text-text-secondary text-[13px] mb-2">
                  Starting from 100: −20 if gross margin changes by more than 8 percentage points in any period.
                  If 2+ net income growth rates exist, compute coefficient of variation; −25 if CV &gt; 1.5
                  (highly erratic earnings). HIGH flag if earnings spike &gt;50% with revenue growth ≤10%.
                </p>
              </div>

              <div>
                <p className="font-medium text-text-primary mb-2">5d. Debt Stress (blended into Financial Quality)</p>
                <p className="text-text-secondary text-[13px]">
                  Starting from 100 per period: −20 if debt-to-revenue &gt; 1.0; −20 more if &gt; 2.0;
                  −15 if debt grows &gt;30% YoY; −20 if interest coverage (operating CF / (debt × 5%)) &lt; 2.0.
                  Financial Quality = (Revenue Quality + Debt Stress) / 2.
                </p>
              </div>
            </div>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 6 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              6. AI-SCORED MODULES (GEMINI 2.5 FLASH, temperature=0)
            </div>
            <p className="text-text-secondary mb-4">
              Two modules use Google Gemini. Both run at temperature=0 with a pinned model
              version. The exact prompt and raw response are persisted per analysis for
              auditability. Each call has a 30-second timeout; a per-process daily cap of 200
              requests guards against runaway loops.
            </p>

            <div className="flex flex-col gap-4">
              <div>
                <p className="font-medium text-text-primary mb-2">6a. Governance Risk</p>
                <p className="text-text-secondary text-[13px] mb-2">
                  Gemini extracts governance events (leadership changes, auditor transitions,
                  regulatory actions) from recent news text. Every event must include a
                  verbatim <em>source quote</em> from the input text — events that fail this
                  grounding check are dropped before scoring to prevent fabricated findings.
                  Deductions: moderate event −15, high −25, severe −35. Returns 50 with a
                  low-confidence marker if news text is under 40 characters or if the API call
                  fails. Returns 100 (clean, not low-confidence) if the API succeeds but finds
                  zero events.
                </p>
              </div>

              <div>
                <p className="font-medium text-text-primary mb-2">6b. News Sentiment</p>
                <p className="text-text-secondary text-[13px]">
                  Keyword-based (not AI): positive words (+1 each) vs. negative words (−1 each)
                  across up to 20 recent headlines from three RSS feeds. Raw average is clamped
                  to [−1, 1] then mapped to [0, 100]. Falls back to 50 if no headlines are found.
                </p>
              </div>
            </div>
          </section>

          <div className="w-full h-[1px] bg-border" />

          {/* 7 */}
          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              7. WHY NARRATIVE IS EXCLUDED
            </div>
            <p className="text-text-secondary">
              Narrative Consistency is computed and shown on the Narrative tab, but carries
              zero weight in the Integrity Score. The current pipeline derives "statements"
              from news headlines, not from management's own earnings-call or filing language.
              It measures press-coverage tone consistency — a real but different signal than
              management narrative consistency. Until a transcript pipeline exists, it is
              labeled "experimental" and excluded from weighting rather than diluting the
              score with a potentially misleading signal.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
