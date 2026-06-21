export interface AuditLogEntry {
  id: string;
  action: string;
  detail: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string | null;
}
