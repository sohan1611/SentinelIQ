import type { EvidenceRow, Severity } from "@/components/modules/RedFlagItem";
import type { ModuleDetails, RedFlag } from "@/types/analysis";
import { formatDate } from "./formatDate";
import { formatCompactNumber, formatPercent } from "./formatNumber";

export function normalizeSeverity(severity: string): Severity {
  const s = severity.toLowerCase();
  if (s === "severe" || s === "high" || s === "moderate") return s;
  return "moderate";
}

export function flagDate(flag: RedFlag): string {
  if (flag.event_date) return formatDate(flag.event_date);
  return flag.period ?? "—";
}

/**
 * Maps a red flag back to the underlying forensic data row(s) or AI
 * provenance that produced it, for the "Evidence" drill-down on
 * RedFlagItem. Returns [] when module_details has nothing for this
 * flag's period/type (e.g. older analyses without module_details).
 */
export function getFlagEvidence(flag: RedFlag, moduleDetails: ModuleDetails | null | undefined): EvidenceRow[] {
  if (!moduleDetails) return [];
  const period = flag.period;
  const rows: EvidenceRow[] = [];

  switch (flag.flag_type) {
    case "revenue": {
      const divergence = moduleDetails.revenue?.divergences?.find((d) => d.period === period);
      if (divergence) rows.push({ label: "Revenue/OCF Divergence", value: formatPercent(divergence.divergence) });

      const recv = moduleDetails.revenue?.recv_ratios?.find((r) => r.period === period);
      if (recv) rows.push({ label: "Receivables / Revenue", value: formatPercent(recv.recv_ratio) });
      break;
    }
    case "cash_flow": {
      const accrual = moduleDetails.cashflow?.accrual_ratios?.find((a) => a.period === period);
      if (accrual) rows.push({ label: "Accrual Ratio (Sloan)", value: formatPercent(accrual.accrual_ratio) });

      const debt = moduleDetails.debt?.debt_metrics?.find((d) => d.period === period);
      if (debt) {
        rows.push({ label: "Debt / Revenue", value: `${debt.debt_to_revenue.toFixed(2)}x` });
        rows.push({ label: "Debt Growth (YoY)", value: formatPercent(debt.debt_growth) });
        if (debt.interest_coverage !== null) {
          rows.push({ label: "Interest Coverage", value: `${debt.interest_coverage.toFixed(2)}x` });
        }
      }
      break;
    }
    case "earnings": {
      const margin = moduleDetails.earnings?.margins?.find((m) => m.period === period);
      if (margin) rows.push({ label: "Gross Margin", value: formatPercent(margin.gross_margin) });

      const netIncome = moduleDetails.earnings?.net_incomes?.find((n) => n.period === period);
      if (netIncome) rows.push({ label: "Net Income", value: formatCompactNumber(netIncome.net_income) });
      break;
    }
    case "governance": {
      const provenance = moduleDetails.governance?.provenance;
      if (provenance?.model_id) {
        rows.push({ label: "Source", value: "Recent news coverage" });
        rows.push({ label: "AI Model", value: provenance.model_id });
      }
      break;
    }
    default:
      break;
  }

  return rows;
}
