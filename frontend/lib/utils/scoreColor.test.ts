import { describe, it, expect } from "vitest"
import { getScoreColor, getScoreTint } from "./scoreColor"
import { RISK_COLORS, RISK_TINTS } from "@/lib/constants/riskThresholds"

describe("getScoreColor", () => {
  // Bands: 0-20 severe, 21-40 high, 41-60 moderate, 61-80 low, 81-100 strong
  it("returns the severe color at the lower bound (0)", () => {
    expect(getScoreColor(0)).toBe(RISK_COLORS.severe)
  })

  it("returns the severe color at the upper bound (20)", () => {
    expect(getScoreColor(20)).toBe(RISK_COLORS.severe)
  })

  it("returns the high color just above the severe/high boundary (21)", () => {
    expect(getScoreColor(21)).toBe(RISK_COLORS.high)
  })

  it("returns the high color at the upper bound (40)", () => {
    expect(getScoreColor(40)).toBe(RISK_COLORS.high)
  })

  it("returns the moderate color just above the high/moderate boundary (41)", () => {
    expect(getScoreColor(41)).toBe(RISK_COLORS.moderate)
  })

  it("returns the moderate color at the upper bound (60)", () => {
    expect(getScoreColor(60)).toBe(RISK_COLORS.moderate)
  })

  it("returns the low color just above the moderate/low boundary (61)", () => {
    expect(getScoreColor(61)).toBe(RISK_COLORS.low)
  })

  it("returns the low color at the upper bound (80)", () => {
    expect(getScoreColor(80)).toBe(RISK_COLORS.low)
  })

  it("returns the strong color just above the low/strong boundary (81)", () => {
    expect(getScoreColor(81)).toBe(RISK_COLORS.strong)
  })

  it("returns the strong color at the upper bound (100)", () => {
    expect(getScoreColor(100)).toBe(RISK_COLORS.strong)
  })

  it("matches the exact design-system hex values", () => {
    expect(getScoreColor(10)).toBe("#6E1010")
    expect(getScoreColor(30)).toBe("#B03028")
    expect(getScoreColor(50)).toBe("#C47A14")
    expect(getScoreColor(70)).toBe("#1C3558")
    expect(getScoreColor(90)).toBe("#1A6B3C")
  })
})

describe("getScoreTint", () => {
  it("returns the severe tint at the lower bound (0)", () => {
    expect(getScoreTint(0)).toBe(RISK_TINTS.severe)
  })

  it("returns the severe tint at the upper bound (20)", () => {
    expect(getScoreTint(20)).toBe(RISK_TINTS.severe)
  })

  it("returns the high tint just above the severe/high boundary (21)", () => {
    expect(getScoreTint(21)).toBe(RISK_TINTS.high)
  })

  it("returns the high tint at the upper bound (40)", () => {
    expect(getScoreTint(40)).toBe(RISK_TINTS.high)
  })

  it("returns the moderate tint just above the high/moderate boundary (41)", () => {
    expect(getScoreTint(41)).toBe(RISK_TINTS.moderate)
  })

  it("returns the moderate tint at the upper bound (60)", () => {
    expect(getScoreTint(60)).toBe(RISK_TINTS.moderate)
  })

  it("returns the low tint just above the moderate/low boundary (61)", () => {
    expect(getScoreTint(61)).toBe(RISK_TINTS.low)
  })

  it("returns the low tint at the upper bound (80)", () => {
    expect(getScoreTint(80)).toBe(RISK_TINTS.low)
  })

  it("returns the strong tint just above the low/strong boundary (81)", () => {
    expect(getScoreTint(81)).toBe(RISK_TINTS.strong)
  })

  it("returns the strong tint at the upper bound (100)", () => {
    expect(getScoreTint(100)).toBe(RISK_TINTS.strong)
  })

  it("matches the exact design-system hex values", () => {
    expect(getScoreTint(10)).toBe("#F5DADA")
    expect(getScoreTint(30)).toBe("#FAE8E8")
    expect(getScoreTint(50)).toBe("#FDF2DC")
    expect(getScoreTint(70)).toBe("#E4F2EB")
    expect(getScoreTint(90)).toBe("#D6EDE0")
  })
})
