export interface Company {
  id: string;
  name: string;
  ticker: string;
  sector: string | null;
  exchange: string | null;
  last_analyzed: string | null;
  created_at: string;
}
