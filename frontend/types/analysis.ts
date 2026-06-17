export interface RedFlag {
  id: string;
  flag_type: string;
  severity: string;
  description: string;
  period: string | null;
  event_date: string | null;
}

export interface DivergencePoint {
  period: string;
  divergence: number;
}

export interface ReceivablesRatioPoint {
  period: string;
  recv_ratio: number;
}

export interface AccrualRatioPoint {
  period: string;
  accrual_ratio: number;
}

export interface MarginPoint {
  period: string;
  gross_margin: number;
}

export interface NetIncomePoint {
  period: string;
  net_income: number;
}

export interface DebtMetricPoint {
  period: string;
  debt_to_revenue: number;
  debt_growth: number;
  interest_coverage: number | null;
}

export interface NarrativeSnapshotData {
  period: string;
  statement_text: string;
  sentiment_label: string;
  sentiment_score: number;
  source: string;
}

export interface ToneShift {
  period: string;
  severity: string;
  description: string;
}

export interface GeminiRawResponse {
  finish_reason: string | null;
  safety_ratings: Array<{ category: string; probability: string }>;
  prompt_token_count: number | null;
  candidates_token_count: number | null;
}

export interface GovernanceProvenance {
  model_id: string | null;
  prompt: string | null;
  raw_response: GeminiRawResponse | null;
  low_confidence: boolean;
}

export interface GovernanceFlagDetail {
  flag_type: string;
  severity: string;
  description: string;
  period: string | null;
  source_quote: string | null;
}

export interface ModuleScores {
  financial?: number;
  cashflow?: number;
  earnings?: number;
  debt?: number;
  governance?: number;
  narrative?: number;
  news?: number;
}

export interface ModuleDetails {
  scores?: ModuleScores;
  confidence?: "low" | "medium" | "high";
  revenue?: {
    divergences?: DivergencePoint[];
    recv_ratios?: ReceivablesRatioPoint[];
  };
  cashflow?: {
    accrual_ratios?: AccrualRatioPoint[];
  };
  earnings?: {
    margins?: MarginPoint[];
    net_incomes?: NetIncomePoint[];
  };
  debt?: {
    debt_metrics?: DebtMetricPoint[];
  };
  narrative?: {
    snapshots?: NarrativeSnapshotData[];
    tone_shifts?: ToneShift[];
  };
  governance?: {
    provenance?: GovernanceProvenance;
    low_confidence?: boolean;
    flags?: GovernanceFlagDetail[];
  };
}

export interface AnalysisResult {
  id: string;
  company_id: string;
  run_at: string;
  integrity_score: number | null;
  financial_score: number | null;
  cashflow_score: number | null;
  governance_score: number | null;
  earnings_score: number | null;
  narrative_score: number | null;
  news_score: number | null;
  module_details: ModuleDetails | null;
  status: string;
}

export interface AnalysisResultWithFlags extends AnalysisResult {
  red_flags: RedFlag[];
}

export interface AnalysisHistoryItem {
  id: string;
  run_at: string;
  integrity_score: number | null;
  financial_score: number | null;
  cashflow_score: number | null;
  governance_score: number | null;
  earnings_score: number | null;
  narrative_score: number | null;
  news_score: number | null;
}

export interface AnalysisStatus {
  status: string;
  integrity_score: number | null;
  stage: string;
  elapsed_seconds: number;
}

export interface AnalysisRunResponse {
  analysis_id: string;
  status: string;
}
