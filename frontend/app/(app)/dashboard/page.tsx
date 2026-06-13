"use client";

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Skeleton } from "@/components/ui/Skeleton"
import { SearchBar } from "@/components/layout/SearchBar"
import { CompanyCard } from "@/components/shared/CompanyCard"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { getRiskLevel, getRiskLabel } from "@/lib/utils/riskLabel"
import { getScoreColor } from "@/lib/utils/scoreColor"
import { formatScore } from "@/lib/utils/formatNumber"
import { formatRelativeTime } from "@/lib/utils/formatDate"
import { ROUTES } from "@/lib/constants/routes"

export default function DashboardPage() {
  const router = useRouter()
  const { items, isLoading, error } = useWatchlist()

  // "Recent Reports" is derived from the most recently analyzed watchlist
  // companies — the backend has no user-scoped recent-reports endpoint.
  const recent = [...items]
    .filter((i) => i.latest_score !== null && i.company.last_analyzed)
    .sort(
      (a, b) =>
        new Date(b.company.last_analyzed as string).getTime() -
        new Date(a.company.last_analyzed as string).getTime()
    )
    .slice(0, 3)

  return (
    <div className="w-full max-w-[1200px]">

      {/* Page Heading Row */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18]">Dashboard</h1>
        <Button variant="secondary" className="!text-[13px]" onClick={() => router.push(ROUTES.search)}>
          Add company +
        </Button>
      </div>

      {/* Search Bar */}
      <div className="mb-[28px] w-full">
        <SearchBar variant="compact" placeholder="Investigate a company — e.g. TSLA, Wirecard" />
      </div>

      {/* Watchlist Section */}
      <div className="mb-10">
        <div className="flex justify-between items-end mb-4">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">WATCHLIST</h2>
          {!isLoading && !error && items.length > 0 && (
            <span className="font-sans text-[12px] text-[#B0ADA7]">
              {items.length} {items.length === 1 ? "company" : "companies"}
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
            {[...Array(5)].map((_, i) => (
              <div key={i} className={`flex items-center px-4 h-[52px] ${i !== 4 ? "border-b border-[#E3DFD8]" : ""}`}>
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
                  />
                )
              })}
            </div>

            {/* Desktop Watchlist */}
            <div className="hidden md:block bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden mb-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#E3DFD8]">
                    <th className="w-[30%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">COMPANY</th>
                    <th className="w-[10%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">TICKER</th>
                    <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">INTEGRITY SCORE</th>
                    <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">RISK LEVEL</th>
                    <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">LAST ANALYZED</th>
                    <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]"></th>
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
                          <Link href={ROUTES.company(item.company.ticker)} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                            {analyzed ? "View Report →" : "Analyze →"}
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="text-right">
              <Link href={ROUTES.watchlist} className="font-sans text-[13px] text-[#1C3558] hover:underline">
                View all {items.length} {items.length === 1 ? "company" : "companies"} →
              </Link>
            </div>
          </>
        )}
      </div>

      {/* Recent Reports Section */}
      {!isLoading && !error && recent.length > 0 && (
        <div>
          <div className="mb-4">
            <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">RECENT REPORTS</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recent.map((item) => {
              const score = item.latest_score as number
              return (
                <div key={item.id} className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-5 flex flex-col hover:bg-[#F1EFE9] transition-colors">
                  <div className="font-sans text-[14px] font-semibold text-[#1A1A18] line-clamp-1 mb-1">{item.company.name}</div>
                  <div className="font-mono text-[12px] text-[#1C3558] mb-4">{item.company.ticker}</div>

                  <div className="flex items-center gap-3 mb-4">
                    <div className="font-mono text-[14px] font-medium flex items-baseline">
                      <span style={{ color: getScoreColor(score) }}>{formatScore(score)}</span>
                      <span className="text-[#7A786F] ml-1">/ 100</span>
                    </div>
                    <Badge risk={getRiskLevel(score)}>{getRiskLabel(score)}</Badge>
                  </div>

                  <div className="mt-auto pt-4 border-t border-[#E3DFD8] flex justify-between items-center">
                    <span className="font-sans text-[12px] text-[#7A786F]">Analyzed {formatRelativeTime(item.company.last_analyzed)}</span>
                    <Link href={ROUTES.companyReport(item.company.ticker)} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      Open Report →
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

    </div>
  )
}
