"use client"

import * as React from "react"
import {
  Chart as ChartJS,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
} from "chart.js"
import { Bar } from "react-chartjs-2"
import { ChartFrame } from "@/components/ui/ChartFrame"
import { baseChartOptions } from "@/lib/theme/chartOptions"
import { formatPercent } from "@/lib/utils/formatNumber"
import { getScoreColor } from "@/lib/utils/scoreColor"
import type { AccrualRatioPoint } from "@/types/analysis"

ChartJS.register(BarElement, LinearScale, CategoryScale, Tooltip)

// Sloan Accrual Ratio score bands — CLAUDE.md Forensics Engine, Module B.
function accrualRatioScore(ratio: number): number {
  if (ratio < 0.05) return 100
  if (ratio <= 0.10) return 70
  if (ratio <= 0.15) return 45
  return 20
}

export interface CashFlowChartProps {
  accrualRatios: AccrualRatioPoint[];
  actions?: React.ReactNode;
}

export function CashFlowChart({ accrualRatios, actions }: CashFlowChartProps) {
  if (accrualRatios.length === 0) {
    return (
      <ChartFrame title="Cash Flow Integrity" subtitle="Sloan accrual ratio by period" actions={actions}>
        <div className="flex items-center justify-center h-full font-sans text-sm text-text-muted text-center px-6">
          Not enough financial history to compute the accrual ratio.
        </div>
      </ChartFrame>
    )
  }

  const sorted = [...accrualRatios].sort((a, b) => a.period.localeCompare(b.period))

  const chartData = {
    labels: sorted.map((p) => p.period),
    datasets: [
      {
        label: "Sloan Accrual Ratio",
        data: sorted.map((p) => p.accrual_ratio),
        backgroundColor: sorted.map((p) => getScoreColor(accrualRatioScore(p.accrual_ratio))),
        borderRadius: 2,
        maxBarThickness: 48,
      },
    ],
  }

  const options = baseChartOptions<"bar">(
    (v) => formatPercent(v, 0),
    (ctx) => `Accrual ratio: ${formatPercent(ctx.parsed.y, 1)}`
  )
  options.plugins = { ...options.plugins, legend: { display: false } }

  return (
    <ChartFrame title="Cash Flow Integrity" subtitle="Sloan accrual ratio by period — lower is better" actions={actions}>
      <Bar data={chartData} options={options} />
    </ChartFrame>
  )
}
