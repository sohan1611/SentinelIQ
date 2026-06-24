"use client";

import Link from "next/link"
import { Badge } from "@/components/ui/Badge"
import { Skeleton } from "@/components/ui/Skeleton"
import { useAlerts } from "@/lib/hooks/useAlerts"
import { getRiskLevel, getRiskLabel } from "@/lib/utils/riskLabel"
import { formatScore } from "@/lib/utils/formatNumber"
import { formatRelativeTime } from "@/lib/utils/formatDate"
import { ROUTES } from "@/lib/constants/routes"
import type { WatchlistAlert } from "@/types/alert"

function RiskChange({ alert }: { alert: WatchlistAlert }) {
  return (
    <div className="flex flex-col items-start gap-1">
      <Badge risk={getRiskLevel(alert.previous_score)}>{getRiskLabel(alert.previous_score)}</Badge>
      <span className="font-sans text-[11px] text-[#B0ADA7] leading-none pl-1">&#8595;</span>
      <Badge risk={getRiskLevel(alert.new_score)}>{getRiskLabel(alert.new_score)}</Badge>
    </div>
  )
}

export default function AlertsPage() {
  const { alerts, isLoading, error, markRead } = useAlerts()

  const handleNavigate = (alert: WatchlistAlert) => {
    if (!alert.is_read) markRead(alert.id)
  }

  return (
    <div className="w-full max-w-[1200px]">

      <div className="flex justify-between items-center mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18]">Alerts</h1>
      </div>

      {isLoading ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <div key={i} className={`flex items-center px-4 py-4 ${i !== 3 ? "border-b border-[#E3DFD8]" : ""}`}>
              <Skeleton className="w-[25%] h-[16px] mr-4" />
              <Skeleton className="w-[10%] h-[16px] mr-4" />
              <Skeleton className="w-[20%] h-[16px] mr-4" />
              <Skeleton className="w-[20%] h-[48px] mr-4" />
              <Skeleton className="w-[15%] h-[16px]" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-[14px] text-[#B03028] mb-1">Couldn&apos;t load your alerts.</div>
          <div className="font-sans text-[12px] text-[#7A786F]">{error}</div>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-10 flex flex-col items-center justify-center text-center">
          <div className="font-sans text-[14px] text-[#1A1A18] mb-1">No alerts yet.</div>
          <div className="font-sans text-[13px] text-[#7A786F]">You&apos;ll see one here when a watched company&apos;s risk level changes.</div>
        </div>
      ) : (
        <>
          {/* Mobile */}
          <div className="flex flex-col gap-3 md:hidden mb-4">
            {alerts.map((alert) => (
              <Link
                key={alert.id}
                href={ROUTES.company(alert.company.ticker)}
                onClick={() => handleNavigate(alert)}
                className={`block bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-4 ${alert.is_read ? "opacity-60" : ""}`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-sans text-[14px] font-semibold text-[#1A1A18]">{alert.company.name}</div>
                    <div className="font-mono text-[12px] text-[#1C3558]">{alert.company.ticker}</div>
                  </div>
                  <div className="font-sans text-[12px] text-[#7A786F]">{formatRelativeTime(alert.created_at)}</div>
                </div>
                <RiskChange alert={alert} />
              </Link>
            ))}
          </div>

          {/* Desktop */}
          <div className="hidden md:block bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E3DFD8]">
                  <th className="w-[22%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">COMPANY</th>
                  <th className="w-[10%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">TICKER</th>
                  <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">SCORE CHANGE</th>
                  <th className="w-[28%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">RISK CHANGE</th>
                  <th className="w-[15%] py-3 px-4 text-[10px] font-sans font-medium uppercase tracking-[0.08em] text-[#7A786F]">WHEN</th>
                  <th className="w-[10%] py-3 px-4"></th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, idx) => (
                  <tr key={alert.id} className={`${idx !== alerts.length - 1 ? "border-b border-[#E3DFD8]" : ""} hover:bg-[#F1EFE9] group ${alert.is_read ? "opacity-60" : ""}`}>
                    <td className="px-4 py-4 font-sans text-[14px] font-semibold text-[#1A1A18] truncate">{alert.company.name}</td>
                    <td className="px-4 py-4 font-mono text-[12px] text-[#1C3558]">{alert.company.ticker}</td>
                    <td className="px-4 py-4 font-mono text-[14px] font-bold text-[#1A1A18]">
                      {formatScore(alert.previous_score)} &#8594; {formatScore(alert.new_score)}
                    </td>
                    <td className="px-4 py-4">
                      <RiskChange alert={alert} />
                    </td>
                    <td className="px-4 py-4 font-sans text-[12px] text-[#7A786F]">{formatRelativeTime(alert.created_at)}</td>
                    <td className="px-4 py-4 text-right align-top">
                      <Link
                        href={ROUTES.company(alert.company.ticker)}
                        onClick={() => handleNavigate(alert)}
                        className="font-sans text-[12px] text-[#1C3558] hover:underline"
                      >
                        View &#8594;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

    </div>
  )
}
