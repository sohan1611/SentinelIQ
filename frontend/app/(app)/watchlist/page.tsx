"use client";

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Skeleton } from "@/components/ui/Skeleton"
import { CompanyCard } from "@/components/shared/CompanyCard"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { getRiskLevel, getRiskLabel } from "@/lib/utils/riskLabel"
import { getScoreColor } from "@/lib/utils/scoreColor"
import { formatScore } from "@/lib/utils/formatNumber"
import { formatRelativeTime } from "@/lib/utils/formatDate"
import { ROUTES } from "@/lib/constants/routes"
import { ApiError } from "@/types/api"
import { useToast } from "@/contexts/ToastContext"

export default function WatchlistPage() {
  const router = useRouter()
  const { items, isLoading, error, remove } = useWatchlist()
  const { showToast } = useToast()
  const [removeError, setRemoveError] = useState<string | null>(null)

  const handleRemove = async (ticker: string, name: string) => {
    if (!window.confirm(`Remove ${name} from your watchlist?`)) return
    setRemoveError(null)
    try {
      await remove(ticker)
      showToast(`Removed ${name} from watchlist`, "info")
    } catch (err) {
      setRemoveError(err instanceof ApiError ? err.message : "Failed to remove company. Please try again.")
    }
  }

  return (
    <div className="w-full max-w-[1200px]">

      {/* Page Heading Row */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18]">Watchlist</h1>
        <Button variant="secondary" className="!text-[13px]" onClick={() => router.push(ROUTES.search)}>
          Add company +
        </Button>
      </div>

      {removeError && (
        <div className="mb-4 font-sans text-[13px] text-[#B03028]">{removeError}</div>
      )}

      {isLoading ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`flex items-center px-4 h-[52px] ${i !== 5 ? "border-b border-[#E3DFD8]" : ""}`}>
              <Skeleton className="w-[30%] h-[16px] mr-4" />
              <Skeleton className="w-[10%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[24px] rounded-full mr-4" />
              <Skeleton className="w-[15%] h-[16px]" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-[14px] text-[#B03028] mb-1">Couldn't load your watchlist.</div>
          <div className="font-sans text-[12px] text-[#7A786F]">{error}</div>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-[14px] text-[#1A1A18] mb-1">Your watchlist is empty.</div>
          <div className="font-sans text-[13px] text-[#7A786F] mb-4">Search for a company to run its first integrity analysis.</div>
          <Link href={ROUTES.search} className="font-sans text-[13px] text-[#1C3558] hover:underline">
            Investigate a company →
          </Link>
        </div>
      ) : (
        <>
          {/* Mobile Watchlist */}
          <div className="flex flex-col md:hidden mb-4">
            {items.map((item) => {
              const score = item.latest_score
              return (
                <CompanyCard
                  key={item.id}
                  name={item.company.name}
                  ticker={item.company.ticker}
                  score={score}
                  risk={score !== null ? getRiskLevel(score) : "analyzing"}
                  lastAnalyzed={formatRelativeTime(item.company.last_analyzed)}
                  href={ROUTES.company(item.company.ticker)}
                  onRemove={() => handleRemove(item.company.ticker, item.company.name)}
                />
              )
            })}
          </div>

          {/* Desktop Watchlist */}
          <div className="hidden md:block bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E3DFD8]">
                  <th className="w-[28%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">COMPANY</th>
                  <th className="w-[10%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">TICKER</th>
                  <th className="w-[14%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">INTEGRITY SCORE</th>
                  <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">RISK LEVEL</th>
                  <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">LAST ANALYZED</th>
                  <th className="w-[18%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => {
                  const score = item.latest_score
                  const analyzed = score !== null
                  return (
                    <tr key={item.id} className={`h-[52px] hover:bg-[#F1EFE9] group ${idx !== items.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}>
                      <td className="px-4 font-sans text-[14px] font-semibold text-[#1A1A18] truncate">{item.company.name}</td>
                      <td className="px-4 font-mono text-[12px] text-[#1C3558]">{item.company.ticker}</td>
                      <td className="px-4 font-mono text-[16px] font-bold">
                        <span style={{ color: analyzed ? getScoreColor(score) : "#B0ADA7" }}>{formatScore(score)}</span>
                      </td>
                      <td className="px-4">
                        {analyzed ? (
                          <Badge risk={getRiskLevel(score)}>{getRiskLabel(score)}</Badge>
                        ) : (
                          <span className="font-sans text-[12px] text-[#B0ADA7]">Not analyzed</span>
                        )}
                      </td>
                      <td className="px-4 font-sans text-[12px] text-[#7A786F]">{formatRelativeTime(item.company.last_analyzed)}</td>
                      <td className="px-4 text-right">
                        <div className="flex items-center justify-end gap-4">
                          <Link href={ROUTES.company(item.company.ticker)} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                            {analyzed ? "View Report →" : "Analyze →"}
                          </Link>
                          <button
                            onClick={() => handleRemove(item.company.ticker, item.company.name)}
                            className="font-sans text-[12px] text-[#B03028] hover:underline"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

    </div>
  )
}
