import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Terms of Service — SentinelIQ",
  description: "Terms of service for SentinelIQ corporate integrity screening platform.",
}

export default function TermsPage() {
  return (
    <div className="w-full bg-canvas min-h-screen">
      <div className="max-w-[720px] mx-auto px-5 md:px-6 py-16 md:py-24">

        <div className="font-sans text-[10px] uppercase tracking-[0.1em] text-text-muted mb-4">
          LEGAL
        </div>
        <h1 className="font-sans text-[28px] md:text-[36px] font-semibold text-text-primary leading-[1.2] mb-3">
          Terms of Service
        </h1>
        <p className="font-sans text-[13px] text-text-muted mb-12">
          Effective date: June 2026
        </p>

        <div className="flex flex-col gap-10 font-sans text-[14px] text-text-primary leading-[1.7]">

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              1. WHAT SENTINELIQ IS
            </div>
            <p className="text-text-secondary">
              SentinelIQ is an automated corporate integrity screening platform. It analyzes
              publicly available financial data, governance information, and news coverage to
              compute an algorithmic Corporate Integrity Score for publicly listed companies.
              The platform is designed for equity analysts, independent investors, auditors,
              and risk officers who use it as one input among many in their own professional
              research workflows.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              2. NOT INVESTMENT ADVICE
            </div>
            <p className="text-text-secondary mb-4">
              SentinelIQ does not provide investment advice, financial advice, legal advice,
              or any other professional advice. Nothing on this platform should be construed
              as a recommendation to buy, sell, hold, or otherwise transact in any security
              or financial instrument.
            </p>
            <p className="text-text-secondary">
              Integrity Scores, forensic module outputs, red flags, and AI-generated reports
              are algorithmic screening signals produced from automated analysis of public
              data. They represent statistical patterns and do not reflect the views of any
              licensed financial advisor, auditor, or legal professional. Always conduct your
              own due diligence and consult qualified professionals before making any
              investment decision.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              3. NOT AN ACCUSATION
            </div>
            <p className="text-text-secondary">
              A low Integrity Score, a red flag, or any other output from SentinelIQ is
              not an accusation of wrongdoing, fraud, or any other illegal or improper
              conduct. These outputs indicate that automated screening detected statistical
              patterns consistent with elevated risk — they do not constitute proof, evidence,
              or a finding of any kind. Companies flagged by this system may have entirely
              legitimate explanations for the patterns detected. SentinelIQ makes no claim
              that any specific company has engaged in fraud or misconduct.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              4. DATA SOURCES AND ACCURACY
            </div>
            <p className="text-text-secondary mb-4">
              Financial data is sourced from Yahoo Finance via the open-source yfinance
              library. Yahoo Finance data may include restated figures, delayed updates, or
              inaccuracies. SentinelIQ makes no warranty as to the completeness, accuracy,
              or timeliness of underlying financial data.
            </p>
            <p className="text-text-secondary mb-4">
              Governance and narrative analysis is powered by Google Gemini, a large language
              model. AI-generated outputs may contain errors, omissions, or hallucinations.
              News coverage is sourced from RSS feeds and may not represent the full universe
              of relevant information.
            </p>
            <p className="text-text-secondary">
              By using SentinelIQ, you acknowledge that all outputs carry inherent uncertainty
              and should be independently verified before being relied upon.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              5. PERMITTED USE
            </div>
            <p className="text-text-secondary mb-4">
              You may use SentinelIQ outputs for your own internal research and analysis.
              You may not reproduce, redistribute, publish, or incorporate SentinelIQ outputs
              (including Integrity Scores, red flags, or AI-generated reports) into any
              product, publication, or financial research distributed to third parties without
              independent verification of the underlying claims.
            </p>
            <p className="text-text-secondary">
              You may not use SentinelIQ to make automated trading decisions, as a component
              of any algorithmic trading system, or as the sole basis for any significant
              financial action.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              6. FREE TIER LIMITS
            </div>
            <p className="text-text-secondary">
              Free accounts are limited to 5 fresh analyses per calendar month. Cached
              results from previous analyses do not count against this limit and may be
              accessed without restriction.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              7. LIMITATION OF LIABILITY
            </div>
            <p className="text-text-secondary">
              SentinelIQ is provided on an &quot;as is&quot; basis without warranties of any kind,
              express or implied. To the maximum extent permitted by applicable law,
              SentinelIQ and its operators shall not be liable for any direct, indirect,
              incidental, consequential, or punitive damages arising from your use of or
              reliance on this platform, including any investment losses or business
              decisions made based on platform outputs.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              8. CHANGES TO THESE TERMS
            </div>
            <p className="text-text-secondary">
              These terms may be updated from time to time. Continued use of SentinelIQ
              after any revision constitutes acceptance of the updated terms. The effective
              date at the top of this page will reflect the most recent revision.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              9. CONTACT
            </div>
            <p className="text-text-secondary">
              Questions about these terms or the platform can be directed to the team
              via the feedback mechanism available within the application.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
