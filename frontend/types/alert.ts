import type { Company } from "./company"

export interface WatchlistAlert {
  id: string;
  company: Company;
  previous_score: number;
  new_score: number;
  previous_risk: string;
  new_risk: string;
  is_read: boolean;
  created_at: string;
}

export interface AlertListResponse {
  alerts: WatchlistAlert[];
  unread_count: number;
}
