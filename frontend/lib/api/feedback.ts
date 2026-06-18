import { apiRequest } from "./client"

export interface FeedbackPayload {
  analysis_id: string
  flag_id?: string
  message: string
}

export function reportAnalysisError(payload: FeedbackPayload): Promise<{ message: string }> {
  return apiRequest<{ message: string }>("/feedback/analysis-error", {
    method: "POST",
    body: payload,
  })
}
