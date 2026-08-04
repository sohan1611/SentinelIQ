import { describe, it, expect } from "vitest"
import { normalizeSeverity, flagDate, getFlagEvidence } from "./redFlag"
import type { ModuleDetails, RedFlag } from "@/types/analysis"

function makeFlag(overrides: Partial<RedFlag> = {}): RedFlag {
  return {
    id: "flag-1",
    flag_type: "revenue",
    severity: "high",
    description: "Revenue/OCF divergence detected",
    period: "2025-Q4",
    event_date: null,
    ...overrides,
  }
}

describe("normalizeSeverity", () => {
  it("passes through 'severe' unchanged", () => {
    expect(normalizeSeverity("severe")).toBe("severe")
  })

  it("passes through 'high' unchanged", () => {
    expect(normalizeSeverity("high")).toBe("high")
  })

  it("passes through 'moderate' unchanged", () => {
    expect(normalizeSeverity("moderate")).toBe("moderate")
  })

  it("lowercases a mixed-case known severity", () => {
    expect(normalizeSeverity("HIGH")).toBe("high")
    expect(normalizeSeverity("Severe")).toBe("severe")
  })

  it("falls back to 'moderate' for an unknown severity", () => {
    expect(normalizeSeverity("critical")).toBe("moderate")
    expect(normalizeSeverity("")).toBe("moderate")
    expect(normalizeSeverity("low")).toBe("moderate")
  })
})

describe("flagDate", () => {
  it("formats event_date via formatDate when present", () => {
    const flag = makeFlag({ event_date: "2026-06-18T02:00:00Z", period: "2025-Q4" })
    expect(flagDate(flag)).toBe("Jun 18, 2026")
  })

  it("falls back to the period string when event_date is null", () => {
    const flag = makeFlag({ event_date: null, period: "2025-Q4" })
    expect(flagDate(flag)).toBe("2025-Q4")
  })

  it("falls back to an em dash when both event_date and period are null", () => {
    const flag = makeFlag({ event_date: null, period: null })
    expect(flagDate(flag)).toBe("—")
  })
})

