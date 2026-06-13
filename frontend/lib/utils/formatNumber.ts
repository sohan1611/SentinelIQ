export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—"
  return Math.round(value).toString()
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return "—"
  return `${(value * 100).toFixed(decimals)}%`
}

export function formatCompactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—"
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value)
}
