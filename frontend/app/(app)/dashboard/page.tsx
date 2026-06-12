import Link from "next/link"
import { Badge } from "@/components/ui/Badge"

export default function DashboardPage() {
  const watchlist = [
    { name: "Tesla, Inc.", ticker: "TSLA", score: 72, risk: "low", analyzed: "2 hrs ago" },
    { name: "NVIDIA Corporation", ticker: "NVDA", score: 85, risk: "low", analyzed: "1 day ago" },
    { name: "Super Micro Computer", ticker: "SMCI", score: 42, risk: "moderate", analyzed: "3 days ago" },
    { name: "New York Community Bancorp", ticker: "NYCB", score: 28, risk: "high", analyzed: "1 week ago" },
  ];

  return (
    <div className="p-10 max-w-6xl mx-auto">
      <div className="mb-10">
        <label className="block text-sm font-medium text-primary mb-2">Investigate a company</label>
        <div className="relative max-w-2xl">
          <input 
            type="text" 
            placeholder="Search by company name or ticker..."
            className="w-full rounded-btn border border-border bg-surface px-4 py-3 text-sm focus:border-navy focus:outline-none focus:ring-1 focus:ring-navy"
          />
        </div>
      </div>

      <div className="mb-4">
        <h2 className="text-lg font-semibold text-primary">Watchlist</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans">Company</th>
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans">Ticker</th>
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans">Integrity Score</th>
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans">Risk Level</th>
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans">Last Analyzed</th>
              <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-secondary font-sans text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {watchlist.map((row) => (
              <tr key={row.ticker} className="hover:bg-surface/50 transition-colors group">
                <td className="py-4 font-medium text-primary">{row.name}</td>
                <td className="py-4 font-mono text-secondary">{row.ticker}</td>
                <td className="py-4 font-mono font-medium text-primary">{row.score}</td>
                <td className="py-4">
                  <Badge risk={row.risk as any}>{row.risk}</Badge>
                </td>
                <td className="py-4 text-secondary">{row.analyzed}</td>
                <td className="py-4 text-right">
                  <Link href={`/company/${row.ticker}`} className="text-navy font-medium hover:underline">
                    View Report
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