describe("getFlagEvidence", () => {
  it("returns [] when moduleDetails is null", () => {
    expect(getFlagEvidence(makeFlag(), null)).toEqual([])
  })

  it("returns [] when moduleDetails is undefined", () => {
    expect(getFlagEvidence(makeFlag(), undefined)).toEqual([])
  })

  it("returns [] when moduleDetails has no matching period for a revenue flag", () => {
    const details: ModuleDetails = {
      revenue: {
        divergences: [{ period: "2024-Q1", divergence: 0.22 }],
        recv_ratios: [],
      },
    }
    const flag = makeFlag({ flag_type: "revenue", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([])
  })

  it("returns [] for an unrecognized flag_type", () => {
    const details: ModuleDetails = {
      revenue: { divergences: [{ period: "2025-Q4", divergence: 0.22 }] },
    }
    const flag = makeFlag({ flag_type: "unknown_type", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([])
  })

  it("maps a 'revenue' flag to divergence and receivables-ratio rows", () => {
    const details: ModuleDetails = {
      revenue: {
        divergences: [{ period: "2025-Q4", divergence: 0.225 }],
        recv_ratios: [{ period: "2025-Q4", recv_ratio: 0.183 }],
      },
    }
    const flag = makeFlag({ flag_type: "revenue", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Revenue/OCF Divergence", value: "22.5%" },
      { label: "Receivables / Revenue", value: "18.3%" },
    ])
  })

  it("maps a 'revenue' flag with only a divergence row (no recv_ratio match)", () => {
    const details: ModuleDetails = {
      revenue: {
        divergences: [{ period: "2025-Q4", divergence: 0.1 }],
        recv_ratios: [{ period: "2024-Q1", recv_ratio: 0.5 }],
      },
    }
    const flag = makeFlag({ flag_type: "revenue", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Revenue/OCF Divergence", value: "10.0%" },
    ])
  })

  it("maps a 'cash_flow' flag to accrual ratio AND debt metric rows (both series checked)", () => {
    const details: ModuleDetails = {
      cashflow: {
        accrual_ratios: [{ period: "2025-Q4", accrual_ratio: 0.12 }],
      },
      debt: {
        debt_metrics: [
          { period: "2025-Q4", debt_to_revenue: 1.256, debt_growth: 0.31, interest_coverage: 1.5 },
        ],
      },
    }
    const flag = makeFlag({ flag_type: "cash_flow", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Accrual Ratio (Sloan)", value: "12.0%" },
      { label: "Debt / Revenue", value: "1.26x" },
      { label: "Debt Growth (YoY)", value: "31.0%" },
      { label: "Interest Coverage", value: "1.50x" },
    ])
  })

  it("omits the Interest Coverage row for a 'cash_flow' flag when interest_coverage is null", () => {
    const details: ModuleDetails = {
      debt: {
        debt_metrics: [
          { period: "2025-Q4", debt_to_revenue: 2.0, debt_growth: 0.5, interest_coverage: null },
        ],
      },
    }
    const flag = makeFlag({ flag_type: "cash_flow", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Debt / Revenue", value: "2.00x" },
      { label: "Debt Growth (YoY)", value: "50.0%" },
    ])
  })

  it("maps an 'earnings' flag to gross margin and net income rows", () => {
    const details: ModuleDetails = {
      earnings: {
        margins: [{ period: "2025-Q4", gross_margin: 0.42 }],
        net_incomes: [{ period: "2025-Q4", net_income: 2500000 }],
      },
    }
    const flag = makeFlag({ flag_type: "earnings", period: "2025-Q4" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Gross Margin", value: "42.0%" },
      { label: "Net Income", value: "2.5M" },
    ])
  })

  it("maps a 'governance' flag to Source/AI Model rows when provenance has a model_id", () => {
    const details: ModuleDetails = {
      governance: {
        provenance: {
          model_id: "gemini-2.5-flash",
          prompt: "some prompt",
          raw_response: null,
          low_confidence: false,
        },
        flags: [],
      },
    }
    const flag = makeFlag({ flag_type: "governance", period: null, description: "SEC inquiry disclosed" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Source", value: "Recent news coverage" },
      { label: "AI Model", value: "gemini-2.5-flash" },
    ])
  })

  it("adds an AI Characterization row when a matching governance flag has ai_summary", () => {
    const details: ModuleDetails = {
      governance: {
        provenance: {
          model_id: "gemini-2.5-flash",
          prompt: "some prompt",
          raw_response: null,
          low_confidence: false,
        },
        flags: [
          {
            flag_type: "governance",
            severity: "high",
            description: "SEC inquiry disclosed",
            period: null,
            source_quote: "quoted text",
            ai_summary: "Regulatory scrutiny increasing",
          },
        ],
      },
    }
    const flag = makeFlag({ flag_type: "governance", period: null, description: "SEC inquiry disclosed" })
    expect(getFlagEvidence(flag, details)).toEqual([
      { label: "Source", value: "Recent news coverage" },
      { label: "AI Model", value: "gemini-2.5-flash" },
      { label: "AI Characterization", value: "Regulatory scrutiny increasing" },
    ])
  })

  it("returns [] for a 'governance' flag when provenance.model_id is absent (guarded)", () => {
    const details: ModuleDetails = {
      governance: {
        provenance: {
          model_id: null,
          prompt: null,
          raw_response: null,
          low_confidence: true,
        },
        flags: [],
      },
    }
    const flag = makeFlag({ flag_type: "governance", period: null })
    expect(getFlagEvidence(flag, details)).toEqual([])
  })

  it("returns [] when module_details is entirely empty for the flag's module", () => {
    const flag = makeFlag({ flag_type: "earnings", period: "2025-Q4" })
    expect(getFlagEvidence(flag, {})).toEqual([])
  })
})
