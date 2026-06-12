import Link from "next/link"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { SearchBar } from "@/components/layout/SearchBar"
import { CompanyCard } from "@/components/shared/CompanyCard"

export default function DashboardPage() {
  const watchlist = [
    { name: "Wirecard AG", ticker: "WDI.DE", score: 22, risk: "high", analyzed: "2 days ago" },
    { name: "Apple Inc.", ticker: "AAPL", score: 88, risk: "strong", analyzed: "1 week ago" },
    { name: "Satyam Computer Services", ticker: "SAY", score: 31, risk: "high", analyzed: "3 weeks ago" },
    { name: "Tesla Inc.", ticker: "TSLA", score: 61, risk: "low", analyzed: "2 hrs ago" },
    { name: "Generic Holdings Ltd.", ticker: "GEN", score: 47, risk: "moderate", analyzed: "1 month ago" },
    { name: "Luckin Coffee", ticker: "LK", score: 19, risk: "severe", analyzed: "2 months ago" },
  ];

  const recentReports = [
    { name: "Super Micro Computer", ticker: "SMCI", score: 42, risk: "moderate", date: "Generated June 9, 2025" },
    { name: "NVIDIA Corporation", ticker: "NVDA", score: 85, risk: "low", date: "Generated June 8, 2025" },
    { name: "New York Community Bancorp", ticker: "NYCB", score: 28, risk: "high", date: "Generated June 1, 2025" },
  ];

  const scoreColors: Record<string, string> = {
    severe: "text-[#6E1010]",
    high: "text-[#B03028]",
    moderate: "text-[#C47A14]",
    low: "text-[#1C3558]",
    strong: "text-[#1A6B3C]",
  };

  return (
    <div className="w-full max-w-[1200px]">
      
      {/* Page Heading Row */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18]">Dashboard</h1>
        <Button variant="secondary" className="!text-[13px]">Add company +</Button>
      </div>

      {/* Search Bar */}
      <div className="mb-[28px] w-full">
        <SearchBar variant="compact" placeholder="Investigate a company — e.g. TSLA, Wirecard" />
      </div>

      {/* Watchlist Section */}
      <div className="mb-10">
        <div className="flex justify-between items-end mb-4">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">WATCHLIST</h2>
          <span className="font-sans text-[12px] text-[#B0ADA7]">12 companies</span>
        </div>

        {/* Mobile Watchlist */}
        <div className="flex flex-col md:hidden mb-4">
          {watchlist.map((row) => (
            <CompanyCard 
              key={row.ticker}
              name={row.name}
              ticker={row.ticker}
              score={row.score}
              risk={row.risk as any}
              lastAnalyzed={row.analyzed}
              href={`/company/${row.ticker}`}
            />
          ))}
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
              {watchlist.map((row, idx) => (
                <tr key={row.ticker} className={`h-[52px] hover:bg-[#F1EFE9] group ${idx !== watchlist.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}>
                  <td className="px-4 font-sans text-[14px] font-semibold text-[#1A1A18] truncate">{row.name}</td>
                  <td className="px-4 font-mono text-[12px] text-[#1C3558]">{row.ticker}</td>
                  <td className="px-4 font-mono text-[16px] font-bold">
                    <span className={scoreColors[row.risk]}>{row.score}</span>
                  </td>
                  <td className="px-4">
                    <Badge risk={row.risk as any}>{row.risk.replace("-", " ")} RISK</Badge>
                  </td>
                  <td className="px-4 font-sans text-[12px] text-[#7A786F]">{row.analyzed}</td>
                  <td className="px-4 text-right">
                    <Link href={`/company/${row.ticker}`} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      View Report →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="text-right">
          <Link href="/watchlist" className="font-sans text-[13px] text-[#1C3558] hover:underline">
            View all 12 companies →
          </Link>
        </div>
      </div>

      {/* Recent Reports Section */}
      <div>
        <div className="mb-4">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">RECENT REPORTS</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recentReports.map((report) => (
            <div key={report.ticker} className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-5 flex flex-col hover:bg-[#F1EFE9] transition-colors">
              <div className="font-sans text-[14px] font-semibold text-[#1A1A18] line-clamp-1 mb-1">{report.name}</div>
              <div className="font-mono text-[12px] text-[#1C3558] mb-4">{report.ticker}</div>
              
              <div className="flex items-center gap-3 mb-4">
                <div className="font-mono text-[14px] font-medium flex items-baseline">
                  <span className={scoreColors[report.risk]}>{report.score}</span>
                  <span className="text-[#7A786F] ml-1">/ 100</span>
                </div>
                <Badge risk={report.risk as any}>{report.risk.replace("-", " ")}</Badge>
              </div>
              
              <div className="mt-auto pt-4 border-t border-[#E3DFD8] flex justify-between items-center">
                <span className="font-sans text-[12px] text-[#7A786F]">{report.date}</span>
                <Link href={`/company/${report.ticker}/report`} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                  Open Report →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
