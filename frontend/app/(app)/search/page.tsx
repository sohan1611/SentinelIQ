import Link from "next/link"
import { Badge } from "@/components/ui/Badge"
import { SearchBar } from "@/components/layout/SearchBar"

export default function SearchResultsPage({ searchParams }: { searchParams: { q?: string } }) {
  const query = searchParams.q || "wirecard";
  const hasResults = query.toLowerCase() === "wirecard";

  // Mock results
  const results = [
    { name: "Wirecard AG", ticker: "WDI.DE", score: 22, risk: "high" },
    { name: "Wirecard North America", ticker: "WCNA", score: 34, risk: "high" },
    { name: "Wire & Cable Co.", ticker: "WCC", score: 71, risk: "low" },
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
      <div className="mb-6">
        <h1 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-1">
          {hasResults ? `Results for "${query}"` : `No results for "${query}"`}
        </h1>
        {hasResults && (
          <div className="font-sans text-[13px] text-[#7A786F]">3 companies found</div>
        )}
      </div>

      <div className="mb-[24px] w-full">
        <SearchBar variant="compact" forceState={hasResults ? "typed" : "default"} />
      </div>

      {hasResults ? (
        <>
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden mb-4">
            <div className="flex flex-col">
              {results.map((row, idx) => (
                <div key={row.ticker} className={`flex items-center px-4 h-[52px] hover:bg-[#F1EFE9] transition-colors group ${idx !== results.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}>
                  <div className={`w-[30%] font-sans text-[14px] font-semibold text-[#1A1A18] truncate pr-4 ${idx === 2 ? "opacity-60" : ""}`}>{row.name}</div>
                  <div className={`w-[15%] font-mono text-[12px] text-[#1C3558] ${idx === 2 ? "opacity-60" : ""}`}>{row.ticker}</div>
                  <div className={`w-[15%] font-mono text-[16px] font-bold ${scoreColors[row.risk]} ${idx === 2 ? "opacity-60" : ""}`}>{row.score}</div>
                  <div className={`w-[20%] ${idx === 2 ? "opacity-60" : ""}`}>
                    <Badge risk={row.risk as any}>{row.risk.replace("-", " ")} RISK</Badge>
                  </div>
                  <div className="w-[20%] text-right">
                    <Link href={`/company/${row.ticker}`} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      Investigate →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="font-sans text-[12px] text-[#B0ADA7]">
            Not finding a company? Try the full ticker.
          </div>
        </>
      ) : (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-12 flex flex-col items-center justify-center min-h-[200px]">
          <div className="font-sans text-[15px] text-[#7A786F] mb-2 text-center">
            No results for "{query}"
          </div>
          <div className="font-sans text-[13px] text-[#B0ADA7] text-center">
            Try a ticker symbol or the full company name.
          </div>
        </div>
      )}
    </div>
  )
}
