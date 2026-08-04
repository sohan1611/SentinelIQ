import { describe, it, expect } from "vitest"
import { buildForensicsCsv } from "./exportCsv"
import type { ModuleDetails } from "@/types/analysis"

describe("buildForensicsCsv", () => {
  it("emits only the header block plus a fallback message when there is no series data", () => {
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", null)
    expect(csv).toBe(
      "Forensic Data Export\nTicker,Generated At\nACME,2026-07-05T00:00:00Z\n\nNo forensic series data is available for this analysis.\n"
    )
  })

  it("emits only the header block when moduleDetails is undefined", () => {
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", undefined)
    expect(csv).toContain("No forensic series data is available for this analysis.")
  })

  it("emits only the header block when moduleDetails is an empty object", () => {
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", {})
    expect(csv).toContain("No forensic series data is available for this analysis.")
  })

  it("includes a Revenue/OCF Divergence block when divergences are present", () => {
    const details: ModuleDetails = {
      revenue: { divergences: [{ period: "2025-Q4", divergence: 0.225 }] },
    }
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", details)
    expect(csv).toContain("Revenue / OCF Growth Divergence\nPeriod,Divergence\n2025-Q4,0.225")
    expect(csv).not.toContain("No forensic series data is available")
  })

  it("includes a Debt Metrics block with a blank field for a null interest_coverage", () => {
    const details: ModuleDetails = {
      debt: {
        debt_metrics: [
          { period: "2025-Q4", debt_to_revenue: 1.2, debt_growth: 0.3, interest_coverage: null },
        ],
      },
    }
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", details)
    expect(csv).toContain("Debt Metrics\nPeriod,Debt to Revenue,Debt Growth,Interest Coverage\n2025-Q4,1.2,0.3,")
  })

  it("includes multiple blocks in the fixed section order when several are present", () => {
    const details: ModuleDetails = {
      revenue: {
        divergences: [{ period: "2025-Q4", divergence: 0.1 }],
        recv_ratios: [{ period: "2025-Q4", recv_ratio: 0.2 }],
      },
      earnings: {
        margins: [{ period: "2025-Q4", gross_margin: 0.4 }],
      },
    }
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", details)
    const revenueIdx = csv.indexOf("Revenue / OCF Growth Divergence")
    const recvIdx = csv.indexOf("Receivables Ratio")
    const marginIdx = csv.indexOf("Gross Margin")
    expect(revenueIdx).toBeGreaterThan(-1)
    expect(recvIdx).toBeGreaterThan(revenueIdx)
    expect(marginIdx).toBeGreaterThan(recvIdx)
  })

  it("escapes a field containing a comma by quoting it", () => {
    // Ticker is attacker/user-adjacent input; verify the CSV-escaping helper
    // is actually applied to the header row's own values.
    const csv = buildForensicsCsv("ACME, Inc", "2026-07-05T00:00:00Z", null)
    expect(csv).toContain('"ACME, Inc"')
  })

  it("escapes a field containing double quotes by doubling them", () => {
    const csv = buildForensicsCsv('ACME "Corp"', "2026-07-05T00:00:00Z", null)
    expect(csv).toContain('"ACME ""Corp"""')
  })

  it("leaves a plain alphanumeric field unquoted", () => {
    const csv = buildForensicsCsv("ACME", "2026-07-05T00:00:00Z", null)
    expect(csv).toContain("ACME,2026-07-05T00:00:00Z")
  })
})
