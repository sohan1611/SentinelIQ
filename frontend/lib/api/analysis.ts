import { apiRequest } from "./client"
import type { AnalysisRunResponse, AnalysisStatus, AnalysisResultWithFlags } from "@/types/analysis"

export function runAnalysis(ticker: string): Promise<AnalysisRunResponse> {
  return apiRequest<AnalysisRunResponse>("/analysis/run", {
    method: "POST",
    body: { ticker },
  })
}

export function getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
  return apiRequest<AnalysisStatus>(`/analysis/${analysisId}/status`)
}

export function getLatestAnalysis(ticker: string): Promise<AnalysisResultWithFlags> {
  return apiRequest<AnalysisResultWithFlags>(`/analysis/company/${encodeURIComponent(ticker)}`)
}
