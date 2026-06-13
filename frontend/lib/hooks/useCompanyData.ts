import { useState, useEffect, useCallback } from "react"
import { getCompany } from "@/lib/api/company"
import { getLatestAnalysis } from "@/lib/api/analysis"
import type { Company } from "@/types/company"
import type { AnalysisResultWithFlags } from "@/types/analysis"
import { ApiError } from "@/types/api"

interface UseCompanyDataResult {
  company: Company | null;
  analysis: AnalysisResultWithFlags | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useCompanyData(ticker: string): UseCompanyDataResult {
  const [company, setCompany] = useState<Company | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResultWithFlags | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)

  const refetch = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    if (!ticker) return
    let cancelled = false

    setIsLoading(true)
    setError(null)

    async function load() {
      try {
        const companyData = await getCompany(ticker)
        if (cancelled) return
        setCompany(companyData)

        try {
          const analysisData = await getLatestAnalysis(ticker)
          if (cancelled) return
          setAnalysis(analysisData)
        } catch (err) {
          if (cancelled) return
          if (err instanceof ApiError && err.status === 404) {
            setAnalysis(null)
          } else {
            throw err
          }
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof ApiError ? err.message : "Failed to load company data.")
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [ticker, version])

  return { company, analysis, isLoading, error, refetch }
}
