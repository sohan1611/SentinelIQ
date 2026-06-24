import { useState, useEffect, useCallback } from "react"
import { getAlerts, markAlertRead } from "@/lib/api/alerts"
import type { WatchlistAlert } from "@/types/alert"
import { ApiError } from "@/types/api"

interface UseAlertsResult {
  alerts: WatchlistAlert[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  markRead: (id: string) => Promise<void>;
  refetch: () => void;
}

export function useAlerts(): UseAlertsResult {
  const [alerts, setAlerts] = useState<WatchlistAlert[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)

  const refetch = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    getAlerts()
      .then((data) => {
        if (!cancelled) {
          setAlerts(data.alerts)
          setUnreadCount(data.unread_count)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load alerts.")
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [version])

  const markRead = useCallback(async (id: string) => {
    await markAlertRead(id)
    setAlerts((prev) => {
      const target = prev.find((a) => a.id === id)
      if (target && !target.is_read) {
        setUnreadCount((count) => Math.max(0, count - 1))
      }
      return prev.map((a) => (a.id === id ? { ...a, is_read: true } : a))
    })
  }, [])

  return { alerts, unreadCount, isLoading, error, markRead, refetch }
}
