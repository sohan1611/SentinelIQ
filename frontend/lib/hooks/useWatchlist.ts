import { useState, useEffect, useCallback } from "react"
import { getWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api/watchlist"
import type { WatchlistItem } from "@/types/watchlist"
import { ApiError } from "@/types/api"

interface UseWatchlistResult {
  items: WatchlistItem[];
  isLoading: boolean;
  error: string | null;
  add: (ticker: string) => Promise<void>;
  remove: (ticker: string) => Promise<void>;
  refetch: () => void;
}

export function useWatchlist(): UseWatchlistResult {
  const [items, setItems] = useState<WatchlistItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)

  const refetch = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    getWatchlist()
      .then((data) => {
        if (!cancelled) setItems(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load watchlist.")
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [version])

  const add = useCallback(async (ticker: string) => {
    await addToWatchlist(ticker)
    refetch()
  }, [refetch])

  const remove = useCallback(async (ticker: string) => {
    await removeFromWatchlist(ticker)
    setItems((prev) => prev.filter((item) => item.company.ticker !== ticker))
  }, [])

  return { items, isLoading, error, add, remove, refetch }
}
