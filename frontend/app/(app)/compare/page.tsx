"use client";

import Link from "next/link"
import { Suspense, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Badge } from "@/components/ui/Badge"
import { Skeleton } from "@/components/ui/Skeleton"
import { compareAnalyses } from "@/lib/api/analysis"
import { getRiskLevel, getRiskLabel } from "@/lib/utils/riskLabel"
import { getScoreColor } from "@/lib/utils/scoreColor"
import { formatScore } from "@/lib/utils/formatNumber"
import { ROUTES } from "@/lib/constants/routes"
import { ApiError } from "@/types/api"
import type { CompareItem } from "@/types/analysis"

// Mirrors the COMPONENT_SCORES list on the Company Overview page, plus
// integrity_score and confidence as their own rows -- Phase 37 (F5) is
// read-only over data those pages already render one company at a time.
const SCORE_ROWS: { key: keyof NonNullable<CompareItem["analysis"]>; label: string }[] = [
  { key: "financial_score", label: "Financial Quality" },
  { key: "cashflow_score", label: "Cash Flow Integrity" },
  { key: "governance_score", label: "Governance Risk" },
  { key: "earnings_score", label: "Earnings Quality" },
  { key: "narrative_score", label: "News Tone (experimental)" },
  { key: "news_score", label: "News Sentiment" },
]

function CompareResults() {
  const params = useSearchParams()
  const tickers = (params.get("tickers") || "").split(",").map((t) => t.trim()).filter(Boolean)

  const [items, setItems] = useState<CompareItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (tickers.length < 2) {
      setIsLoading(false)
      return
    }
    let cancelled = false
    setIsLoading(true)
    setError(null)
    compareAnalyses(tickers)
      .then((data) => {
        if (!cancelled) setItems(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load the comparison. Please try again.")
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.toString()])

  if (tickers.length < 2) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center min-h-[200px]">
        <div className="font-sans text-[15px] text-[#7A786F] mb-2">Select at least 2 companies to compare.</div>
        <Link href={ROUTES.watchlist} className="font-sans text-[13px] text-[#1C3558] hover:underline">
          Go to Watchlist →
        </Link>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <div key={i} className={`flex items-center px-4 h-[52px] ${i !== 5 ? "border-b border-[#E3DFD8]" : ""}`}>
            <Skeleton className="w-[20%] h-[16px] mr-4" />
            <Skeleton className="w-[20%] h-[16px] mr-4" />
            <Skeleton className="w-[20%] h-[16px] mr-4" />
            <Skeleton className="w-[20%] h-[16px]" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
        <div className="font-sans text-[14px] text-[#B03028]">{error}</div>
      </div>
    )
  }

  return (
    <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-x-auto">
      <table className="w-full text-left border-collapse min-w-[600px]">
        <thead>
          <tr className="border-b border-[#E3DFD8]">
            <th className="py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F] sticky left-0 bg-[#FFFFFF]"></th>
            {items.map((item) => (
              <th key={item.ticker} className="py-3 px-4 text-left min-w-[160px]">
                {item.found ? (
                  <Link href={ROUTES.company(item.ticker)} className="font-sans text-[14px] font-semibold text-[#1A1A18] hover:underline">
                    {item.company_name ?? item.ticker}
                  </Link>
                ) : (
                  <span className="font-sans text-[14px] font-semibold text-[#B0ADA7]">{item.ticker}</span>
                )}
                <div className="font-mono text-[11px] text-[#1C3558] mt-0.5">{item.ticker}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-[#E3DFD8] bg-[#F6F4EF]">
            <td className="py-3 px-4 font-sans text-[11px] font-medium uppercase tracking-[0.06em] text-[#7A786F] sticky left-0 bg-[#F6F4EF]">
              Integrity Score
            </td>
            {items.map((item) => {
              const score = item.analysis?.integrity_score ?? null
              return (
                <td key={item.ticker} className="py-3 px-4">
                  {!item.found ? (
                    <span className="font-sans text-[12px] text-[#B0ADA7]">Unknown ticker</span>
                  ) : !item.analysis ? (
                    <Link href={ROUTES.company(item.ticker)} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      Not yet analyzed →
                    </Link>
                  ) : (
                    <div className="flex flex-col gap-1">
                      <span className="font-mono text-[18px] font-bold" style={{ color: score !== null ? getScoreColor(score) : "#B0ADA7" }}>
                        {formatScore(score)}
                      </span>
                      {score !== null && <Badge risk={getRiskLevel(score)}>{getRiskLabel(score)}</Badge>}
                    </div>
                  )}
                </td>
              )
            })}
          </tr>

          {SCORE_ROWS.map((row) => (
            <tr key={row.key} className="border-b border-[#E3DFD8]">
              <td className="py-3 px-4 font-sans text-[12px] text-[#7A786F] sticky left-0 bg-[#FFFFFF]">{row.label}</td>
              {items.map((item) => {
                const score = item.analysis ? (item.analysis[row.key] as number | null) : null
                return (
                  <td key={item.ticker} className="py-3 px-4 font-mono text-[14px]">
                    {score !== null ? (
                      <span style={{ color: getScoreColor(score) }}>{formatScore(score)}</span>
                    ) : (
                      <span className="text-[#B0ADA7]">—</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}

          <tr className="border-b border-[#E3DFD8]">
            <td className="py-3 px-4 font-sans text-[12px] text-[#7A786F] sticky left-0 bg-[#FFFFFF]">Confidence</td>
            {items.map((item) => (
              <td key={item.ticker} className="py-3 px-4 font-sans text-[12px] uppercase tracking-[0.04em] text-[#1A1A18]">
                {item.analysis?.module_details?.confidence ?? "—"}
              </td>
            ))}
          </tr>

          <tr>
            <td className="py-3 px-4 font-sans text-[12px] text-[#7A786F] sticky left-0 bg-[#FFFFFF]">Red Flags</td>
            {items.map((item) => (
              <td key={item.ticker} className="py-3 px-4 font-mono text-[14px]">
                {item.analysis ? (
                  <span className={item.red_flag_count > 0 ? "text-[#B03028]" : "text-[#1A6B3C]"}>
                    {item.red_flag_count}
                  </span>
                ) : (
                  <span className="text-[#B0ADA7]">—</span>
                )}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  )
}

export default function ComparePage() {
  return (
    <div className="w-full max-w-[1200px]">
      <div className="mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18] mb-1">Compare Companies</h1>
        <p className="font-sans text-[13px] text-[#7A786F]">
          Side-by-side Integrity Scores from each company&apos;s most recent completed analysis.
        </p>
      </div>
      <Suspense
        fallback={
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 min-h-[200px]">
            <Skeleton className="w-full h-[160px]" />
          </div>
        }
      >
        <CompareResults />
      </Suspense>
    </div>
  )
}
