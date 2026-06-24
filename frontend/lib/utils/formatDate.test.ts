import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { formatDate, formatRelativeTime } from "./formatDate"

describe("formatDate", () => {
  it("returns an em dash for null", () => {
    expect(formatDate(null)).toBe("—")
  })

  it("returns an em dash for undefined", () => {
    expect(formatDate(undefined)).toBe("—")
  })

  it("returns an em dash for an unparseable string", () => {
    expect(formatDate("not-a-date")).toBe("—")
  })

  it("formats a Date object directly without reinterpreting it", () => {
    // Constructed via the local-time multi-arg form -- parseAsUtc's
    // `instanceof Date` branch must return it unchanged, not reparse it.
    const d = new Date(2026, 5, 18)
    expect(formatDate(d)).toBe("Jun 18, 2026")
  })

  describe("naive-UTC timestamp parsing (Phase 28 regression)", () => {
    // The backend serializes naive timestamps with no timezone suffix (e.g.
    // "2026-06-18T02:00:00"). Per the JS spec, such a string parses as
    // LOCAL time unless explicitly marked UTC -- silently shifting the
    // displayed date depending on the viewer's timezone. Pinning TZ to a
    // fixed, non-DST, clearly-offset zone (deliberately NOT UTC -- that
    // would make the bug invisible, since the offset would be zero) makes
    // the buggy-vs-fixed behavior deterministically distinguishable
    // regardless of which machine actually runs this test.
    let originalTz: string | undefined

    beforeEach(() => {
      originalTz = process.env.TZ
      process.env.TZ = "Etc/GMT+5" // fixed UTC-5, no DST
    })

    afterEach(() => {
      process.env.TZ = originalTz
    })

    it("treats a naive timestamp as UTC, not as the local timezone", () => {
      // 02:00 UTC -> 21:00 the PREVIOUS day in UTC-5. If this ever
      // regresses to parsing as local time instead, the result flips to
      // "Jun 18, 2026" (no day shift) -- this assertion would catch that.
      expect(formatDate("2026-06-18T02:00:00")).toBe("Jun 17, 2026")
    })

    it("does not double-shift a string that already carries a timezone offset", () => {
      expect(formatDate("2026-06-18T02:00:00Z")).toBe("Jun 17, 2026")
    })
  })
})

describe("formatRelativeTime", () => {
  const NOW = new Date("2026-06-20T12:00:00Z")

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const minutesAgo = (n: number) => new Date(NOW.getTime() - n * 60_000).toISOString()
  const hoursAgo = (n: number) => new Date(NOW.getTime() - n * 60 * 60_000).toISOString()
  const daysAgo = (n: number) => new Date(NOW.getTime() - n * 24 * 60 * 60_000).toISOString()

  it("returns 'Never' for null", () => {
    expect(formatRelativeTime(null)).toBe("Never")
  })

  it("returns 'Never' for undefined", () => {
    expect(formatRelativeTime(undefined)).toBe("Never")
  })

  it("returns 'Never' for an unparseable string", () => {
    expect(formatRelativeTime("not-a-date")).toBe("Never")
  })

  it("returns 'Just now' for a few seconds ago", () => {
    expect(formatRelativeTime(new Date(NOW.getTime() - 10_000).toISOString())).toBe("Just now")
  })

  it("uses singular 'minute' for exactly 1 minute ago", () => {
    expect(formatRelativeTime(minutesAgo(1))).toBe("1 minute ago")
  })

  it("uses plural 'minutes' for 5 minutes ago", () => {
    expect(formatRelativeTime(minutesAgo(5))).toBe("5 minutes ago")
  })

  it("uses singular 'hour' for exactly 1 hour ago", () => {
    expect(formatRelativeTime(hoursAgo(1))).toBe("1 hour ago")
  })

  it("uses plural 'hours' for 3 hours ago", () => {
    expect(formatRelativeTime(hoursAgo(3))).toBe("3 hours ago")
  })

  it("uses singular 'day' for exactly 1 day ago", () => {
    expect(formatRelativeTime(daysAgo(1))).toBe("1 day ago")
  })

  it("uses plural 'days' for 5 days ago", () => {
    expect(formatRelativeTime(daysAgo(5))).toBe("5 days ago")
  })

  it("falls back to the absolute date at 30+ days ago", () => {
    const thirtyDaysAgo = new Date(NOW.getTime() - 30 * 24 * 60 * 60_000)
    expect(formatRelativeTime(thirtyDaysAgo.toISOString())).toBe(formatDate(thirtyDaysAgo))
  })
})
