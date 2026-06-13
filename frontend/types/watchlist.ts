import type { Company } from "./company"

export interface WatchlistItem {
  id: string;
  company: Company;
  added_at: string;
  latest_score: number | null;
}
