import { describe, it, expect } from "vitest"
import { formatScore, formatPercent, formatCompactNumber } from "./formatNumber"

describe("formatScore", () => {
  it("returns an em dash for null", () => {
    expect(formatScore(null)).toBe("—")
  })

  it("returns an em dash for undefined", () => {
    expect(formatScore(undefined)).toBe("—")
  })

  it("returns '0' for zero", () => {
    expect(formatScore(0)).toBe("0")
  })

  it("rounds down a fractional value below the midpoint", () => {
    expect(formatScore(72.4)).toBe("72")
  })

  it("rounds up a fractional value at/above the midpoint", () => {
    expect(formatScore(72.5)).toBe("73")
  })

  it("formats a negative value, rounding toward positive infinity per Math.round", () => {
    // Math.round(-7.5) === -7 (rounds half up, i.e. toward +Infinity)
    expect(formatScore(-7.5)).toBe("-7")
  })

  it("formats a whole negative number", () => {
    expect(formatScore(-10)).toBe("-10")
  })

  it("formats a large number without separators (toString, not toLocaleString)", () => {
    expect(formatScore(123456)).toBe("123456")
  })
})

describe("formatPercent", () => {
  it("returns an em dash for null", () => {
    expect(formatPercent(null)).toBe("—")
  })

  it("returns an em dash for undefined", () => {
    expect(formatPercent(undefined)).toBe("—")
  })

  it("formats zero as 0.0%", () => {
    expect(formatPercent(0)).toBe("0.0%")
  })

  it("formats a fractional ratio at the default 1 decimal place", () => {
    expect(formatPercent(0.153)).toBe("15.3%")
  })

  it("formats a negative ratio", () => {
    expect(formatPercent(-0.2)).toBe("-20.0%")
  })

  it("respects a custom decimals argument", () => {
    expect(formatPercent(0.15321, 3)).toBe("15.321%")
  })

  it("respects zero decimals", () => {
    expect(formatPercent(0.5, 0)).toBe("50%")
  })

  it("formats a ratio greater than 1 (e.g. 150%)", () => {
    expect(formatPercent(1.5)).toBe("150.0%")
  })
})

describe("formatCompactNumber", () => {
  it("returns an em dash for null", () => {
    expect(formatCompactNumber(null)).toBe("—")
  })

  it("returns an em dash for undefined", () => {
    expect(formatCompactNumber(undefined)).toBe("—")
  })

  it("formats zero as '0'", () => {
    expect(formatCompactNumber(0)).toBe("0")
  })

  it("formats thousands with a 'K' suffix", () => {
    expect(formatCompactNumber(15000)).toBe("15K")
  })

  it("formats millions with an 'M' suffix", () => {
    expect(formatCompactNumber(2500000)).toBe("2.5M")
  })

  it("formats billions with a 'B' suffix", () => {
    expect(formatCompactNumber(3200000000)).toBe("3.2B")
  })

  it("formats a negative large number", () => {
    expect(formatCompactNumber(-2500000)).toBe("-2.5M")
  })

  it("formats a small number (< 1000) unchanged", () => {
    expect(formatCompactNumber(42)).toBe("42")
  })
})
