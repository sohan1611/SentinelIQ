import type { ModuleDetails } from "@/types/analysis"

interface CsvSection {
  title: string;
  header: string[];
  rows: (string | number)[][];
}

function escapeCsvField(value: string | number): string {
  const str = String(value)
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

function toCsvRow(values: (string | number)[]): string {
  return values.map(escapeCsvField).join(",")
}

function toCsvBlock(section: CsvSection): string {
  return [section.title, toCsvRow(section.header), ...section.rows.map(toCsvRow)].join("\n")
}

export function buildForensicsCsv(ticker: string, generatedAt: string, details: ModuleDetails | null | undefined): string {
  const blocks: string[] = [
    toCsvBlock({
      title: "Forensic Data Export",
      header: ["Ticker", "Generated At"],
      rows: [[ticker, generatedAt]],
    }),
  ]

  const divergences = details?.revenue?.divergences ?? []
  if (divergences.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Revenue / OCF Growth Divergence",
        header: ["Period", "Divergence"],
        rows: divergences.map((d) => [d.period, d.divergence]),
      })
    )
  }

  const recvRatios = details?.revenue?.recv_ratios ?? []
  if (recvRatios.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Receivables Ratio",
        header: ["Period", "Receivables Ratio"],
        rows: recvRatios.map((d) => [d.period, d.recv_ratio]),
      })
    )
  }

  const accrualRatios = details?.cashflow?.accrual_ratios ?? []
  if (accrualRatios.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Cash Flow Accrual Ratio",
        header: ["Period", "Accrual Ratio"],
        rows: accrualRatios.map((d) => [d.period, d.accrual_ratio]),
      })
    )
  }

  const margins = details?.earnings?.margins ?? []
  if (margins.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Gross Margin",
        header: ["Period", "Gross Margin"],
        rows: margins.map((d) => [d.period, d.gross_margin]),
      })
    )
  }

  const netIncomes = details?.earnings?.net_incomes ?? []
  if (netIncomes.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Net Income",
        header: ["Period", "Net Income"],
        rows: netIncomes.map((d) => [d.period, d.net_income]),
      })
    )
  }

  const debtMetrics = details?.debt?.debt_metrics ?? []
  if (debtMetrics.length > 0) {
    blocks.push(
      toCsvBlock({
        title: "Debt Metrics",
        header: ["Period", "Debt to Revenue", "Debt Growth", "Interest Coverage"],
        rows: debtMetrics.map((d) => [d.period, d.debt_to_revenue, d.debt_growth, d.interest_coverage ?? ""]),
      })
    )
  }

  if (blocks.length === 1) {
    blocks.push("No forensic series data is available for this analysis.")
  }

  return blocks.join("\n\n") + "\n"
}

export function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
