import { useState, useRef, useCallback, useEffect } from "react"
import { runAnalysis, getAnalysisStatus } from "@/lib/api/analysis"
import type { AnalysisStatus } from "@/types/analysis"
import { ApiError } from "@/types/api"

const POLL_INTERVAL_MS = 3000

interface UseAnalysisResult {
  status: AnalysisStatus | null;
  isRunning: boolean;
  error: string | null;
  start: (ticker: string) => Promise<void>;
}

export function useAnalysis(onComplete?: () => void): UseAnalysisResult {
  const [status, setStatus] = useState<AnalysisStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => stopPolling, [stopPolling])

  const start = useCallback(async (ticker: string) => {
    setError(null)
    setStatus(null)
    setIsRunning(true)

    try {
      const { analysis_id } = await runAnalysis(ticker)

      const poll = async () => {
        try {
          const result = await getAnalysisStatus(analysis_id)
          setStatus(result)
          if (result.status === "complete" || result.status === "failed" || result.status === "error") {
            stopPolling()
            setIsRunning(false)
            if (result.status === "complete") {
              onComplete?.()
            } else if (result.status === "error") {
              setError("Analysis was interrupted. Please retry.")
            }
          }
        } catch (err) {
          stopPolling()
          setIsRunning(false)
          setError(err instanceof ApiError ? err.message : "Failed to check analysis status.")
        }
      }

      await poll()
      intervalRef.current = setInterval(poll, POLL_INTERVAL_MS)
    } catch (err) {
      setIsRunning(false)
      if (err instanceof ApiError && err.code === "LIMIT_REACHED") {
        setError("You've reached your free analysis limit for this month.")
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to start analysis.")
      }
    }
  }, [onComplete, stopPolling])

  return { status, isRunning, error, start }
}
