import { describe, it, expect } from "vitest"
import { alignByPeriod } from "./chartData"

describe("alignByPeriod", () => {
  it("returns empty labels and per-series empty arrays for no series", () => {
    expect(alignByPeriod([])).toEqual({ labels: [], data: [] })
  })

  it("returns a sorted label axis from a single series", () => {
    const result = alignByPeriod([
      [
        { period: "2025-Q2", value: 10 },
        { period: "2025-Q1", value: 5 },
        { period: "2025-Q3", value: 15 },
      ],
    ])
    expect(result.labels).toEqual(["2025-Q1", "2025-Q2", "2025-Q3"])
    expect(result.data).toEqual([[5, 10, 15]])
  })

  it("merges multiple series onto a shared, deduplicated, sorted label axis", () => {
    const seriesA = [
      { period: "2025-Q1", value: 1 },
      { period: "2025-Q2", value: 2 },
    ]
    const seriesB = [
      { period: "2025-Q2", value: 20 },
      { period: "2025-Q3", value: 30 },
    ]
    const result = alignByPeriod([seriesA, seriesB])

    expect(result.labels).toEqual(["2025-Q1", "2025-Q2", "2025-Q3"])
    expect(result.data).toEqual([
      [1, 2, null],
      [null, 20, 30],
    ])
  })

  it("fills gaps with null rather than misaligning points", () => {
    const seriesA = [{ period: "2020", value: 100 }]
    const seriesB = [{ period: "2021", value: 200 }]
    const result = alignByPeriod([seriesA, seriesB])

    expect(result.labels).toEqual(["2020", "2021"])
    expect(result.data).toEqual([
      [100, null],
      [null, 200],
    ])
  })

  it("handles an empty individual series alongside a populated one", () => {
    const result = alignByPeriod([[], [{ period: "2025-Q1", value: 7 }]])
    expect(result.labels).toEqual(["2025-Q1"])
    expect(result.data).toEqual([[null], [7]])
  })

  it("preserves a value of 0 rather than treating it as missing", () => {
    const result = alignByPeriod([[{ period: "2025-Q1", value: 0 }]])
    expect(result.data).toEqual([[0]])
  })

  it("last value wins when a series has a duplicate period (Map overwrite semantics)", () => {
    const series = [
      { period: "2025-Q1", value: 1 },
      { period: "2025-Q1", value: 99 },
    ]
    const result = alignByPeriod([series])
    expect(result.labels).toEqual(["2025-Q1"])
    expect(result.data).toEqual([[99]])
  })
})
