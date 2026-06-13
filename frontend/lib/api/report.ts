import { apiRequest } from "./client"
import type { Report } from "@/types/report"

export function getReport(ticker: string): Promise<Report> {
  return apiRequest<Report>(`/report/company/${encodeURIComponent(ticker)}`)
}
