import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Privacy Policy — SentinelIQ",
  description: "Privacy policy for SentinelIQ corporate integrity screening platform.",
}

export default function PrivacyPage() {
  return (
    <div className="w-full bg-canvas min-h-screen">
      <div className="max-w-[720px] mx-auto px-5 md:px-6 py-16 md:py-24">

        <div className="font-sans text-[10px] uppercase tracking-[0.1em] text-text-muted mb-4">
          LEGAL
        </div>
        <h1 className="font-sans text-[28px] md:text-[36px] font-semibold text-text-primary leading-[1.2] mb-3">
          Privacy Policy
        </h1>
        <p className="font-sans text-[13px] text-text-muted mb-12">
          Effective date: June 2026
        </p>

        <div className="flex flex-col gap-10 font-sans text-[14px] text-text-primary leading-[1.7]">

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              1. OVERVIEW
            </div>
            <p className="text-text-secondary">
              SentinelIQ collects only the minimum data necessary to provide the service.
              We do not sell your data, run advertising, or share your information with
              third parties except as required to operate the platform. This policy
              describes what we collect, why, and how long we keep it.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              2. WHAT WE COLLECT
            </div>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">Account information.</span>{" "}
              When you register, we collect your email address, a display name, and a
              hashed password. We never store your password in plain text.
            </p>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">Analysis history.</span>{" "}
              We record which companies you have analyzed, the resulting scores, red flags,
              and generated reports. This data is associated with your account and is used
              to enforce the free-tier usage limit (5 fresh analyses per calendar month)
              and to let you revisit past results.
            </p>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">Watchlist.</span>{" "}
              If you add companies to your watchlist, we store that list under your account.
            </p>
            <p className="text-text-secondary">
              <span className="font-medium text-text-primary">Error feedback.</span>{" "}
              If you submit a flag issue report via the &quot;Report an issue&quot; feature, we log
              the analysis ID, the flag ID, and the message you wrote. This is stored in
              server logs and is not attached to a permanent database record.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              3. WHAT WE DO NOT COLLECT
            </div>
            <p className="text-text-secondary mb-4">
              We do not run third-party analytics (no Google Analytics, no Meta Pixel,
              no tracking cookies). We do not collect IP addresses beyond what is incidentally
              captured in server access logs (which rotate automatically). We do not collect
              payment information — there is currently no paid tier.
            </p>
            <p className="text-text-secondary">
              We do not use cookies beyond the JWT session token required to authenticate
              your requests. There are no tracking, advertising, or preference cookies.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              4. THIRD-PARTY SERVICES
            </div>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">Google Gemini.</span>{" "}
              Governance and narrative analysis sends news text to Google&apos;s Gemini API.
              This means excerpts of recent news coverage about a company you analyze are
              transmitted to Google. We do not send your personal information or account
              details to Google. Google&apos;s data use is governed by its API terms of service.
            </p>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">Yahoo Finance (via yfinance).</span>{" "}
              Financial data is fetched from Yahoo Finance using the open-source yfinance
              library. Ticker lookups are transmitted to Yahoo. No personal data is shared.
            </p>
            <p className="text-text-secondary mb-4">
              <span className="font-medium text-text-primary">RSS news feeds.</span>{" "}
              News headlines are fetched from public RSS feeds (Google News). No personal
              data is included in these requests.
            </p>
            <p className="text-text-secondary">
              <span className="font-medium text-text-primary">Infrastructure.</span>{" "}
              The backend runs on Render and the frontend runs on Vercel. Both providers
              may retain server access logs. Their respective privacy policies apply to
              infrastructure-level data.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              5. DATA RETENTION
            </div>
            <p className="text-text-secondary mb-4">
              Analysis results and associated red flags and reports are retained
              indefinitely to support the trend history feature (which lets you see how a
              company&apos;s Integrity Score changes over time across multiple runs). Watchlist
              data is retained until you remove items or delete your account.
            </p>
            <p className="text-text-secondary">
              In-memory caches (financial data, news) expire automatically after 2–24 hours
              and are not persisted to the database.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              6. YOUR RIGHTS
            </div>
            <p className="text-text-secondary">
              You may request deletion of your account and associated data at any time by
              contacting us through the feedback mechanism in the application. We will
              process deletion requests within 30 days. Analysis results that do not
              contain personally identifiable information may be retained in aggregate
              or anonymized form.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              7. SECURITY
            </div>
            <p className="text-text-secondary">
              Passwords are stored as bcrypt hashes. Authentication uses short-lived JWT
              tokens. All data in transit is encrypted via TLS. We apply rate limiting on
              authentication and analysis endpoints to reduce abuse risk. No security
              measure is perfect — if you discover a vulnerability, please report it
              through the feedback mechanism.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              8. CHANGES TO THIS POLICY
            </div>
            <p className="text-text-secondary">
              This policy may be updated from time to time. The effective date above
              reflects the most recent revision. Material changes will be noted here.
              Continued use of SentinelIQ after a policy update constitutes acceptance
              of the revised terms.
            </p>
          </section>

          <div className="w-full h-[1px] bg-border" />

          <section>
            <div className="font-sans text-[10px] uppercase tracking-[0.08em] text-text-secondary mb-3">
              9. CONTACT
            </div>
            <p className="text-text-secondary">
              Questions about this privacy policy can be directed to the team via the
              feedback mechanism available within the application.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
