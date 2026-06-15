import type { Severity } from "@/components/modules/RedFlagItem";
import type { RedFlag } from "@/types/analysis";
import { formatDate } from "./formatDate";

export function normalizeSeverity(severity: string): Severity {
  const s = severity.toLowerCase();
  if (s === "severe" || s === "high" || s === "moderate") return s;
  return "moderate";
}

export function flagDate(flag: RedFlag): string {
  if (flag.event_date) return formatDate(flag.event_date);
  return flag.period ?? "—";
}
