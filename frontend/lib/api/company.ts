import { apiRequest } from "./client"
import type { Company } from "@/types/company"

export function searchCompanies(query: string): Promise<Company[]> {
  return apiRequest<Company[]>(`/company/search?q=${encodeURIComponent(query)}`)
}

export function getCompany(ticker: string): Promise<Company> {
  return apiRequest<Company>(`/company/${encodeURIComponent(ticker)}`)
}
