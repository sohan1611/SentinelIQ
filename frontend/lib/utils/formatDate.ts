// The backend serializes naive UTC timestamps with no timezone suffix (e.g.
// "2026-06-18T23:30:00"). Per the JS spec, a date-time string with no offset
// parses as local time, not UTC — silently shifting the displayed date/time
// by the browser's UTC offset. Append "Z" when no offset is already present
// so these are always interpreted as UTC.
function parseAsUtc(dateInput: string | Date): Date {
  if (dateInput instanceof Date) return dateInput
  const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(dateInput)
  return new Date(hasTimezone ? dateInput : `${dateInput}Z`)
}

export function formatDate(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "—"
  const date = parseAsUtc(dateInput)
  if (isNaN(date.getTime())) return "—"
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
}

export function formatRelativeTime(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "Never"
  const date = parseAsUtc(dateInput)
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
