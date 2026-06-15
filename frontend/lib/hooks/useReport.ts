import { useState, useEffect } from "react"
import { getReport } from "@/lib/api/report"
import type { Report } from "@/types/report"
import { ApiError } from "@/types/api"

interface UseReportResult {
  report: Report | null;
  isLoading: boolean;
  error: string | null;
}

export function useReport(ticker: string, enabled: boolean): UseReportResult {
  const [report, setReport] = useState<Report | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ticker || !enabled) {
      setIsLoading(false)
      return
    }
    let cancelled = false

    setIsLoading(true)
    setError(null)

    getReport(ticker)
      .then((data) => {
        if (!cancelled) setReport(data)
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 404) {
          setReport(null)
        } else {
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [ticker, enabled])

  return { report, isLoading, error }
}
