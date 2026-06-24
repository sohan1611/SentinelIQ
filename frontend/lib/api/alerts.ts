import { apiRequest } from "./client"
import type { AlertListResponse } from "@/types/alert"

export function getAlerts(): Promise<AlertListResponse> {
  return apiRequest<AlertListResponse>("/alerts/")
}

export function markAlertRead(id: string): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`/alerts/${encodeURIComponent(id)}/read`, {
    method: "POST",
  })
}
