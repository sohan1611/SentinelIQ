import { useState, useEffect } from "react"
import { getAnalysisHistory } from "@/lib/api/analysis"
import type { AnalysisHistoryItem } from "@/types/analysis"

interface UseAnalysisHistoryResult {
  history: AnalysisHistoryItem[];
  isLoading: boolean;
}

export function useAnalysisHistory(ticker: string, refreshKey?: string | null): UseAnalysisHistoryResult {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // A new completed-analysis ID must refresh this hook: ticker-only dependencies previously
  // left the chart rendering pre-analysis data until a manual page reload, as confirmed live.
  useEffect(() => {
    if (!ticker) return
    let cancelled = false

    setIsLoading(true)

    getAnalysisHistory(ticker)
      .then((data) => {
        if (!cancelled) setHistory(data)
      })
      .catch(() => {
        if (!cancelled) setHistory([])
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [ticker, refreshKey])

  return { history, isLoading }
}
