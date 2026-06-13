import { apiRequest } from "./client"
import type { WatchlistItem } from "@/types/watchlist"

export function getWatchlist(): Promise<WatchlistItem[]> {
  return apiRequest<WatchlistItem[]>("/watchlist/")
}

export function addToWatchlist(ticker: string): Promise<{ message: string }> {
  return apiRequest<{ message: string }>("/watchlist/", {
    method: "POST",
    body: { ticker },
  })
}

export function removeFromWatchlist(ticker: string): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`/watchlist/${encodeURIComponent(ticker)}`, {
    method: "DELETE",
  })
}
