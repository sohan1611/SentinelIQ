import { apiRequest } from "./client"
import type { AuditLogEntry } from "@/types/auditLog"

export function getAuditLog(): Promise<AuditLogEntry[]> {
  return apiRequest<AuditLogEntry[]>("/audit-log/")
}
