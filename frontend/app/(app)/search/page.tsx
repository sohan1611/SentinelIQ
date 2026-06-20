"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/layout/SearchBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { searchCompanies } from "@/lib/api/company";
import type { Company } from "@/types/company";
import { ROUTES } from "@/lib/constants/routes";
import { ApiError } from "@/types/api";

// Conservative ticker shape: AAPL, TSLA, WDI.DE, RDS-B, 0700.HK — but not multi-word names.
const TICKER_PATTERN = /^[A-Za-z0-9]{1,5}([.\-][A-Za-z0-9]{1,4})?$/;

function SearchResults() {
  const params = useSearchParams();
  const query = (params.get("q") || "").trim();

  const [results, setResults] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) {
      setResults([]);
      setIsLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    searchCompanies(query)
      .then((data) => {
        if (!cancelled) setResults(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Search failed. Please try again.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query]);

  const directTicker = query.toUpperCase();
  const looksLikeTicker = TICKER_PATTERN.test(query);

  return (
    <div className="w-full max-w-[1200px]">
      <div className="mb-6">
        <h1 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-1">
          {query ? `Results for "${query}"` : "Search companies"}
        </h1>
        {query && !isLoading && !error && (
          <div className="font-sans text-[13px] text-[#7A786F]">
            {results.length} {results.length === 1 ? "company" : "companies"} found
          </div>
        )}
      </div>

      <div className="mb-[24px] w-full">
        <SearchBar variant="compact" initialValue={query} />
      </div>

      {!query ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-12 flex flex-col items-center justify-center min-h-[200px]">
          <div className="font-sans text-[15px] text-[#7A786F] mb-2 text-center">
            Enter a company name or ticker to begin.
          </div>
          <div className="font-sans text-[13px] text-[#B0ADA7] text-center">
            e.g. TSLA, AAPL, or &quot;Wirecard&quot;
          </div>
        </div>
      ) : isLoading ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <div key={i} className={`flex items-center px-4 h-[52px] ${i !== 3 ? "border-b border-[#E3DFD8]" : ""}`}>
              <Skeleton className="w-[35%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[16px] mr-4" />
              <Skeleton className="w-[25%] h-[16px]" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-12 flex flex-col items-center justify-center min-h-[200px]">
          <div className="font-sans text-[15px] text-[#B03028] mb-2 text-center">{error}</div>
        </div>
      ) : results.length > 0 ? (
        <>
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden mb-4">
            <div className="flex flex-col">
              {results.map((row, idx) => (
                <div
                  key={row.id}
                  className={`flex items-center px-4 h-[52px] hover:bg-[#F1EFE9] transition-colors group ${idx !== results.length - 1 ? "border-b border-[#E3DFD8]" : ""}`}
                >
                  <div className="w-[40%] font-sans text-[14px] font-semibold text-[#1A1A18] truncate pr-4">{row.name}</div>
                  <div className="w-[15%] font-mono text-[12px] text-[#1C3558]">{row.ticker}</div>
                  <div className="w-[25%] font-sans text-[13px] text-[#7A786F] truncate pr-4">{row.sector || "—"}</div>
                  <div className="w-[20%] text-right">
                    <Link href={ROUTES.company(row.ticker)} className="font-sans text-[12px] text-[#1C3558] hover:underline">
                      Investigate →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
          {looksLikeTicker && (
            <div className="font-sans text-[12px] text-[#7A786F]">
              Looking for a specific ticker?{" "}
              <Link href={ROUTES.company(directTicker)} className="text-[#1C3558] hover:underline">
                Investigate {directTicker} directly →
              </Link>
            </div>
          )}
        </>
      ) : (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-12 flex flex-col items-center justify-center min-h-[200px]">
          <div className="font-sans text-[15px] text-[#7A786F] mb-2 text-center">
            No results for &quot;{query}&quot;
          </div>
          {looksLikeTicker ? (
            <Link href={ROUTES.company(directTicker)} className="font-sans text-[13px] text-[#1C3558] hover:underline text-center">
              Investigate {directTicker} directly →
            </Link>
          ) : (
            <div className="font-sans text-[13px] text-[#B0ADA7] text-center">
              Try a ticker symbol or the full company name.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-[1200px]">
          <Skeleton className="w-[200px] h-[24px] mb-6" />
          <Skeleton className="w-full h-[42px] rounded-[6px] mb-[24px]" />
          <Skeleton className="w-full h-[160px] rounded-[8px]" />
        </div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}
