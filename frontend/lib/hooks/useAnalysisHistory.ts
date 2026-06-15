import { useState, useEffect } from "react"
import { getAnalysisHistory } from "@/lib/api/analysis"
import type { AnalysisHistoryItem } from "@/types/analysis"

interface UseAnalysisHistoryResult {
  history: AnalysisHistoryItem[];
  isLoading: boolean;
}

export function useAnalysisHistory(ticker: string): UseAnalysisHistoryResult {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

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
  }, [ticker])

  return { history, isLoading }
}
