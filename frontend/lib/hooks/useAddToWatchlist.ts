import { useState } from "react"
import { addToWatchlist } from "@/lib/api/watchlist"
import { useToast } from "@/contexts/ToastContext"
import { ApiError } from "@/types/api"

interface UseAddToWatchlistResult {
  isAdding: boolean;
  add: () => Promise<void>;
}

export function useAddToWatchlist(ticker: string): UseAddToWatchlistResult {
  const { showToast } = useToast()
  const [isAdding, setIsAdding] = useState(false)

  const add = async () => {
    setIsAdding(true)
    try {
      await addToWatchlist(ticker)
      showToast(`Added ${ticker} to watchlist`, "success")
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        showToast(`${ticker} is already on your watchlist`, "info")
      } else {
        showToast(err instanceof ApiError ? err.message : "Failed to add to watchlist.", "error")
      }
    } finally {
      setIsAdding(false)
    }
  }

  return { isAdding, add }
}
