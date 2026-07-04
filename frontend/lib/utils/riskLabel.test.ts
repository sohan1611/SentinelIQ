import { describe, it, expect } from "vitest"
import { getRiskLevel, getRiskLabel } from "./riskLabel"

describe("getRiskLevel", () => {
  // Bands: 0-20 severe, 21-40 high, 41-60 moderate, 61-80 low, 81-100 strong
  it("returns 'severe' at the lower bound (0)", () => {
    expect(getRiskLevel(0)).toBe("severe")
  })

  it("returns 'severe' at the upper bound (20)", () => {
    expect(getRiskLevel(20)).toBe("severe")
  })

  it("returns 'high' just above the severe/high boundary (21)", () => {
    expect(getRiskLevel(21)).toBe("high")
  })

  it("returns 'high' at the upper bound (40)", () => {
    expect(getRiskLevel(40)).toBe("high")
  })

  it("returns 'moderate' just above the high/moderate boundary (41)", () => {
    expect(getRiskLevel(41)).toBe("moderate")
  })

  it("returns 'moderate' at the upper bound (60)", () => {
    expect(getRiskLevel(60)).toBe("moderate")
  })

  it("returns 'low' just above the moderate/low boundary (61)", () => {
    expect(getRiskLevel(61)).toBe("low")
  })

  it("returns 'low' at the upper bound (80)", () => {
    expect(getRiskLevel(80)).toBe("low")
  })

  it("returns 'strong' just above the low/strong boundary (81)", () => {
    expect(getRiskLevel(81)).toBe("strong")
  })

  it("returns 'strong' at the upper bound (100)", () => {
    expect(getRiskLevel(100)).toBe("strong")
  })

  it("falls back to 'strong' for a score above 100", () => {
    // RISK_THRESHOLDS.find() returns undefined past the last tier's max (100);
    // getRiskLevel's fallback branch (tier ? ... : "strong") covers that case.
    expect(getRiskLevel(150)).toBe("strong")
  })
})

describe("getRiskLabel", () => {
  it("returns 'Severe Risk' at the lower bound (0)", () => {
    expect(getRiskLabel(0)).toBe("Severe Risk")
  })

  it("returns 'Severe Risk' at the upper bound (20)", () => {
    expect(getRiskLabel(20)).toBe("Severe Risk")
  })

  it("returns 'High Risk' just above the severe/high boundary (21)", () => {
    expect(getRiskLabel(21)).toBe("High Risk")
  })

  it("returns 'High Risk' at the upper bound (40)", () => {
    expect(getRiskLabel(40)).toBe("High Risk")
  })

  it("returns 'Moderate Risk' just above the high/moderate boundary (41)", () => {
    expect(getRiskLabel(41)).toBe("Moderate Risk")
  })

  it("returns 'Moderate Risk' at the upper bound (60)", () => {
    expect(getRiskLabel(60)).toBe("Moderate Risk")
  })

  it("returns 'Low Risk' just above the moderate/low boundary (61)", () => {
    expect(getRiskLabel(61)).toBe("Low Risk")
  })

  it("returns 'Low Risk' at the upper bound (80)", () => {
    expect(getRiskLabel(80)).toBe("Low Risk")
  })

  it("returns 'Strong Integrity' just above the low/strong boundary (81)", () => {
    expect(getRiskLabel(81)).toBe("Strong Integrity")
  })

  it("returns 'Strong Integrity' at the upper bound (100)", () => {
    expect(getRiskLabel(100)).toBe("Strong Integrity")
  })

  it("falls back to 'Strong Integrity' for a score above 100", () => {
    expect(getRiskLabel(150)).toBe("Strong Integrity")
  })
})
