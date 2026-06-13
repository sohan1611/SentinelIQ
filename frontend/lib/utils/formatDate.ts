export function formatDate(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "—"
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput
  if (isNaN(date.getTime())) return "—"
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
}

export function formatRelativeTime(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "Never"
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput
  if (isNaN(date.getTime())) return "Never"

  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diffSec < 60) return "Just now"

  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? "" : "s"} ago`

  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? "" : "s"} ago`

  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 30) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`

  return formatDate(date)
}
